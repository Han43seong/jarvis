---
title: RAG vs LLM Wiki
created: 2026-05-07
updated: 2026-05-07
type: comparison
status: active
tags: [llm-wiki, wiki, knowledge-management, ontology]
sources: [https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f]
confidence: high
relations:
  - type: references
    target: llm-wiki-pattern
  - type: references
    target: ontology-informed-wiki
---

# RAG vs LLM Wiki

| Dimension | RAG | LLM Wiki |
|---|---|---|
| Main action | Retrieve chunks at query time | Compile sources into persistent pages |
| Memory | Usually answer disappears | Answers and syntheses can be filed back |
| Structure | Often implicit in embeddings/chunks | Explicit pages, links, index, log, schema |
| Maintenance | Query-time rediscovery | Ongoing updates, lint, contradiction handling |
| Best for | Large ad-hoc corpora | Compounding knowledge over time |

## JARVIS Choice

JARVIS should start with an agent-curated [[concepts/llm-wiki-pattern|LLM Wiki Pattern]] because its knowledge domain is operational, evolving, and small enough to maintain directly in markdown. Search tools such as qmd can be added later if the wiki grows.

## See also

- [[concepts/ontology-informed-wiki|Ontology-Informed Wiki]]
- [[concepts/learning-harness|Learning Harness]]
- [[entities/jarvis|JARVIS]]
