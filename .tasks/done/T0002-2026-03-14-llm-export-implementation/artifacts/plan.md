# Plan

This is the canonical plan surface for the task. Keep it current.

## Current stage

- Stage: release
- Exit condition: ship boundary is closed and the task is archived under `.tasks/done/`.

## Decision summary

- Default path: keep one `senior_dev` owner for the product change, with Manager retaining QA + changelog + commit.
- Why: the change spans overlapping CLI/core/formatting paths, so splitting owners now would create avoidable merge risk.
- Frozen contract:
  - Use `.gitignore` from the config root plus built-in noise ignores as the default baseline; keep `.locus` config support as an optional override, but never create `.locus/*` during default analyze/export.
  - Treat `-o <path-without-extension>` as directory export mode; if the path exists as a non-directory, fail clearly.
  - Make `--include` / `--exclude` effective in actual scan/export selection; `--exclude` must remain authoritative after dependency resolution.
  - Directory export should emit deterministic LLM package surfaces: manifest + tree + description + part files; compatibility `index.txt` is optional only if it matches the new package contract.
  - Use hybrid packing with target around 5k lines per part and hard ceiling around 10k lines; split oversized single files into continuation parts instead of silently overflowing or skipping them.
  - Export notebook markdown/code cells by default; include outputs/media only behind an explicit flag when available.
- Baseline captured on `2026-03-14`:
  - `PYTHONPATH=src python3 -m pytest tests/test_cli.py tests/test_core.py tests/test_formatting.py tests/test_utils.py -q` -> `21 passed in 2.16s`.
  - Report-mode smoke succeeded in `1.60s` but created `.locus/settings.json` in the analyzed repo.
  - `-o <path-without-extension>` currently writes a single report-like file instead of a directory export.
  - `-o <existing-directory>` currently fails with `IsADirectoryError`.

## Workstreams / owners

- `spark_contract_scout` -> `.tasks/done/T0002-2026-03-14-llm-export-implementation/artifacts/agents/contracts.md`
  - Scope: exact source-of-truth paths, traps, and test touchpoints for the frozen contract.
  - Done-when: artifact lists concrete files/functions/regression risks for the dev owner.
- `senior_dev` -> `.tasks/done/T0002-2026-03-14-llm-export-implementation/artifacts/agents/dev_impl.md`
  - Scope: product code + tests for CLI mode selection, filter/ignore behavior, export package, notebook support, perf/docs updates.
  - Verify: targeted pytest slice plus CLI export/report/notebook smokes.
  - Done-when: task acceptance criteria are satisfied or any deferral is explicit and justified in the handoff.
- `qa` -> `.tasks/done/T0002-2026-03-14-llm-export-implementation/artifacts/qa.md`
  - Scope: integrated verification and verdict before shipping.
  - Done-when: ACCEPTED or concrete FINDINGS.

## Verification plan

- Command / check: `PYTHONPATH=src python3 -m pytest tests/test_cli.py tests/test_core.py tests/test_formatting.py tests/test_utils.py -q`
- Expected signal: existing analyze/export contracts stay green before and after the changes.
- Command / check: `PYTHONPATH=src python3 -m locus analyze -o /tmp/locus-export --include "**/*.py" -p`
- Expected signal: path-without-extension creates a directory export package instead of a report-like file.
- Command / check: run the same command against an existing output directory path
- Expected signal: existing directories are handled cleanly; no `IsADirectoryError`.
- Command / check: verify working tree after report/export smoke
- Expected signal: no `.locus/settings.json` or other repo-local bootstrap files are created as side effects.
- Command / check: notebook fixture smoke + `time -p` perf smoke
- Expected signal: notebook export is readable, optional outputs/media stay flag-gated, and runtime stays within agreed baseline.

## Closure decision

- Target: DONE
- Why: this future task should end only after implementation, QA, changelog, and commit.

## Tasks (2–6 max)

- [x] Task 1: Record frozen contract and measure baseline
  - Files: task artifacts
  - Action: record the frozen contract from T0001 and capture current pytest/report/export baseline behavior.
  - Verify: timings + current failure modes are documented in `brief.md` / this plan.
  - Done-when: implementation work can proceed without scope churn.

- [x] Task 2: Fix filtering and gitignore-based ignore workflow
  - Files: `src/locus/cli/*`, `src/locus/core/*`, `src/locus/utils/config.py`, tests
  - Action: make CLI filters effective and align default ignore behavior with `.gitignore` without writing bootstrap config into target repo for the default path.
  - Verify: CLI/core tests + targeted e2e smoke.
  - Done-when: selection behavior matches CLI surface and docs.

- [x] Task 3: Add hybrid export package
  - Files: `src/locus/core/modular_export.py`, `src/locus/formatting/code.py`, `src/locus/formatting/tree.py`, tests/docs
  - Action: implement deterministic manifest/tree/description outputs plus hybrid packing (target ~5k lines, ceiling ~10k).
  - Verify: export fixture asserts part count/order/manifest contents.
  - Done-when: LLM-ready output contract is stable.

- [x] Task 4: Add notebook support
  - Files: processor/config/export path + tests/docs
  - Action: include `.ipynb` and convert notebook content into LLM-friendly text; gate outputs/media behind an explicit flag.
  - Verify: fixture notebook export tests.
  - Done-when: notebook handling is deterministic and documented.

- [x] Task 5: Add perf smoke and finalize docs
  - Files: tests/docs/changelog
  - Action: add timing/perf verification and update README/help/docs.
  - Verify: perf smoke + doc references.
  - Done-when: feature is shippable.

## Ordered next actions

1. None. QA is ACCEPTED, changelog is updated, and the task is ready to be archived in `.tasks/done/`.

## Stop / ask-user conditions

- A new requirement asks for token-budget packing as the primary contract instead of the agreed line-based hybrid heuristic.
- Notebook outputs/media must be always-on instead of explicit-flag behavior.

## Tracking sync

- Epic stage/status updated: yes
- Epic checkboxes updated: yes
