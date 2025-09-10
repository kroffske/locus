# Locus Similarity Benchmarks

This folder defines a lightweight, reproducible benchmark suite for code similarity. It provides canonical positive examples (true duplicates/near-duplicates) and negative look‑alikes (e.g., trivial `__init__`, boilerplate), with a clear schema to express “A is similar to B” relationships.

## What We Mean by Similarity
- Type‑1 (exact): Identical except for whitespace/comments.
- Type‑2 (renamed): Identifier/literal renames with otherwise same structure.
- Type‑3 (near‑miss): Small insertions/deletions/reorders tolerated (thresholded).
- Non‑goals by default: trivial/boilerplate (e.g., empty `__init__`, simple getters, dataclass auto‑patterns) unless explicitly opted in for a test.

Guiding principles:
- Deterministic fixtures, minimal dependencies, easy to extend.
- One unit (function/class) per file where feasible for clarity.
- Explicit metadata per case to avoid ambiguity and enable automation.

## Layout
- `tests/benchmarks/cases/` – Positive and mixed cases grouped per scenario.
  - `case-001/` … `case-XYZ/` – A single benchmark case (see Naming).
    - `a.py`, `b.py`[, `c.py`…] – Each file contains exactly one primary unit.
    - `meta.yaml` – Ground truth and expectations for this case.
- `tests/benchmarks/negatives/` – Negative‑only examples by category (no pairs).
  - `trivial/`, `boilerplate/`, `generated/`, etc. Each file has a single unit.
- `tests/benchmarks/snippets/` – Tiny seeds used by potential generators/mutators.

Example tree:

```
tests/benchmarks/
  cases/
    case-001/
      a.py
      b.py
      meta.yaml
    case-002/
      a.py
      b.py
      c.py
      meta.yaml
  negatives/
    trivial/
      empty_init.py
      simple_getter.py
    boilerplate/
      dunder_repr.py
  snippets/
    sum_two_numbers.py
```

## Naming Conventions
- Case directories: `case-NNN` (zero‑padded, e.g., `case-001`).
- Members within a case: `a.py`, `b.py`, `c.py`… to indicate cluster membership.
- One primary unit per file (function or class). Use the file content and `meta.yaml` to define the fully qualified name when needed.
- Negative examples (not paired): descriptive filenames under `negatives/<category>/` (e.g., `empty_init.py`).

## Linking “A is similar to B”
Each case carries its own `meta.yaml` to encode ground truth, expected strategy behavior, and thresholds. Minimal schema:

```yaml
id: case-001
description: Simple Type-2 rename of function with constant change
kind: function  # function | class | module
type: T2        # T1 | T2 | T3 | mixed
tags: [rename, literals]
expected:
  strategy: any        # exact | simhash | minhash | any
  threshold: 0.85      # similarity threshold considered a hit
members:
  - label: a
    file: a.py
    qualname: foo
  - label: b
    file: b.py
    qualname: foo
pairs:
  - left: a
    right: b
    relation: similar   # similar | duplicate | negative
    notes: Renamed param, same structure
negatives: []           # optionally reference negatives by relative path
```

Notes:
- `kind` indicates the unit type; tests can assert strategy behavior per kind.
- `strategy` lets cases declare which strategies should succeed. Use `any` for generic expectations.
- `threshold` is the minimum similarity score for a hit (when applicable).
- For clusters with more than two members, add more `members` and `pairs`.
- Use `relation: negative` to encode purposely confusing pairs inside a case.

## Code Conventions in Member Files
- Exactly one primary unit per file:
  - Function cases: define a single top‑level function with a clear name.
  - Class cases: define a single class with one or more methods; ensure method under test is unambiguous.
- Avoid external imports unless necessary; prefer self‑contained logic.
- Keep docstrings/comments minimal; we test stripping behavior elsewhere.

Optional inline annotation (non‑blocking):
```python
# bench: case=case-001 member=a kind=function qualname=foo
```
This is purely informational for humans; tooling should rely on `meta.yaml`.

## Negative Examples
Placed under `negatives/` and not paired by default. Examples include:
- `trivial/empty_init.py` – empty or boilerplate `__init__`.
- `trivial/simple_getter.py` – one‑line return of an attribute.
- `boilerplate/dunder_repr.py` – simple `__repr__` implementations.

These inform “noise control” tests to ensure defaults do not flag them, unless explicitly configured.

## Adding a New Case (Checklist)
1) Create directory `tests/benchmarks/cases/case-XYZ/`.
2) Add `a.py`, `b.py` (and optionally `c.py`…), each with one primary unit.
3) Write `meta.yaml` using the schema above:
   - Set `kind`, `type` (T1/T2/T3), `expected.strategy`, `expected.threshold`.
   - List `members` (`label`, `file`, and optional `qualname`).
   - List `pairs` with `relation` and optional `notes`.
   - Add `tags` as helpful (e.g., `rename`, `insert`, `reorder`).
4) If relevant, place confusing non‑matches in `negatives/` and reference them in `negatives` or keep them global for noise tests.

## Future Automation Hooks
- Loader: a small utility (pytest fixture) to parse `meta.yaml` and yield test cases.
- Synthetic generator: produce controlled T2/T3 mutations from `snippets/` seeds.
- Metrics: per‑strategy success rate vs. `threshold`, cluster accuracy for multi‑member cases.

## Test Integration (Outline)
- A fixture, e.g., `bench_cases()` enumerates `tests/benchmarks/cases/**/meta.yaml`.
- For each case:
  - Load members, run requested strategy/threshold, assert pairwise results.
  - Ensure negatives (global or referenced) are not flagged under default settings.
- Keep tests deterministic and portable; avoid time‑ or env‑dependent logic.

## Style
- Python 3.8+; one unit per file; double quotes preferred.
- Keep lines readable; descriptive names for clarity in reports.

## Running the Benchmarks (Evaluation)

Goal: Evaluate each similarity algorithm against all curated cases to learn where it succeeds or fails. We run every case and count passes/fails — failures are informative (e.g., T3 near‑miss cases with strategies that are not designed to catch them).

Quick start:
- Ensure dev extras (PyYAML) are installed:
  - `pip install -e .[dev]`
- Run the full sweep and get a concise summary:
  - Installed package: `python tests/benchmarks/run_benchmarks.py`
  - From source tree: `PYTHONPATH=src python tests/benchmarks/run_benchmarks.py`

Strategy selection:
- `--strategy exact` – run all cases with the exact hashing strategy.
- `--strategy ast` – run all cases with the AST‑canonical hashing strategy.
- `--strategy all` (default) – run both strategies and report metrics per strategy.

Output and metrics:
- Per‑case status per strategy: PASS if all expected pairs are satisfied and no negatives are clustered; FAIL otherwise (including missing units).
- Per‑strategy summary:
  - Positives: expected vs detected (recall)
  - Negatives: total vs false positives
  - Missing units count
  - Cases passed/failed
- Optional JSON for CI dashboards:
  - `--json-out out/bench-summary.json`

Notes:
- Bench meta may include class‑level cases. Current extractor yields function/method units; prefer specifying `qualname: Class.method` to target methods. Class‑unit extraction is on the roadmap.
- Thresholds (`expected.threshold`) are future‑ready for approximate strategies; current exact/ast strategies treat same‑cluster as a hit with score 1.0.
