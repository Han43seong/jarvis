---
title: Slide Harness Hermes Content-Authoring Runbook
created: 2026-05-13
updated: 2026-05-13
type: runbook
project: slide-harness
tags: [jarvis, slide-harness, hermes, content-plan, llm]
confidence: high
---

# Slide Harness Hermes Content-Authoring Runbook

## Purpose

Use this runbook when Hermes/JARVIS should write the actual slide content for `slide-harness`.

The boundary is intentional:

- Hermes/JARVIS writes a structured `content-plan.json` using the active LLM/model and project context.
- `slide-harness` validates and renders that JSON deterministically.
- `slide-harness` does not import Hermes, call model APIs, handle auth, or require network access.

This means missing Hermes model credentials only disables automatic authoring. Existing brief-only rendering, content-plan rendering, QA, dashboard, review, rerun, and compare still work.

## Inputs

Minimum inputs:

- User request or project topic.
- Brief fields:
  - `topic`
  - `audience`
  - `purpose`
  - `key_message` or key messages
  - optional `style_preset`
  - optional constraints/context.

Useful context sources:

- `/home/hskim/jarvis/wiki/projects/slide-harness/status.md`
- `/home/hskim/jarvis/wiki/concepts/slide-generation-harness.md`
- Project-specific wiki notes, RFP notes, or research notes.
- Existing `brief.json` and `examples/content-plan-template.json` in `/home/hskim/projects/slide-harness`.

## Standard workflow

From `/home/hskim/projects/slide-harness`:

```bash
python -m slide_harness.cli draft-brief \
  --topic "<topic>" \
  --audience "<audience>" \
  --purpose "<purpose>" \
  --key-message "<main message>" \
  --style-preset technical-review \
  --out /tmp/slide-brief.json

python -m slide_harness.cli content-template \
  --out /tmp/content-plan-template.json
```

Then generate an authoring prompt bundle from JARVIS:

```bash
python /home/hskim/jarvis/scripts/slide_harness_content_authoring_bundle.py \
  --brief /tmp/slide-brief.json \
  --template /tmp/content-plan-template.json \
  --context /home/hskim/jarvis/wiki/projects/slide-harness/status.md \
  --out /tmp/slide-content-authoring-prompt.md
```

Hermes uses `/tmp/slide-content-authoring-prompt.md` as the instruction to produce `/tmp/content-plan.json`.

Render and verify:

```bash
python -m slide_harness.cli run \
  --brief /tmp/slide-brief.json \
  --content-plan /tmp/content-plan.json \
  --out runs/<run-id>

python -m slide_harness.cli summary <run-id> --runs-root runs
python -m slide_harness.cli doctor --brief /tmp/slide-brief.json
```

Open dashboard if needed:

```bash
SLIDE_HARNESS_RUNS_ROOT=/home/hskim/projects/slide-harness/runs \
  python -m uvicorn slide_harness.server.app:app --host 127.0.0.1 --port 8000

cd /home/hskim/projects/slide-harness/web
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000 npm run dev -- --hostname 127.0.0.1 --port 3000
```

Dashboard URL:

```text
http://127.0.0.1:3000
```

## Revision loop

When the user asks for changes:

1. Read current `content-plan.json`, QA summary, and if relevant `compare-runs` output.
2. Ask Hermes to produce a revised content plan JSON, not prose instructions.
3. Save as a new file such as `/tmp/content-plan-v2.json`.
4. Run a new harness run with the same brief and revised content plan.
5. Use `compare-runs` to inspect metadata deltas.

Example:

```bash
python -m slide_harness.cli run \
  --brief /tmp/slide-brief.json \
  --content-plan /tmp/content-plan-v2.json \
  --out runs/<run-id-v2>

python -m slide_harness.cli compare-runs <run-id> <run-id-v2> --runs-root runs --json
```

## Content quality guidance

Hermes should create a coherent story:

1. Situation/problem.
2. Why current approach is insufficient.
3. Proposed solution.
4. Architecture or workflow.
5. Proof points/KPIs.
6. Risk/security/operations.
7. Roadmap or next action.

For RFP/proposal decks, prioritize:

- Evaluation criteria alignment.
- Security and operational feasibility.
- Concrete KPIs.
- Field validation plan.
- Clear differentiation.
- Evidence/source notes where claims need support.

## Safety and validation

The content plan must be plain text. Avoid:

- Raw HTML tags.
- JavaScript or script-like strings.
- CSS snippets.
- Markdown code fences.
- Unsupported fields unless the harness schema accepts them.

The harness validator intentionally rejects risky markers before rendering. Treat validation failures as authoring errors, then revise the JSON.

## Model/provider note

Hermes model credentials are only required for automatic authoring. If Hermes cannot call a model:

- A human can fill `content-plan.json` manually.
- Codex/Claude/another authorized model can produce the JSON externally.
- `slide-harness` can still validate, render, QA, review, compare, and show the result.
