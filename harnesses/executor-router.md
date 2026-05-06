# Executor Router Harness

Use this harness whenever the user asks JARVIS to perform work without explicitly naming an executor.

## Inputs

- User request.
- Target project, if mentioned.
- Current control-plane context.
- Project registry: `config/projects.yaml`.
- Routing policy: `config/routing.yaml`.

## Classification steps

1. Identify the target:
   - JARVIS control plane.
   - A registered project.
   - An unregistered path.
   - Unknown target.

2. Identify task type:
   - docs/config/wiki
   - analysis/search/inspection
   - environment/setup
   - small code edit
   - medium/large implementation
   - iterative test/lint/type fixing
   - parallelizable work
   - recurring work
   - dangerous/ambiguous work

3. Identify risk:
   - low: read-only, docs, config under JARVIS, tests.
   - medium: repo file edits, dependency installs, migrations inside repo.
   - high: destructive commands, secrets, system config, deployment, git push.

4. Select executor:
   - Hermes direct for low-risk control-plane/docs/config/verification work.
   - Hermes goal loop for multi-step JARVIS/control-plane work.
   - Codex exec for clear small repo-local implementation.
   - Codex goal for repo-local iterative cleanup when OMX orchestration is unnecessary.
   - OMX ralph for medium/large implementation and "finish automatically" requests.
   - OMX team for large parallelizable work.
   - Cron for recurring work.
   - Kanban for durable backlog/multi-worker work.
   - Ask user when target/scope/risk is unclear.

## Default decision rules

- If the user says "끝까지", "자동으로", "구현해", "완성해", and the task is coding-related, prefer `omx-ralph`.
- If the task is only under `/home/hskim/jarvis`, prefer `hermes-direct` unless it is long and multi-step.
- If the task modifies an existing project repo and touches many files, prefer `omx-ralph`.
- If the task is test/lint cleanup across a repo, prefer `omx-ralph`; consider `codex-goal` if the user asks for Codex specifically.
- If the user explicitly chooses an executor, use it unless unsafe.

## Required output before high-impact execution

Before running Codex/OMX for medium/large work, state:

- Selected executor.
- Target path.
- Reason for routing.
- Scope.
- Forbidden actions.
- Completion criteria.
- Whether user approval is required before execution.

## Stop and ask user when

- Target project is unknown.
- Completion condition is not defined.
- The task involves deletion, reset, push, deploy, sudo, secrets, production, or paid services.
- The requested scope is too broad to verify.
