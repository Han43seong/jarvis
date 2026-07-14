# JARVIS Decisions

## 2026-06-26 — Visible GJC execution bridge remains host-owned and evidence-gated

Decision:
- Add `scripts/just_chill_gjc_execution_bridge.py` and `scripts/check_just_chill_gjc_execution_bridge.py`.
- The bridge consumes `gjcHandoffPlan` output and prepares host-owned task files, visible-session metadata, prompt handoff records, and operator argv plans.
- The bridge verifies completion only from durable evidence accepted by the visible-session helper contract.
- The bridge does not start GJC, inject prompts, call coordinator/delegate tools, write Hermes, or accept tmux scrollback as completion evidence.

Rationale:
- Hermes needs a concrete next hop after `just_chill.gjc_handoff.plan`, but the just-chill layer must not become a hidden executor.
- Separating preparation from actual execution preserves visibility while giving production automation a stable contract to wrap later.

Consequences:
- A production operator bridge can run the emitted argv plan, but it must remain host-owned and return durable evidence.
- Coordinator/delegation paths still require the consent policy before mutation.

Reference:
- `scripts/just_chill_gjc_execution_bridge.py`
- `scripts/check_just_chill_gjc_execution_bridge.py`
- `harnesses/just-chill-live-bindings.md`

## 2026-06-26 — Approval tokens require registry verification for production use

Decision:
- Add `scripts/just_chill_approval_registry.py` and `scripts/check_just_chill_approval_registry.py`.
- Registry-backed approvals are host-owned JSONL events that store only token hashes, token previews, scope, optional subject hash, expiry, actor, reason, and revocation events.
- `scripts/just_chill_cli.py`, `scripts/just_chill_harness.py`, and `scripts/just_chill_harness_mcp.py` accept optional `approvalRegistry` / `--approval-registry` / `JUST_CHILL_APPROVAL_REGISTRY` inputs for sensitive memory and recall gates.
- Production-sensitive remember/recall paths must use registry-backed verification or a future Hermes-native equivalent; shape-only token acceptance remains a local debug/fixture compatibility mode.

Rationale:
- Prefix-shape checks block arbitrary strings but do not prove approval authenticity, scope, subject, expiry, or revocation state.
- A host-owned registry closes that gap without making just-chill the Hermes memory writer or executor.

Consequences:
- Sensitive memory/recall can now be tested with real scope/subject-bound approvals while preserving no-execution/no-Hermes-write authority boundaries.
- Future Hermes-native approval/audit APIs can replace the local registry if they preserve the same fail-closed verification semantics.

Reference:
- `scripts/just_chill_approval_registry.py`
- `scripts/check_just_chill_approval_registry.py`
- `harnesses/just-chill-live-bindings.md`

## 2026-06-26 — Hermes is the product UX and just-chill is a harness

Decision:
- Add `scripts/just_chill_harness.py`, `scripts/just_chill_harness_mcp.py`, `scripts/just_chill_hermes_harness.py`, and focused checks for each.
- Hermes remains the user-facing agent/UI. just-chill is a Hermes-facing policy/routing/memory/GJC-handoff harness.
- The repo-local `scripts/just-chill` CLI is retained for debug, CI, and fixture generation only; it is not the product UX.
- The harness MCP exposes `just_chill.route`, `just_chill.remember.plan`, `just_chill.recall.gate`, `just_chill.gjc_handoff.plan`, `just_chill.consent.evaluate`, `just_chill.handle`, and `just_chill.status`.
- Registering the harness MCP into Hermes config requires explicit operator approval because it mutates external Hermes configuration.
- After explicit approval, register the harness MCP in Hermes as `just_chill_harness`; `hermes mcp test just_chill_harness` must verify connection and all 7 tools.

Rationale:
- A separate just-chill user CLI would compete with Hermes and weaken the architecture.
- Keeping just-chill as a harness preserves the separation: Hermes owns user interaction and tool execution, GJC owns development work, Hermes memory APIs own storage, and just-chill owns policy/contract generation.

Consequences:
- Future product UX work should dogfood Hermes-main flows, not a standalone just-chill CLI.
- Host-owned execution bridges consume harness/MCP output and must return durable evidence; just-chill still does not execute GJC or write Hermes.
- `just_chill_harness` is now the Hermes-facing MCP registration for product dogfood, but future remove/re-register operations still require explicit approval because they mutate external Hermes config.

Reference:
- `scripts/just_chill_harness.py`
- `scripts/just_chill_harness_mcp.py`
- `scripts/just_chill_hermes_harness.py`
- `harnesses/just-chill-live-bindings.md`
## 2026-06-25 — Integrated dogfood remains deterministic until host execution is approved

Decision:
- Add `scripts/just_chill_dogfood_harness.py` and `scripts/check_just_chill_dogfood_harness.py`.
- The dogfood harness exercises the integrated route -> GJC handoff -> memory/raw/RDF/SHACL/vector contract -> recall gate -> consent policy chain.
- The harness must stay deterministic and local: no GJC session start, no Hermes MCP calls, no live SHACL execution, and no vector search execution from just-chill.
- Stale, deleted, redacted recall evidence and sensitive memory are negative-path blockers.

Rationale:
- Individual contract checks can pass while the stitched product path drifts.
- The integrated harness gives one safe regression target before any host-owned executable bridge consumes the contracts.

Consequences:
- Future live bridge work should extend this harness with host-owned evidence receipts rather than moving execution into just-chill.
- Real personal memory migration remains outside the dogfood fixture unless explicitly approved.

Reference:
- `scripts/just_chill_dogfood_harness.py`
- `scripts/check_just_chill_dogfood_harness.py`
- `harnesses/just-chill-live-bindings.md`

## 2026-06-25 — Coordinator/delegation mutation requires explicit host consent

Decision:
- Add `scripts/just_chill_gjc_consent_policy.py` and `scripts/check_just_chill_gjc_consent_policy.py`.
- Keep visible routed sessions as the default execution bridge.
- Coordinator MCP and `gjc_delegate_*` paths are host-mutation-ready only when coordinator smoke is clean, required mutation classes (`sessions`, `questions`, `reports`) are enabled, per-call `allow_mutation` is supplied, delegate tools are available when applicable, durable evidence is required, and scrollback is rejected as completion evidence.
- The policy emits JSON only; just-chill still does not call coordinator or delegate tools.

Rationale:
- Coordinator/delegation tools are powerful machine-control surfaces and must not become implicit hidden execution.
- Mutation classes without per-call consent are too broad; per-call consent without coordinator/tool readiness is not enough.
- Durable non-scrollback evidence is the completion source of truth.

Consequences:
- Existing coordinator/delegation live-binding checks remain fail-closed and now have a dedicated policy artifact for future host bridges.
- GJC execution bridges must consume this policy or preserve equivalent checks before mutating work.

Reference:
- `scripts/just_chill_gjc_consent_policy.py`
- `scripts/check_just_chill_gjc_consent_policy.py`
- `harnesses/just-chill-live-bindings.md`

## 2026-06-25 — just-chill CLI is a contract producer, not an executor

Decision:
- Add `scripts/just_chill_cli.py`, executable wrapper `scripts/just-chill`, and `scripts/check_just_chill_cli.py`.
- The CLI supports `route`, `remember`, `recall`, and `handoff-gjc` flows by composing existing router, bridge, memory, and recall contracts.
- Every CLI output keeps `executionAllowedHere: false`, `justChillExecutesGjc: false`, `justChillWritesHermes: false`, and `justChillOwnsCanonicalMemory: false`.
- `handoff-gjc --allow-mutation` records requested mutation consent but still does not execute; host-owned GJC tooling must consume the contract and return durable evidence.
- `recall` requires host-owned retrieval evidence plus fresh canonical source hash/deletion/redaction state before a memory candidate can enter context.
- Approval tokens are treated as host approval references, not arbitrary strings; acceptable CLI token forms use `approval://`, `host-approval://`, or `hermes-approval://` prefixes, invalid tokens do not clear sensitive-memory or recall gates, and shape acceptance is not authenticity until a host approval registry verifies it.

Rationale:
- Users need a simple entrypoint, but adding one must not blur just-chill into a second GJC or Hermes writer.
- The CLI gives Hermes/operator layers a stable JSON contract to consume while preserving fail-closed authority boundaries.

Consequences:
- The next e2e dogfood harness can exercise CLI route -> memory contract -> recall gate -> GJC handoff plan without hidden execution.
- Future executable bridges must remain host-owned and evidence-returning rather than moving execution into the CLI.

Reference:
- `scripts/just_chill_cli.py`
- `scripts/just-chill`
- `scripts/check_just_chill_cli.py`
- `harnesses/just-chill-live-bindings.md`

## 2026-06-25 — Non-sensitive memory migration fixture replay is host-owned

Decision:
- Add `scripts/just_chill_memory_migration_fixture.py` and `scripts/check_just_chill_memory_migration_fixture.py`.
- The fixture may replay only non-sensitive repository wiki design facts, not private memories.
- The replay uses host-owned Hermes raw artifact, RDF graph, and vector sidecar MCP lifecycles plus local summary receipts, then deletes fixture raw/RDF/vector records after read-back verification.
- just-chill remains the policy/contract layer and does not call Hermes directly.

Rationale:
- Real memory migration needs a safe rehearsal that proves provenance, read-back hashes, retention/access/deletion fields, and cleanup receipts before any personal memory is promoted.
- Repository design facts are public-to-the-repo and non-sensitive, making them suitable fixture candidates.

Consequences:
- The fixture demonstrates the migration shape without granting canonical promotion authority.
- Personal or production memory migration still requires explicit source selection and approval.

Reference:
- `scripts/just_chill_memory_migration_fixture.py`
- `scripts/check_just_chill_memory_migration_fixture.py`
- `harnesses/just-chill-live-bindings.md`

## 2026-06-25 — Host-owned vector sidecar MCP API is mapped

Decision:
- Extend `just_chill_memory_api` with `hermes.vector_sidecar.create/search/read/delete`.
- Keep sidecars non-canonical and host-owned: every sidecar references Hermes-owned source ids, hashes, receipt refs, deletion/redaction state, access policy, and embedding metadata.
- Use exact text-hash or canonical-source-id search for the current deterministic API; do not claim semantic vector retrieval until a production embedding/index runner and model policy are chosen.
- just-chill may discover these tools and validate recall gates, but it still must not call Hermes/vector tools directly or become storage/search authority.

Rationale:
- Recall needs durable retrieval evidence, not provider scrollback or opaque search output.
- Deletion/redaction/sensitivity gates must be enforced at storage, search, and recall-admission boundaries.
- A deterministic exact-hash/source-id API is safer than pretending semantic search exists before the operator-owned vector model/index policy is selected.

Consequences:
- MCP lifecycle receipts now include vector create/read/search/delete and negative approval/deleted-source checks.
- `scripts/just_chill_vector_recall.py --boundary --probe` can report `live-vector-api-mapped` when `just_chill_memory_api` is configured.
- Production semantic recall remains a later extension, but the authority and evidence contract is now live.

Reference:
- `scripts/just_chill_hermes_memory_mcp.py`
- `scripts/just_chill_hermes_mcp_receipts.py`
- `scripts/just_chill_vector_recall.py`
- `harnesses/just-chill-live-bindings.md`

## 2026-06-25 — Vector recall is a gated sidecar over Hermes memory

Decision:
- Add `scripts/just_chill_vector_recall.py` for vector sidecar candidates and recall-gate decisions.
- Treat compatible provider summary search as distinct from vector-sidecar authority.
- Keep vector sidecars non-canonical: they reference Hermes-owned source ids/hashes and cannot replace raw/RDF/summary storage.
- Require recall gates to check canonical Hermes provenance, fresh read-back hashes, access scope, deletion/redaction state, sensitivity approval, retrieval score, and durable host retrieval evidence.

Rationale:
- Recall is where stale or over-broad memory can silently change behavior, so it needs an explicit gate rather than direct vector-search output injection.
- A sidecar can improve retrieval only if Hermes remains the authority for deletion, retention, access, and provenance.
- Provider search may be useful evidence, but it is not the same as a mapped Hermes vector store/search API.

Consequences:
- Vector-recall checks join the focused just-chill verification suite.
- Live vector search is now mapped through host-owned MCP exact-hash/source-id sidecar tools; semantic vector ranking remains fail-closed until an operator-owned model/index policy is selected.
- Real memory promotion must preserve the sidecar gate shape so deleted/redacted/stale sources cannot be recalled.

Reference:
- `scripts/just_chill_vector_recall.py`
- `scripts/check_just_chill_vector_recall.py`
- `harnesses/just-chill-live-bindings.md`

## 2026-06-25 — Host-owned receipts prove Hermes/RDF lifecycle before canonical promotion

Decision:
- Add `scripts/just_chill_hermes_mcp_receipts.py` to exercise `just_chill_memory_api` raw artifact and RDF graph create/read/delete through stdio JSON-RPC and record read-back hash plus delete receipt evidence.
- Install/map live `pyshacl` in the host environment and add `scripts/just_chill_rdf_persistence_receipts.py` for eligible fixture candidates.
- Keep receipts host-owned: just-chill consumes evidence but keeps `justChillCallsHermes: false` and `justChillRunsShaclEngine: false`.

Rationale:
- API mapping alone does not prove lifecycle semantics; read-back hash and delete receipts are required before migration/persistence is credible.
- Live SHACL evidence must be distinguishable from deterministic contract validation.
- The operating layer must not quietly become the Hermes executor.

Consequences:
- Raw/RDF MCP lifecycle and RDF persistence receipt checks are part of the focused just-chill verification suite.
- Eligible fixture candidates can now produce live SHACL + Hermes RDF graph receipts.
- Real canonical promotion still requires selecting approved source artifacts/candidates and preserving the same receipt shape.

Reference:
- `scripts/just_chill_hermes_mcp_receipts.py`
- `scripts/check_just_chill_hermes_mcp_receipts.py`
- `scripts/just_chill_rdf_persistence_receipts.py`
- `scripts/check_just_chill_rdf_persistence_receipts.py`
- `harnesses/just-chill-live-bindings.md`
- `harnesses/just-chill-ontology-contracts.md`

## 2026-06-24 — just-chill memory MCP provides host-owned Hermes raw/RDF APIs

Decision:
- Add `scripts/just_chill_hermes_memory_mcp.py` as a host-owned stdio MCP server and register it in Hermes as `just_chill_memory_api`.
- Expose raw artifact lifecycle tools (`hermes.raw_artifact.create/read/delete`) and RDF graph lifecycle tools (`hermes.rdf_graph.create/read/delete`) plus `hermes.memory_api.status`.
- Enforce content-hash checks, conforming SHACL-result requirements for RDF graph creation, explicit approval for sensitive/destructive operations, and deletion receipts in the host-owned store.
- Keep just-chill from calling these tools directly; just-chill discovers them, emits plans, and requires host/Hermes result evidence.

Rationale:
- Local staging and contract exports were reviewable but not live Hermes APIs.
- Hermes needs a concrete MCP tool boundary before raw artifacts or RDF graph persistence can be treated as externally executable.
- Read-back hashes and delete/redact lifecycle tools are required before canonical storage can be trusted.

Consequences:
- Host registration is an external, approval-gated operation; current configuration and tool availability are not published.
- The canonical host-owned store root is environment-configured and intentionally not published.
- Raw artifact promotion can become ready when it has local staging receipts and approval gates; RDF/ABox persistence needed a live SHACL engine such as `pyshacl`, which the later host-owned receipt decision maps for evidence production.

Reference:
- `scripts/just_chill_hermes_memory_mcp.py`
- `scripts/check_just_chill_hermes_memory_mcp.py`
- `harnesses/just-chill-live-bindings.md`

## 2026-06-24 — RDF/ABox persistence needs live SHACL and graph lifecycle APIs

Decision:
- Add read-only RDF/SHACL live-boundary discovery to ontology contracts before attempting canonical RDF/ABox persistence.
- Treat RDF parsing support (`rdflib`/`rdfpipe`) as necessary but insufficient: a live SHACL engine plus Hermes RDF graph create/read/delete APIs must be mapped before a persistence plan can become ready. The later `just_chill_memory_api` decision maps the graph lifecycle tools; SHACL remains the open gate.
- Keep persistence host-owned: just-chill emits `wouldCall` plans and requires future SHACL engine results, Hermes graph create results, and read-back hash evidence, but it does not run the live SHACL engine or call Hermes graph APIs directly.

Rationale:
- Deterministic Turtle and SHACL contract exports are review artifacts, not proof of live validation or canonical storage.
- Canonical ontology memory can affect future routing and policy, so promotion needs both semantic validation and storage lifecycle controls.
- Delete/redact capability is required before graph persistence because retention and removal must be auditable.

Consequences:
- `scripts/just_chill_ontology_contracts.py` now owns RDF/SHACL live-boundary reporting and host-owned persistence planning.
- At this decision point, local state was partial: RDF parsing was available, but `pyshacl`/live SHACL execution and Hermes RDF graph create/read/delete APIs were unmapped.
- Follow-up required mapping those live surfaces, then executing persistence through a host-owned runner with durable result evidence; the later host-owned receipt decision completes the fixture evidence path.

Reference:
- `scripts/check_just_chill_ontology_contracts.py`
- `harnesses/just-chill-ontology-contracts.md`

## 2026-06-24 — Raw artifact promotion needs create/read/delete APIs

Decision:
- Add read-only Hermes raw artifact API discovery before attempting local-staging-to-Hermes promotion.
- Require mapped raw artifact create/write, read, and delete/redact APIs or MCP tools before a promotion plan can become ready.
- Keep promotion host-owned: just-chill emits `wouldCall` plans and requires future Hermes create result plus read-back hash evidence, but it does not call Hermes raw artifact APIs directly.
- At this decision point, treat the local state as unmapped/fail-closed because Hermes help/tools/MCP probes exposed no raw artifact create/read/delete surface.

Rationale:
- Local raw artifact staging preserves evidence, but canonical promotion is unsafe without both write and read-back verification.
- Delete/redact capability is part of retention/deletion policy; mapping only create would make cleanup semantics unverifiable.
- Read-only probes prevent false confidence and avoid mutating Hermes while discovering capabilities.

Consequences:
- `scripts/just_chill_hermes_raw_artifact_boundary.py` owns raw artifact API discovery and promotion planning.
- `scripts/just_chill_hermes_adapter.py` exposes `rawArtifactApiDiscovery` for raw artifact contracts.
- Follow-up required installing or mapping a real Hermes raw artifact API/MCP tool, then executing promotion through a host-owned runner with durable result evidence; the later `just_chill_memory_api` decision maps that API surface.

Reference:
- `scripts/check_just_chill_hermes_raw_artifact_boundary.py`
- `harnesses/just-chill-live-bindings.md`

## 2026-06-24 — Summary provider receipts are local evidence, not provider execution

Decision:
- Add a host-owned receipt bridge for provider-backed summary memories without assuming a current provider or receipt/audit mapping.
- Emit add/remove provider-tool plans and record local add/remove receipts only when the host supplies durable provider result evidence.
- Require explicit approval for sensitive summary writes and every summary removal; removal also requires a prior add receipt and a reason.
- Keep Hermes as canonical memory authority and keep just-chill from calling provider tools directly.

Rationale:
- A compatible provider may store summary/fact memories, but auditable retention/deletion evidence remains required before those memories influence routing or policy.
- Recording host-supplied provider results preserves provenance without pretending that just-chill executed the provider call.
- Requiring prior add receipts prevents destructive memory operations from being logged without provenance.

Consequences:
- `scripts/just_chill_summary_memory_receipts.py` owns local summary provider add/remove receipt plans and receipts.
- `scripts/just_chill_hermes_adapter.py` exposes a summary provider receipt plan for summary-memory contracts.
- A future Hermes-native receipt/audit API can consume or supersede these local receipts once mapped.

Reference:
- `scripts/check_just_chill_summary_memory_receipts.py`
- `harnesses/just-chill-live-bindings.md`

## 2026-06-24 — Local raw artifact staging is a bridge, not Hermes authority

Decision:
- Add a repo-local raw artifact staging store for just-chill raw artifact contracts while Hermes raw artifact APIs remain unmapped.
- Store content, the source contract, write receipts, and deletion receipts under ignored local storage; validate content hashes and require approval for sensitive staging, sensitive reads, or deletion.
- Keep Hermes as the canonical storage authority and keep Hermes raw artifact writes blocked until a real Hermes API or MCP tool is mapped.

Rationale:
- A summary/fact provider does not by itself preserve raw source artifacts or standalone retention/deletion evidence.
- The ontology and memory gates need source provenance receipts now, without pretending that a live Hermes artifact backend exists.
- Using ignored local staging preserves evidence for migration and testing while keeping authority boundaries explicit.

Consequences:
- `scripts/just_chill_raw_artifact_store.py` owns local staging receipts.
- `scripts/just_chill_hermes_adapter.py` exposes the local staging plan for raw contracts while preserving `storageAuthority: Hermes`.
- The next storage slice should map a real Hermes raw artifact write/read/delete surface and migrate or replay staged receipts into it.

Reference:
- `scripts/check_just_chill_raw_artifact_store.py`
- `harnesses/just-chill-live-bindings.md`

## 2026-06-24 — Summary/fact-memory providers are not raw artifact stores

Decision:
- When a compatible summary/fact provider is available, map it only as a host-owned summary/fact-memory write surface.
- Keep raw artifact storage unmapped and write-blocked until Hermes exposes a raw artifact create/read/delete API or MCP tool.
- Keep just-chill local execution disabled: adapter output may include a `fact_store(action=add)` write plan, but the host/Hermes side owns the actual call and evidence receipt.

Rationale:
- Provider-specific installation and availability are host-local state and are not recorded in the public contract.
- A compatible structured fact-memory interface can carry summary-memory candidates.
- It does not by itself provide a raw artifact store, standalone retention/deletion receipts, or canonical ontology promotion.

Consequences:
- `scripts/just_chill_live_bindings.py` models compatible provider-tool availability without publishing current host state.
- `scripts/just_chill_hermes_adapter.py` can emit a host-owned summary-memory write plan with `allowedHere: false`.
- The next live storage slice is raw artifact storage/provenance plus provider-backed retention/deletion evidence.

Reference:
- `harnesses/just-chill-live-bindings.md`
- `scripts/check_just_chill_hermes_boundary.py`

## 2026-06-24 — RDF/SHACL exports are serialization contracts, not persistence evidence

Decision:
- Extend ontology contracts with deterministic RDF/OWL Turtle export manifests and SHACL shape/validation-report exports.
- Keep exports contract-only: no RDF store write, no Hermes write, no canonical ABox promotion, and no claim that a live SHACL engine executed.
- Require export manifests to preserve `storageAuthority: Hermes`, `contractAuthority: just-chill`, source contract hashes, source artifact provenance, live-binding status, and fake-persistence guards.
- Treat SHACL export conformance as a deterministic report over the existing candidate blockers until live SHACL receipts are accepted as canonical evidence for a specific host-owned persistence run.

Rationale:
- just-chill needs a stable semantic interchange shape before wiring a real RDF store or SHACL runtime.
- Deterministic Turtle and SHACL reports make review and regression testing possible without inventing storage authority.
- Blocking fake persistence receipts prevents a serialization artifact from being misread as live memory promotion.

Consequences:
- `scripts/just_chill_ontology_contracts.py` now owns both candidate construction and deterministic RDF/SHACL export contracts.
- `scripts/check_just_chill_ontology_contracts.py` now covers stable Turtle output, source hash/provenance triples, SHACL shape reports, authority guards, and fake-persistence rejection.
- The next memory slice should map real RDF graph persistence and a live SHACL engine before adding vector recall gates.

Reference:
- `harnesses/just-chill-ontology-contracts.md`

## 2026-06-24 — Ontology promotion is contract-only until Hermes/RDF/SHACL are live

Decision:
- Add deterministic ontology contracts for just-chill memory candidates: TBox classes/properties, ABox promotion candidates, source provenance, assertion kind, promotion policy, and SHACL-style validation blockers.
- Keep ontology output contract-only; do not persist RDF/OWL, run a live SHACL engine, or promote canonical ABox assertions in this repo slice.
- Require explicit confirmation for `DecisionAssertion` and `PolicyAssertion`.
- Allow `PreferenceAssertion` auto-promotion only when repeated independent sources, non-sensitive content, non-destructive semantics, access allowed, retention valid, conflict-free state, high confidence, and a ready Hermes boundary are all true.
- Block promotion when provenance is missing, sources are sensitive without approval, sources are deleted/redacted, or Hermes live write boundary is unmapped.

Rationale:
- The design needs machine-checkable ontology gates before any canonical memory can influence future routing or policy.
- A deterministic contract keeps the ontology semantics testable while Hermes raw/summary write APIs, RDF persistence, and SHACL runtime remain unmapped.
- Separating candidate generation from canonical promotion prevents operational/audit facts from becoming durable personal memory accidentally.

Consequences:
- `scripts/just_chill_ontology_contracts.py` is the contract-level ontology builder.
- `scripts/check_just_chill_ontology_contracts.py` is the regression check for assertion-kind and promotion blockers.
- The next memory slice should map real RDF/OWL serialization/persistence or add vector sidecar recall gates; it must not skip Hermes provenance and SHACL policy.

Reference:
- `harnesses/just-chill-ontology-contracts.md`

## 2026-06-24 — Hermes live-boundary reports are read/write authority separators

Decision:
- Add `just-chill-hermes-live-boundary-v1` reports to the Hermes adapter so each raw artifact or summary memory contract records which Hermes surfaces are merely readable/status-visible and which write APIs are actually mapped.
- Treat `hermes memory status`, `hermes mcp list`, and `gjc setup hermes --smoke` as read-only visibility. They do not prove raw artifact storage, summary memory storage, or canonical memory promotion.
- Preserve `storageAuthority: Hermes` and `contractAuthority: just-chill`; just-chill may construct policy/write-gate envelopes but may not claim storage authority.
- Keep `allowedHere: false` even when future fake or live write APIs are present; a separate host/operator bridge must own the actual Hermes write call with approval and evidence.
- Block sensitive-memory writes unless an explicit approval token is present, and keep unmapped raw artifact / summary memory APIs fail-closed.
- Require mapped Hermes write APIs to be create/write/store/persist/upsert-shaped raw-artifact or summary-memory surfaces; status/list/read-shaped identifiers remain blocked.

Rationale:
- The local Hermes CLI exposes memory status and MCP configuration visibility, but no raw artifact or summary memory write API is mapped in this repo.
- Without a separate live-boundary report, status probes could be misread as storage readiness.
- The report lets the next RDF/OWL and SHACL slices depend on explicit provenance and promotion gates instead of implicit storage assumptions.

Consequences:
- `scripts/check_just_chill_hermes_boundary.py` now covers authority preservation, sensitive approval blocking, and ready-but-not-local write gates.
- `scripts/just_chill_hermes_adapter.py` exposes `rawLiveBoundary` and `summaryLiveBoundary` alongside adapter stubs.
- The next memory slice can build RDF/OWL TBox/ABox and SHACL validation over contract records without pretending Hermes live writes are available.

Reference:
- `harnesses/just-chill-live-bindings.md`
- <https://gajae-code.com/docs/hermes-mcp-bridge.html>

## 2026-06-24 — Visible-session orchestration is plan-only until an operator bridge executes it

Decision:
- Extend repo-local visible-session helpers with `--tmux-plan` and `tmux-orchestration-plan-v1` so just-chill can emit deterministic tmux/GJC argv plans for create, attach, readiness check, prompt handoff notice, and debug-only tail.
- Keep helpers non-executing: they do not run tmux, start hidden GJC turns, inject prompts, call `gjc_delegate_*`, write Hermes memory, or mark development work complete.
- Mark the visible path `orchestration-plan-ready` only when helper contracts are probed cleanly and both `tmux` and `gjc` are available; missing tools fall back to `metadata-only-ready` and fail closed.
- Preserve durable evidence as the completion boundary; tmux pane capture remains debug-only.

Rationale:
- The bridge reference separates host-owned visible sessions from hidden delegation. A deterministic argv plan is the safe next step before any operator-executed tmux bridge.
- Planning the tmux/TUI steps makes the handoff auditable without pretending this repo owns a live operator environment.
- Fail-closed readiness prevents just-chill from silently downgrading into hidden execution or scrollback-based completion.

Consequences:
- `scripts/check_just_chill_visible_helpers.py` now covers tmux plan generation, invalid targets, and no-hidden-execution flags.
- `scripts/check_just_chill_live_bindings.py` now distinguishes `orchestration-plan-ready`, `metadata-only-ready`, missing helpers, and unprobed helpers.
- The next live execution slice must be an explicit operator bridge that runs the planned argv steps and still reports durable evidence.

Reference:
- `harnesses/just-chill-live-bindings.md`
- <https://gajae-code.com/docs/hermes-mcp-bridge.html>

## 2026-06-24 — Repo-local visible-session helpers are metadata gates, not hidden workers

Decision:
- Add repo-local host-owned `create-gjc-session`, `prompt-gjc-session`, and `tail-gjc-session` helper scripts so the visible routed-session path has a concrete helper contract in this repo.
- Keep the helper v1 implementation metadata-only: it validates worktree, prompt-file, and evidence inputs and records handoff metadata, but it does not start hidden GJC product work, call `gjc_delegate_*`, or write Hermes memory.
- Require helper `--contract --json` probes before `scripts/just_chill_live_bindings.py` marks the visible path ready.
- Reject tmux scrollback/tail output as completion evidence; durable tool/file/todo/diff/test/report/artifact/PR/turn evidence remains required.

Rationale:
- The Hermes/GJC bridge reference says visible routed-session helpers are host/operator-owned, not shipped by GJC.
- A repo-local metadata helper gives just-chill a testable contract without hard-coding private tmux/channel details or pretending that scrollback proves completion.
- Later operator-specific tmux/TUI orchestration can wrap or extend these helpers while preserving the same safety contract.

Consequences:
- `scripts/check_just_chill_visible_helpers.py` is the focused regression check for helper contracts, metadata flow, evidence validation, and repo-local readiness.
- `scripts/just_chill_live_bindings.py --probe` can now report visible-session readiness when helper contracts are clean.
- Real GJC work still belongs to GJC; just-chill only emits and verifies the handoff/evidence boundary.

Reference:
- `harnesses/just-chill-live-bindings.md`
- <https://gajae-code.com/docs/hermes-mcp-bridge.html>

## 2026-06-24 — Keep live GJC/Hermes bindings fail-closed until host surfaces are installed

Decision:
- Treat local coordinator MCP smoke success and `gjc_delegate_*` discovery as evidence of available GJC machine-control surfaces, not as permission to execute work automatically.
- Keep executable visible routed-session work blocked unless helper contracts are probed cleanly and later operator evidence proves real GJC work; helper presence alone is not completion.
- Keep Hermes memory/artifact writes blocked until a real raw artifact and summary memory API or MCP tool is mapped; just-chill may only emit contract records and adapter write plans.
- Keep RPC host-tools `contract-only` until a live `customTools` registry exposes Hermes/just-chill host tools.

Rationale:
- The Hermes/GJC bridge reference is fail-closed by design: mutation classes and per-call `allow_mutation: true` are required for executable coordinator/delegation calls.
- Hermes currently reports built-in memory only and no configured MCP servers, so claiming live storage authority from just-chill would be false.
- Visible routed sessions remain the recommended starter path, and the repo-local helper scripts now provide the portable metadata/evidence contract while leaving private tmux/channel orchestration to the operator environment.

Consequences:
- `scripts/just_chill_live_bindings.py` reports the live surface map and visible-session handoff status.
- `scripts/just_chill_hermes_adapter.py` keeps `writePlan.enabled: false` while Hermes write APIs are unmapped.
- The next implementation slice should either extend helper v1 into real operator tmux/TUI orchestration or map real Hermes storage APIs before advancing to RDF/OWL promotion gates.

Reference:
- `harnesses/just-chill-live-bindings.md`
- <https://gajae-code.com/docs/hermes-mcp-bridge.html>

## 2026-06-23 — Rename JARVIS vNext direction to just-chill and narrow it to an operating layer

Decision:
- Rename the current vNext product direction to `just-chill` while preserving the existing `$HOME/jarvis` repository and Git history.
- Treat just-chill as a personal operating console, router, result summarizer, long-term memory gate, and knowledge-management layer.
- Route development-related requests to GJC by default, using only observable subroute hints for GJC direct, `deep-interview`, `ralplan`, `ultragoal`, or `team`.
- Do not make just-chill a second development requirements interviewer, planner, coding agent, or implementation workflow runtime.
- Use Hermes as the authoritative state/artifact/memory access infrastructure, while just-chill owns memory policy and promotion judgment.
- Model durable semantic memory with raw artifact provenance, summary memory, RDF/OWL TBox/ABox, SHACL validation, separate operational/audit graphs, and vector recall sidecars.
- Use the Gajae Code Hermes MCP Bridge documentation as the canonical reference for connecting Hermes/just-chill to GJC: start with visible routed sessions for observability, then adopt coordinator MCP, `gjc_delegate_*`, or RPC host tools when durable machine control or reverse host-tool access is required.

Rationale:
- GJC already covers the development clarification, planning, execution, verification, and durable-goal roles that earlier JARVIS vNext drafts risked duplicating.
- The defensible layer is before and after specialist tools: classify intent/risk, choose the right worker/tool, summarize outcomes, and decide what becomes long-term memory.
- Preserving the existing Jarvis repo keeps design lineage and operational history auditable.
- The bridge documentation already defines the safe GJC/Hermes control boundary, so just-chill should adapt that contract rather than inventing a separate terminal or MCP protocol.

Consequences:
- The current canonical vNext design is `wiki/concepts/just-chill-vnext-operating-layer.md`.
- Older JARVIS vNext pages remain predecessor context and should link forward rather than be erased.
- Initial implementation work is Phase 0/1 documentation and contract mapping only; Phase 2+ implementation waits for mapped GJC/Hermes surfaces, privacy policy, graph boundary, and migration inventory.
- GJC/Hermes contract mapping should cite the bridge reference and treat durable turns, reports, artifacts, diffs/tests/PRs, or equivalent work evidence as completion signals; tmux scrollback alone is not completion evidence.

Reference:
- `wiki/concepts/just-chill-vnext-operating-layer.md`
- `wiki/concepts/jarvis-vnext-meta-control-plane.md`
- `wiki/concepts/jarvis-vnext-intent-to-contract-director.md`
- `wiki/concepts/jarvis-vnext-executor-ontology.md`
- <https://gajae-code.com/docs/hermes-mcp-bridge.html>

## 2026-06-12 — Adversarial design review applied: redefine P1/P2, correct P4, grade enforcement

Decision:
- Apply the 7 MAJOR revision proposals from the 2026-06-12 adversarial design review (verdict: revise / conditionally keep direction; BLOCK 0 · MAJOR 7 · MINOR 6 · NOTE 4) to the vNext concept docs.
- Redefine the differentiation claim (P2): not the intent-to-contract compiler alone — intent→spec compilation is already commoditized (AWS Kiro, GitHub Spec Kit, backend plan modes) — but the closed loop: compile → delegate → contract-derived, interest-separated final judgment.
- Redefine verification residency (P1): what stays with JARVIS is not "verification" in general but the final judgment that is contract-derived and interest-separated. Backend self cross-review (including Claude Code dynamic workflows adversarial review, official GA) is evidence, not judgment.
- Correct the 2026-06-10 statement that competing control planes provide no contract+verification layer: competitors already ship verification gates that delegate to external CI/review (Optio: CI polling + review agent + auto-merge, multi-vendor A/B). The actually-empty layer is contract-derived judgment, and the contract-compilation layer itself.
- Introduce per-field guardrail enforcement levels (native | wrapper | post_hoc); any field below native auto-escalates to completion_gates post-hoc checks. Confirmed: completion gates are not natively enforceable on any backend, and Codex cannot deny per-file writes inside the workspace.
- Split final judgment into two stages: deterministic mechanical gate (necessary condition) → model-based Director judgment.
- Grade contract fields must/should/optional with backend-strength thickness profiles, and add a contract quality feedback loop (run ledger links contracts to outcomes with defect classification) to the MVP priorities.

Rationale:
- Adversarial review against 24 external sources (all verified 2026-06-12; 3 top claims checked directly against original sources) found the target layer genuinely empty across 6 competitor control planes, but the existing wording indefensible as written against current backend-native capabilities.

Reference:
- wiki/projects/jarvis/reviews/vnext-adversarial-review-2026-06-12.md
- wiki/concepts/jarvis-vnext-intent-to-contract-director.md

## 2026-06-11 — JARVIS vNext should optimize intent-to-contract over orchestration

Decision:
- Treat the default vNext workflow as `Understand -> Contract -> Delegate -> Verify -> Report`.
- Narrow JARVIS's core role to requirement normalization, backend-native task-contract generation, policy/approval gating, evidence-backed verification, and result arbitration.
- Assume modern backends such as Claude Code/Fable, Codex, Cursor Cloud Agents, Devin, OpenHands, OMX, and Gajae-Code may act as both Runtime and Producer in a single selected backend.
- Do not make separate orchestration layers the default path. Use them only when multi-backend arbitration, long-running programs, queues, cron/kanban, cross-repo coordination, high risk, or audit needs justify the overhead.
- Expose backend-native systems through adapters that standardize capability, contract preparation, launch, status, result collection, and cancellation while preserving backend-specific strengths.

Rationale:
- Backend-native systems increasingly include planning, subagents, background/cloud execution, worktree isolation, test/fix loops, PR workflows, hooks, skills, and MCP-style extension surfaces.
- As backend execution improves, the bottleneck shifts from running agents to giving them high-quality requirements and judging whether the result is trustworthy.
- JARVIS's defensible value is converting vague user intent and accumulated project knowledge into executable contracts, then verifying explicit QA plus implicit user/project constraints.

Consequences:
- MVP schemas should prioritize `task-contract.yaml`, backend capability metadata, backend result records, workflow-level routing, and verification reports.
- JARVIS thin runtime should remain a ledger/adapter/evidence layer rather than a full custom orchestrator.
- Multi-agent or multi-backend flows should be escalation levels, not the default.

Reference:
- `wiki/concepts/jarvis-vnext-intent-to-contract-director.md`

## 2026-06-11 — vNext must separate Markdown instructions from executable guardrails

Decision:
- Treat Markdown instruction files (`AGENTS.md`, `CLAUDE.md`, skills, wiki, runbooks) as guidance, not as deterministic enforcement.
- Add an explicit Contract Enforcement Layer to the vNext design: task contracts should include allowed paths, denied paths, denied commands, approval gates, required evidence, budget limits, and completion gates.
- Model backend-native deep workflow modes, including Claude Code `ultracode` / Dynamic workflows, as control-flow orchestration capabilities rather than as policy enforcement by themselves.
- Require adapters to map JARVIS guardrails to the strongest available backend mechanisms: permissions, hooks, sandboxing, managed settings, command/path policy, wrapper checks, isolated worktrees, post-run diff checks, and JARVIS completion refusal when evidence is missing.

Rationale:
- Markdown can be skipped, summarized away, or inconsistently followed by LLM backends.
- Dynamic workflows improve execution structure by scripting phases, loops, subagent fanout, result aggregation, and verifier passes, but they do not guarantee that prose instructions are semantically obeyed.
- Deterministic safety requires executable guardrails and evidence gates: “do not edit secrets” must become path/tool denial, and “run verification before completion” must become a completion gate backed by logs or an explicit failed/blocked status.

Consequences:
- The vNext MVP should include an executable guardrail schema before investing in a full custom workflow engine.
- Backend capability records should distinguish `native_features.deep_workflow` from `enforcement_features.permissions/hooks/sandbox/managed_settings`.
- JARVIS remains the final judge: a backend workflow can complete, but JARVIS should report success only after scope, secret, diff, and verification evidence pass.

Reference:
- `wiki/concepts/jarvis-vnext-intent-to-contract-director.md`
- `wiki/concepts/jarvis-vnext-meta-control-plane.md`
- Claude Code Dynamic workflows: `https://docs.anthropic.com/en/docs/claude-code/workflows`
- Claude Code permissions/hooks/sandboxing docs: `https://docs.anthropic.com/en/docs/claude-code/settings`

## 2026-06-11 — JARVIS sits above harness and loop engineering

Decision:
- Define harness engineering as the design of task wrappers that help AI work reliably: instructions, context, tools, environment, permissions, sandbox, output schema, validation, logging, and evidence capture.
- Define loop engineering as closed-cycle AI automation: observe, judge, act, verify, repair, and repeat until success, failure, or escalation.
- Treat loops as execution patterns available to JARVIS, not as the top-level JARVIS identity.
- Position JARVIS as the Director/Governor above loops: it chooses whether a loop is needed, selects or designs the loop, binds harnesses into loop steps, applies guardrails, controls budget/risk, verifies evidence, and makes the final stop/pass/escalate judgment.

Rationale:
- Harnesses make individual AI work units more reliable; loops create autonomous progress across repeated work units.
- A loop can contain multiple harnesses, such as diagnosis, implementation, test, review, and report harnesses inside a test-fix loop.
- JARVIS's differentiator is not merely running loops, but deciding which loop and harness combination is appropriate for a user's intent, project context, backend capability, and risk profile.

Consequences:
- vNext schemas should include reusable harness manifests and loop contracts in addition to task contracts and guardrails.
- Run ledgers should record the selected loop type, harnesses used, iteration count, stop condition, evidence, and JARVIS final judgment.
- The product language should describe JARVIS as an Agent Operations Director/Governor that uses harness and loop engineering, not as a generic loop runner.

Reference:
- `wiki/concepts/jarvis-vnext-intent-to-contract-director.md`
- `wiki/concepts/jarvis-vnext-meta-control-plane.md`

## 2026-06-11 — vNext plans should be agent implementation briefs, not line-by-line manuals

Decision:
- Keep the vNext planning documents at the level of architecture constraints, implementation contracts, invariants, non-goals, and first artifacts.
- Do not expand them into a detailed human step-by-step build manual unless a future task specifically needs that.
- Make the documents usable in a fresh environment by an implementation agent: it should be able to infer repo/module layout and implementation details while preserving JARVIS Director/Governor semantics, task contracts, harnesses, loops, guardrails, evidence gates, and backend adapters.

Rationale:
- The intended implementation path will use capable coding agents, so over-specifying every build step may reduce backend-native planning, subagent, workflow, and repair-loop strengths.
- What must be preserved is the operating contract: JARVIS turns vague intent into bounded contracts, applies executable guardrails, delegates to backend-native systems, collects evidence, and makes the final judgment.
- A greenfield agent needs clear invariants and acceptance criteria more than a hand-coded installation recipe.

Consequences:
- Add an Agent implementation brief to the intent-to-contract concept page.
- Treat future implementation prompts as task contracts derived from the concept pages.
- Keep current-environment details such as Hermes, OMX, Gajae, Codex, and Claude Code as adapter examples rather than mandatory dependencies for a portable core.

Reference:
- `wiki/concepts/jarvis-vnext-intent-to-contract-director.md`
- `wiki/concepts/jarvis-vnext-meta-control-plane.md`

## 2026-06-10 — JARVIS vNext should be a Director over runtimes and producers

Decision:
- Narrow JARVIS vNext away from being another generic coding agent runner or multi-agent orchestrator.
- Position JARVIS vNext as a project-operations Director/meta-control-plane above existing coding agents and orchestration/runtime systems.
- Replace the ambiguous shorthand `orchestrator/executor` with role-based terms: `Director`, `Runtime`, `Producer`, and `Verifier`.
- Treat tools such as Codex, OMX/Gajae-Code, Claude Code, AgentWrapper, CodeMachine, Golutra, Agor, Optio, cron, and kanban as possible role-bearing backends rather than fixed categories. A tool can be a Runtime in one Run and a Producer in another.
- JARVIS should own task interpretation, backend selection rationale, approval/risk gates, task contracts, evidence-backed completion judgment, long-term project memory, and next-action decisions.
- Runtimes should own low-level execution mechanics such as process spawning, worktree isolation, parallel agents, CI/PR automation, workflow execution, dashboard/log streaming, and session management.

Rationale:
- Modern coding agents with goal modes can already complete many single-repo tasks when given a strong design document.
- GitHub already has many overlapping projects in the agent-orchestrator/control-plane space, including AgentWrapper, Golutra, CodeMachine, Agor, Optio, Overstory, Codex Mate, aiagentflow, and c9r orchestrator.
- Therefore “multi-agent orchestration” by itself is not a durable differentiator.
- JARVIS's stronger differentiator is the long-term conversational Director layer: route, gate, contract, verify, remember, and escalate across projects and tools.

Consequences:
- MVP priority should shift toward run ledger, route-decision records, approval/verification gate models, task-contract generation, and project operations memory queries.
- Custom multi-agent spawning, workflow engines, dashboards, PR/CI auto-fix, and own coding-agent development should be lower priority unless needed as adapters.
- Initial external-orchestrator integration can be manual/prompt or CLI-based before deeper API/daemon integration.

Reference:
- `wiki/concepts/jarvis-vnext-meta-control-plane.md`

## 2026-06-08 — Ouroboros as JARVIS vNext reference, not replacement

Decision:
- Use `Q00/ouroboros` as a useful reference and partial-absorption source for JARVIS vNext design.
- Do not replace JARVIS with Ouroboros, and do not install/register Ouroboros into the default Hermes profile without explicit approval and sandbox evidence.
- Absorb patterns selectively into JARVIS-native design: Seed-like task contracts, run-ledger event logs, ambiguity/interview gates, evaluation ladders, executor adapter contracts, and harness manifests.
- Existing JARVIS harnesses remain assets to register, wrap, refactor, compare, or archive; they are not discarded because of ontology/runtime redesign.

Rationale:
- Ouroboros overlaps strongly with JARVIS vNext goals, but it is itself an Agent OS and could blur the user's desired JARVIS Director boundary if adopted wholesale.
- JARVIS needs a broader project-operations control plane across wiki, registry, Telegram/CLI continuity, approvals, multiple executors, and project-specific harnesses.
- A sandbox/shadow-mode path preserves safety while still extracting valuable architecture patterns.

Reference:
- `wiki/concepts/ouroboros-adoption-review.md`
- `wiki/concepts/jarvis-vnext-executor-ontology.md`
- `wiki/concepts/jarvis-office-runtime-direction.md`

## 2026-06-08 — Open-source target should be Hermes-agnostic core plus adapters

Decision:
- The JARVIS system has open-source potential as an Agent Operations Control Plane, but the private `$HOME/jarvis` instance should not be published as-is.
- Public extraction should separate a runtime-agnostic core from host/runtime adapters.
- The private JARVIS instance may remain Hermes-first because Hermes is operationally useful for memory, skills, session search, tools, cron, gateway, and wiki orchestration.
- The public core must not require Hermes; Hermes should be a first-class adapter and recommended host, not a hard dependency.
- Avoid using `JARVIS` as the public project name until naming/trademark risk is resolved.

Rationale:
- Open-source users may use Claude Code, Codex, OpenCode, shell runners, local LLMs, or other hosts; a Hermes-only core would unnecessarily narrow adoption.
- The valuable generalizable piece is the operating contract: task contracts, routing ontology, run ledgers, approval queues, executor/harness adapters, verification gates, and status/resume.
- Keeping the private JARVIS repo separate prevents leaking personal paths, project registry entries, internal wiki/status notes, session-derived context, and approval/security assumptions.

Reference:
- `wiki/concepts/jarvis-open-source-strategy.md`
- `wiki/concepts/jarvis-office-runtime-direction.md`
- `wiki/concepts/jarvis-vnext-executor-ontology.md`

## 2026-05-28 — JARVIS judgment-first office runtime direction

Decision:
- Future JARVIS hardening should keep JARVIS as the intelligent Director for user-intent interpretation, work design, executor selection, quality judgment, and escalation decisions.
- CLI/runtime helpers should automate run ledgers, approval queues, status views, prompt/log storage, verification capture, and Producer/Reviewer loop mechanics.
- Routing rules should be treated as guardrails and decision support, not as a rigid replacement for JARVIS judgment.

Rationale:
- A rules-only dispatcher could lower work-design quality by missing user intent, business/taste tradeoffs, context, scope nuance, and quality expectations.
- JARVIS should reduce repetitive administrative work without reducing Director-level reasoning.
- Durable ledgers and approval queues are prerequisites for safer Telegram/CLI continuity, long-running work, and future multi-agent office-style orchestration.

Reference:
- `wiki/concepts/jarvis-office-runtime-direction.md`

## 2026-05-12 — Claude Code and OMC as secondary external executors

Decision:
- Keep Hermes' main model/provider on the current Codex/OpenAI-Codex path.
- Keep Codex CLI + OMX as the primary implementation executor line.
- Add Claude Code + OMC as a secondary external CLI executor line.
- Use Claude Code's Claude Max OAuth login for the external `claude` CLI rather than treating it as a Hermes main-provider switch.

Rationale:
- Codex/OMX is already validated for the user's default coding workflow.
- Claude Code/OMC provides a useful second executor for review, planning, refactoring, Claude-specific reasoning strengths, and quota/load balancing.
- Separating Hermes provider auth from external CLI executor auth avoids conflating Claude Code subscription OAuth with direct Anthropic API-key usage.

Verification:
- `claude auth status --text` showed Claude Max account login.
- `claude -p 'Reply with exactly CLAUDE-CODE-OK' --max-turns 1 --output-format json` returned `CLAUDE-CODE-OK`.
- `omc --version` returned `4.13.7` after installing `oh-my-claude-sisyphus`.
- `omc setup` completed agent/skill/hook sync under `~/.claude`.

## 2026-05-06 — Hermes-first hybrid architecture

Decision:
- Use Hermes Agent as the JARVIS control plane.
- Use Codex CLI + OMX as implementation executors.
- Keep Hermes available for direct small coding, docs, validation, wiki updates, and orchestration.

Rationale:
- User wants to use Codex subscription/OAuth path for coding workflows.
- Hermes provides memory, skills, session search, cron, tool orchestration, and gateway features.
- OMX provides stronger coding execution loops for medium/large implementation.

## 2026-05-06 — Workspace layout

Decision:
- JARVIS root: `$HOME/jarvis`
- Active WSL project root: `$HOME/projects`
- Application project source stays outside the JARVIS control-plane repo.
- Each project is managed as an independent git repository and can map to its own GitHub repository.
- If `$HOME/jarvis/projects/` is created locally as a root-level folder or symlink, it is ignored by `.gitignore`.

Rationale:
- Keeps the control plane separate from application repositories.
- Allows Hermes to manage many projects from one place.
- Allows Codex/OMX to run inside specific target repos with `-C <repo>`.
- Keeps project history, remotes, CI, and executor work isolated per project.

## 2026-05-06 — Permission policy

Decision:
- `approvals.mode: smart`
- `approvals.cron_mode: deny`
- `security.tirith_enabled: true`
- `security.redact_secrets: true`

Rationale:
- Allows low-risk automation while keeping high-risk actions gated.
