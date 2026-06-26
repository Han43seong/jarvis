<div align="center">

# just-chill Operating Layer

**A Hermes-facing routing, memory-policy, approval, and GJC-handoff harness.**

Hermes is the user-facing agent. just-chill is the policy layer. GJC is the development executor.

<br />

![Status](https://img.shields.io/badge/status-active-10b981?style=for-the-badge)
![Hermes](https://img.shields.io/badge/UX-Hermes-5e6ad2?style=for-the-badge)
![just-chill](https://img.shields.io/badge/policy-just--chill-7170ff?style=for-the-badge)
![GJC](https://img.shields.io/badge/executor-GJC-111827?style=for-the-badge)

<br />

[Overview](#overview) · [Architecture](#architecture) · [Current status](#current-status) · [Execution mode](#execution-mode) · [Verification](#verification) · [Update history](#update-history-and-lessons-learned)

</div>

---

## Overview

This repository is the working home for the `just-chill` vNext operating layer inside the existing JARVIS control-plane repository.

The final product direction is:

- **Hermes is the main user-facing UX.** Users talk to Hermes, and Hermes owns session continuity, tool access, canonical memory/artifact authority, and user-facing orchestration.
- **just-chill is a Hermes-facing harness.** It classifies requests, applies routing policy, builds memory and recall gates, verifies approval-token contracts, and emits GJC handoff plans.
- **GJC is the development execution layer.** Development planning, implementation, verification, durable workflow state, and multi-agent execution remain GJC responsibilities.

just-chill is not a standalone daily CLI product, not a hidden executor, not a memory database, and not a replacement for Hermes or GJC.

## Architecture

```text
User
  -> Hermes
       -> just-chill harness
            -> route request
            -> build memory / recall / approval gates
            -> build GJC handoff plan when development work is needed
       -> host-owned bridge
            -> visible GJC session or approved coordinator/delegate path
            -> durable evidence returned to Hermes
       -> Hermes memory/artifact tools
            -> canonical storage, recall, audit, and user-facing continuity
```

Authority boundaries:

| Layer | Owns | Must not own |
| --- | --- | --- |
| Hermes | User-facing UX, canonical memory/artifact access, tool calls, session continuity | GJC implementation internals or just-chill policy decisions |
| just-chill | Routing, policy, approval verification, recall gates, GJC handoff contracts | GJC execution, Hermes writes, canonical memory, SHACL execution, vector search |
| GJC | Development execution, planning workflows, verification-ready implementation, durable development evidence | Personal memory authority or Hermes UX |
| Host bridge | Approved visible-session or coordinator/delegate execution mechanics | Completing work from tmux scrollback alone |

## Current status

Implemented and verified surfaces include:

| Surface | Main files |
| --- | --- |
| Request router and GJC bridge contracts | `scripts/just_chill_router.py`, `scripts/just_chill_bridge.py` |
| Memory contract records | `scripts/just_chill_memory_contracts.py` |
| Live-boundary discovery | `scripts/just_chill_live_bindings.py`, `scripts/just_chill_hermes_adapter.py` |
| Visible GJC session helper contracts | `scripts/just_chill_visible_session_helpers.py`, `scripts/create-gjc-session`, `scripts/prompt-gjc-session`, `scripts/tail-gjc-session` |
| Hermes raw/RDF/vector MCP API | `scripts/just_chill_hermes_memory_mcp.py` |
| MCP receipt checks | `scripts/just_chill_hermes_mcp_receipts.py` |
| Raw artifact staging | `scripts/just_chill_raw_artifact_store.py` |
| Summary memory receipts | `scripts/just_chill_summary_memory_receipts.py` |
| Ontology/RDF/SHACL contracts | `scripts/just_chill_ontology_contracts.py`, `scripts/just_chill_rdf_persistence_receipts.py` |
| Vector sidecar and recall gates | `scripts/just_chill_vector_recall.py` |
| Non-sensitive memory migration fixture | `scripts/just_chill_memory_migration_fixture.py` |
| Debug/test CLI contract surface | `scripts/just_chill_cli.py`, `scripts/just-chill` |
| Coordinator/delegation consent policy | `scripts/just_chill_gjc_consent_policy.py` |
| Hermes-facing harness adapter | `scripts/just_chill_harness.py` |
| Hermes-facing harness MCP wrapper | `scripts/just_chill_harness_mcp.py` |
| Hermes-main dogfood harness | `scripts/just_chill_hermes_harness.py` |
| Approval registry | `scripts/just_chill_approval_registry.py` |
| Visible-session-only GJC execution bridge | `scripts/just_chill_gjc_execution_bridge.py` |

Hermes MCP registration status:

- `just_chill_memory_api` is registered and enabled.
- `just_chill_harness` is registered and enabled.
- A fresh Hermes session returned `just_chill.status: ready` with GJC, Hermes, tmux, coordinator MCP, delegate tools, visible-session helpers, and memory API surfaces visible.

## Execution mode

Visible-session-only execution is enabled in `config/routing.yaml`.

This mode may prepare host-owned visible GJC handoff artifacts:

- task file,
- session metadata,
- prompt handoff metadata,
- operator-visible argv plan,
- durable evidence validation.

It still does **not**:

- start hidden GJC work from just-chill,
- inject prompts from just-chill,
- call coordinator/delegate tools automatically,
- write Hermes memory,
- run SHACL locally,
- run vector search locally,
- accept tmux scrollback as completion evidence.

Completion requires durable evidence such as a `turn_id`, report, artifact, diff, test output, or PR reference.

## Approval and memory policy

Approval tokens have two modes:

| Mode | Use |
| --- | --- |
| Shape-only | Local debug and fixture compatibility only. Accepts host-style token prefixes but does not prove authenticity. |
| Registry-backed | Production-meaningful local host approval. Verifies token hash, scope, optional subject hash, expiry, and revocation state. |

The local host-owned registry is implemented in `scripts/just_chill_approval_registry.py`. It stores only token hashes and token previews, not plaintext tokens.

Sensitive memory and recall paths must use registry-backed approval or a future Hermes-native approval/audit equivalent before production promotion.

## Repository layout

| Path | Purpose |
| --- | --- |
| `scripts/just_chill_*.py` | Executable contracts and harnesses for routing, memory, approval, recall, MCP, and GJC handoff. |
| `scripts/check_just_chill_*.py` | Deterministic regression checks for each just-chill surface. |
| `harnesses/just-chill-*.md` | Human-readable contracts and operating boundaries. |
| `wiki/concepts/just-chill-vnext-operating-layer.md` | Canonical concept page for the vNext direction. |
| `wiki/projects/jarvis/status.md` | Current project status and next steps. |
| `wiki/projects/jarvis/decisions.md` | Durable decisions and rationale. |
| `wiki/projects/jarvis/just-chill-migration-inventory.md` | Migration inventory and asset classification. |
| `config/routing.yaml` | Routing defaults and visible-session-only execution bridge setting. |

Runtime/session folders such as `.gjc/`, browser profiles, local research checkouts, and local evidence stores are not product source surfaces.

## Verification

The full just-chill regression suite currently includes:

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
python3 scripts/check_executor_routing_policy.py
```

Verification run for this README correction:

- README now leads with the final just-chill product description,
- README contains no Hangul characters,
- `git diff --check -- README.md` passed,
- focused harness, MCP, and execution-bridge checks passed.

## Update history and lessons learned

| Step | Problem or trial | Resolution |
| --- | --- | --- |
| Product boundary | The earlier JARVIS vNext framing still looked like a broad control plane or another executor. | Reframed the final product as Hermes UX + just-chill policy harness + GJC executor. |
| CLI direction | A standalone just-chill CLI was tempting, but it would compete with Hermes. | Kept `scripts/just-chill` as a debug/test/fixture contract surface only. |
| Hermes integration | MCP registration mutates external Hermes configuration. | Required explicit approval, registered `just_chill_harness`, then verified a fresh Hermes session with `just_chill.status: ready`. |
| Approval tokens | Prefix-shape checks did not prove scope, subject, expiry, or revocation. | Added a local host-owned approval registry storing only token hashes. |
| Recall safety | Recall can become unsafe if stale, deleted, redacted, sensitive, or scope-mismatched evidence enters context. | Required host-owned retrieval evidence, fresh source hash, deletion/redaction state, access scope, and approval gates. |
| Coordinator/delegate execution | Direct machine-control mutation is powerful and should not be default. | Kept visible sessions first and added deterministic consent policy for coordinator/delegate mutation. |
| Execution bridge | Hermes needs a concrete next hop after `gjcHandoffPlan`, but just-chill must not execute GJC. | Added visible-session-only bridge preparation and durable evidence verification without hidden execution. |
| Completion evidence | tmux scrollback is useful for debugging but weak as proof. | Kept scrollback debug-only and required durable evidence such as turn ids, reports, artifacts, diffs, tests, or PR references. |
| Regression coverage | Individual contracts could pass while stitched behavior drifted. | Added dogfood harnesses and a full just-chill suite covering router, bridge, memory, MCP, approval, consent, harness, and execution-bridge behavior. |

## Remaining productization work

The implementation is structurally complete for the current safe operating layer. Remaining work is operational/productization work:

1. Wrap the visible-session-only argv plan in a host-owned operator bridge that actually opens tmux/GJC and returns durable evidence.
2. Replace or connect the local approval registry to a Hermes-native approval/audit API when available.
3. Run real personal or production memory migration only after explicit source selection, approval, and deletion/redaction policy gates.
4. Bind summary add/remove receipts to Hermes-native audit receipts when Hermes exposes that API.
5. Add a production semantic vector runner only after choosing embedding model, dimensions, rebuild policy, invalidation, and deletion propagation rules.
6. Map RPC `customTools` only after the same authority and evidence boundaries are preserved.
