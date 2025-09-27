from __future__ import annotations

from typing import List

from ...di.container import get_container


def search_codebase(
    query: str,
    k: int = 10,
    path_glob: str | None = None,
    identifiers: List[str] | None = None,
) -> List[dict]:
    """Find top-K relevant code snippets using hybrid retrieval."""
    try:
        from mcp import TextContent
    except ImportError:
        raise ImportError("MCP types not found. Please install with: pip install 'locus-analyzer[mcp]'")

    container = get_container()
    engine = container.code_search_engine()

    where = None
    if path_glob:
        where = f"rel_path GLOB '{path_glob}'"

    try:
        hits = engine.search(query, k=k, where=where, identifiers=identifiers)
        if not hits:
            return [TextContent(text="No relevant code snippets found.")]

        output_blocks = []
        for hit in hits:
            header = f"File: {hit['path']} (L{hit['start']}-{hit['end']}) score={hit['score']:.4f}"
            code_block = f"```\n{hit['text']}\n```"
            output_blocks.append(TextContent(text=f"{header}\n{code_block}"))
        return output_blocks
    except Exception as e:
        return [TextContent(text=f"Error during search: {e}")]
