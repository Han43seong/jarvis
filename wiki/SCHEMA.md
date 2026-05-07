# JARVIS LLM Wiki Schema

## Domain

This wiki covers the user's Hermes-centered JARVIS operating system: control-plane architecture, executor routing, project registry, ontology-informed knowledge management, Hermes skills, memory policy, automation workflows, coding delegation, verification policy, and operational decisions.

The wiki is an ontology-informed LLM Wiki, not a formal RDF/OWL store. Its source of truth is git-tracked markdown plus YAML frontmatter, typed relations, controlled tags, and periodic linting.

## Layers

1. Raw sources: curated source material. Public/sanitized sources may be tracked; private/session/executor raw material must not be tracked unless explicitly sanitized.
2. Wiki pages: LLM-maintained markdown pages under `entities/`, `concepts/`, `comparisons/`, `queries/`, `projects/`, and `skills/`.
3. Schema: this file plus `index.md` and `log.md` guide future Hermes/JARVIS sessions.

## Directory Layout

```text
wiki/
  SCHEMA.md
  index.md
  log.md
  raw/
    public/
    private/          # gitignored; unsanitized source material only
    sessions/         # gitignored unless sanitized
    executor-runs/    # gitignored unless sanitized
    assets/
  entities/
  concepts/
  comparisons/
  queries/
  projects/
  skills/
    index.md
    lifecycle.md
    candidates/
    reviews/
  templates/
```

## Page Types

- `entity`: a concrete system, tool, repo, document, config, executor, project, or skill system.
- `concept`: a reusable idea, policy, workflow, architecture pattern, or lifecycle model.
- `comparison`: side-by-side analysis of alternatives.
- `query`: a preserved answer that would be costly to re-derive.
- `project`: operational project state under `projects/`.
- `skill-catalog`: catalog/lifecycle pages for Hermes skills.
- `template`: reusable page template.

## Entity Types

Use `entity_type` on entity pages:

- `system`
- `agent`
- `executor`
- `tool`
- `repository`
- `project`
- `document`
- `config`
- `skill-system`
- `workflow`
- `source`

## Concept Types

Use `concept_type` on concept pages:

- `architecture`
- `routing-policy`
- `safety-policy`
- `memory-policy`
- `skill-lifecycle`
- `wiki-pattern`
- `execution-mode`
- `verification-policy`
- `repository-model`
- `knowledge-management`

## Controlled Tags

Allowed tags:

- `jarvis`
- `hermes`
- `codex`
- `omx`
- `executor-routing`
- `background-execution`
- `skill`
- `memory`
- `wiki`
- `llm-wiki`
- `ontology`
- `project-registry`
- `github`
- `safety`
- `workflow`
- `automation`
- `verification`
- `control-plane`
- `repository-model`
- `knowledge-management`

Add new tags here before using them.

## Relation Types

Use `relations` frontmatter entries with `type` and `target` fields. Preferred relation types:

- `orchestrates`
- `delegates_to`
- `executes_in`
- `configured_by`
- `documented_in`
- `governed_by`
- `governs`
- `verifies`
- `verified_by`
- `records`
- `loads`
- `updates`
- `depends_on`
- `supersedes`
- `contradicts`
- `implements`
- `references`
- `promotes_to`
- `archives`
- `catalogs`
- `stores`
- `retrieves_from`

Targets should use page slugs or stable document identifiers, for example `hermes-agent`, `executor-routing`, `projects-yaml`, or `projects/jarvis/architecture`.

## Required Frontmatter

Every page under `entities/`, `concepts/`, `comparisons/`, `queries/`, and `skills/` should start with YAML frontmatter:

```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | skill-catalog
status: active | draft | candidate | deprecated | archived
tags: [jarvis, wiki]
sources: []
confidence: high | medium | low
relations:
  - type: references
    target: another-page-slug
---
```

Additional fields:

- `entity_type` for `type: entity`
- `concept_type` for `type: concept`
- `scope` for comparison/query pages when useful
- `contested: true` and `contradictions: [...]` for unresolved contradictions

## Wikilink Rules

- Use `[[page-slug]]` or `[[path/page-slug|Display Name]]` links.
- Every non-index page should have at least two outbound links when possible.
- Prefer typed frontmatter relations for machine-readable edges and wikilinks for human navigation.

## Source and Privacy Rules

- Never store secrets, credentials, OAuth tokens, private keys, `.env` contents, or auth JSON in the wiki.
- Unsanitized session transcripts and executor logs belong under ignored raw folders, not git-tracked pages.
- Convert sensitive raw material into sanitized summaries before tracking.
- Pages may cite raw sources with `sources`, but raw private sources should not be pushed.

## Operation Rules

### Orient

At the start of wiki work:

1. Read `SCHEMA.md`.
2. Read `index.md`.
3. Read recent `log.md` entries.
4. Search existing pages before creating new pages.

### Ingest

1. Capture or reference the source.
2. Identify entities, concepts, comparisons, and durable queries.
3. Create or update pages using required frontmatter.
4. Add typed relations and wikilinks.
5. Update `index.md`.
6. Append to `log.md`.

### Query

1. Read `index.md` and relevant pages.
2. Synthesize an answer citing wiki pages.
3. Save only durable, high-value answers to `queries/`.
4. Update `index.md` and `log.md` if a query page is saved.

### Lint

Check for:

- broken wikilinks
- orphan pages
- missing index entries
- missing/invalid frontmatter
- tags not listed in this schema
- relation types not listed in this schema
- pages over roughly 200 lines
- low-confidence or contested pages
- raw private material accidentally tracked

## Relationship to Hermes Memory and Skills

- Hermes memory stores compact durable facts and user preferences.
- Hermes skills store executable reusable procedures.
- This wiki stores human-readable and LLM-readable long-term knowledge, typed relations, decisions, and conceptual synthesis.
- `wiki/skills/` catalogs skill purpose/lifecycle, but does not duplicate full `SKILL.md` bodies.
