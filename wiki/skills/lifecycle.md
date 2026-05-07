---
title: Skill Library Lifecycle
created: 2026-05-07
updated: 2026-05-07
type: skill-catalog
status: active
tags: [skill, jarvis, hermes, wiki, workflow]
sources: [wiki/skills/index.md]
confidence: high
relations:
  - type: governs
    target: skill-catalog
  - type: references
    target: skill-lifecycle
---

# Skill Library Lifecycle

JARVIS controls skill sprawl by separating candidate workflows from active executable skills.

## States

- Candidate: documented in `wiki/skills/candidates/`, not yet a Hermes skill.
- Active: a Hermes skill that should be loaded for relevant work.
- Deprecated: superseded by a better skill or policy.
- Archived: retained for history but not used by default.
- Promoted: candidate workflow turned into a Hermes skill.

## Promotion Criteria

Promote a candidate to a Hermes skill only when most of these are true:

1. The workflow was used successfully more than once.
2. It has 5+ concrete steps or a non-obvious command pattern.
3. Mistakes are likely without a checklist.
4. It applies across projects or sessions.
5. It needs to guide future agent behavior, not just inform a human.

## Review Policy

Review the skill catalog after real JARVIS routing/executor runs. Patch stale skills immediately when a pitfall or missing step is discovered.

## See also

- [[skills/index|Skill Catalog]]
- [[concepts/skill-lifecycle|Skill Lifecycle]]
- [[comparisons/skills-vs-wiki-vs-memory|Skills vs Wiki vs Memory]]
