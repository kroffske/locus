---
title: "Roadmap"
updated_at: "2026-03-14"
---

# Roadmap

> Keep this short and current. Prefer a small number of phases and explicit “not now”.

## Links
- Goal: `.miloc/goal.md`
- Changelog: `.miloc/changelog.md`
- Drift log: `.miloc/global-notes.miloc.md`

## Current milestone
- Theme: Stabilize the core Locus CLI and keep the repo easy for humans and agents to navigate.
- Definition of done: Core analyze/update/sim/init workflows are documented, the fast test path is green, and optional MCP surfaces remain clearly separated from the base install.

## Near-term (next 1–3)
1. Harden the main CLI flows and keep usage/docs aligned with actual behavior.
2. Improve optional MCP indexing/search boundaries, dependency checks, and operator guidance.
3. Keep similarity detection moving from exact matches toward stronger near-duplicate detection without destabilizing the base CLI.

## Backlog / later
- Better repo-specific config UX for `.locus/settings.json`
- More guided export/update workflows for common LLM collaboration loops
- Additional documentation automation around repo maps and architecture surfaces

## Not now (explicit)
- Turning Locus into a full IDE or hosted search platform
- Making heavy MCP/embedding dependencies part of the default installation
