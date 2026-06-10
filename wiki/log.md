# JARVIS LLM Wiki Log

> Chronological record of all LLM Wiki actions.
> Format: `## [YYYY-MM-DD] action | subject`.
> Actions: create, ingest, update, query, lint, archive, review.

## [2026-06-08] update | Open-source strategy and Hermes-agnostic public core captured

- Added `concepts/jarvis-open-source-strategy.md` to record that JARVIS has open-source potential as an Agent Operations Control Plane, but the private JARVIS repo should not be published as-is.
- Captured the architecture rule: private JARVIS remains Hermes-first, while any public core must be Hermes-agnostic with Hermes provided as a first-class adapter/recommended host.
- Updated `concepts/jarvis-office-runtime-direction.md`, `concepts/jarvis-vnext-executor-ontology.md`, `projects/jarvis/decisions.md`, and `index.md` with the public-core extraction strategy.

## [2026-06-08] review | Ouroboros partial-adoption design captured

- Reviewed `Q00/ouroboros` as a useful reference implementation for specification-first AI coding workflows, event/ledger thinking, runtime adapters, and evaluation gates.
- Added `concepts/ouroboros-adoption-review.md` with the JARVIS decision: do not replace JARVIS or install into the default Hermes profile immediately; selectively absorb task-contract, run-ledger, evaluation, adapter, and harness-manifest patterns.
- Updated `concepts/jarvis-office-runtime-direction.md`, `concepts/jarvis-vnext-executor-ontology.md`, and `index.md` to link the decision and refine vNext priorities.

## [2026-05-07] create | Ontology-informed JARVIS LLM Wiki initialized

- Added `SCHEMA.md`, `index.md`, and this `log.md`.
- Added ontology-oriented `entities/`, `concepts/`, `comparisons/`, `queries/`, `raw/`, and `skills/` layers.
- Seeded pages for JARVIS, Hermes Agent, Codex CLI, OMX, executor routing, learning harness, skill lifecycle, and LLM Wiki concepts.
- Kept existing `projects/jarvis/` operational wiki pages intact.

## [2026-05-28] create | JARVIS office runtime direction captured

- Added `concepts/jarvis-office-runtime-direction.md` to preserve the future direction that JARVIS should remain the intelligent Director while CLI/runtime helpers automate run ledgers, approval queues, status views, and Producer/Reviewer loop mechanics.
- Updated `index.md` with the new concept page.

## [2026-06-05] create | JARVIS vNext executor ontology captured

- Added `concepts/jarvis-vnext-executor-ontology.md` to preserve the future ontology-backed executor pool design: Gajae-Code as preferred default candidate, OMX-Codex as Codex-specific fallback, LazyCodex-Codex as high-intensity complex-codebase path, OpenCode as provider-agnostic alternate, and raw Codex as simple fallback.
- Linked the new page from `index.md`, `concepts/executor-routing.md`, and `concepts/jarvis-office-runtime-direction.md`.
- Explicitly marked the design as a vNext plan rather than an immediate active routing-policy change.

## [2026-05-11] query | Ontology-informed wiki rationale preserved

- Updated `projects/jarvis/status.md` with the current JARVIS progress checkpoint and ontology discussion summary.
- Added `queries/ontology-informed-wiki-rationale-2026-05-11.md` to preserve the explanation of metadata as node properties, typed relations as graph edges, and the current rationale for not using RDF/OWL yet.
- Updated `index.md` to include the saved query page and bump the indexed page count.
