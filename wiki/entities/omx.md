---
title: OMX
created: 2026-05-07
updated: 2026-05-07
type: entity
entity_type: executor
status: active
tags: [omx, jarvis, executor-routing, background-execution, automation]
sources: [AGENTS.md, harnesses/execute-codex-omx.md]
confidence: high
relations:
  - type: executes_in
    target: project-repositories
  - type: governed_by
    target: executor-routing
  - type: verified_by
    target: hermes-agent
---

# OMX

OMX is the preferred medium/large implementation executor for [[entities/jarvis|JARVIS]], especially for multi-file work, test/fix loops, and requests that imply autonomous completion.

## JARVIS Usage

`omx-ralph` is the default route for larger implementation tasks. Hermes remains the planner, prompt author, background-process monitor, verifier, and reporter.

## Guardrails

- Work only inside the target repo.
- Do not push or deploy.
- Do not modify secrets/auth files.
- Run feasible tests and report results.

## See also

- [[concepts/executor-routing|Executor Routing]]
- [[concepts/jarvis-control-plane|JARVIS Control Plane]]
- [[entities/codex-cli|Codex CLI]]
