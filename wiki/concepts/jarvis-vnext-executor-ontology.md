---
title: JARVIS vNext Executor Ontology
created: 2026-06-05
updated: 2026-06-12
type: concept
concept_type: architecture
status: draft
tags: [jarvis, executor-routing, ontology, vnext, gajae-code, omx, lazycodex, opencode, codex]
sources: [conversation-2026-06-05, AGENTS.md, config/routing.yaml, harnesses/executor-router.md]
confidence: medium
relations:
  - type: extends
    target: executor-routing
  - type: supports
    target: jarvis-office-runtime-direction
  - type: references
    target: codex-cli
  - type: references
    target: omx
  - type: informed_by
    target: ouroboros-adoption-review
  - type: supports
    target: jarvis-open-source-strategy
---

# JARVIS vNext Executor Ontology

This note records the planned executor-pool direction for a future JARVIS vNext routing/ontology redesign. It is a design target, not an immediate change to the active runtime policy.

## Scope

Current JARVIS operation remains governed by `AGENTS.md`, `config/routing.yaml`, and `harnesses/executor-router.md`. At the time of writing, the live default implementation path is still the existing Codex/OMX line. The private JARVIS instance remains Hermes-first, while any future public core should be runtime-agnostic and express Hermes as an adapter.

The vNext design should add an ontology-backed executor pool and route tasks by executor attributes rather than by keyword-only rules. The Ouroboros review adds one important refinement: the ontology should also model Seed-like task contracts, harness manifests, evaluation gates, and event/ledger state, not only executor identities.

Role-terminology alignment: in the role terms adopted on 2026-06-10 (`Director`, `Runtime`, `Producer`, `Verifier` — see [[concepts/jarvis-vnext-meta-control-plane|JARVIS vNext Meta-Control-Plane Direction]]), the "executors" on this page are Producer- and/or Runtime-role backends, classified per Run rather than per tool. The single `executor:` field in the ontology schema below predates that decision; a future revision should split it into role fields (`runtime.backend`, `production.producer`, `verification.final_judge`) as recommended there. (Adversarial review 2026-06-12, F-B3)

## Design principle

JARVIS remains the Director. Executors are bounded Producers.

```text
User
  ↓
JARVIS Director
  - interpret intent
  - recover project context
  - select executor
  - define scope, forbidden actions, and acceptance criteria
  - manage approvals
  - verify diffs, tests, smoke checks, and evidence
  ↓
Executor Pool
  - implement or inspect within bounded scope
  - report changed files, commands, checks, risks, and evidence
```

Executor completion is never final completion. JARVIS must verify before reporting success.

## Planned coding executor pool

```text
1. gajae-code
2. omx-codex
3. lazycodex-codex
4. opencode
5. raw-codex
6. hermes-direct
```

Non-coding operating modes such as `hermes-background`, `cron`, and `kanban` remain part of the wider router, but this page focuses on implementation executors.

## Executor roles

### gajae-code

Planned role:

```text
future preferred default coding Producer
```

Classification:

```yaml
kind: standalone_workflow_coding_agent
engine: gjc
status: future_preferred_default
```

Rationale:

- Gajae-Code is a standalone coding agent, not a runtime injection into Codex, OpenCode, or Claude Code.
- Its workflow surface resembles the patterns JARVIS wants from a Producer: `deep-interview`, `ralplan`, `ultragoal`, optional `team`, tmux, worktree isolation, verification, and evidence summaries.
- It appears to generalize workflow lessons from OMX into an independent executor form, which is cleaner for a Director/executor architecture.

Best for:

- medium/large repo implementation;
- ambiguous requirements that need interview before mutation;
- plan-then-execute work;
- durable completion loops;
- evidence-heavy changes;
- tmux/worktree-backed long-running work;
- optional team execution when parallel workers materially help.

Safeguards:

- require JARVIS-generated task spec;
- no push/deploy/delete/secrets without approval;
- run in target repo or dedicated worktree;
- JARVIS re-verifies git status, diff, tests, smoke checks, and evidence.

### omx-codex

Planned role:

```text
Codex-specific fallback and legacy verified path
```

Classification:

```yaml
kind: codex_wrapper
engine: codex
status: future_fallback
```

Rationale:

- OMX is a workflow layer for OpenAI Codex CLI; Codex remains the execution engine.
- It is currently the verified practical path in the existing JARVIS setup.
- It should remain available when a task benefits from Codex-specific setup, hooks, plugin delivery, `omx exec`, `.omx/` artifacts, or existing OMX project state.

Best for:

- user explicitly requests OMX;
- GJC is unavailable or fails smoke testing;
- Codex-specific workflow or auth/session behavior is required;
- existing `.omx/` plans/logs/runtime state should be reused;
- migration fallback during the vNext transition.

### lazycodex-codex

Planned role:

```text
high-intensity Codex/OmO harness for complex codebases
```

Classification:

```yaml
kind: codex_harness_distribution
engine: codex_omo
status: future_high_intensity_candidate
```

Rationale:

- LazyCodex packages an OmO-style harness around Codex for project memory, planning, execution, and verified completion.
- It should be part of the executor pool, but not the default path until cost, license, complexity, and smoke-test behavior are understood.

Best for:

- very complex codebases;
- long-running verified-completion loops;
- project-memory-heavy work;
- multi-agent or multi-model orchestration experiments;
- tasks where GJC's normal workflow is insufficient and the extra overhead is justified.

Cautions:

- check license and operational constraints before production use;
- expect higher token/cost/complexity overhead;
- require explicit route reason and JARVIS verification;
- keep as specialized executor, not everyday default.

### opencode

Planned role:

```text
provider-agnostic alternate coding Producer
```

Classification:

```yaml
kind: standalone_coding_agent
engine: provider_agnostic
status: future_alternate
```

Best for:

- non-Codex model/provider paths;
- Codex/OpenAI line unavailable or undesirable;
- plan/build style coding sessions;
- comparative executor evaluation.

### raw-codex

Planned role:

```text
simple official Codex fallback
```

Classification:

```yaml
kind: standalone_coding_agent
engine: codex
status: future_simple_fallback
```

Best for:

- small, clear, one-shot repo-local tasks;
- wrapper overhead is unnecessary;
- direct Codex behavior is being tested or compared.

### hermes-direct

Planned role:

```text
small control-plane and quick verification mode
```

Classification:

```yaml
kind: internal_direct
engine: hermes
status: active_small_task_mode
```

Best for:

- JARVIS wiki/config/registry edits;
- quick git status/diff checks;
- small scripts;
- validation and final readback;
- tiny surgical changes expected to finish in roughly 1-2 minutes.

Do not let Hermes-direct drift into multi-file implementation loops.

## Draft routing rules

```text
Small JARVIS/control-plane task:
  hermes-direct

Default medium/large repo implementation:
  gajae-code

Ambiguous requirements:
  gajae-code deep-interview → ralplan

Durable implementation with evidence:
  gajae-code ultragoal

Parallelizable implementation:
  gajae-code team, or lazycodex-codex when high-intensity orchestration is justified

Codex-specific wrapper/setup/hook/artifact need:
  omx-codex

Very complex codebase + project memory + verified-completion loop:
  lazycodex-codex

Provider flexibility / non-OpenAI path:
  opencode

Small clear Codex one-shot:
  raw-codex
```

## Ontology fields

A future structured router should model at least these fields.

```yaml
executor:
  id: string
  kind: internal_direct | standalone_coding_agent | standalone_workflow_coding_agent | codex_wrapper | codex_harness_distribution
  engine: hermes | gjc | codex | codex_omo | opencode
  status: active | future_preferred_default | future_fallback | future_alternate | experimental | deprecated
  default_rank: integer
  strengths: list[string]
  route_when: list[condition]
  cautions: list[string]
  prerequisites: list[string]
  safeguards: list[string]
  verification_required: list[string]
```

Task records should expose matching fields.

```yaml
task:
  target_path: string
  project_id: string
  type: docs | config | implementation | refactor | test_fix | research | verification
  size: tiny | small | medium | large | very_large
  ambiguity: low | medium | high
  ambiguity_score: number | null
  risk: low | medium | high
  needs_plan: boolean
  needs_task_contract: boolean
  needs_evidence: boolean
  needs_worktree: boolean
  needs_parallelism: boolean
  needs_provider_flexibility: boolean
  requires_codex_specific_runtime: boolean
  approval_required: boolean
```

Ouroboros-inspired contract and harness records should also be modeled.

```yaml
task_contract:
  run_id: string
  objective: string
  target_project: string
  target_path: string
  success_criteria: list[string]
  constraints: list[string]
  forbidden_actions: list[string]
  approval_gates: list[string]
  evidence_required: list[string]
  route_recommendation: object
  jarvis_decision: object

harness:
  id: string
  kind: system_operating | executor | quality_gate | project_specific | functional | background | recurring
  status: active | reference | legacy | candidate | deprecated
  entrypoints: list[string]
  inputs: list[string]
  outputs: list[string]
  permissions: list[string]
  approval_gates: list[string]
  evidence_contract: list[string]
  compatible_executors: list[string]

evaluation_gate:
  id: string
  stage: mechanical | semantic | consensus
  checks: list[string]
  required_for: list[condition]
```

Existing harnesses should become ontology/manifest nodes. The goal is not to discard them, but to let JARVIS select, wrap, compare, refactor, or archive them with explicit status and evidence contracts.

## Migration plan

1. Keep current runtime policy unchanged.
2. Use the Ouroboros review as reference input, not as a production integration.
3. Add a JARVIS-native task contract schema and run-ledger event log before changing executor defaults.
4. Add GJC and LazyCodex to the vNext executor ontology as planned candidates.
5. Register existing system and functional harnesses as manifest/ontology nodes with `active`, `reference`, `legacy`, `candidate`, or `deprecated` status.
6. Create smoke tests for GJC, LazyCodex, OpenCode, OMX, raw Codex, and any Ouroboros sandbox adapter:
   - install/version check;
   - non-interactive or controlled-launch check;
   - worktree isolation check;
   - changed-file/evidence report quality;
   - exit status and log capture;
   - JARVIS verification ease;
   - config/skill/MCP side effects.
7. Run A/B evaluations on safe sample repos before changing defaults.
8. If GJC passes, promote it to default coding Producer in vNext router config.
9. Keep OMX as Codex-specific fallback until GJC has proven stable across real work.
10. Keep LazyCodex specialized for high-intensity complex-codebase runs.
11. Keep Ouroboros as sandbox/shadow-mode reference unless a specific adapter passes review.

## Non-goals

- Do not immediately edit the active routing policy to make GJC default.
- Do not remove OMX from the current system.
- Do not treat LazyCodex as default before license, cost, and operational checks.
- Do not let any executor bypass JARVIS approval and verification gates.
- Do not install Ouroboros into the default Hermes profile or let it become the top-level JARVIS OS without explicit approval and sandbox evidence.
- Do not design the public/open-source core as Hermes-only; keep host runtimes behind adapter interfaces.

## Open questions

- What exact GJC command shape should JARVIS use for non-interactive/background execution?
- Can GJC produce structured JSON summaries suitable for run ledgers?
- Which LazyCodex license and runtime constraints affect commercial/internal use?
- How should Reviewer selection avoid using the same model/runtime family as the Producer?
- What is the minimum smoke-test matrix required before changing the active default?
- Should JARVIS ambiguity scoring be numeric, categorical, or both?
- Which existing harness should be the first manifest pilot?
- Can an Ouroboros Hermes adapter be tested in a sandbox without mutating the default Hermes profile?
- What public project name avoids `JARVIS` trademark/name ambiguity while preserving the Agent Operations Control Plane positioning?
- Which APIs must be in the runtime adapter protocol so the public core can dogfood private Hermes-first JARVIS without depending on Hermes?

## See also

- [[concepts/executor-routing|Executor Routing]]
- [[concepts/jarvis-office-runtime-direction|JARVIS Office Runtime Direction]]
- [[concepts/jarvis-control-plane|JARVIS Control Plane]]
- [[concepts/ouroboros-adoption-review|Ouroboros Adoption Review for JARVIS vNext]]
- [[concepts/jarvis-open-source-strategy|JARVIS Open Source Strategy]]
- [[entities/codex-cli|Codex CLI]]
- [[entities/omx|OMX]]
