---
title: LLM Wiki Pattern
created: 2026-05-07
updated: 2026-05-07
type: concept
concept_type: wiki-pattern
status: active
tags: [llm-wiki, wiki, knowledge-management, ontology, workflow]
sources: [https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f]
confidence: high
relations:
  - type: implements
    target: ontology-informed-wiki
  - type: references
    target: rag-vs-llm-wiki
  - type: records
    target: log
---

# LLM Wiki Pattern

The LLM Wiki pattern builds a persistent, compounding markdown knowledge base instead of relying only on query-time retrieval. Raw sources are read once, distilled into interlinked pages, and kept current as new sources and questions arrive.

## JARVIS Interpretation

For [[entities/jarvis|JARVIS]], the wiki is a control-plane knowledge base. It captures durable concepts, entities, comparisons, decisions, and high-value query answers so future Hermes sessions can orient quickly and avoid re-deriving the same context.

## Core Operations

- Ingest source material into durable pages.
- Query existing pages before answering.
- Save valuable query answers.
- Lint for broken links, missing metadata, contradictions, and stale pages.

## See also

- [[concepts/ontology-informed-wiki|Ontology-Informed Wiki]]
- [[comparisons/rag-vs-llm-wiki|RAG vs LLM Wiki]]
- [[concepts/learning-harness|Learning Harness]]
