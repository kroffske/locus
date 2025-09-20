# AI Agent Guidelines — Locus MCP (System Prompt)

**Goal:** produce clean, reliable code changes with clear separation of logic and a strict, file-by-file reply format.

---

## 1) Response Contract (very important)

* **Always answer file-by-file.**
  For **every changed file**, output one code block that **starts with** the file header comment:

  ```
  # source: <relative/path/from/repo/root>
  ```
* **Deleted or now-empty files must still be listed** with a header and a single line:

  ```
  # todo delete
  ```
* **One code block per file.** No extra prose between blocks. Use correct language fences (e.g., \`\`\`python).
* **Include all touched files** (new, modified, renamed, deleted).

  * **Rename:** output a `# todo delete` block for the **old path** and a full code block for the **new path**.
* When asked to implement or refactor, **output only these file blocks** (no narrative outside the blocks).

**Examples**

*New/changed file*

```python
# source: packages/locus/locus/search/engine.py
from __future__ import annotations
from typing import Protocol, Iterable, List, Dict, Any

class VectorStore(Protocol):
    def query(self, query_vec: List[float], k: int, where: Dict[str, Any] | None = None): ...
    def keyword(self, terms: List[str], k: int, where: Dict[str, Any] | None = None): ...
    def get_file(self, rel_path: str) -> Iterable[dict]: ...

# ...implementation...
```

*Deleted file*

```python
# source: packages/locus/locus/legacy/old_engine.py
# todo delete
```

*Renamed file (old → new)*

```python
# source: packages/locus/locus/old/path/module.py
# todo delete
```

```python
# source: packages/locus/locus/new/path/module.py
# ...new implementation...
```

---

## 2) Separation of Logic (minimal architecture rule)

* Keep **core logic pure** (no I/O, no globals, deterministic; easy to test).
* Put I/O, config parsing, logging, and integration code at **boundaries** (thin wrappers).
* Formatting/assembly code should not contain business logic.

---

## 3) Code Style (Python)

**General**

* Follow PEP 8 naming; **line length ≤ 100**.
* **4-space indent**, UTF-8, **trailing newline**, no trailing whitespace.
* Prefer **explicit** over implicit; small, focused functions.

**Typing**

* Use **type hints everywhere** (params, returns, attrs).
* Prefer `from __future__ import annotations`.
* Use `TypedDict` / `dataclass(frozen=True)` / `Protocol` for structured/contracted data.
* Avoid `Any`; use `cast(...)` sparingly with a comment.

**Imports**

* Order: **stdlib → third-party → first-party**, separated by blank lines.
* No wildcard imports; no unused imports.

**Strings & f-strings**

* Use **f-strings** for interpolation; double quotes by default.

**Docstrings & comments**

* Public modules/classes/functions: **docstring** (Google or NumPy style).
* Keep comments **why-focused** (not what). TODO/FIXME with ticket/issue ref.

**Immutability & side effects**

* Avoid mutable default args.
* No side effects at import time (no I/O, no network, no heavy computation).

**Logging**

* `logger = logging.getLogger(__name__)` per module.
* No `print`.
* Messages actionable; do not log secrets.

**Exceptions**

* Raise **specific** exception types; never bare `except:`.
* Fail fast with clear messages; don’t return sentinel `None` on errors unless typed as optional and documented.

**Performance**

* Avoid quadratic scans; batch work; short-circuit early; measure hot paths.

---

## 4) Configuration Conventions (describe, don’t install)

* **Profiles**: keep environment-selectable profiles (e.g., `local`, `cloud`) that tune behavior without changing code.
* **Style config (abstract)**:

  * `line_length: 100`
  * `indent: 4`
  * `string_quotes: "double"`
  * `disallow_wildcard_imports: true`
  * `import_order: ["stdlib", "third_party", "first_party"]`
  * `max_cyclomatic_complexity: 10`
  * `typing: strict`
  * `allow_todo_delete_blocks: true` (enforce response contract)
* **Test discovery**: files `test_*.py`, classes `Test*`, funcs `test_*`.
* **Paths**: use POSIX-style repo-relative paths in headers (`# source: ...`).

*(Do not include installation or tool invocation commands in responses.)*

---

## 5) Quality & Testing

* **Unit tests** for core logic; integration tests for boundaries.
* **AAA pattern** (Arrange-Act-Assert); isolate side effects behind fakes.
* Edge cases: empty inputs, large inputs, invalid types, failure modes.
* Deterministic behavior; avoid time/randomness unless seeded.

---

## 6) Anti-Patterns to Avoid

* Mixing I/O with core logic; hidden globals/config singletons.
* Silent failures (returning `None` on error without typing/notice).
* Catch-all exceptions; swallowing stack traces.
* Over-broad interfaces; passing giant config objects where a few params suffice.
* Non-deterministic retrieval/ordering without explicit sort/score.
* Unbounded output: keep code blocks concise and relevant.

---

## 7) When Producing Code in Chat

* **Only** output the file blocks defined in the Response Contract.
* **Include every touched file**, even if empty/deleted (with `# todo delete`).
* Use **correct relative paths** and **language fences**.
* No execution logs, no install commands, no linter/formatter commands.
* If uncertain, **prefer minimal, pure core changes** and leave clear TODOs with rationale.
