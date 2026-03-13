# Verify Scout — LLM-export review (analyze/export path)

## 1) Current verification surface
- `src/locus/cli/args.py`: analyze flags, aliases, help paths are declared (`--include`, `--exclude`, `-p`, `-t`, `-a`, `--style`, `-o`, `--comments`, `--flat`, `--ascii-tree`, etc.).
- `src/locus/core/orchestrator.py`: orchestrator reads `.locus` config, scans, resolves imports, processes files, fills `result.required_files`.
- `src/locus/cli/main.py`: `mode` branch in `handle_analyze_command` (interactive/report/collection) and where export artifacts are written.
- `src/locus/core/scanner.py` + `src/locus/utils/helpers.py`: ignore/include logic and hardcoded ignore rules.
- `src/locus/formatting/code.py`: `collect_files_to_directory`, `collect_files_modular`, `collect_files_modular` index generation path.
- `src/locus/core/modular_export.py` + `src/locus/core/config.py`: grouping/splitting and default config used for directory output.

### Existing tests touching these areas
- Parser: `tests/test_cli.py`.
  - Covers argument parsing and target parsing only.
- Core scanning/orchestration: `tests/test_core.py`.
  - Covers `scan_directory` allow/ignore behavior and `orchestrator.analyze()` happy path.
- Config and ignore util behavior: `tests/test_utils.py`.
  - Covers `.locus` loading, path-ignore matching, glob handling.
- Formatting + modular index content: `tests/test_formatting.py`.
  - Covers tree formatting and `generate_index_content` output, no filesystem export write.
- Similarity as adjacent signal: `tests/test_similarity.py`, `tests/benchmarks/run_benchmarks.py`, `tests/benchmarks/README.md`, `tests/dummy_similarity/README.md`.

### What is missing today
- No automated CLI e2e for `locus analyze` in any output mode (stdout report directory).
- No tests for `collect_files_modular` actual file writes (`.txt` outputs + `index.txt`).
- No targeted test for `--include/--exclude` filtering in the full CLI path.
- No test for notebook (`*.ipynb`) handling semantics.
- No dedicated performance benchmark for analyze/export throughput.

## 2) Minimal future verification plan by workstream

### W1 — CLI contract smoke (pre-implementation baseline)
- Commands:
  - `cd <repo> && PYTHONPATH=src python3 -m locus analyze -p`
  - `cd <repo> && PYTHONPATH=src python3 -m locus analyze -o /tmp/locus-report.md -p -t -a --no-code -f`
  - `cd <repo> && PYTHONPATH=src python3 -m locus analyze -o /tmp/locus-export --include "**/*.py" --exclude "tests/**" -p`
- Pass signal:
  - exit code 0, command prints/creates expected artifacts.
  - no exception trace in stdout/stderr.
  - for report mode file exists and contains `# Code Analysis Report` + `## File Contents` when requested.

### W2 — Include/ignore behavior (analysis correctness)
- Commands:
  - Build fixture with `.locus/allow` and `.locus/ignore` containing `tests/**` and `build/**`, then run `PYTHONPATH=src python3 -m locus analyze -p`.
  - `--include` / `--exclude` smoke:
    - `PYTHONPATH=src python3 -m locus analyze -o /tmp/exp-a.md --include "src/**" --exclude "**/*test*"`
- Pass signal:
  - expected file classes included/excluded in tree/report summaries.
  - `tests/*` and ignored folders absent from scan when using default/explicit rules.

### W3 — Modular export behavior
- Commands:
  - `cd <repo> && PYTHONPATH=src python3 -m locus analyze -o /tmp/locus-out --include "**/*.py" -p`
  - `cd <repo> && PYTHONPATH=src python3 -m locus analyze -o /tmp/locus-out --include "**/*.py" --no-code -o /tmp/locus-out --ascii-tree`
- Pass signal:
  - exit 0.
  - output dir exists.
  - at least one `.txt` group file created.
  - `index.txt` exists in collection mode when groups non-empty.
  - `index.txt` line ranges are monotonic and point to real files (`grep '^## '` count > 0).

### W4 — Similarity-included analyze path
- Commands:
  - `cd <repo>/tests/dummy_similarity && PYTHONPATH=src python3 -m locus analyze --similarity -p --include "**/*.py"`
  - `... analyze --similarity -o /tmp/sim-report.md --include "**/*.py"`
- Pass signal:
  - exit 0.
  - report output contains duplicate cluster summary lines (non-empty) when expected input has exact duplicates.

## 3) Perf-specific checks/signals
- Current state: no formal analyze/export benchmark exists (only similarity benchmark exists).
- Minimal perf smoke to establish trend:
  - `cd <repo>`
  - `time -p PYTHONPATH=src python3 -m locus analyze -o /tmp/locus-report.md -p --include "**/*.py"`
  - `time -p PYTHONPATH=src python3 -m locus analyze -o /tmp/locus-export --include "**/*.py"`
  - `time -p PYTHONPATH=src python3 -m locus analyze -o /tmp/locus-export --include "**/*"`
- Signals:
  - exit code 0.
  - wall time and RSS/IO trend across same fixture should be stable.
  - output count (files, lines, groups) deterministic for same input.
- Optional stronger check after implementation:
  - add tiny `pytest`-based perf guard using one medium synthetic tree and assert upper bound on runtime + max group count to prevent regressions.

## 4) Notebook-specific checks/signals
- Current status:
  - no explicit `ipynb` extension listed in default allow list (`src/locus/utils/config.py`), so notebooks are not included by default.
  - notebooks are treated as plain text files when explicitly included, but no dedicated formatter/parser is in place.
- Minimal verify now:
  - create minimal `sample.ipynb` fixture and run:
    - `PYTHONPATH=src python3 -m locus analyze --include "**/*.ipynb" -o /tmp/nbook.md`
  - pass if file is present and exported output contains `# source: sample.ipynb`.
- Post-implementation checks (for true notebook export):
  - assert converted content contains extracted code cells in deterministic order.
  - assert raw binary metadata is not dumped into code summary.
  - verify include/print modes (`--no-code`, style variants) don't silently lose notebook context.

## 5) Gaps / blockers / lightweight verification notes
- Gaps:
  - No CLI e2e regression suite for analyze/export; easiest is to add 2 smoke tests:
    1) report mode CLI roundtrip
    2) modular export roundtrip + index format sanity
  - No notebook coverage (no parser + no fixture).
  - No perf harness for analyze/export.
- Environment/runtime blockers:
  - Use `PYTHONPATH=src` fallback if package is not installed (`.miloc/docs/ASSEMBLY.md`, `system design` mention local-source fallback).
  - `make` docs mix `python` and `python3`; for consistency prefer `python3` in verification commands on dev hosts.
  - `.venv` and virtual-env dirs are excluded by default config/helpers (`**/.venv/**`, `.venv`, `venv`); if test roots include shared / non-writable env dirs, scans are intentionally blind and perf numbers will be optimistic.
  - default config creation in `.locus` is attempted by `load_project_config`; if cwd is read-only or ownership is strict, config init can fail harmlessly but changes observable defaults (`allow`/`ignore`) and can make results less explicit.

