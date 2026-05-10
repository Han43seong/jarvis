# JARVIS LLM Wiki Index

> Ontology-informed content catalog for the Hermes-centered JARVIS control plane.
> Read this after `SCHEMA.md` and before creating or updating pages.
> Last updated: 2026-05-11 | Total indexed pages: 14

## Core Orientation

- [[SCHEMA|JARVIS LLM Wiki Schema]] — ontology-informed schema, page types, controlled tags, typed relations, and wiki operation rules.
- [[log|Wiki Log]] — chronological record of wiki initialization, ingest, query, lint, and maintenance actions.
- [[_index|Legacy Wiki Index]] — original JARVIS operating wiki index.

## Entities

- [[entities/codex-cli|Codex CLI]] — repo-local coding executor available to JARVIS through the user's Codex OAuth/subscription path.
- [[entities/hermes-agent|Hermes Agent]] — primary JARVIS control-plane agent, orchestrator, memory manager, verifier, and wiki maintainer.
- [[entities/jarvis|JARVIS]] — user's Hermes-centered operating system spanning control-plane docs, routing, skills, wiki, and executors.
- [[entities/omx|OMX]] — medium/large implementation executor, especially for `$ralph`-style multi-file and test/fix loops.

## Concepts

- [[concepts/executor-routing|Executor Routing]] — policy for mapping tasks to Hermes direct work, Codex, OMX, cron, kanban, or ask-user.
- [[concepts/jarvis-control-plane|JARVIS Control Plane]] — architecture pattern keeping orchestration, docs, registry, and verification separate from app repos.
- [[concepts/learning-harness|Learning Harness]] — how memory, skills, session search, wiki, config, and verification compound across sessions.
- [[concepts/llm-wiki-pattern|LLM Wiki Pattern]] — persistent interlinked markdown wiki that compiles knowledge rather than re-deriving it per query.
- [[concepts/ontology-informed-wiki|Ontology-Informed Wiki]] — lightweight ontology approach using frontmatter types, relations, tags, and wikilinks.
- [[concepts/project-repository-model|Project Repository Model]] — active application repos live under `/home/hskim/projects/<project>`, outside the JARVIS repo.
- [[concepts/skill-lifecycle|Skill Lifecycle]] — candidate, active, deprecated, archived, and promoted states for Hermes skill growth control.

## Comparisons

- [[comparisons/rag-vs-llm-wiki|RAG vs LLM Wiki]] — retrieval-time rediscovery compared with persistent compiled knowledge.
- [[comparisons/skills-vs-wiki-vs-memory|Skills vs Wiki vs Memory]] — division of labor between executable procedures, durable concepts, and compact facts.

## Projects

- [[projects/jarvis/status|JARVIS Status]] — current operating state and next steps for the JARVIS control-plane project.
- [[projects/jarvis/architecture|JARVIS Architecture]] — workspace layout, project repository model, and executor boundaries.
- [[projects/jarvis/decisions|JARVIS Decisions]] — durable architecture and workflow decisions.

## Skills

- [[skills/index|Skill Catalog]] — catalog of active JARVIS Hermes skills and candidates.
- [[skills/lifecycle|Skill Library Lifecycle]] — rules for when workflows stay as wiki notes, become skills, or get archived.

## Queries

- [[queries/ontology-informed-wiki-rationale-2026-05-11|Ontology-Informed Wiki Rationale]] — saved explanation of metadata, typed relations, and why JARVIS uses markdown-native lightweight ontology before RDF/OWL.
