---
title: "Project Goal"
owner: "Locus maintainers"
updated_at: "2026-03-14"
---

# Goal

## North star
Make large codebases easier for humans and LLMs to inspect, slice, and update safely through a small Python CLI and optional MCP tooling.

## Primary users / stakeholders
- Developers preparing high-signal repo context for LLM chats
- Maintainers who need fast structure scans, modular exports, and safe file updates
- Agents and tools that consume the optional MCP search/index surfaces

## Problem statement
Useful code context is usually buried in repositories that are too large to paste into a chat or inspect manually every time. Locus exists to scan a repo, surface the right files and annotations, export context in LLM-friendly formats, and apply structured Markdown-based edits back to the filesystem with minimal friction.

## Scope
### In scope
- CLI workflows for `analyze`, `sim`, `update`, and `init`
- Repo scanning, dependency resolution, and annotation extraction
- Output formatting for interactive views, reports, and modular exports
- Similarity detection for duplicate or near-duplicate Python functions
- Optional MCP indexing/search capabilities behind extra dependencies

### Out of scope (non-goals)
- Replacing IDEs, language servers, or full code search platforms
- Executing arbitrary project code as part of analysis
- Making heavy MCP/ML dependencies mandatory for the base install

## Success metrics (optional)
- Core CLI flows are understandable and runnable from the repo docs
- Fast test suite stays green without requiring MCP extras
- New contributors can find where to change major features in a few minutes

## Key constraints / invariants
- Keep core analysis and formatting logic modular and testable
- Preserve a lightweight base install; gate MCP features behind optional extras
- Use filesystem and Markdown contracts that are explicit and reviewable
- Keep docs and task execution aligned with `.miloc/roadmap.md`

## Task alignment rule
All work in `.tasks/**` should be traceable to this goal and the current roadmap (`.miloc/roadmap.md`).

If a task drifts:
- record the reason in `.miloc/global-notes.miloc.md`
- decide whether to update the goal/roadmap (intentional drift) or correct course (unintentional drift)
