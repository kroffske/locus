# Project Analyzer

A powerful Python CLI tool for analyzing source code projects, generating comprehensive reports, and applying code updates from Markdown files.

## Features

- **Project Analysis**: Scan and analyze source code with dependency resolution
- **Intelligent Output Modes**: Automatically determine output format based on destination
- **README Integration**: Automatically include project documentation in reports
- **Flexible Content Styles**: Choose between full code, annotations only, or minimal output
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

### Interactive Mode (Terminal Output)

```bash
# Quick project overview
pr-analyze analyze

# Analyze specific directory
pr-analyze analyze src/

# Show tree with descriptive comments
pr-analyze analyze -c
```

### Report Mode (Markdown File)

```bash
# Full analysis report with all code
pr-analyze analyze -o analysis.md

# Minimal summary (tree + README only)
pr-analyze analyze -o summary.md --style minimal

# Structure report with signatures only
pr-analyze analyze -o structure.md --style annotations
```

### Collection Mode (Directory Export)

```bash
# Export analyzed files to directory
pr-analyze analyze -o output/

# Export with annotations report
pr-analyze analyze -o output/ --add-annotations
```

## Commands

### `pr-analyze analyze`

Analyzes source code and generates reports. The output mode is determined by the `-o` option:
- **No `-o` flag**: Interactive mode (prints to terminal)
- **`-o file.md`**: Report mode (writes comprehensive report to file)
- **`-o directory/`**: Collection mode (extracts files to directory)

#### Basic Options

- `targets`: Files or directories to analyze (default: current directory)
- `-o, --output`: Output destination - determines the mode:
  - Omit for interactive terminal output
  - Specify `.md` file for report mode
  - Specify directory for collection mode
- `-d, --depth`: Dependency resolution depth (0=disabled, -1=unlimited, default: 1)

#### Content Style Options

- `--style {full|annotations|minimal}`: Control report content (report mode only)
  - `full` (default): Include README, tree, and complete source code
  - `annotations`: Include README, tree, and function/class signatures only
  - `minimal`: Include README and tree only (no code)
- `--skip-readme`: Exclude README from any output
- `--with-readme`: Force include README (useful when piping output)
- `-c, --comments`: Include summary comments in file tree
- `-a, --annotations`: Add detailed annotations (compatible with all modes)
- `--add-annotations`: Add OUT.md annotations file (collection mode only)

#### Filtering Options

- `--include`: Glob patterns for files to include (can be used multiple times)
- `--exclude`: Glob patterns for files to exclude (can be used multiple times)
- `--full-code-regex`: Regex pattern for files to include full code
- `--annotation-regex`: Regex pattern for files to show as stubs only

#### Usage Examples by Mode

##### Interactive Mode (Terminal Output)

```bash
# Quick overview of current directory
pr-analyze analyze

# View project structure with comments
pr-analyze analyze -c

# Analyze specific directory interactively
pr-analyze analyze src/

# Include README even when piping to another command
pr-analyze analyze --with-readme | less
```

##### Report Mode (Markdown File Output)

```bash
# Full report with all code (default)
pr-analyze analyze -o analysis.md

# Minimal report (README + tree only, no code)
pr-analyze analyze -o summary.md --style minimal

# Report with only function/class signatures
pr-analyze analyze -o structure.md --style annotations

# Full report without README
pr-analyze analyze -o code_only.md --skip-readme

# Report with dependency resolution
pr-analyze analyze src/ -o deep_analysis.md -d 3

# Report with filtered content
pr-analyze analyze -o report.md --include "*.py" --exclude "test_*.py"
```

##### Collection Mode (Directory Output)

```bash
# Extract all files to a directory
pr-analyze analyze -o extracted_files/

# Collection with annotations report
pr-analyze analyze -o output/ --add-annotations

# Collection without README
pr-analyze analyze -o files/ --skip-readme

# Extract specific module with dependencies
pr-analyze analyze src/main.py -o module_export/ -d 2
```

##### Advanced Examples

```bash
# Analyze specific lines in a file
pr-analyze analyze src/main.py:10-50,100-150 -o report.md

# Use regex to control code inclusion
pr-analyze analyze -o report.md --full-code-regex ".*main.*" --annotation-regex ".*test.*"

# Combine multiple options
pr-analyze analyze src/ -o detailed.md --style full -c -a -d 2 --exclude "**/tests/**"
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

### Content Control

Control what content appears in reports:

```bash
# Exclude README from output
pr-analyze analyze -o report.md --skip-readme

# Force include README when piping
pr-analyze analyze --with-readme | grep "TODO"

# Different content styles
pr-analyze analyze -o full_report.md --style full        # Everything
pr-analyze analyze -o stubs_only.md --style annotations  # Signatures only
pr-analyze analyze -o overview.md --style minimal        # Tree only

# Pattern-based inclusion
pr-analyze analyze -o report.md --full-code-regex ".*main.*"
pr-analyze analyze -o report.md --annotation-regex ".*test.*"
```

## Output Modes

### Interactive Mode (Default)

When no `-o` option is provided, output goes to the terminal:
- Shows README content (if TTY, or with `--with-readme`)
- Displays project structure tree
- Perfect for quick project overview

```
## Project README

[README content here...]

---

## Project Structure
├── src/
│   ├── main.py (150 lines)
│   └── utils/
│       └── helpers.py (200 lines)
└── tests/
    └── test_main.py (100 lines)
```

### Report Mode (`-o file.md`)

Generates a comprehensive Markdown report. Content controlled by `--style`:

#### Full Style (default)
- Project README/documentation
- Project structure tree
- Complete source code with syntax highlighting
- All file contents preserved

#### Annotations Style
- Project README/documentation  
- Project structure tree
- Function and class signatures only
- Docstrings and type hints preserved
- Implementation details omitted

#### Minimal Style
- Project README/documentation
- Project structure tree only
- No source code included
- Equivalent to deprecated `--generate-summary`

### Collection Mode (`-o directory/`)

Extracts files to a directory with flat structure:
- All files exported to single directory level
- Path separators replaced with underscores in filenames
- Copies README.md to output (unless `--skip-readme`)
- Optionally generates OUT.md with annotations (`--add-annotations`)
- Applies any filtering patterns

```
output_dir/
├── README.md              # Project README (if present)
├── OUT.md                # Annotations report (with --add-annotations)
├── src_main.py           # From src/main.py
├── src_utils_helpers.py  # From src/utils/helpers.py
├── src_utils_config.py   # From src/utils/config.py
└── tests_test_main.py    # From tests/test_main.py
```

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