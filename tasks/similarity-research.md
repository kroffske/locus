# Deep Research: Code Similarity and Clone Detection

## Purpose
- Provide a rigorous foundation for detecting duplicate and near-duplicate code (function-level focus) within a repository.
- Guide algorithm selection, parameterization, indexing, and evaluation for a scalable, accurate similarity module.

## Problem Definition
- Task: Given a set of code units (functions/methods), surface pairs/clusters that are similar above a threshold.
- Clone taxonomy (widely used):
  - Type-1: Exact clones (whitespace/comments differences only).
  - Type-2: Renamed identifiers/literals with same structure.
  - Type-3: Near-miss clones (added/removed/modified statements).
  - Type-4: Semantic clones (functionally equivalent, syntactically different).
- Scope for MVP→v1: Type-1 and Type-2; partial Type-3 at scale; Type-4 is research-grade (future, limited support).

## Granularity & Representation
- Unit: function/method (optionally nested), captured with qualname, file path, span, and source.
- Language: Python (initial). Multi-language optional later.
- Normalizations:
  - Whitespace normalization (collapse, trim) — Type-1.
  - Comment/docstring stripping — Type-1.
  - Identifier anonymization and literal masking — Type-2.
  - Canonical AST linearization — Type-2/3.
  - Optional: control-flow insensitive block ordering tolerance (advanced).

## Algorithm Families

### 1) Exact Hash (Normalized Text)
- Idea: Hash normalized source; identical hashes → duplicates (score 1.0).
- Pros: Simple, fast, tiny memory.
- Cons: No near-duplicate detection; sensitive to small edits unless normalization is aggressive.
- Complexity: O(N) hashing; memory O(N) for map.

### 2) Document Fingerprinting / Winnowing (MOSS-style)
- Idea: Compute rolling hashes over k-grams; select fingerprints via winnowing; identical or overlapping fingerprints imply duplication.
- Pros: Robust to insertions/deletions; detects Type-1/2 and some Type-3 near misses.
- Cons: Parameter tuning (k, window) matters; false positives for boilerplate.
- Complexity: O(L) per unit to fingerprint; set overlap for candidates.

### 3) Token n-gram + MinHash + LSH
- Idea: Tokenize normalized code; build n-gram shingles; approximate Jaccard similarity via MinHash; use banded LSH for candidate generation.
- Pros: Scales to large corpora; tunable recall/precision via bands/rows; captures Type-2/3 small edits.
- Cons: Tokenization/normalization design critical; memory for signatures; tuning required.
- Complexity: O(L) tokenize + O(S) signature; index/query sublinear with LSH; comparisons only on candidates.

### 4) SimHash (Locality-Sensitive Hamming)
- Idea: Feature-weighted hashing to a b-bit fingerprint; Hamming distance approximates cosine similarity of features.
- Pros: Very fast indexing; small memory; good for near-duplicates.
- Cons: Feature design affects quality; distance thresholds approximate similarity.
- Complexity: O(L) to compute; multi-index by masks enables r-distance candidate retrieval in near O(1) average.

### 5) AST-based Canonical Hash
- Idea: Parse to AST; canonicalize by replacing identifiers/literals with placeholders; hash canonical form.
- Pros: Catches Type-2 exactly; resilient to superficial changes.
- Cons: Ignores reordering/insertions; language-specific and AST-version-sensitive.
- Complexity: O(L) to parse + normalize; O(N) hashing and bucket grouping.

### 6) AST Edit Distance / Tree Similarity (e.g., APTED, Zhang–Shasha)
- Idea: Compute tree edit distance or structured similarity between ASTs.
- Pros: Fine-grained similarity; can capture Type-3 with edits modeled.
- Cons: Expensive O(n^3) worst-case; needs candidate pruning via index; brittle without normalization.
- Use: As re-ranker on candidates from LSH/SimHash.

### 7) PDG/CFG and Semantic Methods
- Idea: Program dependency graphs/control-flow graphs; compare graph kernels or embeddings.
- Pros: Moves toward Type-4 semantic similarity.
- Cons: Heavyweight, language- and analysis-dependent; complexity and engineering cost high.
- Use: Future research; limited scope where semantics matter.

### 8) Embedding-based Similarity (TF-IDF, Code Models)
- Bag-of-tokens TF-IDF + cosine: simple baseline for near duplicates.
- Pretrained code models (e.g., CodeBERT, GraphCodeBERT) → vector embeddings; ANN search (HNSW/FAISS) for candidates.
- Pros: Captures broader similarity patterns; adjustable via thresholds.
- Cons: Model size, dependency, runtime; cross-language drift; reproducibility.
- Use: Optional tier after hash/LSH tiers; keep offline or gated behind extras.

## Indexing & Candidate Generation
- Exact/canonical hashes: dict map `hash → [unit_ids]`.
- MinHash LSH: band signatures into buckets; union candidates across shared buckets.
- SimHash: multi-probe via bit masks within Hamming radius r; classic partitioning or DKT multi-index.
- Inverted indices: tokens → posting lists; prune via DF thresholds to avoid boilerplate.
- ANN: HNSW/IVF-PQ for embeddings; cap results per query.

## Scoring & Clustering
- Scores:
  - Jaccard over shingles (exact or estimated via MinHash): s ∈ [0,1].
  - Cosine similarity for TF-IDF/embeddings.
  - Hamming distance d on b-bit simhash → similarity ≈ 1 - d/b.
  - AST distance normalized to [0,1] (1 - normalized edit distance).
- Aggregation:
  - Multi-tier cascade: exact → AST → (simhash|minhash) re-ranked by precise score.
  - Weighted ensembles possible; prefer simple, explainable scoring initially.
- Clustering:
  - Union-Find on pairs with score ≥ threshold.
  - Connected components over similarity graph.
  - Report per-cluster score range and exemplars.

## Normalization Design (Python)
- Text: strip comments/docstrings, normalize whitespace, unify quotes, remove trailing commas where safe, normalize numeric literals (optional).
- Tokens: split identifiers (snake/camel), lowercase keywords, mask identifiers and literals (Type-2).
- AST: replace Name/Attribute/Constant with placeholders retaining types and shapes; preserve control structures.

## Performance Considerations
- Pipeline: extract → normalize → fingerprint → index → candidates → score → cluster.
- Budgeting: limit candidates per unit; stop early when clusters formed; sample heavy buckets.
- Streaming/Incremental: index incrementally; cache per-file fingerprints keyed by mtime.
- Limits: warn when units > 20k; recommend scoping flags (`--include/--exclude`, `--depth`).

## Evaluation Plan
- Datasets:
  - Public: BigCloneBench (Java), CodeXGLUE tasks; adapt or create Python clone fixtures.
  - Synthetic: programmatically mutate functions (rename, reorder, insert/delete) to create labeled Type-1/2/3 sets.
- Metrics:
  - Pairwise: precision, recall, F1 at thresholds.
  - Cluster-level: B-Cubed precision/recall, Adjusted Rand Index.
  - Runtime/memory: throughput (units/sec), peak RAM.
- Ablations:
  - Shingle size (n), MinHash signatures length, LSH bands/rows.
  - SimHash bits (b) and radius (r).
  - Normalization toggles (mask identifiers, strip docstrings).
- Procedure:
  - Split: per-repo or per-function; ensure non-leakage.
  - Calibration: choose defaults for 0.90–0.95 recall on Type-1/2 while keeping precision > 0.95.

## Integration with Locus
- Encapsulate within `src/locus/similarity/` using Strategy pattern and factory.
- Stages: `extractor` (units) → `normalize` → `fingerprints/strategies` → `index` → `search`.
- CLI flags: strategy, threshold, candidate cap, JSON output.
- Reporting: clusters with score range, paths, qualnames, previews gated by `--no-code`.
- Caching: reuse `utils.file_cache` to store normalized/fingerprint artifacts by file mtime.

## Risks & Mitigations
- False positives on boilerplate: apply stop-token filters, DF caps, ignore trivial functions (e.g., < 3 statements), add per-language keyword whitelists.
- Performance on large repos: LSH/SimHash for sublinear candidate generation; cap candidates; sample heavy buckets.
- Parser/AST drift: pin Python version for AST normalization; defensively handle SyntaxError.
- Determinism: seed hashing/LSH; stable sorts for output.

## Roadmap (Targeted)
1) Extend normalization (strip comments/docstrings; identifier/literal masking) + tests.
2) AST canonical hashing strategy + tests for Type-2 clones.
3) SimHash candidate generation + Hamming thresholds + tests.
4) Token n-gram MinHash + LSH + parameterized thresholds + tests.
5) Report enhancements: score ranges, previews, `--report-duplicates-only`.
6) Evaluation harness: synthetic mutations, metrics dashboard; calibrate defaults.
7) Optional embeddings tier gated by extras; ANN index.

## References (Representative)
- MOSS & Winnowing (document fingerprinting).
- Deckard (AST-based clone detection).
- NiCad (near-miss clone detection with pretty-printing and filtering).
- SourcererCC (scalable clone detection via inverted index and filtering).
- SimHash (Charikar) for near-duplicate detection at scale.
- GumTree/Tree-diff (AST edit distance approximations).

