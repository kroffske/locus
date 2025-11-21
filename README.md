# locus

Brief description of your project.

## Installation

```bash
pip install -e .
```

## Usage

```bash
python -m locus --help
```

## Development

### Quick Start (using uv - recommended, faster)

```bash
# Install with dev dependencies
make install-dev
# or manually (if not using a virtual environment, add --system flag):
uv pip install --system -e .[dev]

# Run quality checks
make quality
```

### Using pip (alternative)

```bash
# Install with dev dependencies
pip install -e .[dev]

# Run tests
pytest tests/ --ignore=tests/mcp -q

# Lint and format
ruff check --fix src/ tests/
ruff format src/ tests/
```

### Available Make targets

Run `make help` to see all available commands:
- `make install-dev` - Install with dev dependencies (fast with uv)
- `make test` - Run core tests
- `make lint-fix` - Fix linting issues
- `make format` - Format code
- `make quality` - Run all quality checks (lint + format + test)

## License

[Add your license here]