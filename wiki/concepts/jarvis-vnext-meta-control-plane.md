---
title: JARVIS vNext Meta-Control-Plane Direction
created: 2026-06-10
updated: 2026-06-12
type: concept
concept_type: architecture
status: draft
tags:
  - jarvis
  - vnext
  - agent-ops
  - control-plane
  - executor-routing
sources: [conversation-2026-06-10, conversation-2026-06-11]
confidence: high
relations:
  - type: relates_to
    target: wiki/concepts/jarvis-office-runtime-direction.md
  - type: relates_to
    target: wiki/concepts/jarvis-vnext-executor-ontology.md
  - type: relates_to
    target: wiki/concepts/jarvis-vnext-intent-to-contract-director.md
  - type: relates_to
    target: wiki/projects/jarvis/decisions.md
---

# JARVIS vNext Meta-Control-Plane Direction

## Conversation context

On 2026-06-10, we reviewed whether JARVIS vNext is still justified when modern coding agents already have strong goal/plan modes and when GitHub already has many agent orchestrators.

The conclusion was not that JARVIS should compete head-on as another coding agent or another multi-agent runner. The direction should narrow: JARVIS vNext should be the project-operations Director layer above coding agents and orchestrators.

## Key conclusion

JARVIS vNext should be positioned as:

> A conversational AI project-operations Director that uses existing coding agents and orchestrators as execution backends, while JARVIS owns long-term project memory, routing judgment, risk/approval governance, task contracts, evidence-backed completion, and next-action decisions.

Short form:

> JARVIS is not an agent runner. JARVIS is the Director over agents and orchestrators.

## Why the plan needs sharpening

Modern goal-mode coding agents can already complete many single-repository implementation tasks if given a good design document.

GitHub also already contains several projects that overlap with generic orchestration:

- AgentWrapper / agent-orchestrator: parallel coding agents, worktrees, CI fixes, review comments, PRs, dashboard.
- Golutra: Claude Code, Codex CLI, OpenCode orchestration, parallel execution, long-running workflows, memory layer.
- CodeMachine-CLI: repeatable long-running workflows for coding CLIs, context passing, multi-agent orchestration.
- Agor: team command center, sessions, tasks, boards, branches, repos, memory/skills, multiple agent runtimes.
- Optio: self-hosted AI engineering platform, task-to-PR pipeline, logs, CI/review/merge/cost tracking.
- Overstory, Codex Mate, aiagentflow, c9r orchestrator: additional examples of multi-agent coding/workflow control planes.

Therefore these are weak differentiators for JARVIS:

- building another coding agent;
- building a generic multi-agent runner;
- building a simple workflow YAML engine;
- building a dashboard for Claude/Codex/OpenCode sessions;
- claiming “we route coding agents” as the core uniqueness.

## Stronger direction

JARVIS should focus on the layer that decides and governs work rather than reproducing execution mechanics.

JARVIS owns:

- interpreting user intent across projects and sessions;
- deciding whether the request is coding, research, validation, documentation, approval, or project-operations work;
- deciding what should be done next in the project, not only decomposing a provided task;
- selecting the executor or external orchestrator and recording why;
- defining automation limits and approval gates;
- producing executor task contracts with allowed paths, forbidden actions, acceptance criteria, tests, evidence requirements, and escalation conditions;
- turning policy prose into executable guardrails where possible: permissions, hooks, sandbox boundaries, command/path deny rules, and completion gates;
- selecting backend-native deep workflow modes, such as Claude Code ultracode / Dynamic workflows, only when their control-flow orchestration is worth the cost;
- designing or selecting the appropriate harness and loop pattern when autonomous iteration is useful;
- collecting execution results and independently verifying them;
- distinguishing executor self-report from JARVIS completion judgment;
- updating project status/wiki/run ledger;
- learning from executor failures, risks, and repeated review findings;
- surfacing only the decisions that genuinely need the user.

Existing agents/orchestrators own:

- process spawning;
- worktree isolation;
- parallel agent execution;
- agent-to-agent decomposition;
- CI auto-fix loops;
- PR creation;
- workflow execution;
- log streaming and dashboards;
- low-level session management.

## How to use existing orchestrators

Treat existing orchestrators as executor backends, not competitors.

Flow:

1. User gives a natural-language goal.
2. JARVIS recovers project state, wiki/status, run history, and safety policy.
3. JARVIS classifies the task and decides whether execution is needed.
4. JARVIS selects a backend: Hermes-direct, Codex, OMX/Gajae-Code, Claude Code, AgentWrapper, CodeMachine, Golutra, Agor, Optio, cron, kanban, etc.
5. JARVIS writes a task contract for that backend.
6. The backend executes.
7. JARVIS collects logs, diff, test results, PR links, artifacts, and reviewer output.
8. JARVIS verifies evidence and returns PASS / REQUEST_CHANGES / APPROVAL_REQUIRED / ESCALATE / ABORT.
9. JARVIS records the run and updates project operations memory.

Principle:

> Existing orchestrators are JARVIS's hands. JARVIS remains the head: judgment, approval, verification, memory, and next-step selection.

## Role terminology: Director, Runtime, Producer, Verifier

The earlier shorthand `JARVIS → orchestrator → executor` is directionally useful, but it becomes ambiguous because modern AI coding tools often combine planning, execution, looping, and verification in one product.

JARVIS vNext should therefore classify tools by the role they play in a specific Run, not by the tool name alone.

Preferred terms:

```text
Director = JARVIS
Runtime = execution operations layer
Producer = actual artifact-producing worker
Verifier = independent checks, tests, review, and evidence evaluation
```

### Director

The Director is the final owner of intent interpretation, scope, routing, approval, verification judgment, memory, and next action. In the private JARVIS system this is Hermes/JARVIS.

Responsibilities:

- interpret the user request;
- recover project context from wiki, registry, sessions, git state, and files;
- define objective, scope, constraints, and acceptance criteria;
- decide automation limits and approval gates;
- select the Runtime and Producer strategy;
- create or approve the task contract;
- interpret Producer/Reviewer results;
- make the final `PASS`, `REQUEST_CHANGES`, `APPROVAL_REQUIRED`, `ESCALATE`, or `ABORT` judgment.

### Runtime

The Runtime is the operational layer that makes a Run happen. It may be a very thin JARVIS-native CLI/runtime or a richer external orchestrator.

Responsibilities:

- create run ids and run folders;
- store `request.md`, `route.json`, `task-contract.yaml`, `events.jsonl`, logs, evidence, and reports;
- launch Producers and Reviewers;
- manage process/session/worktree/tmux/background execution where applicable;
- support retries, loops, queues, status, cancellation, and approval records;
- collect outputs without becoming the final judge.

Runtime types include:

```text
- direct/no-runtime
- jarvis-thin-runtime
- workflow-wrapper, such as OMX
- compound coding runtime, such as Gajae-Code
- multi-agent orchestrator, such as AgentWrapper, CodeMachine, or Golutra
- scheduler, such as cron or GitHub Actions
- kanban/worker queue
- project-specific harness runtime
- app-level workflow engine, such as LangGraph or Airflow, when the Run is inside an application project
```

### Producer

The Producer is the worker that directly creates or mutates the artifact.

Responsibilities:

- edit code;
- write tests or docs;
- generate slides, images, reports, or other assets;
- run implementation commands;
- produce artifacts and a self-report.

Examples include Codex, Claude Code, OpenCode, Gajae-Code in a producer role, Hermes direct edits, scripts, ComfyUI for image assets, or project-specific generators.

### Verifier

The Verifier checks whether the artifact satisfies the original task contract. It may be deterministic tooling, an independent Reviewer agent, JARVIS direct inspection, or a combination.

Responsibilities:

- inspect git status and diff;
- run tests, lint, build, smoke checks, or browser/API checks;
- compare output with acceptance criteria;
- check scope, secrets, safety, and artifact freshness;
- return evidence and a verdict for JARVIS to interpret.

Verifier output is evidence, not the final user-facing completion judgment. JARVIS remains the final judge.

### Role-based classification rule

A tool is not permanently an orchestrator or executor. Classify it by what it does in the current Run:

```text
If it directly changes files/artifacts, it is acting as a Producer.
If it launches/manages/loops/queues other workers, it is acting as a Runtime.
If it independently checks the result, it is acting as a Verifier.
If it decides intent, risk, approvals, route, and final completion, it is acting as Director.
```

The same tool can appear in multiple roles. For example:

```yaml
run:
  director: jarvis
  runtime:
    backend: omx
    responsibilities: [launch, loop, log, manage-codex-session]
  producer:
    backend: codex
    responsibilities: [edit-code, run-tests, report]
  verifier:
    backend: jarvis
    responsibilities: [git-diff, tests, scope-check, final-verdict]
```

For a compound tool such as Gajae-Code:

```yaml
run:
  director: jarvis
  runtime:
    backend: gajae-code
    responsibilities: [interview, plan, execute-loop, log]
  producer:
    backend: gajae-code
    responsibilities: [edit-code, run-tests, report]
  verifier:
    backend: jarvis
    responsibilities: [independent-check, final-verdict]
```

For a multi-agent orchestrator:

```yaml
run:
  director: jarvis
  runtime:
    backend: agentwrapper
    responsibilities: [split-tasks, spawn-workers, manage-worktrees, collect-results]
  producers:
    - backend: codex
    - backend: claude-code
    - backend: opencode
  verifier:
    backend: jarvis
```

### Recommended schema wording

Avoid a single overloaded field such as:

```yaml
executor: omx
```

Prefer explicit role fields:

```yaml
route:
  director: jarvis
  runtime:
    mode: workflow-wrapper
    backend: omx
  production:
    producer: codex
    role: code-producer
  verification:
    mode: git-diff-tests-smoke
    final_judge: jarvis
```

This preserves the key JARVIS distinction: Runtime and Producer can report completion, but JARVIS decides whether the Run is actually complete.

## Harness and loop model

JARVIS vNext should treat harness engineering and loop engineering as first-class concepts, but not as the same layer.

```text
Harness engineering
  -> wraps AI work with instructions, context, tools, environment,
     permissions, sandbox, output schema, validation, and evidence capture.

Loop engineering
  -> closes the cycle around AI work: observe, judge, act, verify,
     repair, and repeat until a success, failure, or escalation condition.

JARVIS Director/Governor
  -> decides which loop is needed, which harnesses to bind into it,
     what guardrails apply, what budget/risk limits exist, when to stop,
     and whether the evidence is trustworthy enough to report completion.
```

Therefore JARVIS is above loop engineering, not merely an implementation of it. Loop engineering is one execution pattern available to JARVIS. JARVIS adds cross-project intent recovery, route selection, approval governance, memory, evidence arbitration, and next-action judgment.

Canonical layered view:

```text
User Intent
  -> JARVIS Director
  -> Task Contract
  -> Harness + Guardrails
  -> Backend / Loop Runtime
  -> Evidence
  -> JARVIS Final Judgment
```

A loop can contain multiple harnesses. For example, a test-fix loop may contain a diagnosis harness, implementation harness, test harness, reviewer harness, and reporting harness. JARVIS should record which harnesses and loop type were used so later routing can learn which patterns worked.

## Policy enforcement model

A vNext Director cannot rely only on Markdown instruction files. `AGENTS.md`, `CLAUDE.md`, skills, wiki pages, and runbooks are necessary context, but they are not deterministic controls. They tell a model what it should do; they do not physically prevent a backend from taking a forbidden action.

JARVIS should therefore treat policy as an executable contract:

```text
Instruction context
  -> task contract
  -> adapter-enforced guardrails
  -> evidence collection
  -> JARVIS final judgment
```

Examples:

```yaml
guardrails:
  allowed_paths:
    - /home/hskim/projects/<project>/**
  denied_paths:
    - "**/.env"
    - "**/auth.json"
    - "**/*key*"
  denied_commands:
    - "rm -rf"
    - "git reset --hard"
    - "git clean -f"
    - "git push"
  approval_required:
    - sudo
    - deploy
    - broad_delete
    - secrets_or_auth_files
  completion_gates:
    - git_status_checked
    - diff_scope_checked
    - verification_attempted
    - secret_diff_checked
```

Backend adapters should map these to native mechanisms when available. Claude Code may support stronger native mapping through permissions, hooks, sandboxed Bash, and managed settings; other backends may require wrapper-side checks, command filters, isolated worktrees, post-run diff checks, and JARVIS refusal to mark completion.

Dynamic workflows should be modeled separately from guardrails. They can force more of the control flow into a workflow runtime — phases, loops, branching, subagent fanout, result aggregation, and verifier passes — but they are not the same as permission enforcement. The design target is both: workflow control flow for complex work, and executable guardrails for safety/policy.

## Integration levels

Initial vNext should not overbuild deep integrations.

1. Manual / prompt adapter
   - JARVIS generates a backend-specific task contract.
   - The user or Hermes passes it to the chosen tool.
   - Results are brought back for JARVIS verification.

2. CLI adapter
   - JARVIS invokes a backend CLI and records command, run id, stdout/log path, and artifacts.

3. API / daemon adapter
   - JARVIS creates tasks and polls status through a backend API when available.

4. Native ledger integration
   - External runs appear as first-class JARVIS runs with evidence, decisions, gates, and next actions.

The MVP should start with levels 1-2.

## Revised MVP priority

After the 2026-06-11 intent-to-contract discussion, the MVP should prioritize the shorter backend-native flow described in [[concepts/jarvis-vnext-intent-to-contract-director|JARVIS vNext Intent-to-Contract Director]]: JARVIS contracts and verifies, while strong backend-native systems handle more of their own planning, background execution, subagents, and self-repair.

The canonical MVP priority list lives in [[concepts/jarvis-vnext-intent-to-contract-director|JARVIS vNext Intent-to-Contract Director]] (schemas-first, 11 items). The high-priority items below are the operational/runtime subset of that list and do not replace it. (Adversarial review 2026-06-12, F-B1)

High priority:

1. Run ledger and decision record
   - original request;
   - interpreted goal;
   - task type;
   - selected backend;
   - selection rationale;
   - approval gates;
   - verification gates;
   - task contract path;
   - evidence paths;
   - final status;
   - next actions.

2. Route decision CLI / command
   - e.g. `jarvis decide "..."`;
   - returns task type, recommended backend, automation level, approval gates, verification gates, and why.

3. Evidence-backed completion gate
   - git status/diff;
   - tests/build/lint;
   - smoke checks;
   - reviewer verdict;
   - secret/scope checks;
   - artifact checks;
   - wiki/status consistency.

4. Project operations memory query
   - “Where did this project stop?”
   - “What approval is blocking us?”
   - “Which executor worked best here before?”
   - “What is the next priority?”

Lower priority:

- custom multi-agent spawning;
- worktree orchestration;
- generic dashboard;
- PR/CI auto-fix automation;
- full workflow language;
- own coding agent.

## Positioning statement

Avoid:

> JARVIS is a multi-agent coding orchestrator.

Prefer:

> JARVIS is an AI development operations Director that governs coding agents and orchestrators with long-term project memory, approval/risk policy, executor task contracts, and evidence-backed completion.

Korean version:

> JARVIS는 코딩 에이전트를 하나 더 만드는 것이 아니라, 여러 코딩 에이전트와 오케스트레이터를 프로젝트 운영 흐름 안에서 안전하게 맡기고, 멈추고, 검증하고, 기억하게 만드는 상위 Director 계층이다.

## Greenfield implementation use

This plan is intended to be usable in a fresh environment as an implementation-agent brief, not only as documentation for the current Hermes/JARVIS workspace.

A new implementation should read these vNext concept pages as constraints:

```text
- build an Agent Operations Director, not another coding agent;
- compile user intent into task contracts;
- represent harnesses, loops, guardrails, evidence, and backend adapters explicitly;
- keep JARVIS as final judge above backend-native runtimes;
- start with minimal schemas, a local/direct adapter, a route/contract command, and evidence gates;
- let backend-native agents own their own planning and repair mechanics where useful.
```

The document is deliberately not a line-by-line build manual. If an AI coding agent implements vNext, it should infer the most suitable repo/module layout for the target environment while preserving the architectural invariants, non-goals, and verification expectations recorded here and in [[concepts/jarvis-vnext-intent-to-contract-director|JARVIS vNext Intent-to-Contract Director]].

## Next discussion prompts

For the next session, continue from these questions:

1. What is the minimum useful `Run` schema?
2. What fields are required in an executor task contract?
3. Should the first implementation be a new `/home/hskim/projects/jarvis-vnext` repo or an extension inside `/home/hskim/jarvis`?
4. Which backends should vNext support first: Hermes-direct, Codex, OMX/Gajae-Code, or manual external-orchestrator contracts?
5. How should JARVIS record backend selection rationale and learn from outcomes?
6. What should be excluded from MVP to avoid becoming just another orchestrator?
