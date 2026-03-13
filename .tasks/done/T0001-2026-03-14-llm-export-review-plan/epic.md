---
schema_version: task.v2
id: T0001
competition_slug: "locus"
title: "Ревью и план переделки LLM-экспорта"
summary: "Проверить текущий analyze/export путь Locus и собрать исполнимый план по LLM-oriented export: ignore/filter UX, лимит числа файлов, tree+описания, perf и notebooks."
status: DONE
priority: P1
stage: release
tags: [cli, llm, export, review]
owner: "miloc-manager"
dependencies: []
created_at: "2026-03-13T22:52:05Z"
updated_at: "2026-03-13T23:06:00Z"
links:
  - README.md
  - .miloc/goal.md
  - .miloc/roadmap.md
artifacts:
  - request.md
  - brief.md
  - artifacts/plan.md
  - artifacts/agents/repo_scout.md
  - artifacts/agents/verify_scout.md
  - artifacts/agents/analyst.md
  - artifacts/qa.md
  - delivered.md
next_steps:
  - "Когда потребуется реализация, перевести `.tasks/planned/T0002-2026-03-14-llm-export-implementation/` в `working/`."
---

# T0001: Ревью и план переделки LLM-экспорта
**Stage:** release
**Tags:** cli, llm, export, review

## Контекст

Пользователь запросил менеджерский разбор текущей утилиты `locus` и план улучшений для LLM-oriented export workflow. Фокус не на немедленной реализации, а на ревью текущего состояния, gaps и исполнимом плане переделки.

## Цель

Подготовить подтвержденный артефактами обзор текущего состояния и план изменений для export/analyze flow, чтобы LLM мог использовать результат без лишней ручной подготовки.

## Не-цели

- Не реализовывать продуктовые изменения в этом таске.
- Не трогать optional MCP path, если для задачи достаточно base CLI.
- Не переписывать unrelated docs/code вне task artifacts.

## План работ

- [x] Собрать repo review по текущим export/analyze entrypoints, конфигам и ограничениям.
- [x] Зафиксировать целевое поведение, допущения и acceptance criteria для LLM export workflow.
- [x] Свести findings в конкретный план изменений, verification path и follow-ups.

## Критерии приёмки

- [x] Есть обзор текущих путей `analyze` / modular export / ignore filtering / formatter surfaces с ссылками на файлы.
- [x] Есть явный gap analysis по пунктам запроса: ignore без копирования файлов в проект, выбор 1-10 файлов, tree + description, grep/rg UX, скорость выгрузки, notebooks.
- [x] Есть исполнимый план с очередностью работ, рисками и verification strategy.

## Как проверить

- Команды:
  - `rg -n "modular|export|ignore|include|exclude|notebook|ipynb|tree|description|summary" src tests README.md`
  - `PYTHONPATH=src python3 -m locus analyze --help`
  - При необходимости: точечные `pytest`/smoke checks по найденным entrypoints
- Ожидаемый сигнал:
  - Артефакты task folder содержат source-backed review и конкретный план без продуктовых изменений.

## Риски / edge cases

- Реализация должна уважать выбранный baseline `.gitignore`, не ломая существующие selection flags и не навязывая запись `.locus/*` в target repo по умолчанию.
- В репо уже есть грязный worktree по docs; task artifacts должны жить изолированно под `.tasks/**`.
- `.venv` root-owned; любые команды, которые упрутся в permission issues внутри canonical env, надо фиксировать как runtime blocker, а не обходить ad-hoc env.

## Ключевые findings

- `--include/--exclude` описаны в CLI, но текущий `analyze()` не применяет эти фильтры в scan path.
- Базовый config path пытается создавать `.locus/*` в анализируемом репозитории, что конфликтует с требованием no-touch ignore workflow.
- Collection export уже умеет `index.txt` с description/lines, но не умеет count-aware packing и не пишет отдельный tree/manifest артефакт для directory mode.
- `*.ipynb` не входят в default allow list и не имеют notebook-aware formatter/processor.
- Для analyze/export нет perf harness: есть только локальные оптимизации вроде `FileCache` и similarity benchmarks.

## Зафиксированные решения

- Default ignore baseline: использовать `.gitignore`; отдельный `ignore-file` как обязательная surface не нужен.
- Packing contract: hybrid heuristic с разумным размером частей; целевой размер около 5k строк на part, жесткий ceiling около 10k строк.
- Notebook export: всегда поддерживать markdown/code cells; outputs/media включать отдельным флагом, когда они доступны.

## Ссылки / артефакты

- `.tasks/done/T0001-2026-03-14-llm-export-review-plan/request.md`
- `.tasks/done/T0001-2026-03-14-llm-export-review-plan/brief.md`
- `.tasks/done/T0001-2026-03-14-llm-export-review-plan/artifacts/plan.md`
- `.tasks/done/T0001-2026-03-14-llm-export-review-plan/artifacts/qa.md`
- `.tasks/done/T0001-2026-03-14-llm-export-review-plan/delivered.md`
- `.tasks/planned/T0002-2026-03-14-llm-export-implementation/epic.md`

## Комментарии

Таск менеджерский закрыт: review + planning package собраны, решения по спорным местам приняты, дальнейшая реализация вынесена в отдельный planned task `T0002`.
