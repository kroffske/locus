---
schema_version: task.v2
id: T0002
competition_slug: "locus"
title: "Реализация LLM-friendly export workflow"
summary: "Исправить фильтрацию analyze/export, перейти на gitignore-based ignore baseline, добавить hybrid export c tree/manifest, notebook cells + optional outputs/media и perf checks."
status: PLANNED
priority: P1
stage: spec
tags: [cli, llm, export]
owner: null
dependencies:
  - T0001
created_at: "2026-03-13T22:58:16Z"
updated_at: "2026-03-13T23:06:00Z"
links:
  - .tasks/done/T0001-2026-03-14-llm-export-review-plan/brief.md
  - .tasks/done/T0001-2026-03-14-llm-export-review-plan/artifacts/plan.md
  - .tasks/done/T0001-2026-03-14-llm-export-review-plan/artifacts/qa.md
artifacts:
  - artifacts/plan.md
next_steps:
  - "Перевести task в `working/` и зафиксировать baseline/perf signal."
  - "Назначить dev owner."
---

# T0002: Реализация LLM-friendly export workflow
**Stage:** spec
**Tags:** cli, llm, export

## Контекст

T0001 зафиксировал текущие gaps в `locus analyze` / collection export path и подготовил execution-facing plan.

## Цель

Реализовать LLM-friendly export workflow с использованием `.gitignore` как default ignore baseline, без записи служебных config-файлов в анализируемый репозиторий и с предсказуемым выходом для tool-use сценариев.

## Не-цели

- Не расширять optional MCP surfaces без прямой необходимости.
- Не превращать задачу в большой рефакторинг unrelated analyze/update/sim code paths.

## План работ

- [ ] Зафиксировать output contract и perf baseline.
- [ ] Исправить filtering и gitignore-based ignore UX без repo-touch bootstrap.
- [ ] Добавить hybrid export package с tree/manifest/description.
- [ ] Добавить notebook export path с optional outputs/media flag.
- [ ] Добавить verification + perf smoke + doc updates.

## Критерии приёмки

- [ ] `--include` / `--exclude` реально влияют на analyze/export path и покрыты тестами.
- [ ] Default ignore baseline опирается на `.gitignore`, не требуя `.locus/ignore` как обязательного user-facing шага.
- [ ] Export использует hybrid packing contract: target около 5k строк на part, hard ceiling около 10k строк.
- [ ] Export package содержит tree/manifest/description и пригоден для LLM/tool-use workflow.
- [ ] `*.ipynb` экспортируются в LLM-friendly представлении; outputs/media можно включать отдельным флагом.
- [ ] Есть lightweight perf verification и обновленная документация.

## Как проверить

- Команды:
  - `PYTHONPATH=src python3 -m pytest tests/test_cli.py tests/test_core.py tests/test_formatting.py tests/test_utils.py -q`
  - `PYTHONPATH=src python3 -m locus analyze -o /tmp/locus-export --include "**/*.py" -p`
  - `time -p PYTHONPATH=src python3 -m locus analyze -o /tmp/locus-export --include "**/*.py"`
  - Notebook smoke на fixture `*.ipynb`
- Ожидаемый сигнал:
  - CLI filters, export packaging, notebook path и perf smoke дают воспроизводимый ожидаемый результат.

## Риски / edge cases

- Нужно явно определить overflow-поведение для одиночных больших файлов, которые не помещаются в target 5k строк и приближаются к 10k ceiling.
- Notebook outputs/media могут раздувать output, поэтому их нужно держать за explicit flag и подчинить общему packing contract.
- Нельзя сломать base CLI и optional MCP boundary.

## Ссылки / артефакты

- `.tasks/done/T0001-2026-03-14-llm-export-review-plan/brief.md`
- `.tasks/done/T0001-2026-03-14-llm-export-review-plan/artifacts/agents/repo_scout.md`
- `.tasks/done/T0001-2026-03-14-llm-export-review-plan/artifacts/agents/verify_scout.md`
- `.tasks/done/T0001-2026-03-14-llm-export-review-plan/artifacts/agents/analyst.md`
