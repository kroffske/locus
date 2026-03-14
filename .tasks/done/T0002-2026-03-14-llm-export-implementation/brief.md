# Brief

## Execution focus

Реализовать LLM-friendly export workflow поверх текущего `analyze` path без большого рефакторинга и без расширения optional MCP surface.

## Frozen product contract

- Default ignore baseline: использовать `.gitignore` из repo/config root вместе со встроенными noise-игнорами; existing `.locus/allow` / `.locus/ignore` остаются поддержанным override path, но analyze по умолчанию не должен создавать `.locus/*`.
- Output mode contract: `-o <path-without-extension>` трактуется как directory export; если такой путь уже существует и это не директория, CLI должен дать ясную ошибку, а не молча писать report-like файл.
- Filter contract: `--include` / `--exclude` должны реально влиять на scan/export path; `--exclude` остается авторитетным и не должен теряться после dependency resolution.
- Export package contract: directory mode выдает детерминированный LLM package с `manifest`, `tree`, `description` и part-файлами; старый `index.txt` можно сохранить только как compatibility/helper surface, если он отражает новый part contract.
- Packing contract: target около `5k` строк на part, hard ceiling около `10k`; одиночные большие файлы не пропускаются молча, а режутся на continuation parts с явной записью в manifest.
- Notebook contract: `*.ipynb` входят в export в LLM-friendly виде (markdown/code cells по порядку) без шумных metadata/outputs по умолчанию; outputs/media включаются отдельным explicit flag.

## Baseline evidence

- `PYTHONPATH=src python3 -m pytest tests/test_cli.py tests/test_core.py tests/test_formatting.py tests/test_utils.py -q` -> `21 passed in 2.16s`.
- `PYTHONPATH=src python3 -m locus analyze -o /tmp/locus-report-baseline.NkqXYS.md -p -t -a --no-code -f` -> success, `real 1.60`, side effect: создается `.locus/settings.json`.
- `PYTHONPATH=src python3 -m locus analyze -o /tmp/locus-export-baseline.9621 --include '**/*.py' -p` -> success, `real 1.57`, но результатом стал один report-like файл, а не directory export.
- `PYTHONPATH=src python3 -m locus analyze -o /tmp/locus-export-baseline.r67Kyn --include '**/*.py' -p` при существующей директории -> `IsADirectoryError`.

## Implementation boundaries

- CLI I/O и mode selection держать в `src/locus/cli/`.
- Reusable selection/ignore logic держать в `src/locus/core/` и `src/locus/utils/config.py`.
- Export packaging и part writing держать в `src/locus/formatting/` / `src/locus/core/modular_export.py`.
- Notebook parsing не должен тащить optional heavy deps; использовать text/JSON conversion в base CLI.
- Docs выровнять минимум в `README.md` и `.miloc/docs/*`, если CLI/output contract меняется.

## Expected verification

- Fast test slice: `PYTHONPATH=src python3 -m pytest tests/test_cli.py tests/test_core.py tests/test_formatting.py tests/test_utils.py -q`
- New/updated export smoke: `PYTHONPATH=src python3 -m locus analyze -o /tmp/locus-export --include "**/*.py" -p`
- No-touch check: analyze/export default path не создает `.locus/settings.json` или другие repo-local config artifacts.
- Perf smoke: report/export timings на локальном repo остаются воспроизводимыми и documented.
