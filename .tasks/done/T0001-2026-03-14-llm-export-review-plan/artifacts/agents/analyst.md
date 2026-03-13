# Analyst — execution-facing requirements (T0001)

## 1) Restated goal

Improve `locus` analyze/export workflow so that a user (or agentic LLM tool-use flow) can reliably produce an LLM-ready export of a repository:
- without having to copy/commit ignore/config files into the analyzed project
- with convenient include/exclude/grep-like selection controls
- producing **1–10** (or user-requested count) export “parts” containing **tree + descriptions**
- with acceptable export speed and basic performance visibility
- including **Jupyter notebook (`.ipynb`) support**

This artifact defines **acceptance criteria and assumptions** for a *future implementation task* (this task remains review/planning only).

## 2) In-scope / out-of-scope (for the future implementation)

### In scope
- CLI/UX changes for analyze/export that make the tool “LLM-friendly” (deterministic output, stable grouping, predictable files on disk).
- Ignore/include/exclude behavior that works **without** placing ignore files inside the analyzed repo.
- Convenience surface for rg/grep-style conditions (at least: file path filters + content regex filtering).
- Export chunking into N parts + a manifest with tree + per-part (and/or per-file) description.
- Jupyter notebook export (at minimum: include notebooks in export in an LLM-friendly representation).
- Performance review + non-flaky perf smoke checks and/or timing instrumentation (baseline + regression guard).

### Out of scope
- Implementing or changing optional MCP flows unless strictly required by export/analyze (keep optional boundaries explicit).
- Full re-implementation of ripgrep; using `rg` as an external optional backend is allowed but not required unless mandated.
- Executing notebooks, rendering rich outputs (images), or resolving notebook dependencies at runtime.
- Large-scale benchmarking across many external repos (can be a follow-up task).

## 3) Assumptions + ambiguity list (needs decisions)

### Assumptions (unless contradicted later)
- The “LLM export” output is primarily intended to be consumed as **text** (Markdown and/or JSON metadata + plain file contents).
- The tool must **not modify** the analyzed repository by default (no writing ignore/config files into it).
- The export command writes to a user-provided output directory (or a safe default outside the repo), and is safe to re-run (idempotent or clearly overwriting with `--force`).

### Ambiguities / open questions
1. **Target consumer**: “LLM uses the utility” means
   - (A) human runs CLI and feeds output into an LLM, or
   - (B) an agentic LLM runs the CLI itself and parses outputs.
   Decision impacts: output strictness (machine-parseable manifest vs human-readable only).
2. **Export format**:
   - only Markdown, or Markdown + JSON manifest, or JSON-only with separate content blobs.
3. **“tree + description”** definition:
   - tree of repo paths only, or tree of exported subset only; description per exported *part* vs per *file*.
4. **“grep/rg conditions”** scope:
   - selecting files by *path only*, or selecting by *file content matches*, or extracting only matching *snippets*.
5. **Chunking criteria**:
   - by file count, byte size, estimated token count, or a mix; and how to handle single huge files.
6. **Notebook representation**:
   - convert `.ipynb` to Markdown (cells), to `.py` (code cells), or include raw JSON; include/exclude outputs.
7. **Performance target**:
   - explicit numeric budgets vs “no regression vs baseline”; depends on current behavior and typical repo sizes.

## 4) Acceptance criteria (execution-facing), grouped by theme

### A. LLM-friendly UX / output determinism
- Export produces a **manifest** describing: tool version, analyzed root, filters applied, export part count, and a stable ordered list of included paths.
- For the same repo state + same args, export results are **stable/deterministic** (ordering, grouping, and manifest are reproducible).
- Export includes a **tree view** of the included set (or whole repo, per decision) and a **short description** for each export part (or per file, per decision).

### B. Ignore rules without copying ignore files into the analyzed repo
- User can supply ignore patterns via CLI flags and/or a config file located **outside** the analyzed repository.
- User can reference one or more ignore files by path (e.g., `--ignore-file /path/to/ignore`), without requiring that file to exist inside the analyzed repo.
- Default ignores include common noise (e.g., `.git/`, `node_modules/`, `.venv/`, build artifacts), with an explicit way to disable/override.

### C. Convenient rg/grep-style selection conditions
- CLI supports convenient expressions for:
  - include/exclude by path (globs)
  - include by content match (regex and/or fixed string)
- Invalid patterns/regex yield a clear error message and non-zero exit code.
- The selection rules are documented with examples that map to familiar `rg`/`grep` mental models.

### D. Chunked export into N files (1–10 or requested count)
- User can request a target number of export parts (e.g., `--parts N`), and the exporter writes **≤ N** part files plus a manifest.
- Default behavior yields a small number of parts suitable for LLM ingestion (e.g., 1–10).
- Each part file includes:
  - a header with the subset scope (paths included)
  - content blocks for included files (or a clear pointer scheme), with unambiguous boundaries
  - per-part description (or per-file description) sufficient to choose what to read next
- Export handles edge cases:
  - very large files (configurable: skip, truncate with notice, or split)
  - binary files (skipped by default with a manifest entry stating why)

### E. Speed / performance review
- Export command reports basic timing info when requested (e.g., `--timings`) covering scan, selection, and write phases.
- There is at least one **perf smoke check** (non-flaky) to detect accidental O(N²) regressions on a representative fixture repo or generated fixture.
- No major speed regression relative to current baseline is introduced (exact threshold to be set after measuring current state).

### F. Jupyter notebooks (`.ipynb`) support
- `.ipynb` files can be included in the export (not silently skipped).
- Notebook export is in an LLM-friendly representation:
  - preserves cell order and types (markdown/code)
  - excludes large/irrelevant metadata by default
  - includes outputs only if explicitly enabled (or a documented default is chosen)
- Failure to parse a notebook yields a clear warning/error and a deterministic behavior (skip-with-reason vs fail-fast, per decision).

### G. Docs, tests, and safety
- Documentation updates cover: new CLI flags, examples, and recommended defaults for LLM use.
- Tests cover: ignore behavior, selection rules, chunking determinism, notebook conversion basics, and key error modes.
- Export never writes into the analyzed repo by default; any write requires explicit output path (or explicit `--in-place`-style opt-in if such a mode exists).

## 5) Suggested implementation phases (follow-up dev task)

1. **Decisions + baseline**
   - Lock open questions (format, chunking heuristic, notebook representation, perf target).
   - Measure current export/analyze timing baseline on a fixture repo.
2. **Ignore/config + selection surface**
   - Implement external ignore-file support + CLI/config wiring.
   - Implement path + content filters (rg/grep-like surface), with docs/examples.
3. **Chunked export + manifest**
   - Implement N-part export, deterministic ordering, tree rendering, and per-part/per-file descriptions.
   - Add large-file/binary handling rules.
4. **Notebook support**
   - Implement `.ipynb` conversion pipeline and integrate into export.
   - Add tests and clear flags for outputs/metadata inclusion.
5. **Perf instrumentation + regression guard + docs**
   - Add timing instrumentation, perf smoke check(s), and update docs.

