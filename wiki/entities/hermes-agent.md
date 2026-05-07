---
title: Hermes Agent
created: 2026-05-07
updated: 2026-05-07
type: entity
entity_type: agent
status: active
tags: [hermes, jarvis, control-plane, workflow, memory, skill, wiki]
sources: [wiki/projects/jarvis/status.md, AGENTS.md]
confidence: high
relations:
  - type: orchestrates
    target: jarvis
  - type: delegates_to
    target: codex-cli
  - type: delegates_to
    target: omx
  - type: records
    target: jarvis-wiki
  - type: loads
    target: hermes-skills
---

# Hermes Agent

Hermes Agent is the primary agentic control plane for [[jarvis|JARVIS]]. In this workspace it plans, routes, verifies, maintains memory, updates wiki pages, and delegates implementation to [[codex-cli|Codex CLI]] or [[omx|OMX]] when work is better handled by a coding executor.

## Role in JARVIS

- Maintains [[concepts/jarvis-control-plane|JARVIS Control Plane]] boundaries.
- Applies [[concepts/executor-routing|Executor Routing]].
- Uses [[concepts/learning-harness|Learning Harness]] layers: memory, skills, session search, wiki, config, and verification.
- Updates this [[concepts/llm-wiki-pattern|LLM Wiki Pattern]] when durable knowledge changes.

## Boundaries

Hermes should remain planner/router/verifier/reporter for larger implementation tasks. Executors can edit target project repos, but Hermes verifies git status, diff, tests, scope, and safety policy before reporting completion.

## See also

- [[entities/jarvis|JARVIS]]
- [[concepts/skill-lifecycle|Skill Lifecycle]]
- [[comparisons/skills-vs-wiki-vs-memory|Skills vs Wiki vs Memory]]
