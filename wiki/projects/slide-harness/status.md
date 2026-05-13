---
title: Slide Harness Project Status
created: 2026-05-12
updated: 2026-05-13
type: project-status
project: slide-harness
status: active
tags: [jarvis, slides, html, pdf, claude-design, qa-loop, dashboard]
sources: [wiki/concepts/slide-generation-harness.md]
confidence: high
---

# Slide Harness Project Status

## Summary

`slide-harness` is an HTML-first presentation/deck generation harness under `/home/hskim/projects/slide-harness`.

It preserves a CLI-first core while adding an optional FastAPI backend and local Next.js operator dashboard. The filesystem run directory remains the source of truth: `run.json`, `events.jsonl`, generated artifacts, QA reports, review state, and revision lineage.

## Current MVP

Implemented:

- JSON/YAML brief intake with a template example
- Requirement selector with audience/purpose-specific criteria
- User-reviewable `requirements.md` and machine-readable `requirements.json`
- Deterministic slide plan generation
- Fixed 16:9 HTML deck renderer
- Keyboard navigation and slide counter
- Print/PDF CSS for deck export
- Static QA for slide count, placeholders, density, and visual elements
- Playwright CLI export to `deck.pdf` and `preview.png` when local Playwright is available
- Shared runner/state layer with `run.json` and `events.jsonl`
- Optional FastAPI backend with run list/detail/artifacts/QA/events/review/rerun endpoints
- Local Next.js + TypeScript operator dashboard under `web/`
- Review/revision workflow:
  - events endpoint
  - safe artifact serving endpoint
  - approve/request-changes/reject review endpoint
  - rerun/revision endpoint that creates a new run instead of overwriting the original
  - dashboard event timeline, artifact links, review panel, and rerun UI
- Operator CLI parity:
  - `list-runs`
  - `show-run`
  - `events`
  - `review`
  - `rerun`
  - brief validation/template support
- Dashboard productization:
  - safe inline HTML deck preview
  - artifact open/download links
  - revision/source run relationship visibility
  - user-facing invalid brief API errors
- Deterministic revision semantics:
  - rerun with `revision_note` creates `input/revision-brief.json`
  - child run metadata records source/revision/applied transformations
  - source run input remains unchanged
  - CLI/API/dashboard surface compact revision details
- Pytest suite with 18 passing tests as of Phase 6

## Verification

Latest verified commands from `/home/hskim/projects/slide-harness`:

```bash
python -m pytest -q
cd web && npm run lint
cd web && npm run build
git diff --check
```

Observed on 2026-05-13 after Phase 6:

- `python -m pytest -q` → `18 passed`
- Targeted revision smoke passed for source run creation, revision rerun, source input immutability, child `input/revision-brief.json`, and revision metadata
- `npm run lint` → passed (`tsc --noEmit`)
- `npm run build` → passed, Next.js production build completed
- `git diff --check` → passed
- No secret/auth-sensitive files were changed

Recent local commits in project repo:

```text
3b25ce5 feat: apply deterministic revision notes
cc63eda feat: improve dashboard artifact previews
0b867ac feat: add operator CLI workflow
168c3c4 feat: add review and revision workflow
9a3c0a2 feat: add operator dashboard skeleton
51ee6d5 feat: initialize slide harness with API foundation
```

## Active Operating Model

- Hermes/JARVIS scopes phases, launches OMX for implementation, verifies results, commits locally, and updates this status note.
- OMX handles repo-local implementation and test/fix loops inside `/home/hskim/projects/slide-harness`.
- Push/deploy remain manual approval gates.
- Long verification should run in background so the main chat remains responsive.
- GStack adoption is intentionally deferred until active slide-harness work is complete, to avoid changing the workflow pipeline mid-project.

## Next Work

Recommended next phases:

1. Add design token files and named style presets.
2. Add dashboard-side requirement checklist editing.
3. Add a Hermes/JARVIS integration surface for creating a run from a natural-language brief and reading status/artifacts through CLI/API.
4. Add template/theme import path.
5. Add PPTX renderer/export adapter only if editable PowerPoint output is required.
