---
title: just-chill vNext Operating Layer
created: 2026-06-23
updated: 2026-06-26
type: concept
concept_type: architecture
status: draft
tags: [jarvis, vnext, agent-ops, control-plane, executor-routing, memory, ontology, hermes, gajae-code, knowledge-management, adapters]
sources: [conversation-2026-06-23, deep-interview-just-chill-vnext, ralplan-just-chill-v1, gajae-code-hermes-mcp-bridge]
confidence: high
relations:
  - type: supersedes
    target: concepts/jarvis-vnext-meta-control-plane
  - type: supersedes
    target: concepts/jarvis-vnext-intent-to-contract-director
  - type: supersedes
    target: concepts/jarvis-vnext-executor-ontology
  - type: supports
    target: projects/jarvis/decisions
  - type: uses
    target: concepts/ontology-informed-wiki
  - type: relates_to
    target: concepts/executor-routing
---

# just-chill vNext Operating Layer

## Summary

`just-chill` is the renamed and narrowed successor direction for JARVIS vNext. It updates the existing `/home/hskim/jarvis` project rather than creating a detached replacement repo.

The core product is a personal operating layer: it receives user requests, classifies intent and risk, routes work to the right tool, summarizes results, and absorbs durable knowledge into memory. It is not a coding agent, not a second GJC, and not a full workflow runtime.

Short form:

```text
User request
  -> just-chill intake / risk / route / context packet
  -> GJC or non-development tool lane
  -> result summary
  -> Hermes-backed memory and ontology gates
```

## Relationship to earlier JARVIS vNext design

The previous vNext pages remain predecessor context:

- [[concepts/jarvis-vnext-meta-control-plane|JARVIS vNext Meta-Control-Plane Direction]] defined the Director-over-backends boundary.
- [[concepts/jarvis-vnext-intent-to-contract-director|JARVIS vNext Intent-to-Contract Director]] defined contract-first delegation and evidence-backed judgment.
- [[concepts/jarvis-vnext-executor-ontology|JARVIS vNext Executor Ontology]] explored the executor pool and Gajae-Code candidate path.

The 2026-06-23 decision narrows the design further:

- keep the Director/control-plane intuition;
- keep evidence, provenance, risk gates, and memory responsibility;
- remove the idea that JARVIS must be its own development requirements compiler;
- route development work to GJC as the development workflow authority;
- make Hermes the state/artifact/memory access authority;
- make just-chill the operating console and memory gate above them.

## Authority boundaries

| Layer | Owns | Must not own |
|---|---|---|
| just-chill | request intake, intent/risk classification, routing decision, context packet, result summary, memory candidate gating, user-facing operating continuity | development planning, development implementation, GJC workflow state, Hermes storage authority |
| GJC | development direct work, deep-interview, ralplan, ultragoal, team, verification-ready implementation workflows | personal long-term memory policy, non-development operating console, Hermes storage internals |
| Hermes | raw artifacts, summaries, memory storage/access, provenance, retention/access/deletion surfaces | user intent judgment, GJC workflow decisions, canonical assertion promotion without just-chill policy |
| External tools | search, calendar, mail, documents, data analysis, domain APIs | final memory truth or irreversible external effects without policy approval |

## Development routing policy

Development-related requests should route to GJC by default when they involve code, repositories, APIs, tests, configuration, deployment, product behavior, debugging, review, or development workflow planning.

just-chill provides only observable subroute hints:

| Signal | GJC route hint |
|---|---|
| small clear edit, explicit file/symbol/test | GJC direct |
| vague development idea or requirements uncertainty | GJC `deep-interview` |
| clear but architecturally non-trivial development work | GJC `ralplan` |
| approved implementation needing durable completion loop | GJC `ultragoal` |
| implementation requiring tmux-backed parallel workers | GJC `team` |

Rule: just-chill must not perform a second development interview or write its own development spec when GJC `deep-interview` or `ralplan` is the correct authority.

## GJC/Hermes integration reference

Use the Gajae Code Hermes MCP Bridge documentation as the canonical integration reference: <https://gajae-code.com/docs/hermes-mcp-bridge.html>.

Integration policy:
- First pass: prefer a visible tmux-backed routed `gjc` session with `/skill:` prompt handoff for observability.
  Repo-local v1 helpers (`scripts/create-gjc-session`, `scripts/prompt-gjc-session`, `scripts/tail-gjc-session`) provide the metadata/evidence contract and can emit dry-run `tmux-orchestration-plan-v1` argv plans; operator-executed tmux/TUI automation remains a separate explicit bridge.
- Pure machine control: use `gjc mcp-serve coordinator` / `gjc setup hermes` for durable turn state, session listing, bounded polling, structured questions, artifact reads, and reports.
- Whole-workflow delegation: use `gjc_delegate_plan`, `gjc_delegate_execute`, and `gjc_delegate_team` when just-chill wants one GJC workflow and a returned `turn_id`.
- Reverse host tools: expose just-chill/Hermes tools to GJC through RPC `customTools`, not GJC MCP internals.
- Evidence and safety: completion must come from durable turn/report/artifact/diff/test/PR evidence rather than tmux scrollback; mutating calls require scoped workdir roots, startup mutation classes, and per-call `allow_mutation: true`.


## Non-development v1 lane

v1 should directly support knowledge and communication work:

- summarization;
- writing and editing prose;
- research synthesis with source tracking;
- meeting notes and document organization;
- memory save and memory recall;
- result summaries and follow-up extraction.

Calendar, email sending, and data-analysis tasks are tool-routed or draft-first in v1. External sends, payments, destructive operations, sensitive data handling, deploys, pushes, and broad deletes require approval.

## Memory and ontology architecture

just-chill uses Hermes as the infrastructure layer and adds policy/live-boundary gates on top:

```text
raw artifact store
  -> summary memory
  -> vector index sidecar
  -> RDF/OWL candidate extraction
  -> SHACL validation
  -> confirmation / promotion gate
  -> canonical ABox
```

Memory layers:

1. **Raw artifacts**: source evidence owned by Hermes, including requests, attachments, handoff packets, tool results, generated drafts, transcripts, and source lists.
2. **Summary memory**: human-readable derived summaries with source artifact links, confidence, sensitivity, retention, access policy, and deletion/redaction state.
3. **Canonical RDF/OWL TBox and ABox**: durable semantic memory that can influence future routing, context assembly, preference behavior, policy decisions, and decision recall.
4. **Operational/audit graph**: routing, task, result, validation, handoff, and privacy events. It is traceability evidence, not canonical personal memory.
5. **Vector sidecar**: recall index over Hermes references and summaries; it must resolve through Hermes and respect access, sensitivity, deletion, and retention rules.

Promotion rules:

- `DecisionAssertion`: explicit user confirmation required.
- `PolicyAssertion`: explicit user confirmation required.
- `PreferenceAssertion`: automatic promotion allowed only when repeated across independent source artifacts, non-sensitive, non-destructive, access-allowed, retention-valid, conflict-free, and high confidence.
- Any canonical assertion without valid raw artifact provenance is invalid.
- Any source deleted, access-denied, expired, or redacted beyond support invalidates or downgrades dependent assertions.
- Hermes status/MCP/setup probes are read-only visibility; active provider tools may support summary/fact-memory candidate plans, but raw artifact writes require an explicit mapped Hermes API or MCP tool before promotion.
- Local raw artifact staging may preserve source evidence and deletion receipts as migration evidence, but Hermes raw artifact promotion now has a mapped host-owned MCP API (`just_chill_memory_api`) and still requires staging receipts, approval gates, Hermes create results, and read-back hash evidence before any canonical promotion is recorded.
- Provider-backed summary/fact-memory plans may target Holographic `fact_store(add/remove)`, but just-chill records only host-supplied local receipts and must not call the provider itself; removal requires prior add provenance, explicit approval, and a reason. Sensitive approval authorizes redacted summary retention only, not plaintext sensitive rehydration.
- A future mapped write surface must be create/write/store/persist/upsert/add-shaped for the correct raw-artifact, summary-memory, or provider-tool resource; status/list/read-only surfaces are visibility only.
- Current implementation emits deterministic ontology contracts (`TBox` classes/properties, `ABox` promotion candidates, RDF/OWL Turtle export manifests, SHACL shape exports, validation reports, and live RDF persistence receipt plans) plus mapped vector sidecar / recall-gate contracts; just-chill still does not own canonical memory, embed text, write/search vector stores itself, run SHACL, or call Hermes APIs directly.
- Approval tokens are production-meaningful only when verified by a host-owned registry or future Hermes-native equivalent; local shape-only acceptance is retained for debug/fixture compatibility but does not prove approval authenticity, scope, subject, expiry, or revocation state.

## Risk and autonomy policy

Default autonomy is aggressive for reversible internal work and conservative for irreversible or external effects.

Auto-allowed candidates:

- local summarization;
- source-backed research synthesis;
- draft generation;
- memory candidate creation;
- reversible organization of internal notes when policy allows.

Approval-required candidates:

- external email/calendar sends;
- payments or purchases;
- deletion, redaction, or broad overwrite;
- deploy, push, release, or public publication;
- secrets, credentials, auth files, or sensitive memory;
- canonical Decision/Policy ABox promotion.

## Brownfield migration policy

The implementation target is the existing `/home/hskim/jarvis` repository.

Migration rules:

- preserve Git history;
- do not delete `.git`, rewrite history, squash history, or force-push without explicit approval;
- prefer normal file moves/renames so lineage is traceable;
- keep old JARVIS vNext pages as predecessor context rather than erasing them;
- classify existing assets as `keep`, `rename`, `adapt`, `deprecate`, or `remove` before broad edits;
- leave evidence for changed files, tests/checks run, migration notes, and unresolved compatibility risks.

## Execution gates

Implemented slices so far:

1. Route-decision packet: `scripts/just_chill_router.py` and `harnesses/just-chill-router.md`.
2. Contract-level GJC/Hermes bridge planning: `scripts/just_chill_bridge.py`, `scripts/just_chill_memory_contracts.py`, and `harnesses/just-chill-bridge-contracts.md`.
3. Live-boundary mapping and fail-closed adapter stubs: `scripts/just_chill_live_bindings.py`, `scripts/just_chill_hermes_adapter.py`, `scripts/check_just_chill_live_bindings.py`, and `harnesses/just-chill-live-bindings.md`.
4. Host-owned visible-session helper contracts: `scripts/just_chill_visible_session_helpers.py`, `scripts/create-gjc-session`, `scripts/prompt-gjc-session`, `scripts/tail-gjc-session`, and `scripts/check_just_chill_visible_helpers.py`.
5. Visible-session orchestration planning: helper `--tmux-plan` support, `orchestration-plan-ready` live readiness, invalid-target checks, and missing-tool fail-closed behavior.
6. Hermes live-boundary reports: `just-chill-hermes-live-boundary-v1` distinguishes status/MCP/setup read visibility from raw artifact storage, maps active Holographic `fact_store` as a host-owned summary/fact-memory provider tool when available, preserves Hermes storage authority, and blocks sensitive memory without approval.
7. Ontology contract skeleton: deterministic TBox/ABox candidate output, source provenance, assertion-kind promotion rules, and SHACL-style blockers in `scripts/just_chill_ontology_contracts.py`, verified by `scripts/check_just_chill_ontology_contracts.py`.
8. RDF/OWL and SHACL export contracts: deterministic Turtle manifests, SHACL shape manifests, and validation reports without live RDF persistence.
9. Local raw artifact staging: `scripts/just_chill_raw_artifact_store.py` preserves raw contract/content/write/delete receipts under ignored repo-local storage while keeping Hermes canonical authority; staging remains migration evidence even after host-owned Hermes raw tools are mapped.
10. Summary provider receipts: `scripts/just_chill_summary_memory_receipts.py` emits host-owned Holographic `fact_store(add/remove)` plans and records local add/remove receipts from supplied provider result evidence without local provider execution.
11. Raw artifact API discovery and promotion planning: `scripts/just_chill_hermes_raw_artifact_boundary.py` detects Hermes raw artifact create/read/delete APIs or MCP tools, now maps the `just_chill_memory_api` raw lifecycle tools, and emits host-owned local-staging-to-Hermes promotion plans without local Hermes execution.
12. RDF/SHACL live-boundary planning: `scripts/just_chill_ontology_contracts.py --live-boundary --plan-persistence` maps host RDF parser / SHACL engine / Hermes RDF graph API readiness and emits host-owned persistence plans without local engine or Hermes execution.
13. External Hermes memory MCP API: `scripts/just_chill_hermes_memory_mcp.py` is registered as `just_chill_memory_api` and exposes host-owned raw artifact, RDF graph, vector sidecar, and status tools with hash, approval, delete, read-back, and retrieval evidence guards.
14. Host-owned live persistence receipts: `scripts/just_chill_hermes_mcp_receipts.py` exercises the mapped raw/RDF/vector MCP lifecycles, and `scripts/just_chill_rdf_persistence_receipts.py` combines live `pyshacl` evidence with Hermes RDF graph read-back/delete receipts while keeping `justChillCallsHermes: false` and `justChillRunsShaclEngine: false`.
15. Vector sidecar and recall gates: `scripts/just_chill_vector_recall.py` maps provider search vs vector authority, creates non-canonical vector candidates from Hermes-canonical refs/hashes, and validates recall admission with scope, sensitivity, deletion/redaction, stale-hash, provenance, and durable host retrieval evidence gates.
16. Host-owned vector sidecar MCP API: `just_chill_memory_api` maps `hermes.vector_sidecar.create/search/read/delete` as exact text-hash/source-id sidecar tools. These tools provide durable retrieval evidence for recall gates but do not make just-chill a vector executor or semantic ranking authority.
17. Non-sensitive migration fixture replay: `scripts/just_chill_memory_migration_fixture.py` selects repository wiki design facts, exercises host-owned raw/RDF/vector MCP lifecycles plus summary receipts in a temporary store, and cleans up with no private memory promotion.
18. Debug CLI contract entrypoint: `scripts/just_chill_cli.py` and `scripts/just-chill` produce JSON for `route`, `remember`, `recall`, and `handoff-gjc`; every output keeps `executionAllowedHere: false`, does not call GJC/Hermes, and preserves Hermes as canonical memory authority. This is not the product UX.
19. GJC coordinator/delegation consent policy: `scripts/just_chill_gjc_consent_policy.py` keeps visible sessions first and only marks host mutation ready when coordinator smoke, mutation classes (`sessions`, `questions`, `reports`), per-call `allow_mutation`, delegate availability, durable evidence, and scrollback rejection are all satisfied.
20. End-to-end dogfood contract harness: `scripts/just_chill_dogfood_harness.py` exercises route -> GJC handoff -> memory/raw/RDF/SHACL/vector contracts -> recall gate -> consent policy, with stale/deleted/redacted recall and sensitive-memory negative cases, without starting GJC or writing Hermes.
21. Hermes-facing harness adapter: `scripts/just_chill_harness.py` exposes route, remember plan, recall gate, GJC handoff plan, consent evaluation, status, and handle operations as importable JSON contracts for Hermes callers while keeping all local execution authority disabled.
22. Harness MCP wrapper: `scripts/just_chill_harness_mcp.py` exposes the same operations as `just_chill.*` stdio MCP tools for Hermes. It is registered in Hermes as `just_chill_harness` after explicit operator approval; it still does not execute GJC, write Hermes memory, run SHACL, call coordinator/delegate tools, or search vector stores.
23. Hermes-main dogfood harness: `scripts/just_chill_hermes_harness.py` proves the intended product flow: Hermes receives the user request, just-chill acts as a policy harness, CLI remains debug-only, and host-owned next steps receive durable contract output.
24. Host-owned approval registry: `scripts/just_chill_approval_registry.py` issues, verifies, and revokes approval tokens bound to scope, optional subject hash, expiry, actor, reason, and revocation events while storing only token hashes; CLI/harness/MCP remember and recall gates can require it through `--approval-registry`, `approvalRegistry`, or `JUST_CHILL_APPROVAL_REGISTRY`.
25. Host-owned visible GJC execution bridge MVP: `scripts/just_chill_gjc_execution_bridge.py` consumes a `gjcHandoffPlan`, writes a task file plus visible-session metadata, emits operator argv plans, and verifies durable completion evidence while refusing hidden GJC starts, prompt injection, coordinator/delegate calls, Hermes writes, and scrollback completion.

Current live-binding state: repo-local visible routed-session helper contracts are available, probe cleanly, and become `orchestration-plan-ready` when `tmux`/`gjc` are available; coordinator MCP and `gjc_delegate_*` smoke discovery are available locally, and executable coordinator/delegation remains gated by `scripts/just_chill_gjc_consent_policy.py`: required mutation classes, explicit per-call `allow_mutation`, clean coordinator smoke, delegate availability, durable evidence, scrollback rejection, and unsupported bridge-path fail-closed checks. RPC host `customTools` is not mapped yet. Hermes reports active provider `holographic`, so just-chill can emit a host-owned summary/fact-memory `fact_store(action=add/remove)` write/receipt plan with `allowedHere: false`; local add/remove receipts require durable provider result evidence and never prove just-chill executed the provider call. The external `just_chill_memory_api` MCP server is configured in Hermes and maps raw artifact, RDF graph, and vector sidecar lifecycle tools; host-owned receipt runners now exercise those tools with read-back/search/delete evidence. just-chill may discover and plan against those tools but must not call them directly. Raw artifact contracts can still be staged locally with hash-checked write/delete receipts for migration evidence, but that staging is not canonical Hermes storage. Ontology output now includes contract-only RDF/OWL + SHACL exports and RDF/SHACL live-boundary reports; current host has RDF parsing support (`rdflib`/`rdfpipe`), live `pyshacl`, and mapped Hermes RDF graph lifecycle tools, so eligible host-owned fixture candidates can produce RDF persistence receipts while real canonical promotion still requires approved source artifacts and policy gates. Vector sidecar exact-hash/source-id tools are mapped for durable recall evidence; production semantic vector ranking remains a later operator-owned model/index policy decision. The non-sensitive migration fixture replay now proves repository wiki design facts can move through raw/RDF/vector receipt lifecycles plus summary receipts without private memory promotion; real personal memory promotion still requires explicit source selection and approval. Hermes is now the intended product UX: `scripts/just_chill_harness.py` and the registered `just_chill_harness` MCP server provide Hermes-facing policy/handoff contracts, while `scripts/just-chill` remains a debug/test/fixture CLI. `hermes mcp add just_chill_harness --command python3 --args /home/hskim/jarvis/scripts/just_chill_harness_mcp.py` connected and enabled all 7 `just_chill.*` tools after explicit approval; `hermes mcp test just_chill_harness` verified connection/tool discovery. The host-owned approval registry now provides scope/subject/expiry/revocation verification for sensitive remember/recall gates while storing only token hashes; shape-only approval token acceptance remains debug/fixture-only. The visible GJC execution bridge MVP now converts a `gjcHandoffPlan` into host-owned task/session artifacts and completion-evidence validation without actually running GJC or accepting scrollback. The Hermes-main dogfood harness proves the integrated flow stays coherent locally and fail-closes on stale, deleted, or redacted recall evidence and sensitive memory.

## Failure criteria

Any one of these is a release blocker:

- just-chill performs development requirements interviews instead of routing to GJC;
- development routing misses broad code/repo/API/test/config/deploy/product-behavior signals;
- high-risk actions run without approval;
- Decision/Policy ABox assertions promote without explicit confirmation;
- ABox assertions lack raw artifact provenance or SHACL validation;
- operational/audit graph facts influence policy, preference, decision, or routing behavior without promotion;
- Hermes or GJC authority boundaries are bypassed.

## Resolved open questions

- The first implementation is an update inside `/home/hskim/jarvis`, not a new `/home/hskim/projects/jarvis-vnext` repo.
- GJC is the preferred development worker family for the just-chill target design.
- LazyCodex remains a specialized Codex-native high-intensity option, not the default.
- Hermes remains the state/artifact/memory infrastructure, while just-chill owns memory policy and promotion judgment.
- Hermes/GJC integration should follow the Gajae Code Hermes MCP Bridge reference, starting with visible routed sessions unless pure machine control or whole-workflow delegation requires coordinator MCP or `gjc_delegate_*`.

## See also

- [[concepts/jarvis-vnext-meta-control-plane|JARVIS vNext Meta-Control-Plane Direction]]
- [[concepts/jarvis-vnext-intent-to-contract-director|JARVIS vNext Intent-to-Contract Director]]
- [[concepts/jarvis-vnext-executor-ontology|JARVIS vNext Executor Ontology]]
- [[concepts/executor-routing|Executor Routing]]
- [[concepts/ontology-informed-wiki|Ontology-Informed Wiki]]
- [Gajae Code Hermes MCP Bridge](https://gajae-code.com/docs/hermes-mcp-bridge.html)
