---
title: JARVIS
created: 2026-05-07
updated: 2026-05-07
type: entity
entity_type: system
status: active
tags: [jarvis, hermes, control-plane, workflow, automation, wiki, ontology]
sources: [AGENTS.md, wiki/projects/jarvis/architecture.md, wiki/projects/jarvis/status.md]
confidence: high
relations:
  - type: orchestrates
    target: hermes-agent
  - type: delegates_to
    target: codex-cli
  - type: delegates_to
    target: omx
  - type: configured_by
    target: projects-yaml
  - type: configured_by
    target: routing-yaml
  - type: records
    target: wiki
---

# JARVIS

JARVIS is the user's Hermes-centered operating system for multi-project automation. Its control-plane repository is `/home/hskim/jarvis`; active application repositories live outside it under `/home/hskim/projects/<project>`.

## Operating Model

JARVIS separates:

- orchestration and verification through [[entities/hermes-agent|Hermes Agent]]
- implementation through [[entities/codex-cli|Codex CLI]] and [[entities/omx|OMX]]
- durable operating knowledge through this [[concepts/ontology-informed-wiki|Ontology-Informed Wiki]]
- reusable procedures through Hermes skills cataloged by [[concepts/skill-lifecycle|Skill Lifecycle]]

## Key Boundaries

- JARVIS repo is not an application repo.
- Project source is not vendored into the control-plane repo.
- Push/deploy/secrets/destructive operations require explicit gating.

## See also

- [[concepts/jarvis-control-plane|JARVIS Control Plane]]
- [[concepts/project-repository-model|Project Repository Model]]
- [[projects/jarvis/architecture|JARVIS Architecture]]
