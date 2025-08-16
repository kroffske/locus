# Project Analyzer

A powerful Python CLI tool for analyzing source code projects, generating comprehensive reports, and applying code updates from Markdown files.

## Features

- **Project Analysis**: Scan and analyze source code with dependency resolution
- **Multiple Output Formats**: Generate reports, file trees, or code collections
- **Smart Filtering**: Use glob patterns to include/exclude files
- **Dependency Resolution**: Automatically follow Python imports
- **Code Updates**: Apply changes from specially formatted Markdown files
- **Data Preview**: View previews of CSV, JSON, Parquet, and other data files
- **Line-Range Targeting**: Analyze specific sections of files

## Installation

### Basic Installation

```bash
pip install project-analyzer
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/kroffske/project-analyzer.git
cd project-analyzer

# Install in development mode
pip install -e .

# Install with data preview support
pip install -e .[data]
```

## Quick Start

### Analyze Current Directory

```bash
pr-analyze analyze .
```

### Analyze Specific Files or Directories

```bash
# Analyze a specific directory
pr-analyze analyze src/

# Analyze a specific file
pr-analyze analyze src/main.py

# Analyze specific lines in a file
pr-analyze analyze src/main.py:10-50,100-150

# Analyze multiple targets
pr-analyze analyze src/core/ tests/ main.py
```

### Generate Output Files

```bash
# Generate a Markdown report
pr-analyze analyze src/ -o analysis.md

# Generate a directory of individual files
pr-analyze analyze src/ -o output_dir/

# Generate a summary file
pr-analyze analyze . --generate-summary project-overview.md
```

## Commands

### `pr-analyze analyze`

Analyzes source code and generates reports.

#### Basic Options

- `targets`: Files or directories to analyze (default: current directory)
- `-o, --output`: Output file (.md) or directory for results
- `-d, --depth`: Dependency resolution depth (0=disabled, -1=unlimited, default: 1)

#### Filtering Options

- `--include`: Glob patterns for files to include (can be used multiple times)
- `--exclude`: Glob patterns for files to exclude (can be used multiple times)

#### Output Formatting

- `-c, --comments`: Include summary comments in file tree
- `-a, --annotations`: Generate detailed annotations report
- `--full-code-regex`: Regex pattern for files to include full code
- `--annotation-regex`: Regex pattern for files to show as stubs only

#### Alternate Modes

- `--generate-summary [FILENAME]`: Generate a claude.md-style summary file

#### Examples

```bash
# Analyze with dependency resolution
pr-analyze analyze src/ -d 2

# Include only Python and Markdown files
pr-analyze analyze . --include "*.py" --include "*.md"

# Exclude test files
pr-analyze analyze src/ --exclude "*test*.py" --exclude "tests/"

# Generate report with comments and annotations
pr-analyze analyze src/ -o report.md -c -a

# Create a project summary
pr-analyze analyze . --generate-summary
```

### `pr-analyze update` (or `pr-update`)

Applies code changes from Markdown files back to source files.

#### Options

- `--backup`: Create .bak files before making changes
- `--dry-run`: Preview changes without applying them

#### Usage

```bash
# Apply updates from a Markdown file
cat changes.md | pr-analyze update

# Or use the shortcut command
cat changes.md | pr-update

# Preview changes without applying
cat changes.md | pr-update --dry-run

# Create backups before applying changes
cat changes.md | pr-update --backup
```

#### Markdown Format

The update command expects Markdown with the following format:

````markdown
### File: `path/to/file.py`
```python
# New or updated file content goes here
def my_function():
    return "Hello, World!"
```

### File: `another/file.js`
```javascript
// JavaScript content
console.log("Updated!");
```
````

## Configuration Files

### `.claudeallow`

Specifies glob patterns for files to include in analysis. One pattern per line:

```
**/*.py
**/*.js
**/*.md
**/README*
```

### `.claudeignore`

Specifies patterns for files to exclude from analysis. One pattern per line:

```
**/__pycache__/**
**/node_modules/**
**/*.pyc
**/.git/**
```

## Advanced Features

### Dependency Resolution

The tool can automatically follow Python imports to include related files:

```bash
# Follow imports up to 2 levels deep
pr-analyze analyze main.py -d 2

# Unlimited depth (use with caution)
pr-analyze analyze main.py -d -1

# Disable dependency resolution
pr-analyze analyze main.py -d 0
```

### Line Range Specification

Analyze specific parts of files:

```bash
# Single range
pr-analyze analyze src/main.py:10-50

# Multiple ranges
pr-analyze analyze src/main.py:10-50,100-150,200

# Mix of files and ranges
pr-analyze analyze src/main.py:1-100 src/utils.py tests/
```

### Pattern-Based Code Inclusion

Control which files show full code vs. stubs:

```bash
# Show full code only for main modules
pr-analyze analyze src/ -o report.md --full-code-regex ".*main.*"

# Show only stubs for test files
pr-analyze analyze . -o report.md --annotation-regex ".*test.*"
```

## Output Formats

### Tree View (Default)

Displays a hierarchical view of the project structure:

```
src/
├── main.py (150 lines)
├── utils/
│   ├── helpers.py (200 lines)
│   └── config.py (75 lines)
└── tests/
    └── test_main.py (100 lines)
```

### Full Report (-o report.md)

Generates a comprehensive Markdown report with:
- Project structure tree
- Detailed annotations (with -a flag)
- Complete source code
- Import relationships

### Code Collection (-o output_dir/)

Creates a directory with:
- Individual files for each analyzed source file
- Preserved directory structure
- Filtered content based on patterns

### Summary File (--generate-summary)

Creates a concise overview suitable for documentation or AI assistants.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=project_analyzer

# Run specific test file
pytest tests/test_core.py
```

### Code Quality

```bash
# Run linter
ruff check src/ tests/

# Format code
ruff format src/ tests/

# Type checking (if configured)
mypy src/
```

## Default Ignored Patterns

The following are always ignored:
- `.git`, `.hg`, `.svn`, `.bzr`
- `__pycache__`, `.pytest_cache`, `.mypy_cache`
- `.venv`, `venv`, `.env`, `env`
- `node_modules`
- `*.pyc`, `*.pyo`, `*.pyd`
- `.DS_Store`, `Thumbs.db`
- `*.egg-info`, `dist`, `build`

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

For issues, questions, or suggestions, please open an issue on the [GitHub repository](https://github.com/your-username/project-analyzer/issues).