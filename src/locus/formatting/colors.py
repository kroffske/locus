"""Color utilities and themes for terminal output using Rich."""

import logging
import os
import sys

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Best-effort UTF-8 stdout on Windows consoles to avoid encode errors
try:
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

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
    legacy_windows=False,
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

    logging.basicConfig(level=getattr(logging, level), format="%(message)s", handlers=handlers, force=True)


def _safe_print(renderable: str):
    try:
        console.print(renderable)
    except UnicodeEncodeError:
        # Fallback to basic print without styles
        try:
            # Strip simple Rich tags
            plain = renderable.replace("[header]", "").replace("[/header]", "")
            plain = plain.replace("[subheader]", "").replace("[/subheader]", "")
            plain = plain.replace("[divider]", "").replace("[/divider]", "")
            plain = plain.replace("[success]", "").replace("[/success]", "")
            plain = plain.replace("[error]", "").replace("[/error]", "")
            plain = plain.replace("[warning]", "").replace("[/warning]", "")
            plain = plain.replace("[info]", "").replace("[/info]", "")
            plain = plain.replace("[filepath]", "").replace("[/filepath]", "")
            plain = plain.replace("[prompt]", "").replace("[/prompt]", "")
            print(plain)
        except Exception:
            pass


def print_header(text: str):
    """Print a main header."""
    _safe_print(f"\n[header]{text}[/header]")


def print_subheader(text: str):
    """Print a subheader."""
    _safe_print(f"[subheader]{text}[/subheader]")


def print_divider():
    """Print a divider line."""
    _safe_print("[divider]" + "-" * 60 + "[/divider]")


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
    _safe_print(f"  [{style}]- {status}:[/{style}] [filepath]{filepath}[/filepath]")


def print_success(message: str):
    """Print a success message."""
    _safe_print(f"[success][OK] {message}[/success]")


def print_error(message: str):
    """Print an error message."""
    _safe_print(f"[error][ERROR] {message}[/error]")


def print_warning(message: str):
    """Print a warning message."""
    _safe_print(f"[warning][WARN] {message}[/warning]")


def print_info(message: str):
    """Print an info message."""
    _safe_print(f"[info]{message}[/info]")


def prompt(text: str, default=None):
    """Show a colored prompt and get user input."""
    if default:
        prompt_text = f"[prompt]{text} [{default}]:[/prompt] "
    else:
        prompt_text = f"[prompt]{text}:[/prompt] "

    try:
        return console.input(prompt_text).strip() or default
    except UnicodeEncodeError:
        return input(text + (f" [{default}]" if default else "") + ": ").strip() or default


def confirm(text: str):
    """Show a yes/no confirmation prompt."""
    try:
        response = console.input(f"[prompt]{text} [y/N]:[/prompt] ").lower().strip()
    except UnicodeEncodeError:
        response = input(f"{text} [y/N]: ").lower().strip()
    return response == "y"
