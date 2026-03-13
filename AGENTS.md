# AGENTS.md — locus

<project>
- `locus` is a local-first Python CLI for repository analysis, modular exports, Markdown-driven file updates, similarity detection, and optional MCP search/indexing.
- Read this repo in this order:
  1. `README.md`
  2. `.miloc/docs/ASSEMBLY.md`
  3. `.miloc/docs/SYSTEM_DESIGN.md`
  4. `CONTRIBUTING.md`
  5. `TESTS.md`
  6. `ARCHITECTURE.md`
</project>

<scope>
- Applies to the whole repository unless a deeper `AGENTS.md` overrides it.
- `src/locus/similarity/AGENTS.md` adds local guidance for the similarity subsystem.
</scope>

<tools>
- Search with `rg` and `rg --files`.
- If the package is not installed, run CLI commands from source with `PYTHONPATH=src python3 -m locus ...`.
- Common setup: `make install-dev`
- Fast checks:
  - `python3 -m pytest tests/ --ignore=tests/mcp -q`
  - `python3 -m ruff check src/ tests/`
  - `python3 -m ruff format src/ tests/`
- MCP-specific work needs optional extras; keep that boundary explicit.
</tools>

<golden_rules>
- Keep diffs minimal and auditable.
- Read the surrounding code before editing.
- Do not move optional MCP dependencies into the base CLI or other default code paths.
- Keep generated artifacts and local scratch outputs out of git, especially under `out/`.
- For shipped repo changes, update `.miloc/changelog.md` before commit.
- Keep durable repo memory in `.miloc/*`, not in root-level scratch files.
</golden_rules>

<layers>
- `src/locus/cli/` — command-line parsing and dispatch
- `src/locus/core/` — scanning, dependency resolution, orchestration, config
- `src/locus/formatting/` — terminal/report rendering only
- `src/locus/init/` — project bootstrap templates and creation flow
- `src/locus/updater/` — Markdown-to-files parsing and safe writes
- `src/locus/similarity/` — duplicate detection strategies and reporting
- `src/locus/mcp/` and `src/locus/search/` — optional MCP server and search abstractions
</layers>

## Repo Workflow

- Prefer behavior-level changes over broad refactors.
- Keep CLI I/O in `cli`, reusable analysis in `core`, rendering in `formatting`, and writes in `updater`.
- When changing docs or root layout, keep `README.md` and `.miloc/docs/*` aligned.
- When changing benchmark or local-output flows, treat `out/` as generated local state, not versioned content.

## Pointers

- Contributor setup and commands: `CONTRIBUTING.md`
- Test strategy: `TESTS.md`
- Architecture principles: `ARCHITECTURE.md`
- Repo map: `.miloc/docs/ASSEMBLY.md`
- Deep design: `.miloc/docs/SYSTEM_DESIGN.md`
