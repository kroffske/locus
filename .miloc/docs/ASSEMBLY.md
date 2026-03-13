---
title: "ASSEMBLY"
generated_by: "miloc-docmap"
generated_at: "2026-03-14"
repo: "locus"
commit: "fab3afa"
---

# ASSEMBLY — locus

> **Read first:** this file is intentionally short. Start here, then go to `.miloc/docs/SYSTEM_DESIGN.md` for the deeper architecture map.

## E — Entrypoints
- Main entrypoint: `python3 -m locus ...` via `src/locus/__main__.py`
- CLI dispatch: `src/locus/cli/args.py` and `src/locus/cli/main.py`
- Optional MCP bridge: `src/locus/cli/mcp_cmd.py` -> `src/locus/mcp/launcher.py`
- Main subcommands: `analyze`, `sim`, `update`, `init`

## U — Usage (minimal)
- Setup: `make install-dev` or `pip install -e .[dev]`
- Analyze from source tree: `PYTHONPATH=src python3 -m locus analyze -p`
- Similarity scan: `PYTHONPATH=src python3 -m locus sim src -s ast`
- Test: `PYTHONPATH=src python3 -m pytest tests/ --ignore=tests/mcp -q`
- Lint/format: `python3 -m ruff check src/ tests/` and `python3 -m ruff format --check src/ tests/`

## L — Layout (top-level)
- `src/locus/cli/` — CLI parsing and subcommand dispatch
- `src/locus/core/` — scanning, dependency resolution, orchestration, modular export config
- `src/locus/formatting/` — tree/report/code formatting and terminal helpers
- `src/locus/init/` — project bootstrap templates and initialization flow
- `src/locus/updater/` — Markdown-to-files parsing and write pipeline
- `src/locus/similarity/` — duplicate and near-duplicate detection
- `src/locus/mcp/` — optional MCP indexing/search server
- `src/locus/search/` — search abstractions shared by the MCP path
- `tests/` — fast tests plus `tests/mcp/` for optional MCP coverage
- `.locus/` — repo-level include/ignore defaults for analysis

## I — Interfaces
- External services: optional embedding/vector-store stack for MCP (`fastmcp`, `sentence-transformers`, `lancedb`, `torch`)
- APIs: CLI flags, stdin update contract, optional MCP server tools
- Data stores: local filesystem; optional LanceDB-backed index in the MCP path

## Existing refs
- `README.md`
- `CONTRIBUTING.md`
- `ARCHITECTURE.md`
- `TESTS.md`
- `src/locus/similarity/README.md`
- `AGENTS.md`

## Where to change X (common tasks)
- Add or change CLI behavior: `src/locus/cli/`
- Change scan/dependency behavior: `src/locus/core/`
- Change output layout or report formatting: `src/locus/formatting/`
- Change project init templates: `src/locus/init/`
- Change Markdown update parsing/writing: `src/locus/updater/`
- Change similarity logic: `src/locus/similarity/`
- Change optional MCP search/index behavior: `src/locus/mcp/` and `src/locus/search/`
- Change default analysis include/ignore rules: `.locus/`, `src/.locus/`, and `src/locus/utils/helpers.py`

## Build & Verify (minimal)
- `make install-dev`
- `PYTHONPATH=src python3 -m locus analyze -p`
- `PYTHONPATH=src python3 -m pytest tests/ --ignore=tests/mcp -q`
- `python3 -m ruff check src/ tests/`
- `python3 -m ruff format --check src/ tests/`
