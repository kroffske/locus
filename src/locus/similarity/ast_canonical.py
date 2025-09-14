from __future__ import annotations

import ast
import textwrap


class _Canonicalize(ast.NodeTransformer):
    """Transforms a function AST into a canonical, identifier/literal-agnostic form.

    - Replaces all identifiers with a placeholder (e.g., ID)
    - Replaces attribute names with placeholder
    - Replaces string/number/bytes constants with normalized sentinel values
    - Drops leading docstring expressions in functions
    - Normalizes arg names and aliases
    """

    def visit_FunctionDef(self, node: ast.FunctionDef):  # type: ignore[override]
        node.name = "FUNC"
        node.decorator_list = [self.visit(d) for d in node.decorator_list]
        node.args = self.visit(node.args)  # type: ignore[assignment]
        # Drop docstring if present
        body = list(node.body)
        if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), (ast.Str, ast.Constant)):
            val = body[0].value
            if isinstance(val, ast.Str) or (isinstance(val, ast.Constant) and isinstance(val.value, str)):
                body = body[1:]
        node.body = [self.visit(b) for b in body]
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):  # type: ignore[override]
        return self.visit_FunctionDef(node)  # type: ignore[arg-type]

    def visit_Name(self, node: ast.Name):  # type: ignore[override]
        return ast.copy_location(ast.Name(id="ID", ctx=node.ctx), node)

    def visit_arg(self, node: ast.arg):  # type: ignore[override]
        node.arg = "ID"
        return node

    def visit_Attribute(self, node: ast.Attribute):  # type: ignore[override]
        node.value = self.visit(node.value)
        node.attr = "ID"
        return node

    def visit_alias(self, node: ast.alias):  # type: ignore[override]
        node.name = "ID"
        if node.asname is not None:
            node.asname = "ID"
        return node

    def visit_keyword(self, node: ast.keyword):  # type: ignore[override]
        # Normalize keyword name (None is for **kwargs)
        if node.arg is not None:
            node.arg = "KW"
        node.value = self.visit(node.value)
        return node

    def visit_Constant(self, node: ast.Constant):  # type: ignore[override]
        v = node.value
        if isinstance(v, str):
            return ast.copy_location(ast.Constant(value="STR"), node)
        if isinstance(v, (int, float, complex)):
            return ast.copy_location(ast.Constant(value=0), node)
        if isinstance(v, bytes):
            return ast.copy_location(ast.Constant(value=b"BYTES"), node)
        # Keep True/False/None as-is for structure
        return node

    # For Python <3.8 AST nodes (compat)
    def visit_Str(self, node: ast.Str):  # pragma: no cover - 3.8+ folds into Constant
        return ast.copy_location(ast.Str(s="STR"), node)

    def visit_Num(self, node: ast.Num):  # pragma: no cover
        return ast.copy_location(ast.Num(n=0), node)


def _count_nodes(node: ast.AST) -> int:
    count = 0
    for _ in ast.walk(node):
        count += 1
    return count


def canonicalize_function_source(source: str) -> str:
    """Return a canonical AST dump string for a function source snippet.

    Falls back to a trimmed, dedented form if parsing fails.
    """
    canon, _ = canonicalize_function_info(source)
    return canon


def canonicalize_function_info(source: str) -> tuple[str, int]:
    """Return (canonical_dump, node_count) for a function source snippet.

    - Canonicalizes identifiers and literals
    - Strips function docstrings
    - Returns a stable `ast.dump` and the node count of the transformed tree
    """
    try:
        src = textwrap.dedent(source)
        tree = ast.parse(src)
        tx = _Canonicalize()
        tree = tx.visit(tree)  # type: ignore[assignment]
        ast.fix_missing_locations(tree)
        return (
            ast.dump(tree, annotate_fields=True, include_attributes=False),
            _count_nodes(tree),
        )
    except Exception:
        # Conservative fallback: dedent + strip; node_count=0 signals unknown
        trimmed = textwrap.dedent(source).strip()
        return trimmed, 0
