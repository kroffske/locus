"""Main entry point for the Locus MCP server."""
import argparse
import logging
import sys

from locus.formatting.colors import setup_rich_logging

from .di.container import get_container

logger = logging.getLogger(__name__)


def check_deps() -> bool:
    """Check for required MCP dependencies and log missing ones."""
    missing = []
    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        missing.append("sentence-transformers")
    try:
        import lancedb  # noqa: F401
    except ImportError:
        missing.append("lancedb")
    try:
        import fastmcp  # noqa: F401
    except ImportError:
        missing.append("fastmcp")

    if missing:
        logger.error(f"Missing dependencies for MCP: {', '.join(missing)}")
        logger.error("Install with: pip install 'locus-analyzer[mcp]'")
        return False
    return True


def main():
    """Parses arguments and launches the MCP server."""
    # Setup logging immediately
    setup_rich_logging()

    parser = argparse.ArgumentParser(description="Locus MCP Server")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_parser = subparsers.add_parser("serve", help="Run the MCP server")
    serve_parser.add_argument(
        "--transport", choices=["stdio", "http"], default="stdio", help="Server transport"
    )

    index_parser = subparsers.add_parser("index", help="Index a codebase")
    index_parser.add_argument("paths", nargs="+", help="Paths to index")
    index_parser.add_argument(
        "--force", action="store_true", help="Force re-indexing of existing files"
    )

    args = parser.parse_args()

    if not check_deps():
        sys.exit(1)

    container = get_container()

    if args.command == "serve":
        logger.info(f"Starting Locus MCP server via {args.transport}...")
        # Lazy import of server to avoid loading heavy deps unless serving
        from .server import mcp_app

        if args.transport == "stdio":
            mcp_app.run_stdio()
        else:
            logger.error("HTTP transport not yet implemented.")
            sys.exit(1)

    elif args.command == "index":
        logger.info(f"Indexing paths: {args.paths}...")
        ingest_component = container.ingest_component()
        results = ingest_component.index_paths(args.paths, force_rebuild=args.force)
        logger.info(
            f"Indexing complete. Files processed: {results['files']}, Chunks created: {results['chunks']}"
        )
