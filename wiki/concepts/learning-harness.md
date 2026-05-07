---
title: Learning Harness
created: 2026-05-07
updated: 2026-05-07
type: concept
concept_type: knowledge-management
status: active
tags: [jarvis, hermes, memory, skill, wiki, llm-wiki, workflow]
sources: [wiki/projects/jarvis/status.md]
confidence: medium
relations:
  - type: stores
    target: hermes-memory
  - type: stores
    target: hermes-skills
  - type: records
    target: wiki
  - type: references
    target: skills-vs-wiki-vs-memory
---

# Learning Harness

The JARVIS learning harness is operational learning, not model weight fine-tuning. Hermes improves across sessions by saving durable facts, reusable procedures, project knowledge, and verified decisions into the right substrate.

## Layers

- Memory: compact stable facts and user preferences.
- Skills: executable reusable procedures.
- Session search: recall of past conversations.
- Wiki: human-readable and LLM-readable durable knowledge.
- Config: machine-readable routing and project registry.
- Verification: git status, diffs, tests, lint, and safety checks before knowledge is hardened.

## JARVIS Rule

When a workflow repeats and needs to guide future agent behavior, promote it through [[concepts/skill-lifecycle|Skill Lifecycle]]. When a concept or decision should be understood later, file it in this [[concepts/ontology-informed-wiki|Ontology-Informed Wiki]].

## See also

- [[comparisons/skills-vs-wiki-vs-memory|Skills vs Wiki vs Memory]]
- [[concepts/llm-wiki-pattern|LLM Wiki Pattern]]
- [[entities/hermes-agent|Hermes Agent]]
