"""Color utilities and themes for terminal output using Rich."""

import logging
import os
import sys

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Check if colors should be disabled
NO_COLOR = os.environ.get("NO_COLOR") or not sys.stdout.isatty()

# Define custom theme
LOCUS_THEME = Theme(
    {
        "header": "bold cyan",
        "subheader": "bold blue",
        "filepath": "blue",
        "create": "bold green",
        "update": "bold yellow",
        "delete": "bold red",
        "success": "green",
        "error": "bold red",
        "warning": "yellow",
        "info": "blue",
        "prompt": "bold magenta",
        "tree": "cyan",
        "comment": "dim italic",
        "divider": "dim white",
    }
)

# Create console instance
console = Console(
    theme=LOCUS_THEME,
    force_terminal=not NO_COLOR,
    no_color=NO_COLOR,
    legacy_windows=False,  # Use modern Windows terminal features
    force_jupyter=False,
)


def setup_rich_logging(level="INFO", log_file=None):
    """Setup logging with Rich handler for colored output."""
    # Configure rich handler
    rich_handler = RichHandler(
        console=console,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
    )

    handlers = [rich_handler]

    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        handlers.append(file_handler)

    logging.basicConfig(
        level=getattr(logging, level),
        format="%(message)s",
        handlers=handlers,
        force=True,
    )


def print_header(text: str):
    """Print a main header."""
    console.print(f"\n[header]{text}[/header]")


def print_subheader(text: str):
    """Print a subheader."""
    console.print(f"[subheader]{text}[/subheader]")


def print_divider():
    """Print a divider line."""
    # Use simple dashes for better compatibility
    console.print("[divider]" + "-" * 60 + "[/divider]")


def print_file_status(status: str, filepath: str):
    """Print file status with appropriate color."""
    status_styles = {
        "CREATE": "create",
        "UPDATE": "update",
        "DELETE": "delete",
        "CREATED": "create",
        "UPDATED": "update",
        "DELETED": "delete",
    }
    style = status_styles.get(status.upper(), "info")
    console.print(f"  [{style}]- {status}:[/{style}] [filepath]{filepath}[/filepath]")


def print_success(message: str):
    """Print a success message."""
    console.print(f"[success][OK] {message}[/success]")


def print_error(message: str):
    """Print an error message."""
    console.print(f"[error][ERROR] {message}[/error]")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"[warning][WARN] {message}[/warning]")


def print_info(message: str):
    """Print an info message."""
    console.print(f"[info]{message}[/info]")


def prompt(text: str, default=None):
    """Show a colored prompt and get user input."""
    if default:
        prompt_text = f"[prompt]{text} [{default}]:[/prompt] "
    else:
        prompt_text = f"[prompt]{text}:[/prompt] "

    return console.input(prompt_text).strip() or default


def confirm(text: str):
    """Show a yes/no confirmation prompt."""
    response = console.input(f"[prompt]{text} [y/N]:[/prompt] ").lower().strip()
    return response == "y"
