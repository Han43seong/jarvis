---
title: JARVIS
created: 2026-05-07
updated: 2026-06-23
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
  - type: relates_to
    target: concepts/just-chill-vnext-operating-layer
---

# JARVIS

JARVIS is the user's Hermes-centered operating system for multi-project automation. Its control-plane repository is `/home/hskim/jarvis`; active application repositories live outside it under `/home/hskim/projects/<project>`.

## 2026-06-23 vNext rename target

The current vNext product direction is [[concepts/just-chill-vnext-operating-layer|just-chill vNext Operating Layer]]. It keeps this repository as the brownfield implementation target while narrowing JARVIS from a broad development Director into a personal operating console, router, result summarizer, and Hermes-backed memory gate. Development work routes to GJC rather than being planned or implemented by just-chill itself.

## Operating Model

JARVIS separates:

- orchestration and verification through [[entities/hermes-agent|Hermes Agent]]
- implementation through legacy [[entities/codex-cli|Codex CLI]] / [[entities/omx|OMX]] paths and, in the just-chill target design, GJC as the preferred development worker
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
