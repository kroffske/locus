---
title: "Debug Notes (MiLoC)"
updated_at: "2026-03-14"
---

# Debug Notes (MiLoC)

Use this file for durable debugging and runtime-discovery facts.
It complements:
- `.miloc/global-notes.miloc.md` for cross-task decisions and drift
- `.miloc/changelog.md` for shipped change history
- `.tasks/**/artifacts/qa.md` for the current run's executed checks and post-restart log review
- `.tasks/**/notes.miloc.md` for active task-local scratch notes

## Update policy

- Record only stable facts that should help future bug hunts.
- Prefer exact paths, commands, entrypoints, manifests, and dependency boundaries.
- Delete stale facts when runtime or layout changes.
- Keep uncertain hypotheses and one-off log dumps out until confirmed.

## Runtime map

- Repo type: Python CLI toolkit with optional MCP server components
- Main entrypoints: `src/locus/__main__.py`, `src/locus/cli/main.py`, `src/locus/mcp/launcher.py`
- Runtime manifests: `pyproject.toml`, `Makefile`, `.github/workflows/*.yml`
- Install/runtime targets to inspect: `src/locus/`, `tests/`, `.locus/`, `.github/workflows/`

## Useful debug commands

- `PYTHONPATH=src python3 -m locus analyze -p`
- `PYTHONPATH=src python3 -m locus sim src -s ast`
- `python3 -m pytest tests/ --ignore=tests/mcp -q`
- `python3 -m ruff check src/ tests/`
- `python3 -m ruff format --check src/ tests/`

## Known traps / invariants

- The shell may not expose a `locus` command until the package is installed in editable mode; from a raw source tree use `PYTHONPATH=src python3 -m locus ...`.
- The shell may expose `python3` but not `python`; prefer `python3` in ad hoc verification commands unless the environment guarantees the alias.
- MCP features are intentionally optional and require `locus-analyzer[mcp]`; missing extras surface as import/dependency errors instead of being silently skipped.
- The `update` command expects Markdown code fences whose first line is `# source: <path>` or `source: <path>`.
- If runtime verification touches optional MCP behavior, verify the heavy dependencies are installed before chasing application logic failures.

## Open runtime questions

- Should the repository’s automation and docs converge on `python3` to reduce environment-specific failures?
