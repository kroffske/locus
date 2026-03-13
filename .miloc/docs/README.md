---
title: ".miloc/docs"
updated_at: "2026-03-14"
---

# `.miloc/docs/`

This folder is the repo-local **technical documentation root** for humans and agents.

## What belongs here (default)
- `ASSEMBLY.md` — short “read first” map of the repo (aim: ~100 lines).
- `SYSTEM_DESIGN.md` — deep technical map + PlantUML diagrams + build/verify commands.

Generate/update these via `miloc-docmap` and `system-design-document`:
- workflow: `~/.miloc/workflow/miloc-docmap/docmap.md`
- templates: `~/.miloc/templates/miloc-docmap/.miloc/.template/docs/`
- deep design template: `~/.miloc/templates/system-design-document/.miloc/.template/docs/SYSTEM_DESIGN.md`

## Legacy note (older repos)
Some repos already have:
- `.miloc/ASSEMBLY.md`
- `.miloc/SYSTEM_DESIGN.md`

That is still valid, but prefer **converging** to `.miloc/docs/{ASSEMBLY,SYSTEM_DESIGN}.md` over time.
No symlinks: copy/move content explicitly when you touch the docs.

## Conventions
- Prefer Markdown with embedded PlantUML blocks (```plantuml ...```).
- Keep `ASSEMBLY.md` short and navigational.
- Always include “Build & Verify” commands in `SYSTEM_DESIGN.md`.
- Link to existing repo docs instead of duplicating large sections.
