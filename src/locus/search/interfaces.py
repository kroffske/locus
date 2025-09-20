from __future__ import annotations

from typing import Any, Dict, Iterable, List, Protocol


class VectorStore(Protocol):
    """Defines the contract for a vector storage and retrieval system."""

    def query(
        self, query_vec: List[float], k: int, where: str | None = None
    ) -> List[Dict]: ...

    def keyword(
        self, terms: List[str], k: int, where: str | None = None
    ) -> List[Dict]: ...

    def get_file(self, rel_path: str) -> Iterable[Dict]: ...


class Embedder(Protocol):
    """Defines the contract for an embedding model."""

    def embed_query(self, query: str) -> List[float]: ...

    def embed_texts(self, texts: List[str]) -> List[List[float]]: ...
