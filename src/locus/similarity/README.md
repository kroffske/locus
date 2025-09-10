# Locus Similarity Module

Detect duplicate or near-duplicate functions within a repository. This module powers the `--similarity` option for `locus analyze`.

## Current Status
- Strategy: Exact hash over normalized function text (collapses whitespace).
- Scope: Python functions and methods (including nested) extracted via AST.
- Output: clusters of identical functions (after whitespace normalization) with file paths and line spans.
- CLI integration: `--similarity` prints interactive summary and can write report sections and raw JSON.

Planned next: AST-canonical hashing for Type-2 clones (identifier/literal masking), SimHash/MinHash-LSH for scalable near-duplicates, richer normalization.

## How It Works (MVP)
1) Extract: parse each analyzed Python file’s AST to collect function-level units:
   - qualname (e.g., `ClassName.method` or `function`)
   - relative path and span (`start_line`–`end_line`)
   - exact source snippet for that function
2) Normalize: collapse whitespace within the function source (trim + spaces condensed).
3) Fingerprint: compute `sha256(normalized_text)`.
4) Group: functions with identical hashes become a cluster (exact duplicates score 1.0).

Notes:
- Whitespace-only changes still match.
- Token/literal changes do not match in the MVP.

## CLI Usage
- Interactive quick view within analyze:
  - `locus analyze -p --similarity --sim-strategy ast`
- Similarity-only command:
  - `locus sim -s ast -j sim.json`
- Write a report and raw JSON payload from analyze:
  - `locus analyze --similarity -o report.md --sim-output sim.json`
  - Strategies: `exact` (whitespace-normalized) or `ast` (identifier/literal masking)

What you’ll see in interactive mode:
- “Similar or Duplicate Functions” section.
- Summary with strategy, unit count, and cluster count.
- For each duplicate cluster, a list of members (path:span and qualname).

## Report Output
When writing a report (`-o report.md`), a “Similar or Duplicate Functions” section is added listing clusters and members.

## JSON Output Example
With `--sim-output sim.json`, the raw result is written. Example shape:
```json
{
  "meta": {"strategy": "exact"},
  "units": [
    {"id": 0, "file": "/abs/path/src/foo.py", "rel_path": "src/foo.py", "qualname": "bar", "span": [1, 5]}
  ],
  "clusters": [
    {"id": 0, "member_ids": [0, 12], "strategy": "exact", "score_min": 1.0, "score_max": 1.0}
  ],
  "matches": [
    {"a_id": 0, "b_id": 12, "score": 1.0, "strategy": "exact"}
  ]
}
```

## Programmatic Usage
```python
from locus.core.orchestrator import analyze
from locus.similarity import run, SimilarityConfig

result = analyze(project_path=repo_root, target_specs=[], max_depth=-1, include_patterns=None, exclude_patterns=None)
sim = run(result, SimilarityConfig(strategy="exact"))
print(sim.clusters)
```

## Limitations (MVP)
- Only whitespace differences are ignored; comments/docstrings are currently retained.
- Identifier or literal changes will not match (planned in AST strategy).
- Only Python is supported.

## Roadmap
- AST-canonical hashing to detect Type-2 clones (identifier/literal masking).
- SimHash and/or MinHash+LSH for scalable near-duplicate detection.
- Extended normalization (strip comments/docstrings, consistent quoting).
- Thresholded reporting with previews and scores.

## Benchmarks
- Location: `tests/benchmarks/` contains canonical cases and schema docs. See `tests/benchmarks/README.md` for layout, naming, and how to add new cases.

### Quick Run (CLI)
- Exact duplicates (Type‑1) on a single case:
  - `locus sim tests/benchmarks/cases/case-001 -s exact`
- AST‑canonical strategy (identifier/literal masking):
  - `locus sim tests/benchmarks/cases/case-002 -s ast`
- Write raw JSON for inspection:
  - `locus sim tests/benchmarks/cases/case-001 -s exact -j out/sim.json`

Tips:
- Add `--no-print-members` for a terse summary.
- Include `--include-init` to consider `__init__` methods.

### Running With Pytest
- Install dev deps: `pip install -e .[dev]`
- Run the test suite (includes similarity tests):
  - `pytest -q`  (or `PYTHONPATH=src pytest -q` if running from source tree)

At present, `tests/benchmarks/` is a data suite used for manual and future automated checks. You can point `locus sim` at any `tests/benchmarks/cases/case-XYZ/` directory to validate strategy behavior interactively or export JSON for downstream analysis.

### Full Benchmark Sweep With Summary
- Prereq: install dev deps (includes PyYAML): `pip install -e .[dev]`
- Run all cases and get PASS/FAIL/SKIP summary:
  - `python tests/benchmarks/run_benchmarks.py`
  - From a source tree without install: `PYTHONPATH=src python tests/benchmarks/run_benchmarks.py`

What it does:
- T1 cases run with `exact` strategy; T2 with `ast`.
- T3 (near-miss) cases are currently marked SKIP (unsupported).
- Compares case-defined pairs against detected clusters and prints a concise summary.

Advanced options:
- Force a specific strategy for all cases (useful because `exact` currently keeps comments/docstrings):
  - `python tests/benchmarks/run_benchmarks.py --strategy ast`
- Attempt T3 cases using the T2 strategy mapping (experimental):
  - `python tests/benchmarks/run_benchmarks.py --include-t3`
- Choose default mapping when `expected.strategy: any`:
  - `--t1-strategy exact|ast` (default: exact), `--t2-strategy exact|ast` (default: ast)
- Emit JSON summary for CI dashboards:
  - `python tests/benchmarks/run_benchmarks.py --strategy ast --json-out out/bench-summary.json`
