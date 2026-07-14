---
title: JARVIS Office Runtime Direction
created: 2026-05-28
updated: 2026-06-08
type: concept
concept_type: architecture
status: draft
tags: [jarvis, hermes, control-plane, workflow, automation, verification]
sources: [conversation-2026-05-28, AGENTS.md, config/routing.yaml, harnesses/producer-reviewer-rejection-loop.md]
confidence: high
relations:
  - type: references
    target: jarvis-control-plane
  - type: references
    target: executor-routing
  - type: governed_by
    target: producer-reviewer-rejection-loop
  - type: delegates_to
    target: omx
  - type: delegates_to
    target: codex-cli
  - type: informed_by
    target: ouroboros-adoption-review
  - type: supports
    target: jarvis-open-source-strategy
---

# JARVIS Office Runtime Direction

This note records the agreed direction for future JARVIS hardening: JARVIS should remain the intelligent Director, while CLI/runtime tools should automate the office work around execution, state, approvals, and verification.

## Core principle

Do not replace JARVIS judgment with a rigid rule-based dispatcher.

The desired design is:

- JARVIS stays the brain: interprets user intent, designs the work, chooses tradeoffs, assigns executors, judges quality, and decides when to ask the user.
- CLI/runtime helpers become the hands, ledger, and office system: create run folders, store prompts/logs/results, track approvals, run checks, and show status.
- Routing rules are guardrails and decision support, not the final decision-maker.

In short: JARVIS should not become smaller. JARVIS should become better supported.

After reviewing `Q00/ouroboros`, keep the same boundary: Ouroboros is a useful reference for specification-first workflows, event/ledger thinking, runtime adapters, and evaluation gates, but it must not replace JARVIS as the top-level Director. See [[concepts/ouroboros-adoption-review|Ouroboros Adoption Review for JARVIS vNext]]. For eventual open-source release, preserve the same principle at a different boundary: private JARVIS can remain Hermes-first, but any public core should be Hermes-agnostic with Hermes provided as a first-class adapter. See [[concepts/jarvis-open-source-strategy|JARVIS Open Source Strategy]].

## Why this matters

A simple rules-only router could reduce quality because user requests often carry implicit context:

- quick MVP vs production-quality outcome;
- business/taste tradeoffs;
- whether to ask more questions or proceed;
- whether to use Hermes directly, Codex, OMX, Claude/OMC, kanban, cron, or a background worker;
- whether a Reviewer is needed;
- how to split work without creating file conflicts or context pollution.

These are Director-level judgments. They should remain with JARVIS.

## Desired role split

### User

- Gives goals, priorities, taste, constraints, and approvals.
- Makes final decisions for push, deploy, delete, secrets, paid actions, and subjective product tradeoffs.

### JARVIS

- Receives and interprets the request.
- Recovers project context from wiki, registry, sessions, git state, and files.
- Writes or approves the work design: objective, scope, acceptance criteria, verification plan, and task split.
- Chooses executor strategy: Hermes direct, Codex, OMX, Claude/OMC, kanban, cron, background worker, or ask-user.
- For the future ontology-backed router, evaluates expanded executor candidates such as Gajae-Code, OMX-Codex, LazyCodex-Codex, OpenCode, and raw Codex as described in [[concepts/jarvis-vnext-executor-ontology|JARVIS vNext Executor Ontology]].
- Acts as Director over Producer/Reviewer loops.
- Interprets Reviewer findings and decides accept, revise, escalate, or abort.
- Produces the final user-facing synthesis.

### CLI/runtime helpers

- Generate run ids and run folders.
- Save `request.md`, `route.json`, `plan.md`, prompts, logs, results, verification evidence, review verdicts, and final reports.
- Launch Producer/Reviewer/background processes.
- Track process status and retries.
- Execute configured verification commands.
- Maintain an approval queue with decision ids.
- Provide `status` output across CLI and Telegram control channels.

The runtime may borrow Ouroboros-like ideas such as Seed-style task contracts, event logs, status/resume/cancel surfaces, and evaluation ladders, but those concepts should be implemented JARVIS-native unless a sandboxed adapter proves safer.

### Producers

- Implement or create artifacts within bounded scope.
- Report changed files, commands run, verification results, and remaining risks.

### Reviewers/Critics

- Inspect the result independently against the original spec and evidence.
- Return `PASS`, `REQUEST_CHANGES`, `ESCALATE_TO_USER`, or `ABORT`.
- Do not replace JARVIS; they provide evidence and judgment for JARVIS to use.

## Recommended building blocks

### 1. Run ledger

Every non-trivial task should get a run id and a durable folder.

Example files:

```text
runs/<run-id>/
  request.md
  task-contract.yaml
  route.json
  plan.md
  events.jsonl
  prompts/
  logs/
  results/
  evidence/
  approvals/
  final-report.md
```

Purpose:

- make resume easy;
- prevent state from being scattered across chat, wiki, git, and logs;
- give Telegram/CLI sessions the same source of truth;
- preserve evidence for later review.

`task-contract.yaml` is the JARVIS-native counterpart to a Seed specification: objective, target, ambiguity, acceptance criteria, constraints, forbidden actions, approval gates, and evidence requirements. `events.jsonl` records route decisions, approvals, producer completion, reviewer verdicts, and final verification without storing secrets.

### 2. Decision-support router

A router command can recommend executor, risk, gates, and alternatives, but JARVIS must make or approve the final design.

Good router output:

- target project/path;
- task type;
- risk level;
- recommended executor;
- whether a Reviewer is required;
- whether user approval is required now;
- alternatives and tradeoffs;
- reason for the recommendation.

Bad router behavior:

- blindly dispatching based only on keywords;
- bypassing JARVIS interpretation;
- treating routing rules as more important than user intent.

### 3. Producer/Reviewer runner

Automate the repeated mechanics of the rejection loop while preserving JARVIS as Director.

Loop:

1. JARVIS writes task spec and acceptance criteria.
2. Runner launches Producer.
3. Runner/JARVIS records git status, diff, tests, and artifacts.
4. Runner launches independent Reviewer.
5. JARVIS interprets verdict.
6. If `REQUEST_CHANGES`, JARVIS or a Revision Planner writes bounded revision instructions.
7. Repeat until `PASS`, escalation, abort, or max iterations.

### 4. Approval queue

Create durable decision records for actions requiring user approval.

Example:

```json
{
  "decision_id": "decision-042",
  "task": "Push SlideForge changes",
  "reason": "git push requires user approval",
  "blocked_command": "git push origin main",
  "allowed_replies": ["승인 decision-042", "반려 decision-042"],
  "owner": "cli"
}
```

Purpose:

- avoid accidental push/deploy/delete/secrets changes;
- support Telegram approvals without pretending Telegram is live-attached to the CLI session;
- preserve a clear approval audit trail.

### 5. Status view

A future `jarvis status` should summarize:

- active runs;
- current owner/executor;
- latest state;
- log/evidence paths;
- pending approvals;
- recently completed runs;
- failures or escalation points.

This turns JARVIS from a chat-only coordinator into an inspectable office system.

## First implementation priorities

1. Task contract: non-trivial work needs a durable Seed-like JARVIS spec before execution.
2. Run ledger: state and evidence must become durable before deeper automation.
3. Approval queue: safety and Telegram/CLI handoff need explicit decision ids.
4. Status view: user and JARVIS need the same picture of active work.
5. Decision-support router: codify recommendations without replacing JARVIS judgment.
6. Executor/harness adapter contracts: make OMX, Gajae-Code, LazyCodex, OpenCode, raw Codex, Hermes direct, cron, kanban, and project-specific harnesses comparable.
7. Producer/Reviewer runner: automate the repeated loop after the state model is reliable.

## Non-goals

- Do not reduce JARVIS to a fixed rules engine.
- Do not let a CLI automatically choose broad rewrites, push, deploy, delete, secrets edits, or paid actions.
- Do not let the Producer self-review replace an independent Reviewer.
- Do not treat `delegate_task` as durable background execution for long work.
- Do not make the run ledger a dumping ground for raw secrets, private keys, `.env`, or auth material.
- Do not install or register Ouroboros into the default Hermes profile as a production integration without an explicit sandbox review and user approval.
- Do not let public-core code import Hermes-only APIs directly; keep Hermes behind an adapter boundary.

## Relationship to current JARVIS

Current JARVIS already has the operating model in docs and skills:

- [[concepts/jarvis-control-plane|JARVIS Control Plane]]
- [[concepts/executor-routing|Executor Routing]]
- `$HOME/jarvis/harnesses/producer-reviewer-rejection-loop.md`
- `$HOME/jarvis/config/routing.yaml`

The future work is not to invent a new philosophy. It is to turn the existing Director/Producer/Reviewer operating model into safer, more durable, more inspectable runtime support while keeping JARVIS as the final interpreter and orchestrator.

Ouroboros reinforces this direction, but the adoption path is selective absorption: use its specification-first, ledger, evaluation, and runtime-adapter patterns as design input while keeping existing JARVIS harnesses registered, wrapped, refactored, or archived rather than discarded.

The open-source path follows the same separation principle: keep this private instance Hermes-first, but extract public reusable code as a Hermes-agnostic Agent Operations core with host adapters. See [[concepts/jarvis-open-source-strategy|JARVIS Open Source Strategy]].
