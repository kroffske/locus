from __future__ import annotations

from typing import Any, Dict, List, Type

DEFAULT_VECTOR_DIMENSIONS = 1024


def _create_code_chunk_schema(dimensions: int):
    """Build a LanceDB schema for stored code chunks."""
    try:
        from lancedb.pydantic import LanceModel, Vector  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ImportError(
            "LanceDB is not installed. Please install with: pip install 'locus-analyzer[mcp]'"
        ) from exc

    class CodeChunkSchema(LanceModel):  # type: ignore[misc,valid-type]
        chunk_id: str
        repo_root: str
        rel_path: str
        language: str | None
        symbols: List[str] | None
        start_line: int
        end_line: int
        text: str
        vector: Vector(dimensions)  # type: ignore[call-arg]

    return CodeChunkSchema


try:
    CodeChunkModel = _create_code_chunk_schema(DEFAULT_VECTOR_DIMENSIONS)
except ImportError:
    CodeChunkModel = None


class LanceDBVectorStore:
    """Adapter for LanceDB vector store with configurable vector dimensions."""

    def __init__(
        self,
        db_path: str,
        table_name: str = "code_chunks",
        *,
        dimensions: int = DEFAULT_VECTOR_DIMENSIONS,
    ) -> None:
        try:
            import lancedb  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ImportError(
                "LanceDB is not installed. Please install with: pip install 'locus-analyzer[mcp]'"
            ) from exc

        self.db_path = db_path
        self.table_name = table_name
        self.dimensions = dimensions

        self.db = lancedb.connect(db_path)  # type: ignore[attr-defined]
        self.table = self.db.create_table(  # type: ignore[call-arg]
            table_name,
            schema=self._resolve_schema(dimensions),
            mode="overwrite_if_exists",
        )

    def _resolve_schema(self, dimensions: int) -> Type[Any]:
        """Return a LanceDB schema class for the requested dimensions."""
        if CodeChunkModel is not None and dimensions == DEFAULT_VECTOR_DIMENSIONS:
            return CodeChunkModel
        return _create_code_chunk_schema(dimensions)

    def upsert(self, rows: List[Any]) -> None:
        if not rows:
            return
        self.table.add(rows)

    def delete_by_file(self, rel_path: str) -> None:
        self.table.delete(f"rel_path == '{rel_path}'")

    def query(
        self, query_vec: List[float], k: int, where: str | None = None
    ) -> List[Dict]:
        q = self.table.search(query_vec)
        if where:
            q = q.where(where)
        return q.limit(k).to_list()

    def keyword(self, terms: List[str], k: int, where: str | None = None) -> List[Dict]:
        if not terms:
            return []
        predicate = " AND ".join([f"text LIKE '%{term}%'" for term in terms])
        if where:
            predicate = f"({where}) AND ({predicate})"
        return self.table.search().where(predicate).limit(k).to_list()

    def get_file(self, rel_path: str) -> List[Dict[str, Any]]:
        return self.table.search().where(f"rel_path == '{rel_path}'").to_list()
