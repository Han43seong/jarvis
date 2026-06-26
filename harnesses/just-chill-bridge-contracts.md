# just-chill Bridge and Memory Contract Harness

Use this harness for the second executable slice of the just-chill vNext design.

## Purpose

The first router slice decides where a request should go. This slice turns that route decision into contract-level handoff records:

```text
user request
  -> scripts/just_chill_router.py
  -> scripts/just_chill_bridge.py
  -> GJC bridge plan JSON, without executing GJC

user request
  -> scripts/just_chill_router.py
  -> scripts/just_chill_memory_contracts.py
  -> Hermes raw artifact / summary memory contract JSON, without writing Hermes
```

The bridge and memory scripts remain deterministic. Live helper scripts are now repo-local host helpers that record visible-session metadata, emit dry-run tmux/GJC orchestration plans, and enforce evidence contracts without hidden execution.

## Canonical inputs

- Current design: `wiki/concepts/just-chill-vnext-operating-layer.md`
- Migration inventory: `wiki/projects/jarvis/just-chill-migration-inventory.md`
- Router contract: `harnesses/just-chill-router.md`
- Hermes/GJC bridge reference: <https://gajae-code.com/docs/hermes-mcp-bridge.html>

## Implemented files

| File | Role |
|---|---|
| `scripts/just_chill_bridge.py` | Converts route packets into GJC bridge plans for visible sessions, coordinator MCP, `gjc_delegate_*`, or RPC host tools. |
| `scripts/just_chill_memory_contracts.py` | Builds raw artifact and summary memory contract records with privacy/provenance fields. |
| `scripts/just_chill_summary_memory_receipts.py` | Builds host-owned summary provider add/remove receipt plans for mapped Hermes memory providers without calling provider tools directly. |
| `scripts/just_chill_hermes_raw_artifact_boundary.py` | Discovers Hermes raw artifact create/read/delete API or MCP tool availability and emits host-owned local-staging-to-Hermes promotion plans without calling Hermes. |
| `scripts/check_just_chill_bridge_contracts.py` | Verifies route-to-bridge and memory contract behavior. |
| `wiki/projects/jarvis/just-chill-migration-inventory.md` | Classifies current Jarvis assets for staged migration. |
| `harnesses/just-chill-live-bindings.md` | Current live-binding and visible helper status for the third/fourth slices. |

## GJC bridge plan rules

`just_chill_bridge.py` must preserve these boundaries:

- It consumes router packets; it does not reclassify user intent independently.
- It emits JSON plans; it does not start tmux, call MCP tools, invoke `gjc_delegate_*`, or run GJC.
- It states that just-chill does not own or mirror GJC workflow state.
- It keeps the original request intact for GJC.
- It requires durable evidence before completion; tmux scrollback alone is not completion.

Bridge paths:

| Bridge path | Contract output |
|---|---|
| `visible-routed-session` | Host-owned helper plan for `create-gjc-session`, `prompt-gjc-session`, and `tail-gjc-session`; includes skill prompt, tmux orchestration plan metadata, and real-work evidence requirement. |
| `coordinator-mcp` | `gjc mcp-serve coordinator` server/tool/turn-model plan with mutation class and `allow_mutation: true` requirements. |
| `gjc-delegation` | Maps `gjc-ralplan` -> `gjc_delegate_plan`, `gjc-ultragoal` -> `gjc_delegate_execute`, and `gjc-team` -> `gjc_delegate_team`. |
| `rpc-host-tools` | RPC boundary plan for exposing just-chill/Hermes host tools to GJC via `customTools`, not direct GJC MCP internals. |

## Hermes memory contract rules

`just_chill_memory_contracts.py` must preserve these boundaries:

- Hermes owns live raw artifact and memory storage.
- just-chill may create contract records and policy decisions, but this slice does not write to Hermes.
- Sensitive content such as API keys, passwords, tokens, SSH/private keys, `.env`, credentials, and `auth.json` cannot auto-persist.
- Summary memory must reference raw artifact provenance.
- Canonical Decision/Policy assertions require explicit confirmation.
- Preference auto-promotion is only allowed for repeated, non-sensitive, non-destructive, access-allowed, retention-valid, conflict-free, high-confidence evidence.
- Provider-backed summary memory add/remove operations require host-supplied provider result evidence; just-chill records local receipts but does not claim canonical Hermes write/delete authority.
- Raw artifact promotion requires mapped Hermes create/read/delete APIs, local staging receipt provenance, host-owned Hermes execution, and read-back hash evidence; just-chill only emits the plan.
- Contract records remain `liveBinding.status = contract-only` until a real Hermes adapter is mapped.

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
python3 scripts/check_just_chill_summary_memory_receipts.py
python3 scripts/check_just_chill_ontology_contracts.py
python3 scripts/check_executor_routing_policy.py
python3 scripts/just_chill_bridge.py --pretty --cwd /home/hskim/jarvis "Execute the approved pending-approval plan with ultragoal"
python3 scripts/just_chill_memory_contracts.py --pretty --summary "User prefers visible routed GJC sessions first." "remember that GJC should use visible routed sessions first"
python3 scripts/just_chill_live_bindings.py --probe --pretty --cwd /home/hskim/jarvis "fix TypeError in src/hooks/bridge.ts and run bun test"
python3 scripts/just_chill_hermes_adapter.py --probe --pretty --cwd /home/hskim/jarvis --summary "Sensitive API key request; no persistence without explicit approval." "remember my API key sk-test-1234567890 for later"
```

## Live-binding status

See `harnesses/just-chill-live-bindings.md` for the current host map. As of the Hermes live-boundary slice, `gjc`, `tmux`, `hermes`, coordinator MCP smoke, `gjc_delegate_*` discovery, repo-local visible-session helper contracts, local raw artifact staging, raw artifact API discovery, and summary provider add/remove receipt contracts pass; visible handoffs are `orchestration-plan-ready` when helper contracts are probed and `tmux`/`gjc` are available. RPC host `customTools` and Hermes raw artifact APIs remain unmapped, and the Hermes adapter reports those paths as contract-only/write-blocked while preserving Hermes storage authority.

## Remaining live-binding work

- Configure Hermes coordinator MCP mutation classes deliberately before executable coordinator/delegation use.
- Install or map real Hermes raw artifact create/read/delete APIs or MCP tools, then consume local staging receipts through the host-owned promotion plan.
- Map real RDF/OWL serialization/persistence, a SHACL engine, vector sidecar, and promotion gates in a later slice.
