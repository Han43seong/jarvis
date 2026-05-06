# Plan-Gate Harness

Use this harness before medium/high-impact implementation.

## Purpose

Create a small approval gate between user intent and executor action.

## Required plan fields

- Goal
- Target project/path
- Current state summary
- Proposed executor
- Rationale for executor choice
- Scope of allowed changes
- Explicitly forbidden actions
- Implementation steps
- Verification commands
- Completion criteria
- Risks and rollback strategy

## Approval requirement

User approval is required before execution if the plan includes:

- Deletion or destructive cleanup.
- sudo or system config changes.
- git push/deploy/release.
- secrets/auth/config changes.
- broad refactor or migration.
- paid API/cloud usage.
- work outside `/home/hskim/jarvis` or the selected project repo.

## Lightweight mode

For low-risk JARVIS control-plane tasks, Hermes can proceed without a separate approval gate, but must still summarize the changes after completion.
