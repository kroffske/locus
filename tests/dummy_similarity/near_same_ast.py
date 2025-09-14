"""
Near-same shape (AST-level similar) — NOT matched by exact strategy yet.

Purpose:
- Demonstrates a Type-2 clone idea (identifier renames) that should be
  caught by an AST-canonical strategy in the future.
"""


def util_sum(a, b):
    """Return the sum of two values (dummy)."""
    total = a + b  # renamed internal variable vs 'tmp'
    return total

