---
title: Slide Harness Agent-First Generation Runbook
created: 2026-05-13
updated: 2026-05-13
type: runbook
project: slide-harness
tags: [jarvis, slide-harness, hermes, brief, content-plan, agent-first]
confidence: high
---

# Slide Harness Agent-First Generation Runbook

## Purpose

Use this when the user asks Hermes/JARVIS to make slides from a natural-language request.

The user should not need to manually write `brief.json` or `content-plan.json`. Hermes should infer the brief, write the content plan, run the harness, and present the dashboard/result paths.

## Operating principle

- Hermes/JARVIS is the authoring agent.
- `slide-harness` remains a deterministic renderer/validator/QA harness.
- The dashboard remains an operator console, not an LLM authoring engine.
- No Hermes SDK, model API, auth, queue, or database is added to `slide-harness`.

## Default Korean workflow

From `$HOME/projects/slide-harness`:

1. Interpret the user's request into a brief.
2. Save the brief under `runs/agent-inputs/<slug>-brief.json` or `/tmp/<slug>-brief.json` for throwaway work.
3. Validate it with `draft-brief` when using explicit fields, or run `doctor --brief` after writing a full JSON brief.
4. Generate a Korean content-plan template:

```bash
python -m slide_harness.cli content-template \
  --language ko \
  --title "<brief topic>" \
  --subtitle "<deck subtitle>" \
  --slide-count <n> \
  --out runs/agent-inputs/<slug>-content-plan.json
```

5. Hermes edits that content-plan JSON directly, filling slide titles, bullets, body, speaker notes, visual hints, evidence, and source notes.
6. Render:

```bash
python -m slide_harness.cli run \
  --brief runs/agent-inputs/<slug>-brief.json \
  --content-plan runs/agent-inputs/<slug>-content-plan.json \
  --out runs/<slug>
```

7. Verify and summarize:

```bash
python -m slide_harness.cli summary <slug> --runs-root runs --api-base-url http://127.0.0.1:8000
python -m slide_harness.cli doctor --brief runs/agent-inputs/<slug>-brief.json
```

8. Tell the user:

- dashboard URL,
- run id,
- `final/deck.html` path,
- QA score/hard failures,
- whether the run is ready for review.

## Brief authoring rules

Hermes should infer these fields unless the user explicitly provides them:

- `topic`: concise deck title.
- `purpose`: why the deck exists and what decision/action it supports.
- `audience`: target decision-makers/operators.
- `language`: default `ko`.
- `style_preset`: `technical-review`, `executive-brief`, or `light-engineering`.
- `slide_count`: 6-8 for ordinary decks; 8-12 for RFP/proposal decks.
- `key_messages`: 3-5 strong takeaways.
- `call_to_action`: what the audience should decide or do next.
- `constraints`: assumptions, mandatory security/operation notes, evidence limits.

Do not ask the user for every field. Ask only when the target audience, deliverable type, or risk posture genuinely changes the result.

## Content-plan authoring rules

Use a coherent story arc:

1. 상황/문제.
2. 왜 기존 방식으로는 부족한지.
3. 제안 솔루션.
4. 구조/워크플로우.
5. 효과/KPI/검증 방법.
6. 리스크/보안/운영 계획.
7. 의사결정/다음 단계.

For RFP/proposal decks, emphasize:

- evaluation criteria alignment,
- security and closed-network/on-prem feasibility,
- concrete KPIs,
- field validation plan,
- maintainability and operations,
- differentiation.

## Minimal user-facing command pattern

When the user says something like:

```text
이 주제로 슬라이드 만들어줘: <request>
```

Hermes should execute the workflow directly and not instruct the user to manually fill JSON.

## Validation gates

Before reporting completion:

```bash
python -m slide_harness.cli summary <slug> --runs-root runs --api-base-url http://127.0.0.1:8000
python -m pytest -q
cd web && npm run lint
cd web && npm run build
```

For quick deck-only runs, full pytest/build can be skipped if no code changed; still inspect `summary`, QA, and generated artifact paths.

## Dashboard

If the local viewer is not running, start:

```bash
SLIDE_HARNESS_RUNS_ROOT=$HOME/projects/slide-harness/runs \
python -m uvicorn slide_harness.server.app:app --host 127.0.0.1 --port 8000

cd $HOME/projects/slide-harness/web
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev -- --hostname 127.0.0.1 --port 3000
```

Dashboard URL:

```text
http://127.0.0.1:3000
```
