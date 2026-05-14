# Producer/Reviewer Rejection Loop Harness

## Purpose

Use this harness before implementing projects that depend on quality loops, including `hermes-slide-director`.

The goal is to make Hermes/JARVIS operate with explicit role separation:

- Director: Hermes/JARVIS controller
- Producer: implementation or creative production agent
- Reviewer/Critic: independent verifier that can reject work
- Revision Planner: converts rejection findings into concrete next instructions

This harness is a JARVIS control-plane workflow. It is not a Hermes core feature flag and does not modify global Hermes source code.

## When to use

Use this harness for:

- medium/large implementation tasks
- design/deck/artifact generation
- tasks with subjective quality gates
- tasks where the user explicitly wants a rejection loop
- `hermes-slide-director` development phases

Do not use this for:

- quick file reads
- status checks
- one-line config/doc edits
- simple local server start/stop

## Roles

### 1. Director

Usually Hermes in the main session.

Responsibilities:

- define target repo/path
- write or load the task spec
- define acceptance criteria
- choose producer/reviewer tools
- dispatch producer
- dispatch reviewer
- decide whether to accept, reject, or escalate to user
- verify final state with tests/diffs/artifacts
- commit only after review passes and scope is clean

### 2. Producer

A separate executor/subagent responsible for making the artifact.

Examples:

- `delegate_task` implementer for short synchronous slices only
- Codex-family producer: `codex exec` directly, or `omx exec` / `omx ralph` as the oh-my-codex orchestration layer on top of Codex CLI
- Claude-family producer: `claude -p` directly, or `omc launch` / OMC team flows as the oh-my-claudecode orchestration layer on top of Claude Code
- spawned Hermes worker

Producer rules:

- work only in the target path
- do not push
- do not edit secrets
- do not delete unrelated files
- run specified checks where feasible
- report changed files, commands, results, and remaining risks

Long Producer or Reviewer work must use a durable background executor when the main Hermes/JARVIS channel needs to remain responsive. Prefer `terminal(background=true, notify_on_complete=true)`, `/background`, cron, kanban, or an equivalent external background process. `delegate_task` is synchronous and non-durable; it can be cancelled when the parent conversation is interrupted and must not be presented as equivalent to background execution for long Producer/Reviewer tasks.

### 3. Reviewer / Critic

A separate reviewer from the producer. It must evaluate against the approved spec, not the producer's intent.

Reviewer checks:

- spec compliance
- quality/design/readability where relevant
- test/build/lint evidence
- security/secrets risk
- scope creep
- artifact correctness

Reviewer output must be one of:

- `PASS`
- `REQUEST_CHANGES`
- `ESCALATE_TO_USER`
- `ABORT`

### 4. Revision Planner

Can be Hermes or another subagent.

Responsibilities:

- turn reviewer findings into concrete producer instructions
- preserve passed work
- keep the next revision bounded
- avoid broad rewrites unless explicitly approved

## Standard loop

```text
1. Director writes task spec + acceptance criteria.
2. Producer creates or modifies artifact.
3. Director verifies basic state: git status, diff, tests/artifacts.
4. Reviewer evaluates against criteria.
5. If PASS: Director runs final verification and reports.
6. If REQUEST_CHANGES: Revision Planner writes bounded fix prompt.
7. Producer revises.
8. Repeat until PASS, max iterations, or escalation.
```

## Default gates

### Pre-flight gate

Required before producer starts:

- target repo/path identified
- allowed paths listed
- forbidden actions listed
- acceptance criteria listed
- verification commands listed
- max iterations selected
- executor lane selected: synchronous for short work, durable background for long work or when main-channel responsiveness matters
- prompt/log/work directory selected under ignored runtime paths, usually `/home/hskim/jarvis/tmp/executor-prompts/` and `/home/hskim/jarvis/tmp/executor-runs/`
- prompt handling checked: no secrets in prompts, and long/sensitive prompts are passed by stdin/file where supported or by a short argv prompt pointing to an ignored prompt file
- background launch plan includes an immediate poll for update/auth/interactive prompts

### Revision gate

Required after each producer pass:

- `git status --short`
- `git diff --stat`
- relevant tests/build/lint or artifact checks
- reviewer verdict

### Escalation gate

Escalate to user when:

- producer/reviewer disagree repeatedly
- scope expands beyond original target
- destructive or auth/secrets changes are needed
- max iterations reached
- quality is subjective and tradeoff requires user taste

### Abort gate

Abort when:

- target path is wrong
- unexpected secret/auth file changes appear
- build/test environment is broken in a way unrelated to the task
- repeated revisions make the artifact worse

## Recommended defaults

- Max producer/reviewer iterations: 3 for normal implementation, 5 for design artifacts.
- Producer and reviewer should not be the same subagent.
- Reviewer should receive the original spec and artifact paths, not only the producer summary.
- For design/deck work, reviewer should inspect rendered artifacts/screenshots where possible.
- For code work, reviewer should inspect diff and test output.
- Runtime artifacts created from the JARVIS control-plane root, including `.omx/`, are local ignored state. Future executor launches should prefer ignored work directories so the repo root stays clean.

## Prompt templates

### Producer prompt skeleton

```text
You are the PRODUCER agent.

Target repo: <absolute path>
Task: <task summary>
Allowed paths: <paths>
Forbidden actions: no push, no secrets/auth edits, no unrelated deletes, no broad rewrites.
Acceptance criteria:
<criteria>
Verification commands:
<commands>

Do the work only inside the target repo. Run feasible checks. Return:
- changed files
- commands run
- test/build/artifact results
- unresolved risks
```

### Reviewer prompt skeleton

```text
You are the REVIEWER/CRITIC agent.

Evaluate the result against the original spec. Do not assume the producer is correct.

Original task:
<task>
Acceptance criteria:
<criteria>
Artifacts/files to inspect:
<paths>
Verification evidence:
<test/build/QA output>

Return exactly:
Verdict: PASS | REQUEST_CHANGES | ESCALATE_TO_USER | ABORT
Spec gaps:
Quality issues:
Scope/security risks:
Required fixes:
```

### Revision planner skeleton

```text
Convert the reviewer findings into a bounded producer revision prompt.
Preserve passed work. Do not broaden scope.
List exact files/areas to change and exact checks to rerun.
```

## Application to hermes-slide-director

Use this harness to build `hermes-slide-director` itself.

Development loop:

```text
Hermes Director
  -> Producer implements Phase task
  -> Reviewer checks spec/quality
  -> Revision Planner writes fix prompt
  -> Producer revises
  -> Hermes final verification
```

Product loop to implement inside `hermes-slide-director`:

```text
User materials + design reference
  -> Criteria proposer
  -> User approval
  -> Deck Producer
  -> Renderer
  -> Deck Critic
  -> Revision Planner
  -> Deck Producer v2/v3
  -> Final deck
```

## Safety boundaries

This harness does not relax JARVIS safety policy.

Still require explicit user approval for:

- push/deploy
- secrets/auth changes
- sudo/system changes
- permanent deletes
- broad rewrites
- paid/cloud actions
