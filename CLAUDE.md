# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Project Analyzer is a Python CLI tool for analyzing source code projects and generating comprehensive reports. It can also apply changes from Markdown files back to source code.

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
```bash
# Analyze current directory
pr-analyze analyze .

# Analyze with dependency resolution
pr-analyze analyze src/ -d 2

# Generate output file
pr-analyze analyze src/ -o analysis.md

# Apply updates from markdown
cat changes.md | pr-analyze update --dry-run
```

## Architecture

### Core Processing Flow
1. **Orchestrator** (`src/project_analyzer/core/orchestrator.py`) - Coordinates the entire analysis workflow
2. **Scanner** (`src/project_analyzer/core/scanner.py`) - Discovers files using pattern matching
3. **Resolver** (`src/project_analyzer/core/resolver.py`) - Handles dependency resolution for Python imports
4. **Processor** (`src/project_analyzer/core/processor.py`) - Analyzes individual files and extracts metadata

### Key Design Patterns

**Data Models** (`src/project_analyzer/models.py`):
- All data structures use Pydantic models for validation
- `TargetSpecifier` handles complex file:line_range specifications
- `FileAnalysis` combines file metadata with content and annotations
- `AnalysisResult` aggregates all analysis outputs

**Configuration System**:
- `.claudeallow` and `.claudeignore` files control file inclusion/exclusion
- Pattern matching uses glob patterns with fallback defaults
- Configuration is loaded once and passed through the pipeline

**CLI Structure** (`src/project_analyzer/cli/`):
- Uses argparse for command parsing
- Subcommands: `analyze` and `update`
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

### Dependency Resolution
- Follows Python imports recursively to specified depth
- Handles relative and absolute imports
- Avoids circular dependencies through visited tracking
- Can be disabled with `-d 0` for faster analysis

### Update Mechanism
The update command expects Markdown with specific format:
- File paths in headers: `### File: \`path/to/file.py\``
- Code in fenced blocks with optional language hints
- Supports creating new files and modifying existing ones
- Always prompts for confirmation unless `--dry-run` is used