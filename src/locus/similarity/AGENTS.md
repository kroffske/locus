Where Normalization Lives

- Core location: `src/locus/similarity/ast_canonical.py` (keep “AST magic” here). This module owns Python-specific AST canonicalization: identifier/literal masking, docstring/decorator handling, and producing a canonical token stream.
- Shared glue: `src/locus/similarity/normalize.py` for small, strategy-agnostic helpers (e.g., whitespace normalization, stable hashing, optional size filters). It should not be Python‑AST aware.

Simple Interface (Similarity Core)

- Input: a simple list of “units” (functions/methods) — not raw ASTs — with minimal fields:
  - `rel_path`, `qualname`, `span`, `source`, and optional `py_ast` for Python strategies.
- Types: `src/locus/similarity/types.py`
  - `Unit`: extracted code unit.
  - `CanonicalForm`: `tokens: list[str]`, `meta: dict` (e.g., policy version, node count).
  - `SimilarityConfig`: strategy, `min_nodes`, flags.
  - `SimilarityResult`: units, clusters, matches, meta.
- Flow:
  - Extract: `similarity/extractor.py` → `[Unit]` (Python‑aware only here).
  - Strategy: `similarity/strategies.py` dispatches:
    - `exact` → `normalize.py` whitespace canonicalization + hash.
    - `ast` → `ast_canonical.canonicalize(unit.py_ast)` → tokens + hash.
  - Cluster: `similarity/search.py` groups by fingerprint and assembles clusters.

Boundaries and Responsibilities

- CLI/orchestrator: unchanged. They call `similarity.run(analysis, config)` and get `SimilarityResult`.
- Similarity interface: remains simple and language‑agnostic at the boundary (list of `Unit`), while AST specifics stay encapsulated in `ast_canonical.py`.
- Future extensibility: if we add other languages, add `lang_<x>_canonical.py` siblings and keep strategies pluggable.

Concrete Tasks

- Define/confirm `Unit` and `CanonicalForm` in `types.py` (ensure `py_ast: Optional[ast.AST]`).
- Implement `canonicalize(ast.AST, opts) -> CanonicalForm` in `ast_canonical.py`:
  - Mask identifiers by role, mask literals by type, strip docstrings, normalize f-strings, preserve operator kinds, standardize params (`self/cls`), compute node sequence and `min_nodes`.
- Add size/trivial filters in `normalize.py` and apply in `strategies.py` before hashing.
- Keep `strategies.py` as the single entry for fingerprinting, so the caller never sees AST.

