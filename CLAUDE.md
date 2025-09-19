# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Locus Analyzer is a Python CLI tool that pinpoints and documents your project structure. It analyzes source code, generates comprehensive reports, and can apply changes from Markdown files back to source code.

## Commands

### Development Setup
```bash
# Install package in development mode
pip install -e .

# Install with data preview dependencies
pip install -e .[data]
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_core.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_core.py::test_scanner_basic
```

### Code Quality
```bash
# Run linter
ruff check src/ tests/

# Auto-fix linting issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/

# Check formatting without changing files
ruff format --check src/ tests/
```

### Using the Tool

#### Interactive Mode (Terminal Output)
```bash
# Quick overview of current directory
locus analyze

# Analyze specific directory
locus analyze src/

# Include file comments in tree
locus analyze -c

# Force include README when piping
locus analyze --with-readme | less
```

#### Report Mode (Markdown File)
```bash
# Full report with all code (default)
locus analyze -o analysis.md

# Minimal report (tree + README only)
locus analyze -o summary.md --style minimal

# Annotations only (function/class signatures)
locus analyze -o structure.md --style annotations

# Report without README
locus analyze -o code.md --skip-readme

# With dependency resolution
locus analyze src/ -o report.md -d 2
```

#### Collection Mode (Flat Directory Export)
```bash
# Export files to flat directory
locus analyze -o output/

# Add annotations report
locus analyze -o output/ --add-annotations

# Export without README
locus analyze -o output/ --skip-readme
```

#### Update Mode
```bash
# Apply updates from markdown
cat changes.md | locus update --dry-run
cat changes.md | locus update --backup
```

## Architecture

### Core Processing Flow
1. **Orchestrator** (`src/locus/core/orchestrator.py`) - Coordinates the entire analysis workflow
   - Automatically discovers and reads README files (README.md, .rst, .txt)
   - Stores README content in `AnalysisResult.project_readme_content`
2. **Scanner** (`src/locus/core/scanner.py`) - Discovers files using pattern matching
3. **Resolver** (`src/locus/core/resolver.py`) - Handles dependency resolution for Python imports
4. **Processor** (`src/locus/core/processor.py`) - Analyzes individual files and extracts metadata

### Key Design Patterns

**Data Models** (`src/locus/models.py`):
- All data structures use Pydantic models for validation
- `TargetSpecifier` handles complex file:line_range specifications
- `FileAnalysis` combines file metadata with content and annotations
- `AnalysisResult` aggregates all analysis outputs and includes `project_readme_content`

**Configuration System**:
- `.locus/allow` and `.locus/ignore` files control file inclusion/exclusion (stored in `.locus/` directory)
- Legacy `.locusallow` and `.locusignore` files in project root are still supported for backwards compatibility
- Default config files are automatically created in `.locus/` directory on first run if no configuration exists
- Pattern matching uses glob patterns with sensible defaults
- Configuration is loaded once and passed through the pipeline

**CLI Structure** (`src/locus/cli/`):
- Uses argparse for command parsing
- Subcommands: `analyze` and `update`
- Mode detection based on output destination:
  - No `-o`: Interactive mode (stdout)
  - `-o file.md`: Report mode
  - `-o directory/`: Collection mode (flat structure)
- Content styles: `--style {full|annotations|minimal}`
- README control: `--skip-readme`, `--with-readme`
- Rich formatting for interactive output

### Testing Approach

Tests use pytest with a comprehensive fixture system:
- `project_structure` fixture creates realistic test projects in temp directories
- Each component has dedicated test files matching the source structure
- Tests cover both unit functionality and integration scenarios

## Important Implementation Details

### File Processing
- Python files are analyzed using AST for accurate extraction of functions, classes, and docstrings
- Data files (CSV, JSON, Parquet) show previews when pandas is available
- Binary files are detected and handled separately
- Encoding detection with fallback to handle various text formats

### README Integration
- Automatically searches for README files in project root
- Priority order: README.md > README.rst > README.txt > README
- Case-insensitive matching for flexibility
- Smart defaults: includes in TTY output, excludes when piped
- Stored in `AnalysisResult.project_readme_content`

### Dependency Resolution
- Follows Python imports recursively to specified depth
- Handles relative and absolute imports
- Avoids circular dependencies through visited tracking
- Can be disabled with `-d 0` for faster analysis

### Collection Mode Export
- Files exported with flat structure (no subdirectories)
- Path separators replaced with underscores
- Example: `src/utils/helpers.py` → `src_utils_helpers.py`
- README.md copied to output unless `--skip-readme`
- Optional OUT.md annotations with `--add-annotations`

### Update Mechanism
The update command expects Markdown with specific format:
- File paths in headers: `### File: \`path/to/file.py\``
- Code in fenced blocks with optional language hints
- Supports creating new files and modifying existing ones
- Always prompts for confirmation unless `--dry-run` is used

## CLI Modes and Options

### Output Modes
- **Interactive Mode**: Default when no `-o` specified, outputs to terminal
- **Report Mode**: When `-o file.md` specified, creates comprehensive markdown
- **Collection Mode**: When `-o directory/` specified, exports files with flat structure

### Style Options (`--style`)
- **full** (default): Include README, tree, and complete source code
- **annotations**: Include README, tree, and function/class signatures only
- **minimal**: Include README and tree only (no code)

### README Control
- **--skip-readme**: Exclude README from any output
- **--with-readme**: Force include README (useful when piping)
- Smart defaults: Includes README in TTY, excludes when piped

### Deprecated Features
- `--generate-summary`: Use `-o file.md --style minimal` instead