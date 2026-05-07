---
title: Ontology-Informed Wiki
created: 2026-05-07
updated: 2026-05-07
type: concept
concept_type: knowledge-management
status: active
tags: [ontology, llm-wiki, wiki, knowledge-management, jarvis]
sources: [wiki/SCHEMA.md]
confidence: high
relations:
  - type: governed_by
    target: SCHEMA
  - type: implements
    target: llm-wiki-pattern
  - type: references
    target: skills-vs-wiki-vs-memory
---

# Ontology-Informed Wiki

An ontology-informed wiki is a lightweight knowledge graph encoded in markdown. It is not a formal RDF/OWL ontology, but it uses typed pages, controlled tags, machine-readable relations, and human-readable wikilinks.

## Why This Fits JARVIS

[[entities/jarvis|JARVIS]] needs stable operating knowledge without the overhead of a formal triple store. Markdown frontmatter provides enough structure for Hermes to reason over relationships, lint consistency, and maintain a coherent control-plane knowledge base.

## Components

- `type`: entity, concept, comparison, query, skill-catalog.
- `entity_type` / `concept_type`: domain-specific classification.
- `relations`: typed edges such as `orchestrates`, `delegates_to`, `configured_by`, and `governed_by`.
- controlled `tags`: prevents vocabulary sprawl.
- `confidence` and contradiction metadata: supports review.

## See also

- [[SCHEMA|JARVIS LLM Wiki Schema]]
- [[concepts/llm-wiki-pattern|LLM Wiki Pattern]]
- [[concepts/learning-harness|Learning Harness]]
