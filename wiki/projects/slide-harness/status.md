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

It preserves a CLI-first core while adding an optional FastAPI backend and local Next.js operator dashboard. The filesystem run directory remains the source of truth: `run.json`, `events.jsonl`, generated artifacts, and QA reports.

## Current MVP

Implemented:

- JSON brief intake
- Requirement selector with audience/purpose-specific criteria
- User-reviewable `requirements.md` and machine-readable `requirements.json`
- Deterministic slide plan generation
- Fixed 16:9 HTML deck renderer
- Keyboard navigation and slide counter
- Print/PDF CSS for deck export
- Static QA for slide count, placeholders, density, and visual elements
- Playwright CLI export to `deck.pdf` and `preview.png` when local Playwright is available
- Shared runner/state layer with `run.json` and `events.jsonl`
- Optional FastAPI backend with run list/detail/artifacts/QA endpoints
- Local Next.js + TypeScript operator dashboard under `web/`
- Phase 3 review/revision workflow:
  - events endpoint
  - safe artifact serving endpoint
  - approve/request-changes/reject review endpoint
  - rerun/revision endpoint that creates a new run instead of overwriting the original
  - dashboard event timeline, artifact links, review panel, and rerun UI
- Pytest suite with 14 passing tests

## Verification

Latest verified commands from `/home/hskim/projects/slide-harness`:

```bash
python -m pytest -q
cd web && npm run lint
cd web && npm run build
git diff --check
```

Observed on 2026-05-13:

- `python -m pytest -q` → `14 passed in 3.44s`
- `npm run lint` → passed (`tsc --noEmit`)
- `npm run build` → passed, Next.js production build completed
- `git diff --check` → passed
- Hermes API route smoke passed for create run, events, artifact lookup, approve review, and rerun/revision creation
- No secret/auth-sensitive files were changed

Recent local commits in project repo:

```text
168c3c4 feat: add review and revision workflow
9a3c0a2 feat: add operator dashboard skeleton
51ee6d5 feat: initialize slide harness with API foundation
```

## Active Operating Model

- Hermes/JARVIS scopes phases, launches OMX for implementation, verifies results, commits locally, and updates this status note.
- OMX handles repo-local implementation and test/fix loops inside `/home/hskim/projects/slide-harness`.
- Push/deploy remain manual approval gates.
- Long verification should run in background so the main chat remains responsive.

## Next Work

Recommended next phases:

1. Add a Hermes/JARVIS integration surface for creating a run from a natural-language brief and reading status/artifacts through CLI/API.
2. Add dashboard-side brief templates/examples and stronger brief validation before run creation.
3. Add artifact preview panes/contact sheet support rather than only links.
4. Add revision input semantics that can alter generated slide content, not only record rerun metadata.
5. Add design token files and named style presets.
6. Add template/theme import path.
7. Add PPTX renderer/export adapter only if editable PowerPoint output is required.
