---
title: Executor Routing
created: 2026-05-07
updated: 2026-06-08
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
  - type: informs
    target: jarvis-open-source-strategy
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

## vNext Direction

The active policy still reflects the current Hermes/Codex/OMX-centered router. The future ontology design is tracked separately in [[concepts/jarvis-vnext-executor-ontology|JARVIS vNext Executor Ontology]]. That draft keeps the current system unchanged while planning a broader executor pool: Gajae-Code as preferred default candidate, OMX-Codex as Codex-specific fallback, LazyCodex-Codex as high-intensity complex-codebase path, OpenCode as provider-agnostic alternate, and raw Codex as simple fallback. The Ouroboros adoption review adds a selective design input for Seed-like task contracts, run-ledger events, evaluation gates, executor adapters, and harness manifests without replacing JARVIS as Director. The open-source strategy extends this into a public-core rule: the private instance can be Hermes-first, but exported routing primitives should be runtime-agnostic and host adapters should implement the executor contract.

## See also

- [[entities/codex-cli|Codex CLI]]
- [[entities/omx|OMX]]
- [[concepts/jarvis-control-plane|JARVIS Control Plane]]
- [[concepts/ouroboros-adoption-review|Ouroboros Adoption Review for JARVIS vNext]]
- [[concepts/jarvis-open-source-strategy|JARVIS Open Source Strategy]]
