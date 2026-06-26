# just-chill Live Binding Harness

Use this harness for the live-binding and host-helper executable slices of the just-chill vNext design: mapping real local GJC/Hermes surfaces and emitting fail-closed visible-session handoff instructions without turning just-chill into a worker.

## Purpose

The bridge-contract slice produced deterministic JSON. This slice checks what is actually available on the host and wraps those facts into safe operator plans:

```text
user request
  -> Hermes main agent / Hermes UI
  -> just_chill_harness MCP/tool call
  -> scripts/just_chill_router.py + bridge/memory/recall/consent contracts
  -> Hermes-owned memory/external tools or host-owned visible GJC bridge, without just-chill executing work

developer/debug fixture
  -> scripts/just-chill or scripts/just_chill_harness.py
  -> same deterministic contracts, still without GJC execution or Hermes writes
```

## Current local surface map

Observed in this repo slice:

| Surface | Status | Evidence / command |
|---|---|---|
| `gjc` CLI | available | `gjc --version` returned `gjc/0.7.0`. |
| `tmux` | available | `tmux -V` returned `tmux 3.4`. |
| Host visible-session helpers | orchestration-plan-ready when probed | `scripts/create-gjc-session`, `scripts/prompt-gjc-session`, and `scripts/tail-gjc-session` expose `--contract --json` plus `--tmux-plan`, record metadata under `JUST_CHILL_VISIBLE_SESSION_DIR` or `/tmp/just-chill-visible-sessions`, emit dry-run tmux/GJC argv plans, and keep `scrollbackIsCompletion: false`. |
| Coordinator MCP | smoke-ok, read-only by default | `gjc mcp-serve coordinator --check --json` returned server `gjc-coordinator-mcp` and the required coordinator/delegate tools. Execution remains blocked until mutation classes and per-call `allow_mutation: true` are enabled. |
| Hermes setup package | render/smoke OK | `gjc setup hermes --root /home/hskim/jarvis --smoke --json` returned `ok: true` and wrote no files. |
| `gjc_delegate_*` tools | present via coordinator MCP | `gjc_delegate_plan`, `gjc_delegate_execute`, and `gjc_delegate_team` are present in the coordinator smoke tool list. They are not treated as executable until coordinator mutation consent is configured. |
| RPC host tools | contract-only | No live RPC `customTools` registry is mapped in this repo slice. |
| Hermes memory provider | `holographic` provider-tool mapped for summary/fact memory | `hermes memory status` reports provider `holographic`. `scripts/just_chill_live_bindings.py` maps Holographic `fact_store(action=add/search/probe/list/remove)` as a host-owned summary-memory provider tool. `scripts/just_chill_summary_memory_receipts.py` records local add/remove receipts for host-executed provider operations. |
| Local raw artifact staging | available as Hermes-compatible staging, not canonical Hermes storage | `scripts/just_chill_raw_artifact_store.py` writes ignored repo-local receipts under `tmp/just-chill-artifacts` by default, validates content hashes, requires approval for sensitive staging/read/deletion, and records deletion receipts. |
| Hermes raw/RDF/vector MCP API | mapped through `just_chill_memory_api`; host-owned | `scripts/just_chill_hermes_memory_mcp.py` exposes `hermes.raw_artifact.create/read/delete`, `hermes.rdf_graph.create/read/delete`, `hermes.vector_sidecar.create/search/read/delete`, and `hermes.memory_api.status`; `hermes mcp add just_chill_memory_api ...` connected and enabled all tools. just-chill discovers the tools but does not call them directly. |
| Hermes MCP config | configured | `hermes mcp list` shows `just_chill_memory_api` and `just_chill_harness` enabled. Memory API store root: `/home/hskim/.local/share/jarvis/just-chill-hermes-memory-api`. |
| Hermes-facing just-chill harness MCP | configured after explicit approval | `scripts/just_chill_harness_mcp.py` exposes `just_chill.route`, `just_chill.remember.plan`, `just_chill.recall.gate`, `just_chill.gjc_handoff.plan`, `just_chill.consent.evaluate`, `just_chill.handle`, and `just_chill.status` as a stdio MCP server. `hermes mcp add just_chill_harness --command python3 --args /home/hskim/jarvis/scripts/just_chill_harness_mcp.py` connected and enabled all 7 tools after operator approval; `hermes mcp test just_chill_harness` connected and discovered 7 tools. |

## Implemented files

| File | Role |
|---|---|
| `scripts/just_chill_live_bindings.py` | Discovers command availability and read-only GJC/Hermes smoke results; builds visible-session operator handoff instructions with tmux orchestration plan metadata; validates selected bridge paths fail closed when required live tooling is missing. |
| `scripts/just_chill_hermes_adapter.py` | Wraps raw artifact / summary memory contracts in a Hermes boundary adapter that keeps just-chill writes disabled, reports mapped host-owned Hermes APIs when available, and requires external host/Hermes result evidence before canonical promotion. |
| `scripts/just_chill_raw_artifact_store.py` | Host-owned local staging store for raw artifact contracts before canonical Hermes promotion; writes content, contract, write receipt, and deletion receipt under an ignored local store, blocks sensitive reads without approval, and does not claim Hermes storage authority. |
| `scripts/just_chill_summary_memory_receipts.py` | Host-owned receipt bridge for provider-backed summary memories; emits `fact_store(add/remove)` plans, records add/remove receipts from supplied provider result evidence, requires approval for sensitive writes/removals, and keeps Hermes as canonical memory authority. |
| `scripts/just_chill_hermes_raw_artifact_boundary.py` | Read-only raw artifact API discovery and host-owned promotion planning; detects Hermes raw artifact create/read/delete APIs or MCP tools when present, otherwise keeps local staging -> Hermes promotion fail-closed. |
| `scripts/just_chill_hermes_memory_mcp.py` | Host-owned stdio MCP server registered in Hermes as `just_chill_memory_api`; exposes raw artifact, RDF graph, and vector sidecar lifecycle tools with hash, approval, deletion, and read-back/retrieval evidence guards. |
| `scripts/just_chill_hermes_mcp_receipts.py` | Host-owned stdio JSON-RPC lifecycle runner that exercises `just_chill_memory_api` raw artifact, RDF graph, and vector sidecar create/read/search/delete paths, captures read-back hashes, negative approval/hash checks, and delete receipts without granting just-chill execution authority. |
| `scripts/just_chill_rdf_persistence_receipts.py` | Host-owned RDF/SHACL persistence receipt bridge that combines deterministic ontology exports, live `pyshacl` evidence, and Hermes RDF graph MCP create/read/delete receipts while keeping just-chill out of SHACL/Hermes execution. |
| `scripts/just_chill_vector_recall.py` | Vector sidecar and recall-gate builder; maps live vector/search boundaries, creates sidecar candidates from Hermes-canonical source refs, and decides recall admission without embedding/searching locally. |
| `scripts/just_chill_memory_migration_fixture.py` | Host-owned non-sensitive fixture replay that selects repository wiki design facts, creates Hermes raw/RDF/vector MCP lifecycle receipts in a temporary store, emits summary memory receipts, then cleans up without private memory promotion. |
| `scripts/just_chill_cli.py` | Safe user-facing CLI contract entrypoint for route, remember, recall, and handoff-gjc flows; composes router/bridge/memory/recall contracts and emits JSON without executing GJC or writing Hermes. |
| `scripts/just-chill` | Thin executable wrapper for the safe CLI entrypoint. |
| `scripts/just_chill_gjc_consent_policy.py` | Deterministic coordinator/delegation mutation-consent policy; keeps visible sessions first and only marks host mutation ready when coordinator tools, mutation classes, per-call consent, durable evidence policy, and delegate availability are all satisfied. |
| `scripts/just_chill_dogfood_harness.py` | Deterministic end-to-end dogfood harness for route -> GJC handoff -> memory/raw/RDF/SHACL/vector contracts -> recall gate -> consent policy without executing GJC or writing Hermes. |
| `scripts/just_chill_harness.py` | Hermes-facing adapter that exposes route, remember plan, recall gate, GJC handoff plan, consent evaluation, status, and full handle operations as stable JSON contracts for Hermes callers. |
| `scripts/just_chill_harness_mcp.py` | Stdio MCP wrapper around `just_chill_harness.py`; exposes `just_chill.*` tools for Hermes without executing GJC, writing Hermes, running SHACL, calling coordinator/delegate tools, or searching vector stores. |
| `scripts/just_chill_hermes_harness.py` | Hermes-main dogfood harness proving Hermes receives the user request, calls just-chill as a policy harness, and routes to host-owned next steps without making the CLI the product UX. |
| `scripts/just_chill_approval_registry.py` | Host-owned approval token registry; issues, verifies, and revokes scope/subject/expiry-bound tokens while storing only token hashes and preserving just-chill no-execution/no-Hermes-write authority boundaries. |
| `scripts/just_chill_gjc_execution_bridge.py` | Host-owned visible GJC execution bridge MVP; consumes `gjcHandoffPlan`, writes a task file plus visible-session metadata, emits operator argv plans, and verifies durable completion evidence without starting GJC, injecting prompts, or accepting scrollback completion. |
| `scripts/check_just_chill_live_bindings.py` | Deterministic focused checks for live-surface mapping, visible-session helper gating, coordinator/delegation/RPC readiness, and Hermes write blocking. |
| `scripts/check_just_chill_hermes_boundary.py` | Deterministic checks for Hermes live-boundary reports, storage-authority preservation, sensitive approval blocking, and ready-but-not-local write gates when fake write APIs are supplied. |
| `scripts/check_just_chill_raw_artifact_store.py` | Deterministic checks for local staging plans, write/read receipts, hash mismatch blocking, sensitive staging/read approval, deletion receipts, invalid id rejection, and Hermes adapter exposure. |
| `scripts/check_just_chill_hermes_raw_artifact_boundary.py` | Deterministic checks for unmapped/partial/mapped raw API discovery, local-staging promotion gates, sensitive promotion approval, local receipt mismatch blocking, and Hermes adapter exposure. |
| `scripts/check_just_chill_hermes_memory_mcp.py` | Deterministic checks for the MCP tool manifest, raw artifact lifecycle, RDF graph lifecycle, approval/hash blockers, and MCP JSON-RPC tool listing/call behavior. |
| `scripts/check_just_chill_hermes_mcp_receipts.py` | Deterministic checks for host-owned MCP lifecycle receipts, read-back hash matching, negative approval/hash blockers, delete receipts, and missing-tool fail-closed validation. |
| `scripts/check_just_chill_rdf_persistence_receipts.py` | Deterministic checks for live SHACL evidence, ready host-owned RDF persistence plans, Hermes RDF read-back hashes, delete receipts, and just-chill boundary guards. |
| `scripts/check_just_chill_vector_recall.py` | Deterministic checks for vector sidecar readiness, provider-search-not-vector-authority mapping, recall allow/reject gates, deletion propagation, stale hash blocking, scope checks, and sensitive-memory blocking. |
| `scripts/check_just_chill_memory_migration_fixture.py` | Deterministic checks for non-sensitive source selection, raw/RDF/vector read-back hashes, summary retention/access/deletion fields, cleanup receipts, and no private memory promotion. |
| `scripts/check_just_chill_cli.py` | Deterministic checks for CLI JSON contracts, stdin/wrapper behavior, route/handoff/memory/recall flows, sensitive-memory blocking, fake approval-token rejection, deterministic no-probe recall defaults, deleted/redacted recall blocking, malformed JSON blocking, and authority-boundary invariants. |
| `scripts/check_just_chill_gjc_consent_policy.py` | Deterministic checks for visible-first policy, coordinator/delegation mutation classes, per-call `allow_mutation`, delegate availability, durable evidence, and scrollback rejection. |
| `scripts/check_just_chill_dogfood_harness.py` | Checks the dogfood harness happy path plus stale, deleted, redacted, and sensitive-memory failure paths. |
| `scripts/check_just_chill_harness.py` | Deterministic checks for the Hermes-facing harness adapter: route, remember, recall, GJC handoff, consent, handle, status, malformed JSON, deleted recall, and authority-boundary invariants. |
| `scripts/check_just_chill_harness_mcp.py` | Deterministic checks for the `just_chill.*` MCP manifest, CLI smoke, JSON-RPC initialize/list/call behavior, error id preservation, stdio serving, and authority-boundary invariants. |
| `scripts/check_just_chill_hermes_harness.py` | Hermes-main dogfood checks for development, memory, recall, sensitive-memory, malformed MCP, and no-hidden-execution paths. |
| `scripts/check_just_chill_approval_registry.py` | Deterministic checks for issue/verify/revoke/status, plaintext-token non-persistence, scope/subject mismatch blocking, registry-backed remember/recall token acceptance, and CLI issue/verify behavior. |
| `scripts/check_just_chill_gjc_execution_bridge.py` | Deterministic checks for visible execution preparation, task-file/session metadata, durable evidence acceptance, scrollback rejection, non-visible bridge blocking, CLI prepare/verify, and no-execution authority invariants. |
| `scripts/check_just_chill_summary_memory_receipts.py` | Deterministic checks for summary provider add/remove plans, sensitive approval, durable provider result evidence, deletion receipt gating, invalid id rejection, and Hermes adapter exposure. |
| `scripts/just_chill_visible_session_helpers.py` | Shared helper contract implementation for repo-local host helper scripts; validates session/task/evidence inputs, records metadata, and emits dry-run tmux/GJC orchestration argv plans without hidden GJC execution. |
| `scripts/create-gjc-session` | Host helper that validates a session/worktree and can record a `tmux-orchestration-plan-v1` create/attach plan; it does not start product work. |
| `scripts/prompt-gjc-session` | Host helper that validates an `@/absolute/task.md` prompt handoff and can record an operator-visible prompt plan without injecting hidden work. |
| `scripts/tail-gjc-session` | Host helper that reads session metadata, validates durable evidence, and can emit a debug-only tmux capture plan; tail/scrollback remains debug-only. |
| `scripts/check_just_chill_visible_helpers.py` | Focused helper checks for contracts, metadata flow, scrollback rejection, durable evidence acceptance, and repo-local readiness. |

## Live-binding rules

- just-chill may discover and report local surface availability.
- just-chill may emit host operator instructions.
- just-chill must not call `gjc_delegate_*`, write Hermes memory, or treat helper output as development completion.
- The repo-local visible helpers are host-owned metadata and orchestration-planning helpers: they validate handoff inputs and evidence contracts, emit argv plans for the operator, but they do not execute hidden GJC turns or claim product work is complete.
- Visible routed-session acceptance requires real evidence: a GJC tool call/file read, todo/plan update, diff, test, report, PR, artifact, or terminal `turn_id`; accepted signals need a concrete `source`/`path`/`artifact`/`turn_id`/description or argv `command`, and tmux scrollback alone is never completion.
- `visibleRoutedSession.status` is `orchestration-plan-ready` only when helper contracts are probed cleanly and both `tmux` and `gjc` are available; missing tools drop to `metadata-only-ready` and fail closed for live orchestration.
- Coordinator/delegation paths fail closed unless the coordinator smoke check is clean and required mutation classes plus per-call `allow_mutation: true` are present.
- Readiness checks may model explicit per-call consent with `--allow-mutation`; mutation classes alone must still fail closed.
- Coordinator/delegation mutation consent is evaluated by `scripts/just_chill_gjc_consent_policy.py`: visible routed sessions remain the default; coordinator/delegate paths are host-ready only with clean coordinator smoke, required mutation classes (`sessions`, `questions`, `reports`), explicit per-call `allow_mutation`, delegate tool availability when applicable, durable evidence policy, and no scrollback completion.
- RPC host-tools remain `contract-only` until a live host `customTools` registry is mapped.
- Hermes summary/fact memory can be planned through an active mapped provider tool such as Holographic `fact_store(action=add/remove)`, but just-chill still emits a host-owned `writePlan` / receipt plan and does not call the tool directly.
- Hermes raw artifact writes are now mapped through the host-owned `just_chill_memory_api` MCP server, but just-chill still does not call them directly; status/MCP/setup probes and provider presence are read-only evidence and never prove raw artifact storage authority by themselves.
- Raw artifact API discovery probes Hermes help, memory help, MCP list, tools list, and GJC Hermes setup smoke output; only MCP/tools listings are accepted as authoritative API candidates, and create/read/delete must all be mapped before a Hermes raw artifact promotion plan can become ready.
- Local raw artifact staging is allowed only as an ignored host-owned bridge under `tmp/just-chill-artifacts` or an explicit store root; it preserves Hermes as canonical authority and must not be treated as live Hermes storage.
- Staged raw artifacts require hash-matching content, durable write receipts, sensitive approval tokens for staging/read when applicable, and deletion receipts for destructive cleanup.
- Local staged raw artifacts can be promoted to Hermes only by a host-owned runner/session using the mapped MCP tools; just-chill emits `wouldCall` plans and requires Hermes create result plus read-back hash evidence, but does not call Hermes raw artifact APIs itself.
- Provider-backed summary memories require local add/remove receipts under `tmp/just-chill-summary-memory-receipts` or an explicit receipt root; removal requires a prior add receipt, explicit approval, a reason, and host-supplied provider result evidence.
- Sensitive summary approval authorizes retaining the redacted summary candidate and receipt metadata; it does not rehydrate or persist plaintext sensitive content.
- A mapped Hermes write API identifier must be a recognized Hermes raw-artifact, summary-memory, or provider-tool create/write/store/persist/upsert/add surface; read/list/status-shaped identifiers remain fail-closed.
- Sensitive requests and summaries must be redacted in live-binding reports; hashes/provenance may remain, but plaintext secret-bearing prompts must not be echoed.
- Host-owned lifecycle receipt runners may call MCP tools or `pyshacl` only as operator/Hermes evidence producers; receipt fields must keep `justChillCallsHermes: false` and `justChillRunsShaclEngine: false`.
- Vector sidecars are non-canonical indexes over Hermes-owned raw/RDF/summary records. The host-owned `just_chill_memory_api` maps `hermes.vector_sidecar.create/search/read/delete`; just-chill may validate sidecar contracts and recall gates, but it must not embed text, write/search a vector store itself, or return a memory candidate without canonical Hermes refs, fresh hashes, access checks, and durable host retrieval evidence.
- Hermes is the user-facing layer. just-chill is a harness/tool dependency for Hermes: it emits routing, memory, recall, GJC handoff, and consent contracts, but it does not become the chat UI or task executor.
- The `scripts/just-chill` CLI is retained for local debug, fixture generation, and CI checks only. Product UX should call `scripts/just_chill_harness.py` directly or use the registered `just_chill_harness` Hermes MCP server.
- The `just_chill_harness_mcp.py` server is registered in Hermes as `just_chill_harness` after explicit operator approval. Registration changed external Hermes config, so future remove/re-register actions remain approval-gated host operations.


## Hermes-facing harness and debug CLI contract

Hermes is the intended user-facing entrypoint. `scripts/just_chill_harness.py` and `scripts/just_chill_harness_mcp.py` are the product integration surfaces Hermes should call. `scripts/just-chill` is retained as a local debug/test/fixture CLI, not as the main user UX. Debug examples:

```sh
scripts/just-chill route --include-bridge --cwd /home/hskim/jarvis "fix src/hooks/bridge.ts"
scripts/just-chill handoff-gjc --cwd /home/hskim/jarvis "fix src/hooks/bridge.ts"
scripts/just-chill remember --summary "Development routes to GJC." "remember that development routes to GJC"
scripts/just-chill recall "How should development be routed?"
```

The CLI always emits JSON with `executionAllowedHere: false`, `justChillExecutesGjc: false`, `justChillWritesHermes: false`, and `justChillOwnsCanonicalMemory: false`. `handoff-gjc --allow-mutation` records requested consent but still does not execute GJC; host-owned visible-session/coordinator/delegation tooling must handle any approved mutation separately and return durable evidence. Sensitive `remember` / `recall` approval tokens must be host approval references such as `approval://...`, `host-approval://...`, or `hermes-approval://...`; arbitrary non-empty strings stay blocked. Without a configured registry, local debug fixtures keep legacy shape-only acceptance. When `--approval-registry` or `JUST_CHILL_APPROVAL_REGISTRY` is supplied, tokens must verify against `scripts/just_chill_approval_registry.py` by scope, optional subject hash, expiry, and revocation state. `recall` defaults to `host-retrieval-required` unless host-owned vector search/read evidence plus fresh canonical source state is supplied.

## End-to-end dogfood contract

`scripts/just_chill_dogfood_harness.py` exercises the current integrated surface without hidden execution:

```text
development request -> route -> visible GJC handoff plan
memory request -> raw artifact contract -> summary memory contract
summary/raw -> ontology candidate -> RDF/OWL export -> SHACL shape export
summary -> vector sidecar candidate -> retrieval evidence -> recall gate
handoff plan -> consent policy
```

The harness is deterministic and local. It does not call Hermes MCP tools, does not run SHACL, does not start GJC, and does not search a vector store. It verifies that the contract chain stays internally coherent and fail-closes on stale, deleted, or redacted recall evidence and sensitive memory.


## Verification

Run:

```sh
python3 scripts/check_just_chill_router.py
python3 scripts/check_just_chill_bridge_contracts.py
python3 scripts/check_just_chill_live_bindings.py
python3 scripts/check_just_chill_visible_helpers.py
python3 scripts/check_just_chill_hermes_boundary.py
python3 scripts/check_just_chill_raw_artifact_store.py
python3 scripts/check_just_chill_hermes_raw_artifact_boundary.py
python3 scripts/check_just_chill_hermes_memory_mcp.py
python3 scripts/check_just_chill_hermes_mcp_receipts.py
python3 scripts/check_just_chill_summary_memory_receipts.py
python3 scripts/check_just_chill_ontology_contracts.py
python3 scripts/check_just_chill_rdf_persistence_receipts.py
python3 scripts/check_executor_routing_policy.py
python3 scripts/check_just_chill_vector_recall.py
python3 scripts/check_just_chill_memory_migration_fixture.py
python3 scripts/check_just_chill_cli.py
python3 scripts/check_just_chill_approval_registry.py
python3 scripts/check_just_chill_gjc_consent_policy.py
python3 scripts/check_just_chill_gjc_execution_bridge.py
python3 scripts/check_just_chill_dogfood_harness.py
python3 scripts/check_just_chill_harness.py
python3 scripts/check_just_chill_harness_mcp.py
python3 scripts/check_just_chill_hermes_harness.py
python3 scripts/just_chill_harness.py --operation handle --arguments '{"request":"fix src/hooks/bridge.ts","cwd":"/home/hskim/jarvis"}' --pretty
python3 scripts/just_chill_harness_mcp.py --check --pretty
python3 scripts/just_chill_hermes_harness.py --cwd /home/hskim/jarvis --pretty
python3 scripts/just_chill_live_bindings.py --probe --pretty --cwd /home/hskim/jarvis "fix TypeError in src/hooks/bridge.ts and run bun test"
python3 scripts/just_chill_hermes_adapter.py --probe --pretty --cwd /home/hskim/jarvis --summary "Sensitive API key request; no persistence without explicit approval." "remember my API key sk-test-1234567890 for later"
python3 scripts/just_chill_summary_memory_receipts.py --probe --pretty --cwd /home/hskim/jarvis --plan-add --summary "Visible routed GJC sessions are preferred." "remember that visible GJC sessions are preferred"
python3 scripts/just_chill_hermes_raw_artifact_boundary.py --probe --pretty --cwd /home/hskim/jarvis
python3 scripts/just_chill_ontology_contracts.py --live-boundary --plan-persistence --pretty "remember that just-chill routes dev work to GJC"
python3 scripts/just_chill_hermes_mcp_receipts.py --require-registration --pretty
python3 scripts/just_chill_rdf_persistence_receipts.py --pretty
python3 scripts/just_chill_vector_recall.py --boundary --probe --pretty --cwd /home/hskim/jarvis
python3 scripts/just_chill_vector_recall.py --candidate --pretty
python3 scripts/just_chill_vector_recall.py --recall --pretty
```

Expected high-level results:

- Router, bridge contract, live-binding, visible-helper, Hermes-boundary, raw-artifact-store, raw-artifact-boundary, Hermes-memory-MCP, Hermes-MCP-receipt, summary-memory-receipt, ontology-contract, RDF-persistence-receipt, vector-recall, memory-migration, CLI-contract, consent-policy, dogfood-harness, Hermes-harness, Hermes-harness-MCP, Hermes-main-harness, and legacy executor-routing checks pass.
- Non-sensitive memory migration fixture checks pass and prove selected repo-wiki design facts can replay through host-owned raw/RDF/vector receipt lifecycles plus summary receipts without private memory promotion.
- CLI contract checks pass and prove `route`, `remember`, `recall`, and `handoff-gjc` emit JSON with local execution disabled, sensitive-memory approval blockers, fake approval token rejection, stale/deleted recall blocking, and host-owned retrieval requirements.
- Approval-registry checks pass and prove issued tokens are stored only as hashes, scope/subject mismatches and revocation block use, registry-backed sensitive remember tokens are accepted only when verified, and recall approval can be verified while still requiring host retrieval evidence.
- Consent policy checks pass and prove coordinator/delegation fail closed without mutation classes, per-call consent, clean coordinator smoke, delegate availability, durable evidence, and scrollback rejection.
- GJC execution bridge checks pass and prove `gjcHandoffPlan` can be converted into host-owned visible-session task/session artifacts, while actual GJC start/prompt injection stays outside just-chill and completion requires durable non-scrollback evidence.
- Dogfood harness checks pass and prove the integrated contract chain can route a development request, build memory/raw/RDF/SHACL/vector contracts, admit recall only with fresh host evidence, and produce a GJC handoff/consent plan without hidden execution.
- Hermes-facing harness checks pass and prove route/remember/recall/handoff/consent/status/handle operations emit stable JSON for Hermes callers with all local execution, Hermes writes, SHACL runs, vector searches, coordinator calls, and delegate calls disabled.
- Harness MCP checks pass and prove the stdio server exposes concrete `just_chill.*` tools, preserves JSON-RPC ids on errors, and is registered in Hermes as `just_chill_harness` only after explicit host approval.
- Hermes-main harness checks pass and prove Hermes is the user-facing layer, just-chill is the policy harness, CLI remains debug-only, and development/memory/recall/sensitive/malformed-MCP paths fail closed or route correctly.
- Visible-session handoff is ready when repo-local helper contracts are probed cleanly and `tmux`/`gjc` are available; without probing or tools, readiness stays unverified or metadata-only and fail-closed.
- Coordinator MCP and `gjc_delegate_*` are available in the smoke tool list but execution is still gated by mutation consent.
- Hermes adapter output includes `liveBoundaryReport` / `rawLiveBoundary` / `summaryLiveBoundary`, preserves `storageAuthority: Hermes`, maps raw artifact writes through host-owned `hermes.raw_artifact.create/read/delete`, exposes local raw artifact staging only as optional migration evidence, exposes `rawArtifactApiDiscovery`, maps active Holographic summary memory to a host-owned `fact_store(action=add)` write plan with `allowedHere: false`, and exposes a summary provider receipt plan that remains host-executed.
- Ontology live-boundary output reports RDF parser availability, live SHACL engine availability, and Hermes RDF graph create/read/delete API mapping; with `pyshacl` installed/mapped, host-owned RDF persistence receipt runs can produce conforming SHACL evidence plus Hermes RDF read-back/delete receipts.
- Vector live-boundary output may report Holographic `fact_store(search/probe/list)` as provider summary search, but that is not vector sidecar authority. The host-owned `just_chill_memory_api` now maps exact-hash/source-id vector sidecar create/search/read/delete tools; recall gates still require canonical Hermes refs, fresh hashes, deletion/redaction checks, access policy, and durable host retrieval evidence.

## Remaining work

- Use `scripts/just_chill_memory_migration_fixture.py` as the current safe replay template for non-sensitive repository design facts; real personal or production memory migration still requires explicit source selection and approval before promotion.
- Use `scripts/just_chill_approval_registry.py` for local host-owned approval tokens until Hermes exposes a native approval registry/audit API; do not treat shape-only debug tokens as production approval.
- Use `scripts/just_chill_gjc_execution_bridge.py` as the current visible-session execution handoff MVP; production automation may run the emitted argv plan only in a host/operator-owned bridge that returns durable evidence.
- Bind local summary add/remove receipts to a real Hermes receipt/audit API if Hermes exposes one; until then the provider result evidence remains host-supplied local receipt evidence.
- Keep `pyshacl` mapped for live SHACL evidence, then promote only eligible ontology candidates through `scripts/just_chill_rdf_persistence_receipts.py` or a future production runner with the same evidence shape.
- Add production semantic embedding/index runners only after an explicit operator-owned model/index policy is chosen; the mapped vector sidecar API currently stores and searches host-owned sidecar metadata by exact text hash or canonical source id and does not make just-chill a vector executor.
