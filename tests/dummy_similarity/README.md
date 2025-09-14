# Dummy Similarity Samples

Purpose: Provide small, hand-crafted examples to manually exercise `locus analyze --similarity`.

What’s included:
- Exact duplicates (should be clustered by the current exact strategy)
- Whitespace-only variations (should also cluster)
- Small code changes (should NOT cluster under exact strategy; expected with future AST/token strategies)

How to run:
- Interactive: `locus analyze -p --similarity`
- Report: `locus analyze --similarity -o dummy-similarity.md`

Expected behavior (MVP exact strategy):
- Files `exact_a.py` and `exact_b.py` cluster together.
- `whitespace_variant.py` should cluster with the exact functions.
- `near_same_ast.py` and `small_diff.py` will NOT cluster (changes beyond whitespace).
