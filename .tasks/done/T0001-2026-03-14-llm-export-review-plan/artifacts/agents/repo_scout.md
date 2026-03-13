# Locus Analyze/Export Scout Summary

## 1) Current-state summary
- Analyze/export pipeline is `cli.args -> cli.main -> core.orchestrator -> core.scanner/core.processor -> formatting code/tree/report` and is implemented without broad refactors.
- Command entrypoint is `src/locus/__main__.py` calling `src/locus/cli/main.py`.
- `handle_analyze_command()` chooses interactive, report (`.md`), or collection (`output_dir`) output by output-path extension.
- Default filtering and docs include loading comes from `src/locus/utils/config.py`; scanner enforces allow/ignore with defaults and config files.
- Modular export path is `collect_files_modular()` in `src/locus/formatting/code.py`, with `index.txt` generation via `generate_index_content()`.
- File-processing and analysis objects live in `src/locus/models.py` and are consumed by orchestrator/core.

## 2) Per-request assessment
- LLM should be able to use the utility comfortably
  - Status: `partially_supported`
  - Evidence: interactive tree/summary flags (`-p`, `-f`), annotations mode, report/collection options, and `index.txt` search guidance are present.
  - Constraint: no dedicated LLM export mode; report mode and collection mode expose different affordances.
- ignore rules should not require copying ignore files into the analyzed project
  - Status: `partially_supported`
  - Evidence: `load_project_config()` can operate by reading repo config and `create_default_config_if_needed()` can bootstrap defaults.
  - Constraint: defaults are written to the analyzed repo (`.locus/`), so behavior is non-destructive for usage but not “no-touch”.
- export should be able to form 1-10 files (or requested count), with tree + description
  - Status: `missing`
  - Evidence: output file count is governed by grouping rules + `max_lines_per_file`, not by requested count; collection mode writes grouped text files and `index.txt`, not an exported tree.
  - Constraint: no `--max-files` / file-count controls and no collection-mode tree artifact.
- grep/rg-style conditions should be convenient
  - Status: `partially_supported`
  - Evidence: CLI exposes `--include` and `--exclude`, plus grep-oriented index hints and flat output.
  - Constraint: `include_patterns` and `exclude_patterns` are not applied in `core.orchestrator.analyze()`;
currently they are accepted, forwarded, then ignored.
- review export speed
  - Status: `partially_supported`
  - Evidence: `FileCache` reduces repeated reads and output chunks are bounded by config thresholds.
  - Constraint: no dedicated export speed tests or timing budget; repeated content-length calculations in export/index paths suggest avoidable overhead.
- support exporting Jupyter notebooks
  - Status: `missing`
  - Evidence: default `.locus/allow` list does not include `*.ipynb`; notebooks are excluded unless user config is changed.
  - Constraint: no notebook-specific processing; if included, notebooks are treated as raw text/JSON.

## 3) Source map (key files and symbols)
- `src/locus/__main__.py`: module entrypoint (`main`).
- `src/locus/cli/args.py`: `parse_arguments()`, `parse_target_specifier()`, `_add_file_selection_arguments()`, `_add_targets_argument()`.
- `src/locus/cli/main.py`: `main()`, `handle_analyze_command()`, report/collection branching and output formatting calls.
- `src/locus/core/orchestrator.py`: `analyze()`, `_find_config_root()`, `_merge_line_ranges()`.
- `src/locus/core/scanner.py`: `scan_directory()`.
- `src/locus/core/processor.py`: `process_file()`, `analyze_python_file()`, `analyze_data_file()`.
- `src/locus/core/resolver.py`: `resolve_dependencies()`, `extract_imports()`.
- `src/locus/core/config.py`: `load_project_config()`, `create_default_config_if_needed()`, `save_default_config()`.
- `src/locus/utils/config.py`: `_read_pattern_file()`, `load_project_config()`.
- `src/locus/utils/helpers.py`: `is_path_ignored()`, `build_file_tree()`, `compile_regex()`.
- `src/locus/core/modular_export.py`: `group_files_by_module()`, `find_matching_rule()`, `get_group_key()`, `check_and_split_large_groups()`.
- `src/locus/formatting/code.py`: `collect_files_modular()`, `collect_files_to_directory()`, `generate_index_content()`.
- `src/locus/formatting/tree.py`: `format_tree_markdown()`, `format_flat_list()`.
- `src/locus/formatting/helpers.py`: `get_output_content()`, `get_summary_from_analysis()`, `_slice_content_by_ranges()`.
- `src/locus/formatting/report.py`: `generate_full_report()`, `generate_headers_report()`.
- `src/locus/models.py`: `TargetSpecifier`, `AnalysisResult`, `FileAnalysis`, `FileInfo`.
- `tests/test_cli.py`, `tests/test_core.py`, `tests/test_utils.py`, `tests/test_formatting.py`.

## 4) Constraints and risks
- `orchestrator` receives `include_patterns`/`exclude_patterns` but does not pass them into scanning, so user filters currently have no effect.
- Default config bootstrap writes files under `.locus`, which can be undesirable for read-only or ephemeral analysis targets.
- No notebook allow/type support by default (`.locus/allow` excludes `*.ipynb`) and no notebook-aware output formatter.
- No explicit export speed/perf tests, and no threshold/contract for large-repo export time.
- Export controls are configuration-driven but not command-level, so many improvements require editing `.locus/settings.json` per repo.

## 5) Recommended implementation touchpoints
- Start with `src/locus/core/orchestrator.py` and `src/locus/core/scanner.py` to apply `--include/--exclude` correctly and deterministically.
- Add non-persistent override mode in `src/locus/utils/config.py` so ignore/allow can be supplied without writing `.locus` into target repos.
- Add explicit export-size/count controls in `src/locus/cli/args.py` and `src/locus/formatting/code.py` (e.g., requested file count, explicit max files, count-aware packing).
- Add collection-mode tree/description package in `src/locus/formatting/code.py` and wire in `cli.main`.
- Add notebook extension support in `.locus` defaults and processor path (`src/locus/processor.py`) with graceful extraction of code cells for export readability.
- Add focused tests in `tests/test_cli.py`, `tests/test_core.py`, and a dedicated performance test file for scan+export timing on synthetic large trees.
