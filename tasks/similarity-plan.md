# Similarity Search Feature Plan

## Summary
- Goal: detect duplicate or near-duplicate functions across the codebase and surface clusters with evidence (score, locations, previews).
- Motivation: LLM-generated code often repeats functions; we want to catch and dedupe.
- Output: a report section (and optional JSON) listing similar/duplicate functions with scores, grouped by clusters.

## Non-Goals (initial)
- Cross-language similarity beyond Python.
- Refactor suggestions or automated edits (may come later via updater).
- Global project embeddings or remote services; keep offline by default.

## User Stories
- As a maintainer, I want to quickly find exact/near-duplicate functions across files.
- As a reviewer, I want to see clusters of similar functions with scores and code snippets.
- As a user, I can choose strategy and sensitivity, and export results to a file.

## CLI Additions
- `--similarity`: enable similarity analysis (default: off for performance).
- `--sim-strategy {exact,ast,tokens,simhash,auto}`: choose detection method (default: `auto`).
- `--sim-threshold FLOAT`: similarity threshold (strategy-specific; default sensible per strategy).
- `--sim-max-candidates INT`: cap candidate comparisons per unit (default: 2000 for large repos).
- `--sim-output PATH`: optional JSON dump of raw results.
- `--report-duplicates-only`: only show clusters with similarity >= threshold.
- `--include-tests/--exclude-tests`: reuse existing include/exclude where possible.

## Architecture
Introduce a new, modular package to avoid bloating core:

```
src/locus/similarity/
  __init__.py          # Facade entrypoints
  types.py             # Dataclasses: CodeUnit, Fingerprint, Match, Cluster
  extractor.py         # Parse files → function-level CodeUnit with metadata
  normalize.py         # Text/AST normalization utilities
  fingerprints.py      # Strategy-specific fingerprints + helpers
  strategies.py        # Strategy pattern implementations
  index.py             # Candidate indexing (LSH/SimHash buckets, inverted index)
  search.py            # Orchestrates: extract → index → compare → cluster
```

Integration points:
- `core/orchestrator.py`: if `args.similarity`, call `similarity.search.run(...)` after standard analysis.
- `cli/args.py`: add flags above.
- `formatting/report.py`: add a new section renderer for clusters.
- `utils/file_cache.py`: optionally cache normalized text/AST fingerprints by file mtime.

## Data Model (types)
- `CodeUnit`: { id, file, rel_path, language ("py"), qualname (e.g., module.Class.func), span (start,end), source, ast (optional), normalized_text }.
- `Fingerprint`: { strategy, value, aux }.
- `Match`: { unit_a_id, unit_b_id, score (0..1), strategy, evidence }.
- `Cluster`: { id, members: [unit_id], centroid/evidence }.

## Extraction (extractor.py)
- Walk resolved Python files (reuse scanner results).
- Use `ast.parse` to collect:
  - Functions (`ast.FunctionDef`, `ast.AsyncFunctionDef`) and class methods (with class context).
  - Record qualname, args signature, decorators (for context), start/end lines.
  - Retrieve exact source slice from file contents (via `ast.get_source_segment`).
  - Optional: store AST for strategy `ast`.

## Normalization (normalize.py)
- Text normalization: strip comments, docstrings, collapse whitespace, normalize quotes, remove trailing commas where safe.
- AST normalization: dump canonical form masking identifiers and literals (e.g., replace names with placeholders), keep structure and operation types.

## Strategies (strategies.py + fingerprints.py)
- Strategy pattern: `SimilarityStrategy` interface with `prepare(units)`, `candidates(unit)`, `score(a, b)`.
- Implementations:
  1) `ExactHashStrategy` (fast exact duplicates):
     - Fingerprint = `sha256(normalized_text)`; identical hash => duplicates (score 1.0).
  2) `AstHashStrategy` (near-duplicate structure):
     - Fingerprint of canonical AST; exact match => strong duplicate; optional subtree comparison for near-miss.
  3) `TokenNgramStrategy` (shingling):
     - Tokenize normalized text → 5-gram shingles; MinHash signatures; Jaccard via LSH for candidates.
  4) `SimHashStrategy` (locality-sensitive):
     - Token features → SimHash; Hamming distance buckets yield candidates; fast for large repos.
  5) `AutoStrategy`:
     - Cascade: exact → ast → simhash → ngram as fallback within budget; stops when clusterable.

Notes:
- Avoid embeddings at start. Optionally add in future behind extra `.[similarity]`.
- All strategies expose tunable parameters (n-gram size, bands/rows for LSH, simhash bits, thresholds).

## Indexing (index.py)
- Exact/Ast: dictionary from hash → list[unit_id].
- MinHash LSH: banded signature → bucket map; `candidates(unit)` from overlapping buckets.
- SimHash: multi-index by bit masks for Hamming radius r (e.g., 2–3 bits for ~0.9 similarity).

## Search Orchestration (search.py)
1) Extract units.
2) Build selected strategy and index via factory.
3) Generate candidates per unit (cap via `--sim-max-candidates`).
4) Compute pairwise scores; emit matches above `--sim-threshold`.
5) Cluster matches (Union-Find or connected-components) to group duplicates.
6) Return clusters and representative evidence (top pairs, representative snippet).

## Reporting (formatting/report.py)
- New section: "Similar or Duplicate Functions" with:
  - Cluster header: score range, size, exemplar qualname.
  - Members: file:line span, qualname, strategy, score.
  - Optional code preview (first N lines) gated by `--no-code`.
- `--sim-output`: emit JSON with units, matches, clusters for tooling.

## Configuration Defaults
- `auto` strategy with thresholds: exact=1.0; ast=1.0; simhash ≥ 0.90; ngram Jaccard ≥ 0.85.
- Max units: warn if > 20k functions; suggest scoping flags.

## Testing Plan
- Unit: extractor produces correct units and spans on fixtures (nested classes, decorators, async).
- Unit: normalization removes comments/docstrings but preserves structure.
- Unit: strategies:
  - Exact duplicates across files detected.
  - Small identifier changes caught by AST strategy.
  - Token-level additions/removals still produce high similarity via n-grams/simhash.
- Integration: CLI flags wire through and report renders clusters deterministically.
- Performance: synthetic repo with 5k–10k functions completes under target time and memory.

## Milestones
1) Extractor + normalization + exact duplicates (MVP).
2) AST canonicalization + exact AST hash.
3) SimHash for scalable near-duplicate search.
4) N-gram MinHash LSH for higher recall.
5) Report section + JSON export.
6) CLI polish + docs.

## Risks & Mitigations
- False positives with token strategies: provide previews and adjustable thresholds.
- Performance on very large repos: use LSH/SimHash and candidate caps; stream processing.
- AST normalization corner cases: start with conservative masking; add tests.

## Design Rationale: Where to Put Code
- Create `src/locus/similarity/` as a dedicated package:
  - Keeps core pipeline slim; exposes a clean facade (`similarity.search.run`).
  - Enables future reuse (e.g., updater could consume similarity data).
  - Strategy pattern avoids branching in core and allows adding methods without touching orchestrator.
- Only minimal changes in:
  - `cli/args.py` (flags), `core/orchestrator.py` (one call + data attachment), `formatting/report.py` (new section). Everything else encapsulated.

## Prototype Pseudocode
```python
# extractor.py
def extract_code_units(files):
    units = []
    for f in files:
        src = read_text(f)
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno
                end = node.end_lineno or start
                snippet = src.splitlines()[start-1:end]
                qual = qualify(node, tree)
                units.append(CodeUnit(file=f, qualname=qual, span=(start,end), source='\n'.join(snippet)))
    return units

# normalize.py
def normalize_text(source: str) -> str:
    src = strip_docstrings_and_comments(source)
    src = collapse_whitespace(src)
    return src

# strategies.py (exact)
class ExactHashStrategy(SimilarityStrategy):
    def prepare(self, units):
        self.map = defaultdict(list)
        for u in units:
            key = sha256(normalize_text(u.source).encode()).hexdigest()
            self.map[key].append(u.id)
    def candidates(self, unit):
        key = sha256(normalize_text(unit.source).encode()).hexdigest()
        return self.map.get(key, [])
    def score(self, a, b):
        return 1.0 if a.id != b.id and self._key(a)==self._key(b) else 0.0
```

## Acceptance Criteria
- Running `locus analyze --similarity` shows a “Similar or Duplicate Functions” section with at least exact duplicates grouped.
- `--sim-strategy ast` detects renamed-but-otherwise-identical functions in tests.
- JSON export matches schema and includes reproducible IDs.

## Next Steps
- Approve layout under `src/locus/similarity/` and CLI flags.
- Implement Milestone 1 and wire into orchestrator + report.

