# Hermes/JARVIS Producer-Reviewer Loop Improvement Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task after the user approves runtime behavior changes.

**Goal:** Improve the base Hermes/JARVIS operating system so non-trivial work uses explicit Producer/Reviewer rejection loops before building `hermes-slide-director`.

**Architecture:** Keep Hermes as Director. Use separate Producer and Reviewer roles for implementation/design tasks. Add a reusable harness document first, then update JARVIS routing/skills in a controlled way, then dogfood the improved workflow on `hermes-slide-director` Phase 0.

**Tech Stack:** Hermes Agent, JARVIS control-plane docs, `delegate_task`, optional OMX/Codex/Claude Code executors, git-based verification.

---

## Current observed Hermes/JARVIS state

- Hermes has base support for tool loops, delegation, cron/background jobs, skills, memory, and approvals.
- Current config supports autonomous work:
  - `approvals.mode: smart`
  - `delegation.max_iterations: 50`
  - `delegation.max_concurrent_children: 3`
  - `delegation.orchestrator_enabled: true`
  - `delegation.max_spawn_depth: 1`
  - `security.tirith_enabled: true`
  - `security.redact_secrets: true`
- A systematic rejection loop is not a single Hermes core feature flag. It is a JARVIS workflow pattern built from delegation, skills, executor prompts, verification, and approval gates.

## Proposed operating model

Use this default mode for non-trivial work:

```text
Hermes Director
  -> Producer Agent/Executor
  -> Hermes basic verification
  -> Reviewer/Critic Agent
  -> Revision Planner
  -> Producer Agent/Executor revision
  -> repeat until PASS / escalation / abort
```

## Task 1: Add reusable harness document

**Objective:** Create a durable producer/reviewer rejection loop harness under the JARVIS control plane.

**Files:**
- Created: `$HOME/jarvis/harnesses/producer-reviewer-rejection-loop.md`

**Status:** Done in planning pass.

**Verification:**
- File exists.
- Defines Director, Producer, Reviewer/Critic, Revision Planner.
- Defines Pre-flight, Revision, Escalation, and Abort gates.
- Includes producer/reviewer/revision prompt skeletons.

## Task 2: Patch JARVIS operating instructions

**Objective:** Make the harness discoverable from `AGENTS.md` without making every trivial task expensive.

**Files:**
- Modify: `$HOME/jarvis/AGENTS.md`

**Change:**
Add a concise policy:

```md
## Producer/Reviewer rejection loop

For non-trivial implementation, design, or artifact-generation tasks, prefer a role-separated loop:
Hermes Director -> Producer -> Reviewer/Critic -> Revision Planner -> Producer revision.
Use `harnesses/producer-reviewer-rejection-loop.md` as the protocol. Do not use the full loop for quick reads, status checks, local server starts, or small edits. Keep safety gates unchanged.
```

**Verification:**
- Read back `AGENTS.md`.
- Confirm the policy is scoped to non-trivial work only.
- Confirm it does not bypass push/deploy/secrets/destructive-action approvals.

## Task 3: Patch `jarvis-core` skill

**Objective:** Make future Hermes sessions load the loop guidance when operating as JARVIS.

**Files:**
- Modify skill: `jarvis-core`

**Change:**
Add a section pointing to `$HOME/jarvis/harnesses/producer-reviewer-rejection-loop.md` and the conditions for use.

**Verification:**
- `skill_view(name='jarvis-core')` shows the new guidance.
- No stale language implies `slide-harness` is still the main new direction.

## Task 4: Add a lightweight route decision table

**Objective:** Decide when to pay the overhead of a full producer/reviewer loop.

**Files:**
- Modify: `$HOME/jarvis/config/routing.yaml` or create `$HOME/jarvis/config/review-loop.yaml` after inspecting current routing config.

**Suggested policy:**

```yaml
review_loop:
  default: selective
  use_for:
    - medium_large_implementation
    - design_or_slide_generation
    - artifact_quality_sensitive_work
    - user_explicitly_requests_rejection_loop
  skip_for:
    - status_checks
    - file_reads
    - small_docs_edits
    - local_server_start_stop
  max_iterations:
    normal: 3
    design_artifact: 5
```

**Verification:**
- YAML parses.
- Policy does not conflict with existing executor routing.

## Task 5: Dogfood on `hermes-slide-director` Phase 0

**Objective:** Use the improved system to implement the first real project phase.

**Process:**

1. Hermes writes a Phase 0 implementation plan for Pydantic models and tests.
2. Producer implements one task.
3. Reviewer checks spec compliance.
4. Reviewer checks quality.
5. Producer revises if needed.
6. Hermes runs final tests and commits.

**Verification:**
- `hermes-slide-director` tests pass.
- Git diff reviewed.
- Reviewer verdict is recorded in task report.

## Non-goals

- Do not modify Hermes source code yet.
- Do not change model/provider credentials.
- Do not enable unsafe auto-approval.
- Do not force full review loops on trivial tasks.
- Do not implement `hermes-slide-director` product loop before the base workflow is agreed.

## Recommendation

Proceed in two steps:

1. Commit the harness and plan as a safe control-plane improvement.
2. After approval, patch `AGENTS.md`/`jarvis-core`/routing policy and dogfood it on `hermes-slide-director` Phase 0.
