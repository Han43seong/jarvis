---
title: Slide Harness Project Status
created: 2026-05-12
updated: 2026-05-20
type: project-status
project: slide-harness
status: legacy-reference
tags: [jarvis, slides, html, pdf, claude-design, qa-loop, dashboard]
sources: [wiki/concepts/slide-generation-harness.md]
confidence: high
---

# Slide Harness Project Status

## Summary

`slide-harness` is a completed/legacy HTML-first presentation/deck generation harness. Its private remote and local checkout details are intentionally excluded from this public archive.

It is no longer the active slide-production direction. The active path is now `hermes-slide-director`, which keeps Hermes/JARVIS conversation-first as the primary operator interface and uses Producer/Reviewer gates for high-fidelity deck generation. `slide-harness` is preserved as a reference implementation for CLI/dashboard ideas, Guided Brief UX, run artifacts, requirement gates, and local QA patterns.

It preserves a CLI-first core while adding an optional FastAPI backend and local Next.js operator dashboard. The filesystem run directory remains the source of truth: `run.json`, `events.jsonl`, generated artifacts, QA reports, review state, revision lineage, effective style/theme metadata, requirement override/effective checklist artifacts, Hermes/JARVIS-friendly summary JSON with optional backend artifact URLs, structured content-plan inputs, and run comparison summaries.

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
- Optional FastAPI backend with run list/detail/artifacts/QA/events/review/rerun/requirements/compare/content-plan endpoints
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
  - `summary`
  - `draft-brief`
  - `content-template`
  - `doctor`
  - `compare-runs`
  - `review`
  - `rerun`
  - brief validation/template support
  - content-plan import support
  - requirement checklist override command support
- Dashboard productization:
  - safe inline HTML deck preview
  - artifact open/download links
  - revision/source run relationship visibility
  - user-facing invalid brief API errors
  - requirement checklist panel with enable/disable and notes overrides
  - lightweight compare panel for source/revision metadata comparison
  - Korean-localized dashboard UI with content-plan operator panel for loading Korean-default or English templates, pasting/editing JSON, creating content-plan runs, surfacing validation errors, and showing compact content-plan metadata in run detail
  - Guided Brief primary authoring panel with assisted structured fields, deterministic requirement proposal, critic/challenge notes, user approval gate, automatic brief/content-plan writing, linked ordinary run artifact generation, and post-generation requirements artifacts sourced from the approved Proposed requirements
- Deterministic revision semantics:
  - rerun with `revision_note` creates `input/revision-brief.json`
  - child run metadata records source/revision/applied transformations
  - source run input remains unchanged
  - CLI/API/dashboard surface compact revision details
- Style presets/design tokens:
  - static local `light-engineering` default preset
  - `executive-brief` and `technical-review` presets
  - optional brief `style_preset` field with validation
  - CSS variable/token application in `deck.html`
  - run/planning/dashboard visibility for effective style preset
- Local theme imports:
  - local JSON token-only theme path support
  - `examples/theme-light-ai.json`
  - unknown token key rejection
  - obvious CSS/HTML injection marker rejection
  - sanitized token application to generated deck CSS variables
- Requirement checklist overrides:
  - non-destructive `planning/requirements-overrides.json`
  - effective checklist artifact generation
  - `requirements_edited` events
  - API/dashboard controls for enabled state and notes
- Hermes/JARVIS integration surface:
  - `draft-brief` command for explicit-field brief JSON creation without LLM calls
  - `content-template` and `run --content-plan` for Hermes/LLM-authored structured slide content without importing Hermes or calling model APIs inside the harness; content-template defaults to Korean placeholders and supports `--language en`
  - API/dashboard content-plan import path for operator-driven Hermes-authored JSON rendering
  - content-plan validation rejects raw HTML/script markers and requires explicit plain-text slide fields
  - JARVIS runbook/prompt bundle for Hermes-side content authoring, including agent-first brief authoring from natural-language user requests:
    - `wiki/runbooks/slide-harness-content-authoring.md`
    - `wiki/runbooks/slide-harness-agent-first-generation.md`
    - `templates/slide-harness/brief-author-prompt.md`
    - `templates/slide-harness/content-plan-author-prompt.md`
    - `scripts/slide_harness_content_authoring_bundle.py`
  - `summary` command for compact machine-readable run summaries
  - optional `summary --api-base-url` artifact URLs using safe backend artifact endpoint paths
  - `doctor` command for non-destructive operator preflight diagnostics with human and JSON output
  - `compare-runs` command and API/dashboard view for source/revision metadata comparison without HTML/PDF body diffs
  - README runbook for create/run/inspect/review/rerun/requirements/diagnostics/comparison/content-plan loops
- Pytest suite with 52 passing tests after Guided Brief backend/API/dashboard implementation

## Verification

Latest verified commands from `$HOME/projects/slide-harness`:

```bash
python -m pytest -q
cd web && npm run lint
cd web && npm run build
git diff --check
```

Observed on 2026-05-14 after Guided Brief requirements/checklist unification:

- `python -m pytest -q` → `52 passed`
- `cd web && npm run lint` → passed (`tsc --noEmit`)
- `cd web && npm run build` → passed, Next.js production build completed
- `git diff --check` → passed
- Guided API smoke passed against local backend:
  - `POST /api/agent-jobs` created `guided-integrated-req-smoke-2` with proposed requirements and slide outline
  - `POST /api/agent-jobs/{job_id}/approve` marked requirements approved
  - `POST /api/agent-jobs/{job_id}/generate` produced ordinary run `guided-integrated-req-smoke-2` with status `done`
  - `GET /api/runs/guided-integrated-req-smoke-2/requirements` returned `source_mode: guided_brief_proposal`, first requirement `GB-REQ-001`, and acceptance criteria items `GB-ACC-*`
- Dashboard visual smoke at `http://127.0.0.1:3000` showed `승인 요구사항 · 생성 후 검증` and explained that the approved Guided Brief Proposed requirements are now the post-generation verification criteria
- No secret/auth-sensitive files were changed

Recent local/project commits:

```text
840b2eb feat: unify guided requirements checklist
e1a3c86 feat: add guided brief dashboard flow
1ab4c68 docs: describe agent-first slide workflow
16d789b feat: localize dashboard UI to Korean
0075906 feat: default content templates to Korean
ed35191 feat: add content plan dashboard UX
42a93ee feat: add content plan import
54edddf feat: add compare dashboard view
8cd5dd6 feat: add run comparison CLI
0255bf6 feat: add operator doctor command
6eadb2d feat: populate summary artifact urls
d7e8fe1 feat: add local theme imports
56fddc4 feat: add jarvis automation commands
ed5dfa6 feat: add requirement checklist overrides
e41966d feat: add style presets
3b25ce5 feat: apply deterministic revision notes
cc63eda feat: improve dashboard artifact previews
0b867ac feat: add operator CLI workflow
168c3c4 feat: add review and revision workflow
51ee6d5 feat: initialize slide harness with API foundation
```


## Legacy Operating Model

- `slide-harness` is kept as a reference/legacy project, not the default target for new slide-production work.
- New slide-generation architecture, candidate bakeoffs, and real generation loops should route to `$HOME/projects/hermes-slide-director` unless the user explicitly asks to maintain or inspect this legacy repo.
- If maintenance is needed here, keep it narrow: bug fixes, read-only reference checks, or targeted documentation updates. Avoid broad new feature work unless the user reactivates the project.
- The latest verified project repo state is clean and synchronized with `origin/main`, with latest commit `018df35 docs: mark slide harness complete`.

## Reference-only Follow-ups

Only do these if explicitly useful for reference or maintenance:

1. Mine useful Guided Brief/dashboard/run-artifact patterns into `hermes-slide-director` docs when they become relevant.
2. Inspect or demo the legacy dashboard only when a reference comparison is needed.
3. Keep the repo clean/synced, but do not route new slide-production phases here by default.
