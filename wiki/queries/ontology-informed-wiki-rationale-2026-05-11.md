---
title: Ontology-Informed Wiki Rationale
created: 2026-05-11
updated: 2026-05-11
type: query
status: active
tags: [ontology, llm-wiki, wiki, knowledge-management, jarvis]
sources: [conversation:2026-05-11]
confidence: high
scope: JARVIS ontology-informed LLM Wiki design discussion
relations:
  - type: references
    target: ontology-informed-wiki
  - type: references
    target: llm-wiki-pattern
  - type: references
    target: SCHEMA
  - type: references
    target: rag-vs-llm-wiki
---

# Ontology-Informed Wiki Rationale

This page preserves the 2026-05-11 discussion about why the JARVIS wiki uses a lightweight ontology-informed markdown structure instead of a full RDF/OWL ontology stack.

## Core understanding

The user's starting definition was correct: ontology gives data connectivity by forming relationships between data. More precisely, an ontology defines what kinds of things exist, how they are classified, what relationships are allowed between them, what those relationships mean, and what reasoning can be done over them.

For JARVIS, an ontology-informed wiki means markdown pages act as knowledge-graph nodes. YAML frontmatter provides node metadata, typed `relations` provide machine-readable edges, and wikilinks provide human-readable navigation.

## Metadata is part of the ontology-informed structure

Document metadata is not separate from the ontology layer. In this wiki model:

- `type`, `entity_type`, and `concept_type` classify the node.
- `tags` provide controlled vocabulary for search and grouping.
- `status`, `confidence`, and `sources` support lifecycle, trust, and provenance.
- `relations` provide typed graph edges to other pages or stable identifiers.
- `SCHEMA.md` defines the allowed node types, properties, tags, and relation types.

A practical mapping is:

```text
Document/page = graph node
Frontmatter metadata = node type and properties
relations = typed graph edges
SCHEMA.md = allowed node/property/edge vocabulary
Markdown body = human-readable narrative context
```

Some metadata is strongly ontological, such as `type`, `entity_type`, `concept_type`, controlled tags, and relation types. Other metadata is more operational, such as `created`, `updated`, `status`, `sources`, and `confidence`, but it still helps Hermes decide whether knowledge is current, trustworthy, and usable.

## Why not RDF/OWL now

The current JARVIS wiki did not start as RDF/OWL because the immediate goal is not a formal semantic-web system. The goal is an agent-operable, git-tracked operating knowledge base that both the user and Hermes can read, patch, review, and evolve quickly.

Markdown plus YAML frontmatter is currently preferred because it is:

- easy for humans to read and edit;
- easy for Hermes to inspect, patch, and summarize;
- friendly to git diff and GitHub review;
- flexible while the schema is still evolving;
- sufficient for JARVIS operational knowledge, decisions, routing rules, runbooks, and status notes;
- infrastructure-light: no triple store, SPARQL server, OWL reasoner, or RDF toolchain is required.

RDF/OWL would be useful later if JARVIS needs formal reasoning, SPARQL queries, external ontology integration, or large-scale graph analytics. For now, that would add premature complexity.

## Future migration path

The current structure does not block RDF/OWL. It intentionally keeps the graph data extractable:

```yaml
type: entity
entity_type: executor
relations:
  - type: delegates_to
    target: omx
```

can later be exported into triples such as:

```text
:hermes-agent :delegatesTo :omx .
:omx rdf:type :Executor .
```

A likely future architecture is:

```text
Markdown wiki = human/agent source of truth
Generated RDF or JSON-LD = machine query/export layer
Lint/reasoner = consistency and relation validation layer
```

## Current conclusion

The JARVIS wiki should remain a markdown-native lightweight ontology for now. It captures the important benefits of ontology—typed nodes, controlled vocabulary, typed relationships, and graph-like navigation—without the operational overhead of a full RDF/OWL stack.

## See also

- [[concepts/ontology-informed-wiki|Ontology-Informed Wiki]]
- [[concepts/llm-wiki-pattern|LLM Wiki Pattern]]
- [[comparisons/rag-vs-llm-wiki|RAG vs LLM Wiki]]
- [[SCHEMA|JARVIS LLM Wiki Schema]]
