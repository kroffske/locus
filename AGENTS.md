# Repository Guidelines

## Project Structure & Module Organization
- Source: `src/locus/` (CLI, core, formatting, updater, utils, models).
  - CLI: `src/locus/cli/` (`args.py`, `main.py`).
  - Core pipeline: `src/locus/core/` (`scanner.py`, `resolver.py`, `processor.py`, `orchestrator.py`).
  - Formatting: `src/locus/formatting/` (tree, report, code, colors, helpers).
  - Updater: `src/locus/updater/` (Markdown parser/writer).
- Tests: `tests/` (`test_*.py`, `conftest.py`).
- Packaging: `pyproject.toml` (entry point `locus`).

## Build, Test, and Development Commands
- Install (editable): `pip install -e .` or with data extras: `pip install -e .[data]`.
- Run CLI: `locus analyze` or `python -m locus analyze src/ -o report.md`.
- Tests: `pytest` (quiet: `pytest -q`).
- Lint: `ruff check src/ tests/` (auto-fix: `ruff check --fix src/ tests/`).
- Format (ruff): `ruff format src/ tests/`.
- Format (black): `black src/ tests/` (installed via `.[dev]`).
 - Quick repo map: `locus analyze -p` (adds structure tree to output).

### Dev environment
- Install dev tools: `pip install -e .[dev]`
- Run both formatters:
  - `black src/ tests/`
  - `ruff check --fix src/ tests/ && ruff format src/ tests/`

### Windows consoles
- If your terminal can’t render Unicode tree characters, pass `--ascii-tree` to `locus analyze`.
- UTF-8 is enabled programmatically; no manual `PYTHONIOENCODING` setup needed.

### Typical workflows
- Quick analyze to file: `locus analyze -p -t -a --no-code -o out.md`
- Interactive skim: `locus analyze -p --ascii-tree`
- Scope by globs: `locus analyze -p --include "src/**/*.py" --exclude "tests/**"`

## Coding Style & Naming Conventions
- Python 3.8+; 4-space indentation; prefer type hints where helpful.
- Line length: 180 (see `[tool.ruff]`). Use double quotes by default.
- Imports: sorted by Ruff’s isort rules; remove unused.
- Naming: `snake_case` for functions/vars/modules, `PascalCase` for classes, `UPPER_CASE` for constants.
- Keep functions cohesive and small; avoid side effects in formatting utilities.

## Testing Guidelines
- Framework: `pytest`. Place tests in `tests/` and name files `test_*.py`.
- Cover: core behaviors in scanner, resolver, orchestrator, formatting, and CLI parsing.
- Use fixtures in `conftest.py`; prefer pure functions and deterministic outputs.
- Run `pytest` locally before opening a PR.

## Commit & Pull Request Guidelines
- Commits: concise, imperative subject line; include scope when useful (e.g., "core: improve resolver depth handling").
- Keep related changes together; avoid noisy reformat-only commits unless necessary.
- PRs must include:
  - Summary of changes and rationale.
  - Before/after examples for CLI output when applicable.
  - Linked issues (e.g., `Closes #123`).
  - Verification: output of `pytest` and `ruff check`.

## Security & Configuration Tips
- Safe updates: when using `locus update`, prefer `--dry-run` first and `--backup` for destructive edits.
- Filtering: edit `.locusallow`/`.locusignore` (or `.claudeallow`/`.claudeignore`) to control analysis scope.
- Large repos: limit dependency resolution with `--depth` and use `--include/--exclude` patterns to keep reports focused.
 - Project defaults: place config in `.locus/` (e.g., `.locus/config.toml`) to predefine common flags and patterns so you don’t repeat long CLI args. Explicit CLI flags always override file defaults.

## Architecture Overview
- CLI orchestrates analysis (`orchestrator.analyze`) and output modes (interactive/report/collection).
- Updater reads Markdown blocks and writes files with optional backups.
- Formatting layer renders tree/report/code consistently for TTY and files.
