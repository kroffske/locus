from __future__ import annotations

from typing import Any, Dict, List


class CodeChunkModel:
    # This is a placeholder for the Pydantic model.
    # We define it lazily to avoid a hard dependency on lancedb at the module level.
    pass


class LanceDBVectorStore:
    """Adapter for LanceDB vector store with lazy imports."""

    def __init__(self, db_path: str, table_name: str = "code_chunks"):
        try:
            import lancedb
            from lancedb.pydantic import LanceModel, Vector
        except ImportError:
            raise ImportError(
                "LanceDB is not installed. Please install with: pip install 'locus-analyzer[mcp]'"
            )

        # Define schema class inside the constructor
        class CodeChunkSchema(LanceModel):
            chunk_id: str
            repo_root: str
            rel_path: str
            language: str | None
            symbols: List[str] | None
            start_line: int
            end_line: int
            text: str
            vector: Vector(1024)  # For nomic-ai/CodeRankEmbed-v1

        # Assign the dynamically created class to the placeholder
        global CodeChunkModel
        CodeChunkModel = CodeChunkSchema

        self.db = lancedb.connect(db_path)
        self.table = self.db.create_table(
            table_name, schema=CodeChunkSchema, mode="overwrite_if_exists"
        )

    def upsert(self, rows: List[CodeChunkModel]) -> None:
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

    def keyword(
        self, terms: List[str], k: int, where: str | None = None
    ) -> List[Dict]:
        if not terms:
            return []
        predicate = " AND ".join([f"text LIKE '%{term}%'" for term in terms])
        if where:
            predicate = f"({where}) AND ({predicate})"
        return self.table.search().where(predicate).limit(k).to_list()

    def get_file(self, rel_path: str) -> List[Dict[str, Any]]:
        return self.table.search().where(f"rel_path == '{rel_path}'").to_list()
