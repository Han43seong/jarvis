---
title: Executor Routing
created: 2026-05-07
updated: 2026-05-11
type: concept
concept_type: routing-policy
status: active
tags: [executor-routing, jarvis, hermes, codex, omx, workflow]
sources: [AGENTS.md, config/routing.yaml, harnesses/executor-router.md]
confidence: high
relations:
  - type: configured_by
    target: routing-yaml
  - type: delegates_to
    target: codex-cli
  - type: delegates_to
    target: omx
  - type: governed_by
    target: plan-gate
---

# Executor Routing

Executor routing maps user requests to the right execution mode: Hermes direct work, Hermes background, Hermes goal loop, Codex, OMX, cron, kanban, or ask-user.

## Default Pattern

- Hermes direct: quick low-risk control-plane edits, docs, config, status/diff checks, validation, and tiny scripts expected to finish in roughly 1-2 minutes.
- Hermes background: research, market analysis, comparison/scouting, report drafting, long inspections, and multi-source reviews likely to exceed about 1 minute while the user may continue talking. Prefer durable mechanisms such as `terminal(background=true, notify_on_complete=true)`, `/background`, one-shot cron, or kanban; do not treat synchronous `delegate_task` as durable background execution.
- Hermes goal loop: multi-step JARVIS/control-plane work where foreground execution is acceptable.
- OMX Ralph: medium/large implementation, multi-file work, test/fix loops, autonomous completion requests.
- Codex goal/exec: repo-local iterative cleanup or small code tasks when appropriate.
- Cron: recurring monitoring/reporting.
- Kanban: durable multi-worker backlog.
- Ask user: unclear target, scope, risk, or completion criteria.

## Verification

Regardless of executor, [[entities/hermes-agent|Hermes Agent]] verifies status, diffs, tests, scope, and safety before reporting completion.

## See also

- [[entities/codex-cli|Codex CLI]]
- [[entities/omx|OMX]]
- [[concepts/jarvis-control-plane|JARVIS Control Plane]]
