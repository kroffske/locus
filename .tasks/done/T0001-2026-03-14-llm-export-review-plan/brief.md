# Brief

## Execution focus

Собрать source-backed review текущей архитектуры export/analyze flow и выпустить исполнимый план переделки под LLM usage без продуктовых изменений в этом таске.

## Target outcome

Пакет артефактов должен ответить на три вопроса:

1. Что уже умеет `locus` по export/analyze и где это реализовано.
2. Чего не хватает относительно пользовательского запроса и какие есть архитектурные ограничения.
3. В каком порядке и с каким verification path это безопасно реализовывать.

## Scope

- CLI entrypoints и аргументы `analyze`.
- Core/export/config logic, влияющая на include/exclude, grouping, tree/report rendering и output layout.
- Наличие или отсутствие notebook support.
- Источники потенциальных bottlenecks в выгрузке.
- Existing tests/docs, покрывающие эти зоны.

## Out of scope

- Реализация фич.
- Бенчмарки на больших внешних репозиториях.
- Изменения update/sim/MCP кроме случаев, когда они пересекаются с export path.

## Acceptance criteria

- Для каждого пункта запроса есть статус: already supported / partially supported / missing / risky.
- Для каждого gap есть reference на конкретные файлы/модули и краткое объяснение текущего ограничения.
- План разбит на небольшие workstreams с verification signal и порядком выполнения.
- Зафиксированы assumptions и неясности, которые реально требуют user/stakeholder decision.

## Current-state assessment

- LLM-friendly export UX: partially supported.
  - Есть interactive/report/collection modes, flat summary и `index.txt`, но нет единого machine-friendly manifest/part contract.
- Ignore rules without copying files into analyzed repo: partially supported.
  - Текущий config loader опирается на `.locus/allow` и `.locus/ignore` и при отсутствии конфигов может попытаться создать их внутри target repo.
- Export into requested 1-10 files with tree + description: missing.
  - Группировка зависит от `grouping_rules` и `max_lines_per_file`; нет CLI-level count control и collection-mode tree artifact.
- Convenient grep/rg-style conditions: partially supported with a correctness gap.
  - Есть `--include` / `--exclude`, flat output и grep hints, но `include_patterns`/`exclude_patterns` сейчас не участвуют в actual scan path.
- Export speed review: partially supported.
  - Есть `FileCache` и line-based splitting, но нет analyze/export perf checks или timing instrumentation.
- Jupyter notebook export: missing.
  - `*.ipynb` не входят в default allow list и не имеют notebook-aware conversion pipeline.

## Review evidence / touchpoints

- CLI surface: `src/locus/cli/args.py`, `src/locus/cli/main.py`
- Scan/config path: `src/locus/core/orchestrator.py`, `src/locus/core/scanner.py`, `src/locus/utils/config.py`, `src/locus/utils/helpers.py`
- Collection export + descriptions: `src/locus/core/modular_export.py`, `src/locus/formatting/code.py`, `src/locus/formatting/tree.py`
- Existing coverage: `tests/test_cli.py`, `tests/test_core.py`, `tests/test_utils.py`, `tests/test_formatting.py`

## Proposed implementation workstreams

1. Baseline + frozen contract
   - Use `.gitignore` as the default ignore baseline, keep CLI selection flags, and record the chosen packing / notebook defaults.
2. No-touch filtering surface
   - Apply CLI include/exclude correctly while avoiding `.locus` bootstrap into target repos for the default path.
3. Count-aware LLM export package
   - Add manifest/tree/description artifacts and hybrid packing with target ~5k lines per part and hard ceiling ~10k lines.
4. Notebook support
   - Add `*.ipynb` intake and LLM-friendly conversion for markdown/code cells; expose outputs/media through an explicit flag when available.
5. Perf + verification + docs
   - Add timing instrumentation or perf smoke, CLI e2e coverage, and doc updates.

## Verification plan

- Repo scout: найти и описать текущие entrypoints, config surfaces, formatter/export modules, существующее покрытие тестами.
- Verify scout: предложить минимальный verification path для будущей реализации и отметить, где нужны perf-smoke checks.
- Manager integration: собрать итоговый план, QA planning package и выбрать closure state.
