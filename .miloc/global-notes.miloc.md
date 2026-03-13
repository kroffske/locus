---
title: "Global Notes (MiLoC)"
updated_at: "2026-03-14"
---

# Global Notes (MiLoC)

This file is the repo’s **long-lived coordination memory** across tasks and sessions.
It complements:
- per-task active notes: `.tasks/**/notes.miloc.md`
- repo debug facts: `.miloc/debug-notes.miloc.md`
- per-task verification evidence: `.tasks/**/artifacts/qa.md`
- engineering log: `.miloc/changelog.md` (update before commits)

## Quick links
- MiLoC root: `.miloc/`
- Active tasks: `.tasks/working/`

## What lives where (policy)
- Update **this file** for evergreen navigation/rules, cross-task decisions, drift rationale, and long-lived risks.
- Update `.miloc/debug-notes.miloc.md` for durable runtime/debugging facts, standard commands, and known traps.
- Update task `artifacts/qa.md` for executed checks, failures, and post-restart log review from the current run.
- Update `.miloc/changelog.md` for shipped change batches before commit or commit-batch.
- Update task-local `notes.miloc.md` only for active scratch notes; remove stale items promptly and delete the file when it becomes empty.

## MiLoC directory
- Root: `.miloc/`

## What each key file is for (short)
- `.miloc/changelog.md` — repo-local changelog; first durable shipping log to inspect before commits.
- `.miloc/goal.md` — stable product purpose and scope boundaries.
- `.miloc/roadmap.md` — prioritized next work and explicit non-goals.
- `.miloc/docs/README.md` — docs index and conventions for repo-local technical docs.
- `.miloc/docs/ASSEMBLY.md` — short “read first” repo map for humans and agents.
- `.miloc/docs/SYSTEM_DESIGN.md` — deeper architecture map with diagrams, interfaces, and build/verify commands.
- `.miloc/debug-notes.miloc.md` — durable runtime and debugging map for the repo.
- `.tasks/**/artifacts/qa.md` — current-run verification ledger.
- `.miloc/global-notes.miloc.md` — this file: durable rules, drift rationale, and cross-task decisions.

## Standing rules
- Manager always checks tasks vs `.miloc/goal.md` and `.miloc/roadmap.md`.
- If work drifts, record the reason here and link the relevant task, commit, or doc.
- Before committing, update `.miloc/changelog.md`.

## Drift log (why work deviated)

### 2026-03-14 — Initialize MiLoC memory for `locus`
- Context: Add repo-local MiLoC memory and documentation entrypoints.
- Drift: None relative to the requested scope.
- Reason: N/A.
- Decision: Create `.miloc/` and seed the docs from the canonical MiLoC templates.
- Links: `.miloc/goal.md`, `.miloc/roadmap.md`, `.miloc/docs/ASSEMBLY.md`, `.miloc/docs/SYSTEM_DESIGN.md`

## Decisions (durable)
- 2026-03-14: Use `.miloc/` as the repo-local memory root for goals, roadmap, changelog, debug notes, and technical docs.
- 2026-03-14: Keep `.miloc/docs/ASSEMBLY.md` short and route deeper architectural detail into `.miloc/docs/SYSTEM_DESIGN.md`.
- 2026-03-14: Treat `.miloc/*` as the durable repo-memory surface for `locus`; do not keep root-level `SESSION.md` history for this repo.
- 2026-03-14: Keep `AGENTS.md` repo-specific and concise; detailed architecture and testing guidance lives in dedicated docs.

## Open questions / risks
- Should the repo standardize on `python3` in docs and automation, or retain `python` in `Makefile` for compatibility? — maintainers — decide when touching dev workflow scripts.
- If MCP support grows, confirm how much runtime/design detail should move into dedicated docs under `.miloc/docs/`.
