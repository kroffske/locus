# Session 01 — Similarity Search MVP

Date: 2025-09-07

## Goals
- Plan and prototype a modular similarity search to detect duplicate/near-duplicate functions in the repo.
- Integrate minimally with CLI and reporting.

## What Was Done
- Drafted plan: `tasks/similarity-plan.md` (scope, strategies, API, integration, tests, risks).
- Scaffolding: created `src/locus/similarity/` package with:
  - `types.py`: CodeUnit, Match, Cluster, SimilarityResult.
  - `extractor.py`: AST-based function extraction (qualname, span, source).
  - `normalize.py`: whitespace-collapsing normalizer.
  - `strategies.py`: ExactHashStrategy (normalized text hash) and base interface.
  - `search.py`: SimilarityConfig and run(...) orchestration.
- Integration:
  - `models.AnalysisResult`: added optional `similarity` attachment.
  - `cli/args.py`: new flags — `--similarity`, `--sim-strategy`, `--sim-threshold`, `--sim-max-candidates`, `--sim-output`, `--report-duplicates-only`.
  - `cli/main.py`: executes similarity when enabled; optional JSON output; attaches to result.
  - `formatting/report.py`: renders “Similar or Duplicate Functions” section.
- Tests:
  - Added `tests/test_similarity.py` with cases for exact duplicates, whitespace variations, small changes not grouped, and basic JSON dump sanity.
  - All tests pass: 19 total.

## Usage
- Interactive quick check: `locus analyze -p --similarity`
- Report + JSON: `locus analyze --similarity -o out.md --sim-output sim.json`

## Notes & Rationale
- Placed similarity under `src/locus/similarity/` to keep core pipeline lean and enable pluggable strategies.
- MVP focuses on exact duplicates via normalized text hash for reliability and speed.

## Next Steps
- Add AST-canonical strategy for structural near-duplicates.
- Add SimHash/LSH token strategy for scalable approximate matching.
- Extend normalization (strip comments/docstrings) with tests.
- Enhance reporting (scores, previews, `--report-duplicates-only`).
- Performance tests on larger synthetic repos; candidate caps when adding approximate methods.

