"""Shim for the 'locus mcp' subcommand."""

import sys


def main():
    """Entry point for the 'mcp' command."""
    try:
        # This will only succeed if 'locus[mcp]' extras are installed
        from locus.mcp.launcher import main as run_mcp
    except ImportError as e:
        print(
            "MCP server functionality is an optional feature and its dependencies are not installed.",
            file=sys.stderr,
        )
        print(
            "Please install it with: pip install 'locus-analyzer[mcp]'",
            file=sys.stderr,
        )
        print(f"(Original error: {e})", file=sys.stderr)
        sys.exit(1)

    # Pass any arguments after 'locus mcp' to the mcp launcher
    # e.g., 'locus mcp serve' -> sys.argv becomes ['locus-mcp', 'serve']
    sys.argv = ["locus-mcp"] + sys.argv[2:]
    run_mcp()
