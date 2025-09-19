"""
Small behavioral difference — NOT matched by exact strategy.

Purpose:
- Slightly different logic (adds 1) to show a near-miss that should not be
  clustered under exact hashing. Token or AST-based strategies could choose
  to treat this as similar with a threshold, but not a duplicate.
"""


def util_sum(a, b):
    """Return the sum of two values (dummy)."""
    tmp = a + b + 1  # small change vs exact samples
    return tmp
