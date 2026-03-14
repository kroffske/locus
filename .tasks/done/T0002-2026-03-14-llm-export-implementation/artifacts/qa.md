## QA Result: ACCEPTED

Scope: T0002 — LLM-friendly export workflow (per frozen contract in `brief.md` + truth map in `artifacts/agents/contracts.md`).

Note: direct `$miloc-verify` skill invocation is unavailable as an automated gate in this environment; this QA run is the substitute gate following the `miloc-verify` protocol.

### Contract / AC cross-check (against current diff)
- Filters: `--include` / `--exclude` affect scan/export, and `--exclude` remains authoritative post-resolution (covered by `tests/test_core.py::test_orchestrator_applies_include_and_exclude`).
- Ignore baseline: default uses `.gitignore` + built-in ignores; no `.locus/*` bootstrap writes during analyze/export (covered by `tests/test_core.py::test_orchestrator_gitignore_directory_rule_ignores_nested_dirs` and `tests/test_core.py::test_orchestrator_does_not_create_locus_side_effects`).
- Output mode contract:
  - `-o <path-without-extension>` => directory export; existing non-directory path => clear error (covered by `tests/test_cli.py::test_collection_mode_rejects_existing_file_path`).
  - Existing output directory with dots => collection mode (covered by `tests/test_cli.py::test_collection_mode_for_existing_directory_with_extension`).
- Export package contract: emits `manifest.json`, `tree.txt`, `description.md`, `part-*.txt`, `index.txt`; packing target ~5k lines, hard ceiling 10k with continuation splits for oversized single files (covered by `tests/test_formatting.py::test_collect_files_modular_writes_package_surfaces` and `tests/test_formatting.py::test_collect_files_modular_splits_oversized_file_with_hard_ceiling`).
- Notebook contract: `.ipynb` exported as cells-only by default; outputs/media only with `--notebook-outputs` (covered by `tests/test_core.py::test_notebook_processing_defaults_without_outputs` and `tests/test_core.py::test_notebook_processing_with_outputs_enabled`).

### Verification
- `PYTHONPATH=src python3 -m pytest tests/test_cli.py tests/test_core.py tests/test_formatting.py tests/test_utils.py -q`: **PASS** (`33 passed in 1.21s`)
- `python3 -m ruff check src/locus/cli/main.py src/locus/cli/args.py src/locus/core/orchestrator.py src/locus/core/scanner.py src/locus/core/modular_export.py src/locus/core/processor.py src/locus/utils/config.py src/locus/formatting/code.py tests/test_cli.py tests/test_core.py tests/test_formatting.py tests/test_utils.py`: **PASS**

### Required smokes (CLI)
- CLI directory export smoke (`-o <no extension>`): **PASS**
  - Output contains: `description.md`, `index.txt`, `manifest.json`, `part-0001.txt`, `tree.txt`.
- existing-directory-with-dots smoke (`-o <existing dir with dots>`): **PASS**
  - Output contains: `description.md`, `index.txt`, `manifest.json`, `part-0001.txt`, `tree.txt`.
- No `.locus/settings.json` side-effect check: **PASS**
  - Temp analyzed repo: `.locus/settings.json` not created.
  - This repo after perf smoke: `.locus/settings.json` not created (note: repo already has `.locus/allow` and `.locus/ignore` tracked).
- Notebook default vs `--notebook-outputs`: **PASS**
  - Default export: no `### Outputs` / `[media ...]` markers in parts.
  - With `--notebook-outputs`: `### Outputs` and `[media image/png: ...]` present.

### Perf smoke (lightweight)
- `/usr/bin/time -p PYTHONPATH=src python3 -m locus analyze -o /tmp/locus-qa-perf --include "**/*.py" -p`: **PASS**
  - `real 1.86` / `user 1.77` / `sys 0.42`

### Post-restart logs
- happened: no
- docker compose logs / docker logs: not run (N/A)

### Residual notes (non-blocking)
- Diff includes doc/task hygiene changes beyond core code/tests (e.g., `README.md`, `.miloc/docs/*`, `AGENTS.md`, deletion under `.tasks/planned/...`). Assumed intentional; quick manager review recommended before commit.

Next: proceed to ship boundary (update `.miloc/changelog.md`, commit).
