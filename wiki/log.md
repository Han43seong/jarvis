# JARVIS LLM Wiki Log

> Chronological record of all LLM Wiki actions.
> Format: `## [YYYY-MM-DD] action | subject`.
> Actions: create, ingest, update, query, lint, archive, review.

## [2026-06-26] create | just-chill visible GJC execution bridge MVP

- Added `scripts/just_chill_gjc_execution_bridge.py` and `scripts/check_just_chill_gjc_execution_bridge.py`.
- The bridge consumes a `gjcHandoffPlan`, writes host-owned task/session metadata, emits visible-session operator argv plans, and verifies durable completion evidence.
- It still does not start GJC, inject prompts, call coordinator/delegate tools, write Hermes, or accept tmux scrollback as completion evidence.

## [2026-06-26] verify | just-chill harness visible in fresh Hermes session

- The status contract was exercised locally; the current host result is intentionally not published.
- The status contract was exercised locally; host-specific registrations and availability are not published.
- Remaining productization work moves to host-owned execution/evidence bridges, production approval/audit integration, and real memory migration policy.

## [2026-06-26] create | just-chill approval registry

- Added `scripts/just_chill_approval_registry.py` and `scripts/check_just_chill_approval_registry.py`.
- Approval tokens can now be issued, verified, and revoked against scope, optional subject hash, expiry, and revocation state while persisting only token hashes.
- CLI, Hermes-facing harness, and MCP remember/recall flows accept optional registry-backed approval inputs; shape-only acceptance remains debug/fixture-only.

## [2026-06-26] update | just-chill harness registration workflow checked

- The approval-gated registration and discovery workflow was checked in a local host environment.
- Current registration state, command paths, and host tool inventory are intentionally not published.

## [2026-06-26] create | just-chill Hermes-facing harness

- Added `scripts/just_chill_harness.py`, `scripts/just_chill_harness_mcp.py`, `scripts/just_chill_hermes_harness.py`, and focused checks for each.
- Hermes is now documented as the user-facing product layer; just-chill is a routing/memory/approval/GJC-handoff harness and `scripts/just-chill` is debug/test/fixture-only.
- The harness MCP exposes `just_chill.*` contract tools; external registration remains host-owned and is not asserted here.
## [2026-06-25] create | just-chill end-to-end dogfood contract harness

- Added `scripts/just_chill_dogfood_harness.py` and `scripts/check_just_chill_dogfood_harness.py`.
- The harness exercises route, GJC handoff, memory/raw/RDF/SHACL/vector contracts, recall gate, and consent policy without starting GJC, calling Hermes, running SHACL, or searching a vector store.
- Updated live-binding harness, canonical concept, status, decisions, and migration inventory with the integrated dogfood contract and negative stale/deleted/redacted-recall and sensitive-memory cases.

## [2026-06-25] create | just-chill GJC consent policy

- Added `scripts/just_chill_gjc_consent_policy.py` and `scripts/check_just_chill_gjc_consent_policy.py`.
- Coordinator/delegation paths now fail closed unless coordinator smoke, mutation classes, per-call `allow_mutation`, delegate availability, durable evidence policy, and scrollback rejection all pass.
- Updated live-binding harness, canonical concept, status, decisions, and migration inventory so the consent policy is the gate before any host-owned executable GJC bridge.

## [2026-06-25] create | just-chill CLI contract entrypoint

- Added `scripts/just_chill_cli.py`, `scripts/just-chill`, and `scripts/check_just_chill_cli.py`.
- The CLI emits JSON contracts for route, remember, recall, and GJC handoff flows without executing GJC, writing Hermes, or owning canonical memory.
- Updated live-binding harness, canonical concept, status, decisions, and migration inventory so the CLI is documented as a contract producer for future host-owned bridges.

## [2026-06-25] create | just-chill memory migration fixture replay

- Added `scripts/just_chill_memory_migration_fixture.py` and `scripts/check_just_chill_memory_migration_fixture.py`.
- The fixture selects non-sensitive canonical wiki design facts, replays them through host-owned Hermes raw/RDF/vector MCP lifecycles plus summary receipts, and cleans up with delete receipts.
- Updated live-binding harness, canonical concept, status, decisions, and migration inventory so real personal memory migration remains explicit-approval work.

## [2026-06-25] update | just-chill vector sidecar MCP API

- Added vector-sidecar lifecycle contracts; external registration state is not asserted here.
- Added vector lifecycle receipt coverage, including read-back hash checks, exact hash/source-id search evidence, delete receipts, sensitive approval blocking, and deleted-source blocking.
- Updated live-binding/vector docs so vector search is mapped as host-owned exact sidecar evidence while production semantic ranking remains a later operator-owned model/index policy.

## [2026-06-25] create | just-chill vector recall gate slice

- Added `scripts/just_chill_vector_recall.py` and checks for vector sidecar contracts, provider-search-not-vector-authority mapping, recall allow/reject decisions, stale hash blocking, deletion/redaction propagation, scope checks, and sensitive-memory blocking.
- Updated live-binding harness, canonical concept, status, decisions, and migration inventory so vector recall remains a gated sidecar over Hermes-canonical refs rather than a new memory authority.
- Recorded that provider summary search is distinct from vector-sidecar authority; current host mappings are not published.

## [2026-06-25] create | just-chill host-owned Hermes/RDF receipt slice

- Added `scripts/just_chill_hermes_mcp_receipts.py` and checks for stdio JSON-RPC raw/RDF lifecycle receipt contracts, read-back hashes, approval/hash negative checks, and tombstone evidence.
- Installed/mapped live `pyshacl` and added `scripts/just_chill_rdf_persistence_receipts.py` with checks for host-owned RDF persistence evidence: deterministic ontology export, live SHACL conformance, Hermes RDF graph read-back, delete receipt, and just-chill boundary guards.
- Updated live-binding, ontology harness, status, decisions, concept, and migration inventory docs so the current state distinguishes host-owned evidence from just-chill execution authority.

## [2026-06-24] create | just-chill RDF/SHACL export slice

- Added deterministic RDF/OWL Turtle export manifests for just-chill ontology candidates, including source contract hashes, source artifact triples, promotion policy, and live-binding status.
- Added deterministic SHACL shape exports and validation reports that mirror candidate blockers without claiming a live SHACL engine ran.
- Updated ontology checks and docs so fake persistence receipts, storage-authority drift, and live-engine claims fail closed.

## [2026-06-24] create | just-chill ontology contract slice

- Added deterministic TBox/ABox ontology contracts for just-chill memory promotion candidates.
- Added SHACL-style validation blockers for explicit confirmation, PreferenceAssertion auto-promotion criteria, missing provenance, sensitive sources, deleted/redacted sources, and unmapped Hermes boundaries.
- Added `scripts/check_just_chill_ontology_contracts.py` and `harnesses/just-chill-ontology-contracts.md` to document and verify the contract-only ontology slice.

## [2026-06-24] create | just-chill Hermes live-boundary slice

- Added `just-chill-hermes-live-boundary-v1` reports to separate Hermes read-only status/MCP/setup visibility from unmapped raw artifact and summary memory write APIs.
- Added `scripts/check_just_chill_hermes_boundary.py` to verify storage authority, sensitive approval blocking, and ready-but-not-local write gates.
- Updated live-binding docs, inventory, status, and decisions so future RDF/OWL and SHACL work depends on explicit Hermes binding evidence rather than storage assumptions.

## [2026-06-24] create | just-chill visible-session orchestration planning slice

- Extended visible-session helpers with `--tmux-plan` and `tmux-orchestration-plan-v1` dry-run argv plans for create/attach/readiness/prompt/tail flows.
- Updated live binding readiness so visible handoff is `orchestration-plan-ready` only after clean helper probes plus `tmux`/`gjc` availability; missing tooling remains fail-closed.
- Added checks for invalid tmux targets, missing-tool readiness, no hidden execution, and durable evidence gates.

## [2026-06-24] create | just-chill visible-session helper slice

- Added repo-local host-owned visible-session helpers: `scripts/create-gjc-session`, `scripts/prompt-gjc-session`, and `scripts/tail-gjc-session`.
- Added `scripts/just_chill_visible_session_helpers.py` and `scripts/check_just_chill_visible_helpers.py` to validate helper contracts, metadata flow, scrollback rejection, and durable evidence acceptance.
- Updated live-binding docs and decisions so visible routed-session readiness depends on clean helper contract probes while real GJC execution remains owned by GJC/operator-visible sessions.

## [2026-06-24] create | just-chill live-binding slice

- Added `scripts/just_chill_live_bindings.py` to map available local GJC/Hermes surfaces with read-only probes and emit fail-closed visible-session handoff instructions.
- Added `scripts/just_chill_hermes_adapter.py` to wrap Hermes memory contracts in a write-blocked boundary adapter that preserves Hermes storage authority.
- Added `scripts/check_just_chill_live_bindings.py` and `harnesses/just-chill-live-bindings.md` to verify and document visible-session, coordinator/delegation, RPC, and Hermes storage readiness.

## [2026-06-24] create | just-chill bridge and memory contract slice

- Added `wiki/projects/jarvis/just-chill-migration-inventory.md` to classify current Jarvis assets as keep/adapt/rename/deprecate/remove for staged just-chill migration.
- Added `scripts/just_chill_bridge.py` to turn router packets into non-executing GJC bridge plans for visible routed sessions, coordinator MCP, `gjc_delegate_*`, and RPC host tools.
- Added `scripts/just_chill_memory_contracts.py`, `scripts/check_just_chill_bridge_contracts.py`, and `harnesses/just-chill-bridge-contracts.md` to define and verify Hermes raw artifact / summary memory contract skeletons before live API binding.

## [2026-06-24] create | just-chill router first executable slice

- Added `scripts/just_chill_router.py` as a deterministic request-to-route handoff packet generator for the just-chill design.
- Added `scripts/check_just_chill_router.py` and `harnesses/just-chill-router.md` to verify and document the first safe implementation slice.
- Updated `projects/jarvis/status.md` with the current operating-layer status and next integration steps.

## [2026-06-23] update | Hermes-GJC bridge reference added to just-chill

- Added the Gajae Code Hermes MCP Bridge documentation as the canonical integration reference for just-chill's GJC/Hermes handoff.
- Updated the canonical just-chill concept and Jarvis decisions to prefer visible routed GJC sessions first, then coordinator MCP, `gjc_delegate_*`, or RPC host tools when durable machine control or reverse host-tool access is needed.
- Clarified that completion evidence must come from durable turn/report/artifact/work signals, not tmux scrollback alone.

## [2026-06-23] update | just-chill vNext design reflected in wiki

- Added `concepts/just-chill-vnext-operating-layer.md` as the current canonical vNext design, preserving older JARVIS vNext pages as predecessor context.
- Recorded the rename and narrowing decision in `projects/jarvis/decisions.md`: just-chill is a personal operating console/router/memory gate, development routes to GJC, and Hermes remains the state/artifact/memory authority.
- Updated `index.md`, `entities/jarvis.md`, and the vNext concept pages to link forward to the just-chill design and resolve the old new-repo-vs-existing-repo question in favor of updating `$HOME/jarvis`.

## [2026-06-14] update | S1000D-RAG status synced to measured repo state

- Verified live repo state and corrected `projects/S1000D-RAG/status.md` drift: full suite `321 passed, 5 warnings` (was 300), focused v4/app/UI/runtime-router subset `88 passed, 2 warnings` (was 52), both run with miniforge python 3.12.
- Updated the "Current gate" section: all v4 closure commits are pushed; `main` tracks `origin/main` at `075c879` with `ahead/behind = 0/0`, replacing the stale "push pending / 353b64f latest" note. Refreshed the recent-commit list to current HEAD.

## [2026-06-12] review | vNext adversarial design review applied to concept docs

- Ran an approval-gated adversarial review of `concepts/jarvis-vnext-intent-to-contract-director.md` and the 2026-06-11 decisions against 24 external sources (verdict: revise / conditionally keep direction; BLOCK 0 · MAJOR 7 · MINOR 6 · NOTE 4). Full report archived at `projects/jarvis/reviews/vnext-adversarial-review-2026-06-12.md`.
- Applied the 7 MAJOR revisions: P2 differentiation redefined as the compile→delegate→contract-derived-judgment closed loop; P1 narrowed to interest-separated, contract-derived final judgment; per-field guardrail `enforcement_level` with auto-escalation; two-stage final judgment (mechanical gate → Director judgment); contract field grading must/should/optional; contract quality feedback loop added to MVP.
- Added `projects/jarvis/decisions.md` entry correcting the 2026-06-10 claim that competitors ship no verification layer (Optio/Symphony counter-evidence).
- Follow-up: applied the 4 MINOR fixes — declared the intent-to-contract MVP list canonical (F-B1), added role-terminology alignment note to `concepts/jarvis-vnext-executor-ontology.md` (F-B3), folded Level 2.5 into a Level 2 deep variant flag (F-A5), and reordered `projects/jarvis/decisions.md` entries newest-first (F-B4).

## [2026-06-11] update | JARVIS vNext intent-to-contract direction captured

- Added `concepts/jarvis-vnext-intent-to-contract-director.md` to capture the revised direction that JARVIS should focus on requirement normalization, backend-native task contracts, policy gates, evidence-backed verification, and result arbitration.
- Recorded the shorter default workflow: `Understand -> Contract -> Delegate -> Verify -> Report`, with strong backend-native systems handling more planning, subagents, background work, worktrees, and self-repair internally.
- Updated `concepts/jarvis-vnext-meta-control-plane.md`, `projects/jarvis/decisions.md`, and `index.md` to link the new direction.

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
