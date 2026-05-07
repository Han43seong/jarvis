---
title: Skill Lifecycle
created: 2026-05-07
updated: 2026-05-07
type: concept
concept_type: skill-lifecycle
status: active
tags: [skill, jarvis, hermes, wiki, workflow]
sources: [wiki/skills/lifecycle.md]
confidence: high
relations:
  - type: governs
    target: hermes-skills
  - type: catalogs
    target: skills-index
  - type: promotes_to
    target: active-skills
  - type: archives
    target: archived-skills
---

# Skill Lifecycle

Skill lifecycle controls Hermes skill growth. Not every useful note should become a skill immediately; unproven workflows should start in the wiki as candidates and only become skills after repeated, verified use.

## States

- candidate: draft workflow or idea in `wiki/skills/candidates/`.
- active: executable Hermes skill used in future sessions.
- deprecated: replaced or no longer preferred.
- archived: kept for history but not loaded by default.
- promoted: moved from wiki candidate into a Hermes skill.

## Promotion Criteria

A candidate should become a skill when it is recurring, multi-step, has meaningful pitfalls, and needs to guide future agent behavior.

## See also

- [[skills/lifecycle|Skill Library Lifecycle]]
- [[skills/index|Skill Catalog]]
- [[comparisons/skills-vs-wiki-vs-memory|Skills vs Wiki vs Memory]]
