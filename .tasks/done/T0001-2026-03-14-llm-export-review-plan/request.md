# Request

## Raw request

Пользователь: "цель таска провести ревью и составить план, чтобы улучшить/переделать утилиту:
- LLM должен ей пользоваться.
- ignore files - не нужно копировать в проект
- нужно формировать 1-10 файлов (или сколько попросят). нужен tree + описание
- удобно задавать grep / rg условия.
- ревью скорости выгрузки.
- научиться экспортировать jupyter notebooks"

## Interpreted request

- Goal:
  - Разобрать текущий `locus analyze` / export path и подготовить план переделки под LLM-friendly workflow.
- In scope:
  - Review текущего CLI/config/export UX.
  - Gap analysis по ignore/include/filter UX, числу экспортируемых файлов, tree/description, perf и notebook support.
  - План работ с приоритетами, verification path и рисками.
- Out of scope:
  - Реализация фич в коде в рамках этого таска.
  - Изменения optional MCP flows без прямой необходимости.
- Assumptions:
  - "ignore files - не нужно копировать в проект" трактуется как требование не навязывать служебные ignore/config файлы в анализируемый repo ради базового workflow.
  - "grep / rg условия" означает удобный CLI surface для text/path prefiltering или source selection, а не обязательно встраивание full ripgrep engine.
- Possible mismatch points:
  - Нужно отдельно проверить, идет ли речь про экспорт исходников, структуры repo, или про генерацию LLM-ready briefs поверх tree/export.
