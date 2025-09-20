def get_mcp_app():
    try:
        from fastmcp import FastMCP
    except ImportError:
        raise ImportError(
            "FastMCP is not installed. Please install with: pip install 'locus-analyzer[mcp]'"
        )

    from .tools.get_file_context import get_file_context
    from .tools.index_control import index_paths
    from .tools.search_codebase import search_codebase

    mcp = FastMCP("locus-mcp-v1")
    mcp.tool()(search_codebase)
    mcp.tool()(get_file_context)
    mcp.tool()(index_paths)
    return mcp

def run_stdio():
    """Run the MCP server over standard I/O."""
    app = get_mcp_app()
    app.run_stdio()
