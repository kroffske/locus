# Contributing to Locus

## Development Setup

### Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Quick Setup

**Option 1: Using uv (recommended - 10-100x faster)**

```bash
# Clone the repository
git clone https://github.com/kroffske/locus.git
cd locus

# Install with dev dependencies using uv
make install-dev
# or manually (add --system if not using a virtual environment):
uv pip install --system -e .[dev]
```

**Option 2: Using pip**

```bash
pip install -e .[dev]
```

**Important:** Always use `.[dev]` for development to install testing dependencies (pytest, ruff).

## Development Workflow

### Running Tests

```bash
# Run core tests (fast)
make test

# Run all tests including MCP tests (requires heavy dependencies)
make test-all

# Run tests with verbose output
make test-verbose
```

### Code Quality

```bash
# Fix linting issues and format code
make quality

# Or run individually:
make lint-fix  # Fix linting issues
make format    # Format code with ruff
```

### Common Tasks

```bash
make help          # Show all available commands
make clean         # Clean build artifacts and cache
make reinstall     # Reinstall the package
```

## Why uv?

`uv` is a Rust-based Python package manager that's 10-100x faster than pip:

| Operation | pip | uv | Speedup |
|-----------|-----|-----|---------|
| Install from cache | 1.5s | 0.05s | 30x |
| Cold install | 10s | 0.5s | 20x |
| Resolution | 5s | 0.2s | 25x |

For development with frequent reinstalls, this makes a huge difference!

## Project Structure

```
locus/
├── src/locus/           # Main package
│   ├── cli/             # CLI commands and arguments
│   ├── core/            # Core logic (analysis, config, modular export)
│   ├── formatting/      # Output formatting (tree, code, reports)
│   ├── init/            # Project initialization
│   ├── similarity/      # Code similarity detection
│   └── updater/         # File update from markdown
├── tests/               # Test suite
│   ├── mcp/             # MCP-specific tests (optional deps)
│   └── ...              # Core tests
├── Makefile             # Development commands
└── pyproject.toml       # Project configuration
```

## Dependency Management

### Dependency Groups

1. **Base dependencies** (required for all users):
   - `rich` - Terminal formatting
   - `pyyaml` - Configuration parsing

2. **Dev dependencies** (`[dev]` extra):
   - `pytest`, `pytest-cov` - Testing
   - `ruff` - Linting and formatting
   - All MCP dependencies (for testing)

3. **MCP dependencies** (`[mcp]` extra - optional):
   - Heavy ML libraries (transformers, torch, lancedb)
   - Only needed for MCP server functionality

### Installing Specific Extras

```bash
# Basic installation (end users)
uv pip install locus-analyzer

# Development (includes everything)
uv pip install -e .[dev]

# Only MCP functionality
uv pip install locus-analyzer[mcp]
```

## Common Issues

### "ModuleNotFoundError: No module named 'pytest'"

**Problem:** You installed without dev dependencies.

**Solution:**
```bash
# Reinstall with dev dependencies
make reinstall
# or
uv pip install -e .[dev]
```

### Tests failing with import errors

**Problem:** Package not installed in editable mode or missing dependencies.

**Solution:**
```bash
# Clean install
make clean
make install-dev
```

### "No module named 'locus'"

**Problem:** Package not installed.

**Solution:**
```bash
# Install in editable mode
uv pip install -e .
```

## Testing Philosophy

- **Core tests**: Fast, no heavy dependencies (run on every commit)
- **MCP tests**: Require ML libraries (run in CI or locally when needed)
- Use `--ignore=tests/mcp` to skip MCP tests in development

## Before Submitting a PR

Run the full quality check:

```bash
make quality
```

This will:
1. Fix linting issues
2. Format code
3. Run core tests

All should pass before pushing!
