---
title: Ouroboros Adoption Review for JARVIS vNext
created: 2026-06-08
updated: 2026-06-08
type: concept
concept_type: architecture-review
status: draft
tags: [jarvis, ouroboros, vnext, agent-os, ontology, runtime, ledger, evaluation, adoption]
sources: [conversation-2026-06-08, github-Q00-ouroboros, ouroboros-readme, ouroboros-hermes-runtime-guide, jarvis-office-runtime-direction, jarvis-vnext-executor-ontology]
confidence: medium
relations:
  - type: informs
    target: jarvis-office-runtime-direction
  - type: informs
    target: jarvis-vnext-executor-ontology
  - type: references
    target: executor-routing
  - type: references
    target: jarvis-control-plane
  - type: complements
    target: jarvis-open-source-strategy
---

# Ouroboros Adoption Review for JARVIS vNext

This note records the JARVIS decision on how to use [`Q00/ouroboros`](https://github.com/Q00/ouroboros) while evolving JARVIS vNext.

## Executive decision

Use Ouroboros as a reference implementation and selective design source, not as a wholesale replacement for JARVIS.

```text
Adoption grade: useful reference / partial absorption candidate
Immediate install into default Hermes profile: no
JARVIS replacement: no
Sandbox or shadow-mode experiment: yes
JARVIS-native extraction of patterns: yes
```

JARVIS remains the top-level Director and control plane. Ouroboros should not be placed above JARVIS as a second Agent OS that owns routing, approvals, or final verification.

## Why it is relevant

Ouroboros describes itself as an Agent OS for replayable, specification-first AI coding workflows. Its core loop is:

```text
Interview -> Seed -> Execute -> Evaluate -> Evolve
```

The project is relevant because it overlaps with the JARVIS vNext direction:

- Socratic interview before execution;
- ambiguity scoring before committing to implementation;
- immutable Seed/spec as the source of truth;
- event sourcing / ledger-like state;
- runtime adapters for coding agents;
- evaluation gates;
- status, resume, cancel, and persistent loop concepts;
- plugin / program layers with scoped capabilities.

These are close to the JARVIS target of ontology-backed routing, run ledgers, approval queues, status views, and Producer/Reviewer runners.

## Non-negotiable boundary

Ouroboros must not replace JARVIS judgment.

```text
User
  -> JARVIS Director
     -> optional Ouroboros-derived specification/ledger/evaluation patterns
     -> JARVIS runtime/router/approval/status
     -> existing or future executor/harness
     -> JARVIS verification and final answer
```

Do not invert this into:

```text
User
  -> Ouroboros Agent OS
     -> Hermes/JARVIS as just one backend
```

That would blur responsibility and could reduce the JARVIS control-plane role that the user wants to preserve.

## Concept mapping

| Ouroboros concept | JARVIS vNext interpretation | Adoption mode |
|---|---|---|
| Socratic Interview | ambiguity/clarification gate before route finalization | absorb pattern |
| Ambiguity score | structured field in task classification | adapt, do not copy blindly |
| Seed Spec | JARVIS task contract / plan / acceptance criteria | absorb schema idea |
| Acceptance Criteria Tree | verifiable task decomposition | absorb selectively |
| EventStore / lineage | run ledger event log and resume trail | adapt to file-first JARVIS ledger |
| Evaluation pipeline | Mechanical -> semantic/reviewer -> optional consensus | map to Producer/Reviewer gates |
| Runtime adapters | executor adapter contract | reference for GJC/OMX/Codex/OpenCode adapters |
| `ooo status` | future `jarvis status` | absorb UX concept |
| `ooo ralph` | durable goal loop / long-running verified loop | compare with JARVIS background/kanban/OMX/GJC |
| UserLevel programs/plugins | functional harness registry / scoped workflow plugins | reference for future harness manifests |
| MCP integration | optional tool surface | sandbox before enabling in default profile |

## What to absorb into JARVIS-native design

### 1. Task contract / Seed-like spec

Every non-trivial JARVIS run should have a durable task contract before execution.

Suggested fields:

```yaml
task_contract:
  run_id: string
  user_request: string
  target_project: string
  target_path: string
  task_type: docs | research | implementation | refactor | test_fix | artifact | verification
  complexity: tiny | small | medium | large | very_large
  ambiguity_score: number | null
  ambiguity_level: low | medium | high
  success_criteria: list[string]
  constraints: list[string]
  forbidden_actions: list[string]
  approval_gates: list[string]
  evidence_required: list[string]
  route_recommendation: object
  jarvis_decision: object
```

This is the JARVIS-native equivalent of a Seed. It does not need to use the Ouroboros database or exact schema.

### 2. Interview / ambiguity gate

For unclear work, the router should recommend one of:

```text
proceed
ask minimal clarifying questions
run a structured interview
create a draft plan and request approval
```

The key idea to absorb from Ouroboros is not the exact formula, but the hard separation between:

```text
unclear goal -> clarify/specify first
clear enough goal -> execute with bounded scope
```

### 3. File-first run ledger with event log

JARVIS should keep the file-first run ledger already planned, but add an event-log concept inspired by Ouroboros event sourcing.

Suggested structure:

```text
runs/<run-id>/
  request.md
  task-contract.yaml
  route.json
  plan.md
  events.jsonl
  prompts/
  logs/
  evidence/
  reviews/
  approvals/
  final-report.md
```

`events.jsonl` should record important state transitions without becoming a secret dump:

```json
{"type":"route_decision","time":"...","executor":"omx-codex","reason":"..."}
{"type":"approval_required","decision_id":"decision-001","reason":"git push"}
{"type":"producer_completed","status":"success","log":"logs/producer.log"}
{"type":"reviewer_verdict","verdict":"REQUEST_CHANGES"}
```

### 4. Evaluation ladder

Map the Ouroboros evaluation idea into JARVIS gates:

```text
Mechanical gate:
  git status/diff
  syntax check
  tests/lint/build
  artifact existence
  smoke checks

Semantic gate:
  independent Reviewer/Critic checks output against task contract
  checks claims, UX, architecture, user intent, and acceptance criteria

Consensus gate, only when needed:
  second reviewer or different model family
  used for high-risk, subjective, or expensive artifacts
```

Do not require consensus for every small task.

### 5. Runtime / executor adapter contract

Use Ouroboros as a reference for cross-runtime thinking, but define a JARVIS-owned adapter contract.

Suggested adapter outputs:

```yaml
executor_result:
  executor_id: string
  command: string
  status: success | failed | interrupted | escalated
  changed_files: list[string]
  commands_run: list[string]
  tests_run: list[object]
  evidence_paths: list[string]
  summary: string
  risks: list[string]
  approval_requests: list[object]
```

This keeps OMX, Gajae-Code, LazyCodex, OpenCode, raw Codex, Hermes direct, cron, and kanban comparable without forcing them into Ouroboros internals.

### 6. Harness/plugin manifest idea

Ouroboros' UserLevel program/plugin direction is useful for JARVIS functional harnesses.

A future JARVIS harness manifest could describe:

```yaml
harness:
  id: slideforge-production
  type: project_specific_functional_harness
  project: SlideForge
  entrypoints: list[string]
  inputs: list[string]
  outputs: list[string]
  permissions: list[string]
  approval_gates: list[string]
  evidence_contract: list[string]
  compatible_executors: list[string]
  status: active | reference | legacy | candidate | deprecated
```

This supports the earlier decision that existing harnesses are not deleted; they are registered, wrapped, refactored, or archived.

## What not to absorb immediately

Do not immediately:

- install Ouroboros into the default Hermes profile;
- let `ouroboros setup --runtime hermes` modify the active `~/.hermes/config.yaml` or skill tree;
- replace JARVIS routing with `ooo` commands;
- treat Ouroboros as the top-level JARVIS OS;
- move current JARVIS run state into Ouroboros' database;
- make Ouroboros `ralph` the default durable loop;
- add MCP servers to the production JARVIS profile without a sandbox smoke test.

## Sandbox experiment plan

If JARVIS tests Ouroboros directly, use an isolated experiment.

Preferred approach:

```text
1. Clone/read repo in a reference workspace.
2. Do not run install script against the default profile.
3. Use a sandbox HOME or dedicated Hermes profile.
4. Run minimal `ouroboros --help`, setup dry-run if available, or isolated setup.
5. Inspect all files it writes: ~/.ouroboros, profile config, skills, MCP entries.
6. Run a tiny interview/seed flow on a throwaway repo.
7. Record generated seed, events, status output, and cleanup path.
8. Decide which patterns to port JARVIS-native.
```

Safety gates:

- no default-profile install without explicit approval;
- no global config mutation without explicit approval;
- no push/deploy/delete/secrets;
- no paid or external provider calls unless explicitly approved;
- preserve current JARVIS routing policy during the experiment.

## Migration impact on existing harnesses

Ouroboros does not change the earlier JARVIS decision:

```text
Existing harnesses are not discarded.
They become ontology/manifest nodes that JARVIS can select, wrap, compare, or archive.
```

Ouroboros reinforces the need for:

- a clear task contract before execution;
- a ledger of what happened;
- explicit evaluation gates;
- runtime adapters;
- scoped workflow manifests.

It does not require replacing SlideForge, Producer/Reviewer loops, OMX, S1000D-RAG QA flows, cron/kanban, or other existing JARVIS harnesses.

## Updated JARVIS vNext priority after Ouroboros review

1. Create a JARVIS-native task contract schema.
2. Add a file-first run ledger with `events.jsonl`.
3. Add approval queue records with decision ids.
4. Add status view that summarizes runs, owners, blockers, approvals, and evidence.
5. Add decision-support router output that references executor and harness ontology nodes.
6. Define executor adapter output contracts.
7. Define harness manifest fields for existing system and functional harnesses.
8. Run Ouroboros only in sandbox/shadow mode before any production integration.

## Open questions

- Should JARVIS ambiguity scoring be numeric, categorical, or both?
- Should the first task contract be YAML-only or split across `request.md`, `task-contract.yaml`, and `plan.md`?
- Which existing JARVIS harness should be the first manifest pilot: Producer/Reviewer loop, SlideForge, or S1000D-RAG QA?
- What is the safest dedicated Hermes profile name for an Ouroboros sandbox test?
- Can Ouroboros' Hermes runtime adapter produce structured outputs useful to JARVIS without taking over the profile?

## See also

- [[concepts/jarvis-office-runtime-direction|JARVIS Office Runtime Direction]]
- [[concepts/jarvis-vnext-executor-ontology|JARVIS vNext Executor Ontology]]
- [[concepts/executor-routing|Executor Routing]]
- [[concepts/jarvis-control-plane|JARVIS Control Plane]]
- [[concepts/jarvis-open-source-strategy|JARVIS Open Source Strategy]]
