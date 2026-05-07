---
title: JARVIS Control Plane
created: 2026-05-07
updated: 2026-05-07
type: concept
concept_type: architecture
status: active
tags: [jarvis, hermes, control-plane, workflow, automation, verification]
sources: [AGENTS.md, wiki/projects/jarvis/architecture.md]
confidence: high
relations:
  - type: orchestrates
    target: hermes-agent
  - type: delegates_to
    target: codex-cli
  - type: delegates_to
    target: omx
  - type: configured_by
    target: routing-yaml
---

# JARVIS Control Plane

The JARVIS control plane is the management workspace at `/home/hskim/jarvis`. It contains registry, routing policy, wiki, harnesses, plans, and operational docs. It does not vendor application source.

## Responsibilities

- Plan and decompose work.
- Route tasks using [[concepts/executor-routing|Executor Routing]].
- Maintain [[concepts/project-repository-model|Project Repository Model]] boundaries.
- Verify executor results using git status, diffs, tests, and safety checks.
- Preserve durable knowledge through [[concepts/llm-wiki-pattern|LLM Wiki Pattern]] pages and Hermes skills.

## See also

- [[entities/jarvis|JARVIS]]
- [[entities/hermes-agent|Hermes Agent]]
- [[projects/jarvis/architecture|JARVIS Architecture]]
