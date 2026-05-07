---
title: Skill Catalog
created: 2026-05-07
updated: 2026-05-07
type: skill-catalog
status: active
tags: [skill, jarvis, hermes, wiki, workflow]
sources: [wiki/projects/jarvis/status.md]
confidence: high
relations:
  - type: governed_by
    target: skill-lifecycle
  - type: catalogs
    target: hermes-skills
---

# Skill Catalog

This page catalogs JARVIS-related Hermes skills. It links to skill sources and lifecycle notes without duplicating full `SKILL.md` bodies.

| Skill | Status | Source | Purpose |
|---|---|---|---|
| `jarvis-core` | active | `/home/hskim/.hermes/skills/software-development/jarvis-core/SKILL.md` | JARVIS session start, workspace boundaries, safety gates, repo hygiene. |
| `jarvis-executor-router` | active | `/home/hskim/.hermes/skills/software-development/jarvis-executor-router/SKILL.md` | Classify work and choose Hermes/Codex/OMX/cron/kanban/ask-user executor modes. |
| `jarvis-codex-omx-executor` | active | `/home/hskim/.hermes/skills/autonomous-ai-agents/jarvis-codex-omx-executor/SKILL.md` | Bounded delegation to Codex/OMX and Hermes post-verification. |
| `jarvis-wiki-manager` | active | `/home/hskim/.hermes/skills/note-taking/jarvis-wiki-manager/SKILL.md` | Maintain JARVIS wiki, registry, project status, decisions, and skill catalog. |

## Candidate Incubator

Draft workflows should start in `wiki/skills/candidates/` until they meet the promotion criteria in [[skills/lifecycle|Skill Library Lifecycle]].

## See also

- [[concepts/skill-lifecycle|Skill Lifecycle]]
- [[comparisons/skills-vs-wiki-vs-memory|Skills vs Wiki vs Memory]]
- [[concepts/learning-harness|Learning Harness]]
