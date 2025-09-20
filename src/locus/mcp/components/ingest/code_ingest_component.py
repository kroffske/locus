from __future__ import annotations

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

    def index_paths(
        self, paths: List[str], force_rebuild: bool = False
    ) -> dict:
        """Indexes all allowed files found in the given paths."""
        config_root = os.path.abspath(paths[0])
        ignore, allow = config.load_project_config(config_root)
        results = {"files": 0, "chunks": 0}

        for path in paths:
            files_to_index = scanner.scan_directory(os.path.abspath(path), ignore, allow)

            for abs_path in files_to_index:
                rel_path = os.path.relpath(abs_path, config_root).replace("\\", "/")
                if force_rebuild:
                    self.vector_store.delete_by_file(rel_path)
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    chunks = chunk_file(content)
                    if not chunks:
                        continue

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
                    results["files"] += 1
                    results["chunks"] += len(rows)
                except Exception:
                    logger.warning(f"Failed to index file: {abs_path}", exc_info=True)
        return results
