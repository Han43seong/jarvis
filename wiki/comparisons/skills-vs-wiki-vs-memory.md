---
title: Skills vs Wiki vs Memory
created: 2026-05-07
updated: 2026-05-07
type: comparison
status: active
tags: [skill, wiki, memory, hermes, jarvis, knowledge-management]
sources: [wiki/projects/jarvis/status.md]
confidence: high
relations:
  - type: references
    target: learning-harness
  - type: references
    target: skill-lifecycle
  - type: references
    target: ontology-informed-wiki
---

# Skills vs Wiki vs Memory

| Layer | Stores | Use for | Avoid |
|---|---|---|---|
| Hermes memory | Compact durable facts | preferences, stable environment facts | task progress, long procedures |
| Hermes skills | Executable procedures | recurring workflows, commands, pitfalls, verification | broad project state, raw notes |
| JARVIS wiki | Durable knowledge | concepts, decisions, project status, ontology relations | full skill body duplication, secrets |
| Session search | Past conversation recall | historical details and prior logs | authoritative long-term policy |
| Config | Machine-readable settings | routing, project registry | prose explanations |

## JARVIS Rule

Use [[concepts/skill-lifecycle|Skill Lifecycle]] to decide when a wiki candidate should become a Hermes skill. Use this [[concepts/ontology-informed-wiki|Ontology-Informed Wiki]] to keep skills discoverable without duplicating full `SKILL.md` content.

## See also

- [[concepts/learning-harness|Learning Harness]]
- [[skills/index|Skill Catalog]]
- [[entities/hermes-agent|Hermes Agent]]
