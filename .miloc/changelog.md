# changelog.md (repo-local engineering log)
#
# Rule: update this file before committing (or before pushing a commit batch).
# If work drifted from tasks/goals, record why in `.miloc/global-notes.miloc.md`.

2026-03-14
- Scope: root cleanup and `AGENTS.md` reduction
- What changed:
  - Replaced the root `AGENTS.md` with a short repo-specific guide that points to `.miloc/docs/*`, `CONTRIBUTING.md`, `TESTS.md`, and `ARCHITECTURE.md`.
  - Removed root-only noise and generated artifacts: `.dev_notes.md`, `DEEPDIVE_PROMTING.md`, `SESSION.md`, and the committed benchmark summary under `out/`.
  - Added `.miloc` doc links to the top-level READMEs and clarified that benchmark JSON output under `out/` is local generated state.
- Why: Keep the root focused on real repo entrypoints, reduce duplicated agent/process guidance, and stop versioning local artifacts.
- Links: `AGENTS.md`, `README.md`, `README.ru.md`, `.miloc/docs/ASSEMBLY.md`, `.miloc/global-notes.miloc.md`
- Verification:
  - `git diff --check`
  - `find . -maxdepth 1 -mindepth 1 | sort`
  - `PYTHONPATH=src python3 -m pytest tests/test_cli.py tests/test_core.py tests/test_formatting.py tests/test_updater.py tests/test_utils.py -q`
  - `rg -n "\\.dev_notes\\.md|DEEPDIVE_PROMTING\\.md|SESSION\\.md|out/bench-summary\\.json" README.md README.ru.md CONTRIBUTING.md ARCHITECTURE.md TESTS.md AGENTS.md .miloc tests/benchmarks/README.md src/locus/similarity/README.md`
- Drift (if any): none

2026-03-14
- Scope: `.miloc` initialization and repo docmap
- What changed:
  - Seeded `.miloc/goal.md`, `.miloc/roadmap.md`, `.miloc/global-notes.miloc.md`, `.miloc/debug-notes.miloc.md`, and `.miloc/docs/README.md` from the canonical MiLoC templates with repo-specific content.
  - Added `.miloc/docs/ASSEMBLY.md` as the short repo map and `.miloc/docs/SYSTEM_DESIGN.md` as the deep architecture document for `locus`.
  - Recorded the repository’s main entrypoints, verification commands, and optional MCP dependency boundary in the new MiLoC docs.
- Why: Establish stable repo-local memory and a durable entrypoint for future human/agent work.
- Links: `.miloc/goal.md`, `.miloc/roadmap.md`, `.miloc/docs/ASSEMBLY.md`, `.miloc/docs/SYSTEM_DESIGN.md`
- Verification:
  - `git diff --check`
  - `python3 -m ruff check src/ tests/`
  - `python3 -m ruff format --check src/ tests/`
  - `PYTHONPATH=src python3 -m pytest tests/test_cli.py tests/test_core.py tests/test_formatting.py tests/test_updater.py tests/test_utils.py -q`
  - `PYTHONPATH=src python3 -m pytest tests/ --ignore=tests/mcp -q` is still blocked in this shell because the base runtime dependency `rich` is not installed.
- Drift (if any): none
