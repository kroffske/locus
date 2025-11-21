from __future__ import annotations

from typing import List

from ...di.container import get_container


async def index_paths(paths: List[str], force_rebuild: bool = False) -> List[dict]:
    """Index or re-index a set of paths (folders or files)."""
    try:
        from mcp import TextContent
    except ImportError:
        raise ImportError(
            "MCP types not found. Please install with: pip install 'locus-analyzer[mcp]'"
        )

    container = get_container()
    ingest_component = container.ingest_component()

    try:
        results = await ingest_component.index_paths(paths, force_rebuild)
        summary = (
            f"Indexing complete. Processed {results['files']} files, "
            f"created {results['chunks']} chunks."
        )
        return [TextContent(text=summary)]
    except Exception as e:
        return [TextContent(text=f"Error during indexing: {e}")]
