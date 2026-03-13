# Plan

This is the canonical plan surface for the task. Keep it current.

## Current stage

- Stage: plan
- Exit condition: baseline/perf signal is captured and dev ownership can start implementation against the frozen contract.

## Decision summary

- Default path: implement in five small workstreams rather than a broad exporter rewrite.
- Why: the key gaps are separable and have clear verification boundaries.
- Frozen contract from T0001:
  - Respect `.gitignore` as the default ignore baseline; no separate ignore-file surface is required by default.
  - Keep CLI selection/filter flags, but make them effective in the scan/export path.
  - Use hybrid packing with target around 5k lines per part and hard ceiling around 10k lines.
  - Export notebook markdown/code cells by default; include outputs/media only behind an explicit flag when available.

## Verification plan

- Command / check: `PYTHONPATH=src python3 -m pytest tests/test_cli.py tests/test_core.py tests/test_formatting.py tests/test_utils.py -q`
- Expected signal: existing analyze/export contracts stay green before and after the changes.
- Command / check: `PYTHONPATH=src python3 -m locus analyze -o /tmp/locus-export --include "**/*.py" -p`
- Expected signal: filters and export outputs behave deterministically in collection mode.
- Command / check: notebook fixture smoke + `time -p` perf smoke
- Expected signal: notebook export is readable, optional outputs/media stay flag-gated, and runtime stays within agreed baseline.

## Closure decision

- Target: DONE
- Why: this future task should end only after implementation, QA, changelog, and commit.

## Tasks (2–6 max)

- [ ] Task 1: Record frozen contract and measure baseline
  - Files: task artifacts, possibly docs
  - Action: record the frozen contract from T0001 in implementation-facing artifacts and capture baseline timings.
  - Verify: decisions are recorded and perf baseline exists.
  - Done-when: implementation work can proceed without scope churn.

- [ ] Task 2: Fix filtering and gitignore-based ignore workflow
  - Files: `src/locus/cli/*`, `src/locus/core/*`, `src/locus/utils/config.py`, tests
  - Action: make CLI filters effective and align default ignore behavior with `.gitignore` without writing bootstrap config into target repo for the default path.
  - Verify: CLI/core tests + targeted e2e smoke.
  - Done-when: selection behavior matches CLI surface and docs.

- [ ] Task 3: Add hybrid export package
  - Files: `src/locus/core/modular_export.py`, `src/locus/formatting/code.py`, `src/locus/formatting/tree.py`, tests/docs
  - Action: implement deterministic manifest/tree/description outputs plus hybrid packing (target ~5k lines, ceiling ~10k).
  - Verify: export fixture asserts part count/order/manifest contents.
  - Done-when: LLM-ready output contract is stable.

- [ ] Task 4: Add notebook support
  - Files: processor/config/export path + tests/docs
  - Action: include `.ipynb` and convert notebook content into LLM-friendly text; gate outputs/media behind an explicit flag.
  - Verify: fixture notebook export tests.
  - Done-when: notebook handling is deterministic and documented.

- [ ] Task 5: Add perf smoke and finalize docs
  - Files: tests/docs/changelog
  - Action: add timing/perf verification and update README/help/docs.
  - Verify: perf smoke + doc references.
  - Done-when: feature is shippable.

## Ordered next actions

1. Move this task to `working/` and assign a dev owner; done when Task 1 baseline work starts.
2. Capture baseline/perf signal on current analyze/export path; done when the first implementation patch has a measured before-state.

## Stop / ask-user conditions

- A new requirement asks for token-budget packing as the primary contract instead of the agreed line-based hybrid heuristic.
- Notebook outputs/media must be always-on instead of explicit-flag behavior.

## Tracking sync

- Epic stage/status updated: yes
- Epic checkboxes updated: yes
