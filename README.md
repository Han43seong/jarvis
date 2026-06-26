<div align="center">

# JARVIS Control Plane

**A Hermes-centered control plane for AI-assisted software work.**

Plan work, route it to the right executor, verify results, and preserve durable knowledge.

<br />

![Status](https://img.shields.io/badge/status-active-10b981?style=for-the-badge)
![Control Plane](https://img.shields.io/badge/role-control--plane-7170ff?style=for-the-badge)
![Hermes](https://img.shields.io/badge/orchestrator-Hermes-5e6ad2?style=for-the-badge)
![Codex OMX](https://img.shields.io/badge/primary-Codex%20%2B%20OMX-111827?style=for-the-badge)
![Claude OMC](https://img.shields.io/badge/secondary-Claude%20Code%20%2B%20OMC-191a1b?style=for-the-badge)

<br />

[Overview](#overview) · [Why](#why-this-exists) · [Methodology](#methodology) · [Architecture](#architecture) · [Harnesses](#harness-taxonomy) · [just-chill](#just-chill-vnext-update) · [History](#build-history-and-lessons-learned)

</div>

---

## Overview

JARVIS is not an application repository. It is a **control plane**: a compact, durable workspace for project registry, routing policy, operating rules, wiki notes, execution harnesses, and verification records.

It exists to make AI-assisted work more operationally reliable:

- choose the right executor for each task,
- keep application code outside the control-plane repository,
- separate production from review for quality-sensitive work,
- verify every meaningful change with git state, diffs, tests, or targeted checks,
- preserve durable decisions in the wiki,
- promote reusable procedures into skills.

## Why this exists

The initial idea was to build a practical personal JARVIS: **not a single all-powerful coding bot**, but a control plane that can coordinate multiple AI executors, remember durable context, and keep work verifiable.

The core design assumption is that AI work becomes safer and more useful when responsibilities are separated:

| Concern | Owner | Purpose |
| --- | --- | --- |
| Planning and routing | Hermes / JARVIS | Choose the smallest capable execution path. |
| Production | Producer agents | Implement code, create artifacts, or generate designs inside bounded scope. |
| Independent review | Reviewer/Critic agents | Judge producer output against the original spec and return pass/change/escalate/abort. |
| Revision planning | Hermes / JARVIS | Convert reviewer findings into bounded producer instructions. |
| Verification | Hermes / JARVIS | Check repo state, diffs, tests, lint, artifacts, and completion criteria. |
| Durable knowledge | Wiki | Preserve decisions, status, architecture, and research. |
| Reusable procedure | Skills | Turn proven workflows into repeatable operating knowledge. |
| Source of truth | Git | Record exactly what changed. |

## Methodology

JARVIS follows a control-plane methodology:

1. Keep the control plane small and focused on documentation, configuration, routing, and verification.
2. Keep application source code in independent project repositories.
3. Route each task to the smallest capable executor.
4. Use a Producer/Reviewer rejection loop for non-trivial implementation, design, and quality-sensitive artifacts.
5. Give executors bounded prompts, allowed scope, forbidden actions, and clear completion criteria.
6. Verify results with repo state, diffs, tests, lint, or targeted checks before reporting success.
7. Promote recurring workflows into skills; promote durable knowledge into the wiki; keep memory compact.
8. Prefer reversible, inspectable changes over hidden automation.

## Architecture

```text
User intent
   │
   ▼
Hermes / JARVIS control plane
   ├─ plans and decomposes work
   ├─ routes to the right executor
   ├─ runs Producer/Reviewer rejection loops when quality warrants it
   ├─ verifies diffs, tests, and repo state
   ├─ updates durable wiki/status notes
   └─ preserves reusable procedures as skills
        │
        ├─ Codex CLI + OMX          Codex-family producer line
        ├─ Claude Code + OMC        Claude-family producer/reviewer line
        ├─ Hermes direct tools      quick edits, docs, checks, wiki maintenance
        ├─ background workers       research, comparison, long inspections
        └─ cron / kanban            recurring or durable multi-step work
```


## Harness taxonomy

JARVIS is best understood as a **top-level operating harness** rather than a single executor, plugin, or project tool. Its job is to decide what work should happen, where it should happen, who should do it, how it should be verified, and where durable knowledge should be recorded.

```text
JARVIS Operating Harness
├─ Project Registry Harness
│  └─ config/projects.yaml
├─ Routing Harness
│  ├─ AGENTS.md
│  ├─ config/routing.yaml
│  └─ jarvis-executor-router skill
├─ Skill Harness
│  └─ reusable operating manuals loaded by Hermes
├─ Wiki / Status Harness
│  └─ wiki/projects/<project>/status.md
├─ External Executor Workflow Harness
│  ├─ Hermes-native direct work
│  ├─ Codex-family: codex direct + OMX wrapper
│  └─ Claude-family: Claude Code + OMC wrapper
├─ Producer / Reviewer Quality Harness
│  └─ maker/checker loop applied where quality warrants it
├─ Background / Cron / Kanban Harnesses
│  └─ long-running, recurring, or durable multi-worker work
└─ Project-specific Harnesses
   └─ executable repos under /home/hskim/projects/<project>
```

### Harness layers

| Harness | What it decides or does | Typical location |
| --- | --- | --- |
| **JARVIS operating harness** | Top-level control plane: interpret the request, choose target/project, route work, enforce safety gates, verify, and record. | `/home/hskim/jarvis`, `AGENTS.md` |
| **Project registry harness** | Knows which projects exist, where they live, whether they are active/legacy, and their default executor. | `config/projects.yaml` |
| **Routing harness** | Dispatches work by target, task type, risk, executor/workflow, quality gate, and recording location. It is a dispatcher, not an artifact producer. | `config/routing.yaml`, `AGENTS.md`, `jarvis-executor-router` skill |
| **External executor workflow harness** | Delegates bounded work to executor processes, collects artifact/evidence/logs, then returns control to Hermes/JARVIS for verification. | `harnesses/`, `jarvis-codex-omx-executor` skill, project run scripts |
| **Producer/Reviewer quality harness** | Separates maker and checker. It can be applied at the JARVIS level, inside external-executor delegation, inside a project harness, or nested across those layers. | `harnesses/producer-reviewer-rejection-loop.md` plus project-specific gates |
| **Project-specific harness** | Executable project repo with CLI, runners, validators, tests, artifacts, and evidence handling. | `/home/hskim/projects/<project>` |
| **Skill harness** | Operating manual that tells Hermes/JARVIS when and how to use a workflow or project harness. It should not replace executable project code. | `~/.hermes/skills/...` |
| **Wiki/status harness** | Durable human-readable project decisions, status, phase results, and next steps. | `wiki/` |

### Executor families

JARVIS distinguishes executor paths by **operating mode**, not only by model family. In particular, OMX is not a separate model family competing with Codex; it is an oh-my-codex wrapper/orchestration layer on top of the Codex CLI line.

```text
Executor families
├─ Hermes-native
│  └─ direct tools, browser, terminal, verification
├─ Codex-family
│  ├─ codex direct
│  │  └─ codex exec
│  └─ OMX wrapper
│     ├─ omx exec
│     ├─ omx ralph
│     └─ omx team
└─ Claude-family
   ├─ Claude Code
   └─ OMC wrapper
```

Use `codex exec` for clear, bounded, direct Codex-family tasks. Use `omx ralph` or related OMX modes when the work benefits from a higher-level, goal-oriented Codex-family workflow such as multi-file implementation or test/fix loops. Use Claude-family tools where their planning, critique, design, or independent review strengths fit the task.

### Producer/Reviewer is a pattern, not one fixed layer

The Producer/Reviewer harness is not a single standalone executor. It is a reusable quality pattern:

```text
Director: Hermes / JARVIS
  -> Producer: creates code, documents, decks, reports, or other artifacts
  -> Hermes verifier: checks git status, diff, tests, scope, secrets, and artifacts
  -> Reviewer: independently returns PASS / REQUEST_CHANGES / ESCALATE_TO_USER / ABORT
  -> JARVIS: accepts, revises, escalates, or aborts
```

It can be used:

- at the JARVIS level when an executor implements project code,
- inside the External executor workflow when Codex/OMX/Claude are assigned Producer and Reviewer roles,
- inside a project-specific harness when that project generates and compares artifacts,
- or nested across levels, for example when JARVIS uses OMX to implement a slide-director phase that itself runs slide Producers and Reviewers.

### Project harness versus skill

A project-specific harness should stay executable. A skill should capture the operating knowledge for selecting and using that harness.

For example, `hermes-slide-director` should remain a repo/CLI/tooling harness under `/home/hskim/projects/hermes-slide-director`, with runners, validators, tests, and evidence handling. After validation, its stabilized routing and operating policy should be extracted into a skill so Hermes/JARVIS knows when and how to use it.

```text
hermes-slide-director repo
= executable project-specific harness

hermes-slide-director skill
= operating manual for routing, candidate selection, QA gates, and evidence expectations
```

## Executor matrix

| Executor path | Best for | Notes |
| --- | --- | --- |
| **Hermes direct** | Small edits, docs, config checks, wiki maintenance | Fastest path for low-risk control-plane work. |
| **Codex CLI + OMX** | Codex-family production work: medium/large implementation, bounded repo-local edits | `omx` is the oh-my-codex orchestration layer on top of Codex CLI. |
| **Claude Code + OMC** | Claude-family production/review work: planning, refactoring, design-heavy artifacts, independent critique | `omc` is the oh-my-claudecode orchestration layer on top of Claude Code. |
| **Producer/Reviewer loop** | Non-trivial implementation, design, and quality-sensitive artifacts | Producer and Reviewer are separate; reviewer returns `PASS`, `REQUEST_CHANGES`, `ESCALATE_TO_USER`, or `ABORT`. |
| **Background workers** | Research, comparison, long inspections | Keeps the main JARVIS session responsive. |
| **cron** | Recurring monitoring/reporting | For scheduled checks and reports. |
| **kanban** | Durable multi-worker backlog | For longer-running coordinated work. |

## Producer/Reviewer rejection loop

For non-trivial work, JARVIS separates creation from review:

```text
User request
  -> JARVIS Director defines scope, criteria, allowed paths, forbidden actions, and verification commands
  -> Producer agent creates or modifies the artifact
  -> JARVIS runs basic git/test/artifact checks
  -> Reviewer/Critic agent independently evaluates against the original criteria
  -> JARVIS accepts, escalates, aborts, or turns findings into a bounded revision prompt
  -> repeat until pass or max iteration
```

This loop is selective. It is used for medium/large implementation, design/deck generation, quality-sensitive artifacts, explicit rejection-loop requests, and `hermes-slide-director` development. It is skipped for quick reads, simple status checks, one-line docs/config edits, and local server start/stop.

The durable protocol lives at `harnesses/producer-reviewer-rejection-loop.md`, with routing policy in `config/routing.yaml` and active agent instructions in `AGENTS.md`.

## Repository layout

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Standing operating rules for JARVIS sessions launched from this repository. |
| `config/projects.yaml` | Project registry. |
| `config/routing.yaml` | Executor routing policy, including selective Producer/Reviewer loop triggers. |
| `harnesses/` | Reusable execution procedures and verification harnesses, including the Producer/Reviewer rejection-loop protocol. |
| `plans/` | Implementation and migration plans. |
| `runs/` | Run logs and executor summaries. |
| `scripts/` | Helper scripts for control-plane checks and automation. |
| `wiki/` | Obsidian-readable long-term project knowledge. |
| `logs/` | Local workflow logs. |
| `tmp/` | Temporary control-plane files. |

## Project repository model

Application source code should stay outside this control-plane repository.

Each application project should normally be:

1. created as its own directory,
2. initialized as its own git repository,
3. optionally connected to its own GitHub repository,
4. registered in `config/projects.yaml`, and
5. documented under `wiki/projects/<project>/` when durable notes are useful.

This separation keeps orchestration history, project source, CI, remotes, and executor activity cleanly isolated.

## Typical workflow

```text
1. Capture the request and identify the target project.
2. Inspect current repo state and relevant project/wiki context.
3. Select an executor mode.
4. Decide whether the Producer/Reviewer loop is warranted.
5. Prepare a bounded prompt or direct edit plan.
6. Execute with the selected tool or external CLI executor.
7. If looped, run an independent reviewer and convert findings into bounded revision instructions.
8. Verify with git status, git diff, tests, lint, or targeted checks.
9. Record durable decisions/status in the wiki.
10. Commit only the intended files.
```

## Safety baseline

JARVIS is designed for high autonomy with explicit safety gates.

| Guardrail | Policy |
| --- | --- |
| Low-risk local automation | Allowed with smart approval. |
| Secrets | Never store API keys, OAuth tokens, private keys, auth files, or credential contents in this repository. |
| Permanent deletion | Requires explicit confirmation naming the exact target. |
| Push/deploy/auth changes | Requires a clear user request. |
| Broad rewrites | Require clear scope and confirmation. |

## Documentation policy

Use the right durability layer:

| Layer | Use it for |
| --- | --- |
| `README.md` | Public orientation and operating model. |
| `AGENTS.md` | Active operating instructions for agents launched in this workspace. |
| `wiki/` | Durable human-readable knowledge, decisions, status, and research. |
| Hermes memory | Compact durable facts and preferences only. |
| Hermes skills | Reusable procedures that should guide future agent behavior. |

## just-chill vNext update

The current implementation adds `just-chill` as a Hermes-facing operating layer for development routing, memory policy, approval checks, and GJC handoff contracts.

### Why it changed

The previous JARVIS vNext direction risked turning the control plane into another coding agent. The new boundary is stricter:

| Layer | Responsibility |
| --- | --- |
| Hermes | User-facing UX, tool access, memory/artifact authority, and session continuity. |
| just-chill | Routing, policy, recall gates, approval verification, and GJC handoff contracts. |
| GJC | Development execution, planning workflows, implementation, verification, and durable execution evidence. |

This keeps the system observable and avoids hidden execution paths. `scripts/just-chill` remains a debug/test/fixture CLI, not the product UX.

### What was implemented

| Surface | Files |
| --- | --- |
| Routing and bridge contracts | `scripts/just_chill_router.py`, `scripts/just_chill_bridge.py`, `scripts/just_chill_memory_contracts.py` |
| Live boundary mapping | `scripts/just_chill_live_bindings.py`, `scripts/just_chill_hermes_adapter.py` |
| Visible GJC session helpers | `scripts/create-gjc-session`, `scripts/prompt-gjc-session`, `scripts/tail-gjc-session`, `scripts/just_chill_visible_session_helpers.py` |
| Hermes memory API | `scripts/just_chill_hermes_memory_mcp.py`, `scripts/just_chill_hermes_mcp_receipts.py` |
| Raw artifact, RDF, SHACL, vector, and migration contracts | `scripts/just_chill_raw_artifact_store.py`, `scripts/just_chill_ontology_contracts.py`, `scripts/just_chill_rdf_persistence_receipts.py`, `scripts/just_chill_vector_recall.py`, `scripts/just_chill_memory_migration_fixture.py` |
| CLI and dogfood contracts | `scripts/just_chill_cli.py`, `scripts/just-chill`, `scripts/just_chill_dogfood_harness.py` |
| Hermes-facing harness | `scripts/just_chill_harness.py`, `scripts/just_chill_harness_mcp.py`, `scripts/just_chill_hermes_harness.py` |
| Approval registry | `scripts/just_chill_approval_registry.py` |
| Visible-session-only GJC bridge | `scripts/just_chill_gjc_execution_bridge.py` |

### Current execution mode

Visible-session-only execution is enabled in `config/routing.yaml`.

The enabled mode prepares visible GJC handoff artifacts but does not hide execution:

- create task and session metadata,
- emit operator-visible argv plans,
- keep coordinator/delegate auto-mutation disabled,
- reject prompt injection from just-chill,
- reject tmux scrollback as completion evidence,
- require durable evidence such as a `turn_id`, report, artifact, diff, test output, or PR reference.

### Update process and lessons learned

| Step | Trial or issue | Resolution |
| --- | --- | --- |
| Requirements discovery | The initial direction mixed product UX, memory authority, and executor behavior. | Re-established Hermes as UX and memory authority, just-chill as policy harness, and GJC as development executor. |
| CLI productization | A standalone just-chill CLI looked convenient but would compete with Hermes. | Kept the CLI as a deterministic debug/test/fixture contract surface only. |
| Approval tokens | Prefix shape checks blocked random strings but did not prove authenticity, scope, subject, expiry, or revocation. | Added a host-owned approval registry that stores only token hashes and verifies scope, subject hash, expiry, and revocation state. |
| Recall gates | Early recall paths could drift toward local probing or stale evidence. | Made host-owned retrieval evidence, fresh source hash, deletion state, redaction state, and scope checks mandatory. |
| GJC handoff | Direct coordinator/delegate mutation was too powerful to enable by default. | Kept visible sessions first, added a consent policy for coordinator/delegate paths, and added visible-session-only bridge preparation. |
| Completion evidence | tmux scrollback is useful for debugging but weak as proof. | Treated scrollback as debug-only and required durable evidence for completion. |
| Hermes integration | MCP registration mutates external Hermes config. | Required explicit approval, registered `just_chill_harness`, then verified a fresh Hermes session with `just_chill.status: ready`. |
| Quality gates | Individual checks could pass while stitched behavior drifted. | Added dogfood harnesses and a full just-chill regression suite covering router, bridge, memory, MCP, approval, consent, harness, and execution-bridge behavior. |

### Verification commands

The current full just-chill regression suite includes:

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

## Build history and lessons learned

The workflow was assembled iteratively. Important decisions and fixes include:

| Area | What happened | Lesson |
| --- | --- | --- |
| Control-plane boundary | Established this repository as a management workspace rather than an application repository. | Keep orchestration separate from application source. |
| Routing | Added a project registry and routing policy so JARVIS can choose between Hermes direct work, Codex/OMX, Claude Code/OMC, background workers, cron, kanban, and selective Producer/Reviewer loops. | Routing should be explicit, not improvised. |
| Producer/Reviewer loop | Wired the loop into `AGENTS.md`, `config/routing.yaml`, `harnesses/producer-reviewer-rejection-loop.md`, README, and relevant JARVIS skills. | Quality-sensitive work needs independent critique, but loop overhead should remain selective. |
| Primary executor | Verified the Codex CLI + OMX line with smoke tests before treating it as the primary implementation path. | Executor trust should be earned by live verification. |
| Safety | Added sandbox and approval hardening so routine automation can proceed while destructive operations remain gated. | Autonomy needs guardrails. |
| Wiki | Built an ontology-informed markdown wiki for decisions, research, status, and architecture notes. | Durable knowledge should be human-readable and git-friendly. |
| Research | Added background/research-worker conventions after long research tasks began blocking the main chat. | Long-running reasoning belongs outside the foreground loop. |
| MCP bridge | Deferred the OMX Hermes MCP bridge after investigation showed it was promising but not yet stable enough for the default path. | Do not promote unstable integration paths into core workflow. |
| Claude Code auth | Refreshed Claude Code OAuth through an interactive terminal session after print mode returned an authentication error. | Interactive login status and print-mode auth must be verified separately. |
| OMC setup | Confirmed the correct package/repository naming before installation. | Similar package names should be verified before installing. |
| Commit hygiene | Avoided committing large or unrelated research artifacts during setup and README commits. | Stage only intended files. |