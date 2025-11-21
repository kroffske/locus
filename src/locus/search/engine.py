from __future__ import annotations

from typing import Any, Dict, List

from locus.search.interfaces import Embedder, VectorStore


class CodeSearchEngine:
    """Orchestrates hybrid code search using abstract embedder and vector store components."""

    def __init__(self, store: VectorStore, embedder: Embedder):
        """Initializes the search engine with its dependencies."""
        self.store = store
        self.embedder = embedder

    def search(
        self,
        query: str,
        k: int = 10,
        where: str | None = None,
        identifiers: List[str] | None = None,
    ) -> List[Dict[str, Any]]:
        """Performs a hybrid search and returns normalized results."""
        query_vector = self.embedder.embed_query(query)
        semantic_hits = self.store.query(query_vector, k, where)

        if identifiers:
            keyword_hits = self.store.keyword(identifiers, k, where)
            merged_hits = self._merge(semantic_hits, keyword_hits, k)
            return self._normalize(merged_hits)

        return self._normalize(semantic_hits)

    def _merge(
        self, semantic_hits: List[Dict], keyword_hits: List[Dict], k: int
    ) -> List[Dict]:
        """Merges and de-duplicates semantic and keyword search results."""
        seen_ids = set()
        merged = []
        for hit in semantic_hits + keyword_hits:
            chunk_id = hit.get("chunk_id")
            if chunk_id and chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                merged.append(hit)
        return merged[: (k * 2)]

    def _normalize(self, rows: List[Dict]) -> List[Dict[str, Any]]:
        """Normalizes vector store results to a common, serializable shape."""
        normalized = []
        for row in rows:
            normalized.append(
                {
                    "path": row.get("rel_path"),
                    "start": row.get("start_line"),
                    "end": row.get("end_line"),
                    "text": row.get("text"),
                    "score": row.get("_distance", 0.0),
                }
            )
        return normalized
