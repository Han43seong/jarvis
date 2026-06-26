# just-chill Router Harness

Use this harness for the first executable slice of the just-chill vNext design.

## Purpose

`just-chill` is not a second development worker. It is the operating layer that classifies a user request, chooses the right lane, prepares a handoff packet, and later records result evidence into memory policy gates.

The deterministic router lives at:

- `scripts/just_chill_router.py`

The acceptance check lives at:

- `scripts/check_just_chill_router.py`

## Canonical inputs

- Current design: `wiki/concepts/just-chill-vnext-operating-layer.md`
- Decision record: `wiki/projects/jarvis/decisions.md`
- Hermes/GJC bridge reference: <https://gajae-code.com/docs/hermes-mcp-bridge.html>

## Mapped repo surfaces

The first implementation slice is intentionally inside the control-plane repo rather than a new application repo.

| Surface | Current file(s) | Role |
|---|---|---|
| Agent operating policy | `AGENTS.md` | Safety, executor selection, and workspace boundary rules. |
| Existing routing policy | `config/routing.yaml`, `harnesses/executor-router.md` | Legacy JARVIS executor taxonomy and selective review-loop policy. |
| Existing route checks | `scripts/check_executor_routing_policy.py` | Stdlib acceptance-test style used by this repo. |
| Canonical just-chill design | `wiki/concepts/just-chill-vnext-operating-layer.md` | Product boundary, GJC routing, Hermes memory, and bridge policy. |
| Decision history | `wiki/projects/jarvis/decisions.md` | Durable rationale and brownfield constraints. |
| New executable slice | `scripts/just_chill_router.py` | Deterministic request-to-route handoff packet generator. |
| New acceptance check | `scripts/check_just_chill_router.py` | Focused tests for development/non-development routing and bridge-path selection. |

## Output contract

The router emits JSON with:

- `schemaVersion`
- `router`
- `bridgeReference`
- `classification.isDevelopment`
- `classification.lane`
- `classification.category`
- `classification.risk`
- `classification.approvalRequired`
- `routing.target`
- `routing.routeHint`
- `routing.skillEntrypoint`
- `routing.bridgePath`
- `signals`
- `handoff.forbiddenActions`
- `handoff.completionEvidenceRequired`

## Development lane

Development-related requests route to GJC by default when they involve code, repositories, APIs, tests, configuration, deployment, product behavior, debugging, review, or development workflow planning.

Route hints:

| Hint | Meaning |
|---|---|
| `gjc-direct` | Small clear edit or concrete anchored task. |
| `gjc-deep-interview` | Vague development idea or requirements uncertainty. |
| `gjc-ralplan` | Clear but architectural, high-risk, auth/security, migration, or planning-heavy work. |
| `gjc-ultragoal` | Approved implementation plan needing durable completion. |
| `gjc-team` | Work requiring tmux-backed parallel workers. |

## Bridge path policy

Follow the Gajae Code Hermes MCP Bridge reference:

| Bridge path | Use when |
|---|---|
| `visible-routed-session` | First integration pass and human-observable routed GJC work. |
| `coordinator-mcp` | Pure machine control with durable turn state, polling, questions, reports, and artifact reads. |
| `gjc-delegation` | Whole GJC workflow delegation through `gjc_delegate_plan`, `gjc_delegate_execute`, or `gjc_delegate_team`. |
| `rpc-host-tools` | GJC needs Hermes/just-chill-owned host tools through RPC `customTools`. |

## Non-development lane

Non-development requests stay in just-chill or route to external tools. v1 categories are:

- `memory`
- `mail`
- `calendar`
- `data-analysis`
- `research`
- `writing`
- `direct-general`

Drafting, summarization, and internal organization can be automatic when reversible. External sends, deletion, publication, payments, deploys, pushes, secrets, credential files, and canonical policy/decision memory promotion require approval.

## Completion evidence rule

A prompt visible in tmux scrollback is not completion. just-chill should summarize completion only from durable turn/report/artifact evidence, diff/test/PR evidence for code, or source-linked artifacts for research and memory work.

## Verification

Run:

```sh
python3 scripts/check_just_chill_router.py
python3 scripts/just_chill_router.py --pretty "fix TypeError in src/hooks/bridge.ts and run bun test"
```
