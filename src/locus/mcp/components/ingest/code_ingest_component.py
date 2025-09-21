from __future__ import annotations

import asyncio
import logging
import os
from typing import List

from locus.core import scanner
from locus.utils import config

from ..embedding.embedding_component import EmbeddingComponent
from ..vector_store.lancedb_store import CodeChunkModel, LanceDBVectorStore
from .chunking import chunk_file

logger = logging.getLogger(__name__)


class CodeIngestComponent:
    """Orchestrates scanning, chunking, embedding, and storing code."""

    def __init__(self, embed_component: EmbeddingComponent, vector_store: LanceDBVectorStore):
        self.embed_component = embed_component
        self.vector_store = vector_store

    async def index_paths(
        self, paths: List[str], force_rebuild: bool = False
    ) -> dict:
        """Indexes all allowed files found in the given paths asynchronously."""
        config_root = os.path.abspath(paths[0])
        ignore, allow = config.load_project_config(config_root)
        results = {"files": 0, "chunks": 0}

        for path in paths:
            files_to_index = scanner.scan_directory(os.path.abspath(path), ignore, allow)

            tasks = []
            for abs_path in files_to_index:
                tasks.append(self._process_file(abs_path, config_root, force_rebuild))
            file_results = await asyncio.gather(*tasks, return_exceptions=True)

            for res in file_results:
                if isinstance(res, Exception):
                    logger.warning(f"Failed to index file: {res}")
                    continue
                if res:
                    results["files"] += 1
                    results["chunks"] += res

        return results

    async def _process_file(self, abs_path: str, config_root: str, force_rebuild: bool) -> int:
        rel_path = os.path.relpath(abs_path, config_root).replace("\\", "/")
        if force_rebuild:
            self.vector_store.delete_by_file(rel_path)
        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            chunks = chunk_file(content)
            if not chunks:
                return 0

            vectors = self.embed_component.embed_chunks([c.text for c in chunks])
            rows = []
            for chunk, vec in zip(chunks, vectors):
                rows.append(
                    CodeChunkModel(
                        chunk_id=chunk.id,
                        repo_root=config_root,
                        rel_path=rel_path,
                        start_line=chunk.start,
                        end_line=chunk.end,
                        text=chunk.text,
                        vector=vec,
                        language="python", # Placeholder
                        symbols=[], # Placeholder
                    )
                )
            self.vector_store.upsert(rows)
            return len(rows)
        except Exception as e:
            logger.warning(f"Failed to index file {abs_path}: {e}", exc_info=True)
            return 0
