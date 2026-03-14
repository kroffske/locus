# Delivered

- Implemented deterministic LLM package export for `locus analyze -o <dir>` with `manifest.json`, `tree.txt`, `description.md`, `part-*.txt`, and compatibility `index.txt`.
- Made `--include` / `--exclude` effective in the real scan/export path and switched the default ignore baseline to read-only `.gitignore` + built-in noise ignores.
- Added notebook export support with cells-only default behavior and explicit `--notebook-outputs` opt-in for outputs/media markers.
- Added regression coverage for mode dispatch, `.gitignore` directory rules, no-side-effect analysis, package surfaces, oversized-file splitting, and notebook rendering.
