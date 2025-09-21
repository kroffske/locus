"""Dependency Injection container for wiring components."""
from __future__ import annotations

import logging

from locus.search.engine import CodeSearchEngine

from ..settings.settings import Settings, load_settings

logger = logging.getLogger(__name__)


class Container:
    """Manages instantiation and wiring of components."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._embedding_component = None
        self._vector_store = None
        self._ingest_component = None
        self._code_search_engine = None

    def embedding_component(self):
        if self._embedding_component is None:
            from ..components.embedding.embedding_component import EmbeddingComponent

            cfg = self._settings.embedding
            logger.debug(f"Initializing EmbeddingComponent with model: {cfg.model_name}")
            self._embedding_component = EmbeddingComponent(
                model_name=cfg.model_name, trust_remote_code=cfg.trust_remote_code
            )
        return self._embedding_component

    def vector_store(self):
        if self._vector_store is None:
            from ..components.vector_store.lancedb_store import LanceDBVectorStore

            cfg = self._settings.vector_store
            logger.debug(f"Initializing LanceDBVectorStore at path: {cfg.path}")
            self._vector_store = LanceDBVectorStore(db_path=cfg.path)
        return self._vector_store

    def ingest_component(self):
        if self._ingest_component is None:
            from ..components.ingest.code_ingest_component import CodeIngestComponent

            self._ingest_component = CodeIngestComponent(
                embed_component=self.embedding_component(),
                vector_store=self.vector_store(),
            )
        return self._ingest_component

    def code_search_engine(self) -> CodeSearchEngine:
        if self._code_search_engine is None:
            self._code_search_engine = CodeSearchEngine(
                store=self.vector_store(), embedder=self.embedding_component()
            )
        return self._code_search_engine


_container_instance = None


def get_container() -> Container:
    """Global factory for the DI container."""
    global _container_instance
    if _container_instance is None:
        settings = load_settings()
        _container_instance = Container(settings)
    return _container_instance
