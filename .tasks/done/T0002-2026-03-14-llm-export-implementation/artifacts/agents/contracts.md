# T0002 Contract: LLM-friendly Export Workflow

## 1) Canonical truth map (Do not invent alternate paths)

### Mode dispatch and output shape
- `src/locus/cli/main.py`
  - `handle_analyze_command(...)` (CLI entry)
    - `if output is None -> interactive`
    - `elif os.path.splitext(output)[1] -> report`
    - `else -> collection`
  - `collect`, `analyze` flows pass `include_patterns=args.include`, `exclude_patterns=args.exclude`.

### Analysis orchestration path
- `src/locus/core/orchestrator.py`
  - `analyze_codebase(...)` and helper `scan_codebase(...)` are the canonical entry for scanning in all analyze modes.
  - Current call chain currently loads project config and calls scanner:
    - `config.load_project_config(config_root)`
    - `scanner.scan_directory(...)`

### Include/Exclude
- User-facing contract should bind to:
  - `src/locus/cli/main.py` argument parsing and forwarding
  - `src/locus/core/orchestrator.py` include/exclude parameters in `analyze_codebase`
  - `src/locus/core/scanner.py` filtering callsite (`is_path_ignored` + allow rules)
- Current baseline gap: include/exclude are parsed and forwarded, but effective behavior is not wired through scan/config defaults in practice.

### Ignore/config baseline + “no .locus writeback” constraint
- Canonical ignore baseline today is in:
  - `src/locus/utils/helpers.py` (`ALWAYS_IGNORE_DIRS`, `DEFAULT_IGNORE_PATTERNS`)
  - `src/locus/core/config.py` (module config schema + defaults)
- Current behavior creates config artifacts in target repo via:
  - `src/locus/core/orchestrator.py` -> `load_project_config`
  - `src/locus/utils/config.py`
    - `create_default_config_if_needed(...)`
    - creates `.locus/` and `.locus/settings.json` when analyzing.
- Legacy requirement observed: `report` mode currently creates `.locus/settings.json` in repo. This MUST be acknowledged and consciously changed/replaced.

### Export package generation (tree/manifest/description + hybrid sizing)
- Canonical modular flow:
  - `src/locus/formatting/code.py`
    - `collect_files_modular(...)`
  - `src/locus/core/modular_export.py`
    - `group_files_by_module(...)`
    - `check_and_split_large_groups(..., max_lines=5000)`
- Canonical manifest-ish output today:
  - `src/locus/formatting/code.py` -> `generate_index_content(...)`
  - writes `index.txt`
- No dedicated `tree`/`manifest`/`description` artifacts are guaranteed by default in collection mode.

### Notebook export
- There is no notebook-specific export path as canonical implementation today:
  - `src/locus/core/processor.py` only has handlers for `.py` and a few special types
  - `.ipynb` falls back to generic text processing; no output/media extraction and no explicit include flag.

### Perf smoke hooks
- No existing targeted perf smoke/checks for analyze/export in pytest suite.
- Existing benchmark tooling is general/performance-only and not tied to contract-critical export correctness (`tests/benchmarks/run_benchmarks.py`).

---

## 2) Implementation contract (bounded, behavior-first)

### A. Filtering contract
- `--include` and `--exclude` must deterministically affect file selection in `collect_files_modular` outputs.
- Canonical pipeline: CLI include/exclude -> orchestrator -> scanner -> file inclusion.
- Include/exclude semantics should be pattern-based and composable as currently intended by the flags.
- Default behavior remains backward-compatible when no flags are passed.

### B. Ignore baseline contract (no repo mutation)
- Default ignore baseline MUST be `.gitignore`-derived when scanning; local repository files must not be written for baseline ignore state.
- In read-only analyze/export mode, analyzer must not write `.locus/*` into the target repo.
- Explicit config files (if supported) should be read but never created as side effects during analysis.

### C. Deterministic hybrid package contract
- collection output should be deterministic and directory-based package:
  - tree file
  - manifest file
  - description file
- Chunking policy must enforce:
  - target ~5000 lines per exported unit
  - hard ceiling ≈10k lines (never exceed)
  - split deterministically and reproducibly (stable ordering).
- Must support fallback path when tree/manual rules produce skewed groups.

### D. Notebook contract
- `.ipynb` content must be exported in markdown-like text form for code/text extraction.
- Outputs/media inclusion is behind an explicit CLI opt-in flag only.
- Default export path for notebooks excludes outputs/media.

### E. Perf smoke contract
- Add a minimal, non-flaky smoke measurement for:
  - include/exclude filter cost sanity
  - export packaging cost over a medium fixture repo
- Smoke should assert no pathological regressions and emit duration metrics, not strict micro-optimistic thresholds.

---

## 3) Current baseline traps / regression risks
- `report` mode side-effect currently writes `.locus/settings.json` (must be removed/contained).
- `--include/--exclude` are currently not effective; introducing filtering must avoid changing non-deterministic traversal order.
- Legacy path behavior: user-observed output without extension currently ends up report-like behavior in practice in some flows; this user-visible oddity must be either explicitly preserved by contract or eliminated with migration-safe behavior.
- `collect_files_modular` currently relies on `max_lines_per_file=5000`; adding hard ceilings must not create many tiny files from one large logical module.
- Splitting may currently only happen once by parent dir; enforce full ceiling behavior without regressing grouping semantics.
- .ipynb currently “just works” as text; new notebook flag defaults can unexpectedly hide content if not clearly documented.

---

## 4) Suggested smallest verification set (only add what is necessary)

### Tests
1. `tests/test_cli.py`
   - add contract assertions for output-mode dispatch (extension/no-extension/no-output)
   - add `--include/--exclude` acceptance in args and pass-through.
2. `tests/test_core.py`
   - add scanner/orchestrator test proving include/exclude affects returned nodes.
   - add no-side-effect test: analyze command does not create `.locus` files in target fixture.
3. `tests/test_formatting.py` (or new focused export test module)
   - add deterministic package assertions: generated `tree`, `manifest`, `description`, stable filenames, chunk size policy near boundaries (<=~5k target, <=~10k ceiling).
4. New focused test module for notebook behavior
   - `.ipynb` basic export baseline
   - explicit flag enables outputs/media; default excludes.
5. `tests/benchmarks` smoke or `tests/test_perf_smoke.py`
   - add short timing smoke for analyze+export over fixture, reporting elapsed values.

### Non-tests checks
- Add/update minimal docs comment in `.miloc/docs/*` or task artifact only if needed for behavior change notes.

---

## 5) Non-breaking compatibility notes
- Keep existing public CLI shape stable; add new flag(s) as additive.
- Preserve deterministic ordering of output paths and stable chunk naming.
- If changing current report-like extension-less output behavior, document as explicit behavior change with migration note.
