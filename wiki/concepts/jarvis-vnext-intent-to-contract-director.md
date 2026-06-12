---
title: JARVIS vNext Intent-to-Contract Director
created: 2026-06-11
updated: 2026-06-12
type: concept
concept_type: architecture
status: draft
tags: [jarvis, vnext, agent-ops, control-plane, executor-routing, automation, verification]
sources: [conversation-2026-06-11]
confidence: high
relations:
  - type: extends
    target: concepts/jarvis-vnext-meta-control-plane
  - type: supports
    target: concepts/jarvis-office-runtime-direction
  - type: relates_to
    target: concepts/jarvis-vnext-executor-ontology
  - type: references
    target: projects/jarvis/decisions
---

# JARVIS vNext Intent-to-Contract Director

## Summary

The current vNext direction narrows JARVIS from a broad agent orchestrator into a specialized Agent Operations Director.

JARVIS should not try to out-code or out-orchestrate backend-native systems such as Claude Code, Codex, Cursor Cloud Agents, Devin, OpenHands, OMX, or Gajae-Code. Those backends increasingly combine runtime and producer roles: planning, subagents, background work, worktrees, testing, repair loops, and PR preparation.

JARVIS's durable value is therefore the layer before and after backend execution:

```text
User vague intent
  -> JARVIS intent/context/policy compiler
  -> backend-native optimized task contract
  -> strong backend-native execution
  -> JARVIS evidence-backed verification and judgment
  -> user-facing decision report
```

Short form:

> JARVIS is the system that turns poor or incomplete user requirements into high-quality backend-native work contracts, then verifies whether the delivered result actually satisfies the contract and the user's implicit intent.

## Why the scope should narrow

Recent Claude Code, Codex, Cursor, Devin, and OpenHands-style systems show a clear trend: single strong backends increasingly include their own native orchestration.

Backend-native capabilities now commonly include:

- codebase exploration;
- planning and task decomposition;
- background or cloud execution;
- subagents or parallel threads;
- worktree or isolated environment handling;
- test/fix/self-repair loops;
- PR/review workflows;
- hooks, skills, MCP, or similar extension surfaces.

Therefore, these are no longer strong JARVIS differentiators by themselves:

- running agents in the background;
- parallelizing multiple coding agents;
- wrapping sessions in a dashboard;
- creating worktrees;
- queueing tasks;
- relaying PR/CI automation;
- acting as another generic orchestrator.

JARVIS should still support those functions through adapters and runtime metadata, but they should not be the core product identity.

## New default workflow

The default workflow should be short:

```text
1. Understand
   JARVIS interprets the user's request with project memory, wiki, repo state, policies, and prior decisions.

2. Contract
   JARVIS converts the interpreted request into an explicit task contract.

3. Delegate
   JARVIS sends the contract to a selected backend-native system through an adapter.

4. Verify
   JARVIS checks the backend result against explicit QA plus implicit user/project constraints.

5. Report
   JARVIS returns PASS / REQUEST_CHANGES / APPROVAL_REQUIRED / ESCALATE / ABORT with evidence and next actions.
```

Simplified:

```text
Understand -> Contract -> Delegate -> Verify -> Report
```

This replaces the heavier default assumption:

```text
JARVIS -> separate orchestrator -> executor -> reviewer -> revision loop -> verifier
```

That heavier flow remains available, but only when risk, ambiguity, quality sensitivity, or cross-backend comparison justifies it.

## Core role: Intent-to-Contract compiler

The most important JARVIS role is requirement normalization.

Users usually provide incomplete requirements:

```text
"이거 좀 고쳐줘"
"어제 하던 거 이어서 해줘"
"품질 좀 올려줘"
"더 고급스럽게 만들어줘"
"끝까지 해줘"
```

Backend-native agents need precise contracts:

```yaml
task_contract:
  objective: clear target outcome
  context: project/user background JARVIS recovered
  target: repo, path, module, artifact, or service
  assumptions: defaults JARVIS is applying
  scope:
    include: []
    exclude: []
  constraints: project rules and architecture constraints
  forbidden_actions: actions the backend must not take
  acceptance_criteria: explicit completion criteria
  qa_checklist: checks the backend should self-run before reporting
  verification_commands: commands or smoke checks expected where feasible
  approval_gates: actions requiring user approval
  escalation_conditions: when the backend should stop and return control
  report_format: required changed files, commands, evidence, risks, and open questions
```

The contract is not merely a prompt. It is the operational boundary between user intent, JARVIS policy, and backend-native execution.

### Contract field grading and thickness profiles

Not every contract field is equally mandatory. Grade fields to avoid over-specification:

```yaml
contract_field_grades:
  must: [objective, forbidden_actions, acceptance_criteria, approval_gates]
  should: [scope, qa_checklist, verification_commands, report_format]
  optional: [assumptions, context_notes, style_preferences]
```

Contract thickness should adapt to backend strength: strong backends get thinner, objective-centric contracts plus a strict final judgment; weaker or unfamiliar backends get thicker contracts.

Counter-position note: OpenAI Symphony explicitly bets on "objectives instead of strict transitions". The JARVIS answer is that objectives without a contract-derived final judgment regress to human review of every result; the must-grade fields exist precisely to keep the final judgment mechanical. (Adversarial review 2026-06-12, F-C2)

## Instruction layer vs enforcement layer

A key vNext design correction is that Markdown instructions are not enough. Files such as `AGENTS.md`, `CLAUDE.md`, skills, wiki notes, and runbooks are valuable instruction context, but they are still interpreted by a model. They can be skipped, forgotten, summarized away, or followed inconsistently.

JARVIS should distinguish four layers:

```text
Instruction layer
  - AGENTS.md, CLAUDE.md, skills, wiki, runbooks
  - tells the model what it should do

Contract layer
  - task-contract.yaml, route record, acceptance criteria
  - makes scope, forbidden actions, QA, evidence, budget, and escalation explicit

Executable enforcement layer
  - permissions, hooks, sandbox, command/path policy, approval gates
  - prevents or blocks actions the backend must not take

Evidence/judgment layer
  - git diff, tests, logs, artifacts, reviewer verdict, JARVIS final decision
  - verifies what actually happened before reporting completion
```

Design principle:

> Markdown says what should happen. Executable guardrails define what cannot happen. Evidence gates decide whether the work is allowed to count as complete.

The task contract should therefore contain machine-checkable policy fields, not only prose instructions:

```yaml
task_contract:
  allowed_paths: []
  denied_paths:
    - "**/.env"
    - "**/auth.json"
    - "**/*key*"
  denied_commands:
    - "rm -rf"
    - "git reset --hard"
    - "git clean -f"
    - "git push"
  approval_gates:
    - sudo
    - deploy
    - paid_api
    - broad_delete
    - secrets_or_auth_files
  required_evidence:
    - git_status
    - git_diff
    - verification_logs
    - changed_files
  completion_gates:
    require_scope_check: true
    require_secret_check: true
    require_verification_attempt: true
    require_jarvis_final_judgment: true
```

Backend adapters should translate these fields into the strongest available native enforcement mechanism. For Claude Code this may include permissions, hooks, sandboxed Bash, and managed settings where available. For Codex/OMX/Gajae-style backends this may be implemented through wrapper policy, preflight checks, post-run diff checks, command allow/deny rules, and JARVIS completion gates.

Enforcement strength varies per field and per backend, and the gap must not be silent:

```yaml
guardrail_enforcement:
  enforcement_level_per_field: native | wrapper | post_hoc
  escalation_rule: any field below native is automatically added to completion_gates post-hoc checks
  adapter_duty: inject explicit denies for unsafe backend defaults (e.g. credential reads allowed by default); never assume backend defaults are safe
```

Known gaps (verified 2026-06-12): Codex cannot deny writes to individual files inside the workspace (e.g. `**/.env`) and lacks per-path read-deny; its rules engine is marked experimental. Completion gates are not natively enforceable on any backend — they remain a Director-side check. (Adversarial review 2026-06-12, F-A3)

## Harness engineering and loop engineering

JARVIS should explicitly model harnesses and loops as different layers.

Definitions:

```text
Harness engineering
  = designing the wrapper that helps an AI perform a task reliably:
    instructions, context, tools, environment, permissions, sandbox,
    output schema, validation criteria, logging, and evidence capture.

Loop engineering
  = designing a closed automation cycle where AI observes, judges,
    acts, verifies, repairs, and repeats until a stop condition is met.
```

Relationship:

```text
Harness = makes one unit of AI work safer, clearer, and more reproducible.
Loop    = repeats one or more harnessed work units until the target state is reached.
JARVIS  = sits above the loops: selects/designs the loop, binds harnesses,
          sets guardrails, controls budget/risk, verifies evidence, and decides stop/pass/escalate.
```

A loop may contain multiple harnesses:

```text
Test-fix loop
  -> diagnosis harness
  -> implementation harness
  -> test harness
  -> review harness
  -> report harness
```

This distinction prevents JARVIS from collapsing into either a prompt library or a generic automation runner. Harnesses make backend work more reliable. Loops create autonomous progress. JARVIS governs which harnesses and loops are appropriate for the user's intent, project state, risk, backend capability, and available evidence.

Example JARVIS loop contract:

```yaml
loop_contract:
  goal: make test suite pass without broad rewrite
  observe:
    - run_tests
    - inspect_failures
  decide:
    - classify_failure
    - choose_next_fix
  act:
    harness: implementation_harness
    allowed_paths: []
  verify:
    harness: test_harness
    commands: []
  repair:
    max_iterations: 5
    stop_if_same_failure_repeats: 2
  stop_conditions:
    success:
      - tests_pass
      - diff_scope_ok
    escalate:
      - approval_required
      - max_iterations_reached
      - architecture_change_needed
```

The key design rule is:

> Loop engineering is an execution pattern JARVIS can use. JARVIS itself is the higher-level Director/Governor that decides whether to run a loop, how to harness it, when to stop it, and whether to trust its result.

## Dynamic workflows and backend-native deep workflow modes

Claude Code `ultracode` / Dynamic workflows are useful references, but they should be modeled precisely.

They do not make Markdown instructions physically impossible to ignore. Instead, they move parts of the work procedure into a backend runtime workflow: phases, loops, branching, subagent spawning, result gathering, and independent verification can be executed by a script/runtime rather than remembered only as prose instructions.

JARVIS should capture this as a backend capability:

```yaml
backend_capabilities:
  native_features:
    deep_workflow: true
    workflow_script: true
    subagents: true
    independent_verification: true
  enforcement_features:
    permissions: true
    pre_tool_hooks: true
    sandbox: true
    managed_settings: optional
```

Use this distinction:

```text
Dynamic workflow = stronger control-flow execution
Executable guardrails = stronger policy enforcement
JARVIS verification = final completion judgment
```

JARVIS should call backend-native deep workflow modes only when the task benefits from broad exploration, independent checks, high-risk review, or many parallelizable subtasks. Routine work should not default to high-cost deep workflow mode.

## Ambiguity handling

JARVIS should not interview the user for every request. It should use accumulated knowledge to infer safe defaults whenever possible.

Rule:

```text
If clear: infer and contract.
If unclear but low-impact: use an explicit default and contract.
If unclear and high-impact: ask a focused question before contracting.
If safety/cost/authority is involved: request approval before execution.
```

Questions are required when ambiguity affects:

- product direction;
- subjective design/tone/quality expectations;
- architecture boundaries;
- model/provider/cost selection;
- security, secrets, data retention, deploy, push, delete, installs, or paid actions;
- broad rewrites or irreversible changes.

For most implementation tasks, JARVIS should produce a contract from context and proceed with the appropriate backend.

## Backend-native adapters

Backends should be pluggable through adapters, but JARVIS should avoid over-normalizing them.

Common lifecycle:

```text
describe_capabilities -> prepare_contract -> launch_run -> get_status -> collect_result -> cancel_run
```

Each adapter should expose:

```yaml
backend_capabilities:
  roles: [runtime, producer, partial_verifier]
  native_features:
    planning: true
    subagents: true
    background: true
    worktree: true
    self_check: true
    pr_workflow: false
  constraints:
    data_retention: optional note
    cost_profile: optional note
    network_policy: optional note
    auth_requirements: optional note
```

Adapter responsibilities:

- translate the JARVIS contract into the backend's best native prompt/API/task format;
- launch work using the backend's native mode where appropriate;
- preserve backend-specific strengths rather than flattening everything into a generic `run(prompt)`;
- map backend state to standard JARVIS states;
- collect logs, self-report, diff, artifacts, test output, warnings, and cost/model metadata where available.

JARVIS core should own policy and judgment. Adapters should own backend mechanics.

## Workflow levels

Use workflow levels to keep the default path short and escalate only when necessary.

### Level 0 — JARVIS direct

```text
JARVIS -> direct edit/check -> JARVIS report
```

Use for small docs, status checks, simple config edits, and quick verification.

### Level 1 — Single backend

```text
JARVIS -> one backend -> JARVIS verify
```

Use for clear single-repo tasks with bounded scope and reasonable tests.

### Level 2 — Single backend with native orchestration

```text
JARVIS -> Claude Code/Codex/Cursor/OpenHands native runtime -> JARVIS verify
```

Use when the selected backend can internally plan, use subagents, run in the background, isolate worktrees, and self-check. This should become the default for many medium implementation tasks.

### Level 2 deep variant — single backend deep workflow mode

This is not a separate routing level. It is Level 2 with the deep workflow capability engaged, selected by `backend_capabilities.native_features.deep_workflow` plus `workflow_constraints.allow_deep_workflow` rather than by a distinct level number. (Adversarial review 2026-06-12, F-A5)

```text
JARVIS contract + guardrails
  -> backend-native deep workflow mode
  -> backend subagents / workflow script / independent checks
  -> JARVIS evidence verification and final judgment
```

Use when one strong backend has a native high-intensity workflow mode and the task justifies the overhead. Claude Code `ultracode` / Dynamic workflows are the reference example: the backend can script phases, spawn subagents, gather intermediate results, and run verifier-style work inside its own runtime.

This level should require explicit budget and guardrail fields:

```yaml
workflow_constraints:
  allow_deep_workflow: true
  require_plan_before_execution: true
  max_subagents: 8
  max_concurrent_agents: 4
  max_runtime_minutes: 60
  require_independent_verification: true
  store_intermediate_results: true
  stop_on_permission_prompt: true
```

Avoid the deep workflow variant for narrow edits, simple docs/config changes, unclear scope, low budget, or any task where executable guardrails cannot be mapped to the selected backend.

### Level 3 — Multi-backend arbitration

```text
JARVIS
  -> Backend A
  -> Backend B
  -> optional Backend C
  -> JARVIS compare / select / reject
```

Use when quality, risk, uncertainty, or multiple viable approaches justify comparing results. The value is not parallel execution itself, but arbitration: choosing which result to trust.

### Level 4 — Managed program

```text
JARVIS -> kanban/cron/queue/program runtime -> many runs -> JARVIS governance
```

Use for long-running project programs, recurring monitoring, multi-issue backlogs, release trains, or durable QA loops.

## QA and verification model

The task contract's QA checklist is used twice.

### Backend self-QA

The backend uses the contract QA checklist during its own producer loop:

```text
implement -> check QA -> fix -> recheck -> self-report
```

This is useful and should be encouraged, especially as backend-native agents become stronger.

### JARVIS final verification

Backend self-QA is not final completion. JARVIS must independently verify:

- whether explicit QA items were actually satisfied;
- whether reported tests/logs/artifacts exist and are credible;
- whether changed files stayed within scope;
- whether forbidden actions were avoided;
- whether user approval is still required;
- whether the output satisfies the user's implicit intent and project context;
- whether QA-list gaps reveal additional problems.

Final judgment is two-stage, and the distinction must stay explicit:

1. Mechanical gate — deterministic, code-enforced necessary conditions: diff scope check, secret diff check, verification-log existence, forbidden-command traces. A run is never reported complete without passing these, because JARVIS's own judgment is also model judgment and must not be the only floor.
2. Director judgment — model-based evaluation (architecture drift, intent fit, taste), allowed only after the mechanical gate passes.

Backend self-verification — including cross-agent adversarial review inside backend-native workflows (e.g. Claude Code dynamic workflows) — is evidence, not judgment: it shares the vendor and session permission boundary, and it does not evaluate against the compiled contract. JARVIS judgment is defined by two properties: contract-derived criteria and separation of interest from the producer. Track backend self-verification capability explicitly:

```yaml
backend_capabilities:
  self_verification: none | self_check | cross_agent_review
```

(Adversarial review 2026-06-12, F-A2/F-A4)

JARVIS may reject a backend result even if all explicit QA items appear green, when Director judgment finds issues such as:

- architecture drift;
- brittle or hardcoded implementation;
- excessive scope creep;
- design/tone mismatch;
- missing evidence;
- security or privacy concerns;
- conflict with durable project decisions.

## Fable 5 and high-end model implications

High-end backend-native models such as Claude Fable 5 strengthen this direction.

Implication:

```text
More delegation to strong backends.
Less middle orchestration by JARVIS.
More contract, policy, data/cost governance, verification, and arbitration.
```

JARVIS should explicitly track model/backend policy when relevant:

```yaml
model_policy:
  requested_model: claude-fable-5
  actual_model: unknown | claude-fable-5 | fallback_model
  data_retention_allowed: true | false
  sensitive_data_allowed: true | false
  max_cost: optional
  fallback_or_refusal_handling_required: true
```

Model strength does not eliminate the need for JARVIS. It increases the importance of good contracts and trustworthy verification because a stronger backend can do more work, faster, in the wrong direction if the contract is poor.

## Revised JARVIS identity

Avoid:

> JARVIS is a better coding agent orchestrator.

Prefer:

> JARVIS is an Agent Operations Director that compiles vague user goals into backend-native work contracts and renders a final judgment that is derived from that contract and independent of the producer. The differentiation is not the compiler alone — intent-to-spec compilation is already commoditized (AWS Kiro, GitHub Spec Kit, backend plan modes) — but the closed loop: compile → delegate → contract-derived, interest-separated judgment.

Korean short form:

> JARVIS는 부실한 요구사항을 계약으로 컴파일하는 것에 그치지 않고, 그 계약에서 파생된 기준으로 실행 주체와 이해관계가 분리된 최종 판정까지 닫는 폐루프 시스템이다. 컴파일러 단독은 이미 상품화되었다. (적대적 검토 2026-06-12, F-A1)

## MVP implications

The MVP should prioritize (canonical vNext MVP priority list; the meta-control-plane page orders only the operational subset):

1. task contract schema;
2. executable guardrail schema for allowed paths, denied paths, denied commands, approval gates, and required evidence;
3. harness schema for instructions, context, tool/environment setup, permissions, output format, validation, and evidence capture;
4. loop contract schema for observe/decide/act/verify/repair cycles, iteration limits, and stop conditions;
5. backend capability schema, including native deep workflow support and native enforcement mechanisms;
6. backend result schema;
7. workflow-level router;
8. evidence-backed verification report;
9. adapter interface for Hermes-direct, Codex CLI, Claude Code, and existing OMX/Gajae path;
10. later multi-backend arbitration.
11. contract quality feedback loop: the run ledger links each contract to outcomes (REQUEST_CHANGES rate, rework count, scope violations, judgment reversals) with failure causes classified as contract_defect | execution_defect | verification_defect. (Adversarial review 2026-06-12, F-C1)

The MVP should defer or minimize:

- custom multi-agent scheduler;
- full dashboard;
- broad PR/CI automation platform;
- cloud agent platform;
- deep queue/kanban mechanics unless a project program requires them.

## Agent implementation brief

When an implementation agent builds JARVIS vNext from a new environment, it should treat this document as architecture constraints and a task-contract source, not as a step-by-step human build manual.

The implementation agent should preserve these invariants:

```yaml
must_preserve:
  - JARVIS is the Director/Governor above backend agents, harnesses, and loops.
  - User intent is normalized into explicit task contracts before substantial execution.
  - Harnesses and loops are first-class concepts but remain subordinate to JARVIS judgment.
  - Markdown instructions are guidance, not deterministic enforcement.
  - Executable guardrails and evidence gates are required for trustworthy completion.
  - Backend adapters should preserve backend-native strengths rather than flattening every tool into a generic prompt runner.
  - Backend self-reports are evidence, not final completion.
  - JARVIS makes the final PASS / REQUEST_CHANGES / APPROVAL_REQUIRED / ESCALATE / ABORT decision.
```

The first implementation artifacts should be minimal and contract-shaped:

```yaml
first_artifacts:
  - task-contract schema
  - executable guardrail schema
  - harness manifest schema
  - loop contract schema
  - backend capability schema
  - backend result schema
  - run ledger schema
  - simple route/contract CLI or API entrypoint
  - local/direct backend adapter
  - evidence verification report
  - small test fixtures for routing, guardrails, and completion judgment
```

The implementation agent should avoid these early traps:

```yaml
non_goals:
  - do not build a new coding agent as the MVP
  - do not build a generic multi-agent dashboard first
  - do not make multi-backend arbitration the default path
  - do not make Hermes a hard dependency in a portable/public core
  - do not treat AGENTS.md, CLAUDE.md, skills, or wiki prose as enforcement
  - do not skip JARVIS final verification just because a backend reports success
  - do not over-specify a build manual that prevents backend-native agents from using their own planning, subagents, repair loops, or workflow modes
```

A suitable greenfield prompt to a coding agent should therefore ask it to design and implement the smallest working skeleton that satisfies these contracts, then verify it with schema tests, routing fixtures, guardrail examples, and an evidence-backed sample run.

## Open design questions

1. What is the exact minimal `task-contract.yaml` schema?
2. What is the minimal `backend-result.json` schema that supports comparison?
3. Which backend adapter should be implemented first after Hermes-direct: Codex CLI or Claude Code?
4. How should JARVIS record model/data-retention/cost policy without leaking sensitive data?
5. When should Level 3 multi-backend arbitration be worth the cost?
6. How should contract quality itself be evaluated over time?
7. What is the minimal reusable harness manifest schema?
8. What loop types should be first-class in vNext: test-fix, review-revision, research-verify, migration, monitor, or release?
