# Plan

This is the canonical plan surface for the task. Keep it current.

## Current stage

- Stage: release
- Exit condition: planning package is archived under `.tasks/done/`, changelog is updated, and follow-up task T0002 is ready to start.

## Decision summary

- Default path: close this task as a review/planning package and defer code changes into a dedicated follow-up implementation task.
- Why: reconnaissance confirmed five concrete product gaps and one correctness bug (`--include/--exclude` ignored in the scan path). Human review has now frozen the remaining product choices, so the right next step is a scoped dev task, not more planning churn.
- Confirmed gaps:
  - `--include/--exclude` are accepted by CLI but ignored in `core.orchestrator.analyze()`.
  - Ignore/config workflow is repo-touching by default via `.locus` bootstrap.
  - Collection export lacks explicit part-count control and tree/manifest artifacts.
  - Notebook export is absent by default.
  - Analyze/export speed lacks a benchmark or timing contract.
- Frozen contract:
  - Ignore baseline: use `.gitignore`; no separate ignore-file surface required by default.
  - Packing: hybrid, target ~5k lines per part with hard ceiling ~10k lines.
  - Notebook export: cells always; outputs/media behind an explicit flag when available.

## Workstreams / owners

- Review package owner: `miloc-manager`
- Future implementation container: `.tasks/planned/T0002-2026-03-14-llm-export-implementation/`
- Source scout evidence:
  - `.tasks/done/T0001-2026-03-14-llm-export-review-plan/artifacts/agents/repo_scout.md`
  - `.tasks/done/T0001-2026-03-14-llm-export-review-plan/artifacts/agents/verify_scout.md`
  - `.tasks/done/T0001-2026-03-14-llm-export-review-plan/artifacts/agents/analyst.md`

## Verification plan

- Command / check: `PYTHONPATH=src python3 -m locus analyze --help`
- Expected signal: CLI help confirms current surface area and option names for `analyze`.
- Current result: blocked in this shell by missing base dependency `rich`; replaced for planning purposes by direct source inspection of `src/locus/cli/args.py` and `src/locus/cli/main.py`.
- Command / check: `rg -n "modular|export|ignore|include|exclude|notebook|ipynb|tree|description|summary" src tests README.md`
- Expected signal: source map covers current implementation and test/doc touchpoints for requested features.
- Current result: pass.
- Command / check: `PYTHONPATH=src python3 -m pytest tests/test_cli.py tests/test_core.py tests/test_formatting.py tests/test_utils.py -q`
- Expected signal: current parser/scan/formatting contracts remain green while planning package points to real behavior.
- Current result: pass (`21 passed`).
- Command / check: QA review of task artifacts for coverage of all requested areas.
- Expected signal: planning package clearly states supported vs missing behavior and an ordered implementation plan.

## Closure decision

- Target: DONE
- Why: human review resolved the three product-level choices; the task now meets its review/plan goal and the next work is already staged as T0002.

## Tasks (2–6 max)

- [x] Task 1: Repo reconnaissance for current export/analyze path
  - Files: `src/locus/cli/*`, `src/locus/core/*`, `src/locus/formatting/*`, `tests/*`, `README.md`
  - Action: map entrypoints, current feature coverage, missing support, and likely touchpoints for requested improvements.
  - Verify: scout artifact cites concrete files and class/function names.
  - Done-when: all user-requested topics have a current-state assessment.

- [x] Task 2: Clarify request into execution-facing acceptance criteria
  - Files: `request.md`, `brief.md`, `artifacts/agents/analyst.md`
  - Action: translate the raw request into concrete behavior-level requirements, assumptions, and mismatch points.
  - Verify: analyst artifact covers each request bullet and highlights blocking ambiguities.
  - Done-when: manager can produce an implementation plan without polling the user on routine choices.

- [x] Task 3: Build final plan with verification and follow-ups
  - Files: `brief.md`, `artifacts/plan.md`, `artifacts/qa.md`, `delivered.md`
  - Action: integrate findings into phased workstreams, verification strategy, and review checklist.
  - Verify: QA artifact marks the planning package accepted or lists gaps.
  - Done-when: the task contains a stable plan and explicit next action for implementation.

- [x] Task 4: Human review of product-shaping assumptions
  - Files: `brief.md`, `.tasks/planned/T0002-2026-03-14-llm-export-implementation/epic.md`
  - Action: confirm output contract assumptions before implementation starts.
  - Verify: review feedback resolves the three open decisions listed in closure.
  - Done-when: T0002 can move from `planned/` to `working/` without changing scope.

## Ordered next actions

1. Start `.tasks/planned/T0002-2026-03-14-llm-export-implementation/` when implementation work is requested; done when the task moves to `working/` and baseline capture begins.

## Stop / ask-user conditions

- None for T0001; unresolved implementation questions should be handled inside T0002 only if they materially change the frozen contract above.

## Tracking sync

- Epic stage/status updated: yes
- Epic checkboxes updated: yes
