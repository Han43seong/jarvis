---
title: JARVIS Open Source Strategy
created: 2026-06-08
updated: 2026-06-08
type: concept
concept_type: open-source-strategy
status: draft
tags: [jarvis, open-source, hermes, adapters, agent-ops, control-plane, vnext]
sources: [conversation-2026-06-08, jarvis-office-runtime-direction, jarvis-vnext-executor-ontology, ouroboros-adoption-review]
confidence: high
relations:
  - type: supports
    target: jarvis-office-runtime-direction
  - type: supports
    target: jarvis-vnext-executor-ontology
  - type: complements
    target: ouroboros-adoption-review
  - type: references
    target: executor-routing
---

# JARVIS Open Source Strategy

This note records the open-source direction for the future JARVIS system.

## Executive decision

JARVIS has open-source potential, but the public project should not be the user's private `$HOME/jarvis` control-plane repository as-is.

The public project should be a generalized agent-operations framework:

```text
Hermes-first for the user's private JARVIS instance.
Hermes-agnostic at the public core layer.
Hermes as a first-class adapter / recommended host, not a hard dependency.
```

## Why it is worth open-sourcing

The problem JARVIS addresses is not just coding. It is agent operations:

```text
Given a user task, decide what it is, how risky/complex it is,
which agent or harness should own it, what evidence is required,
where approvals are needed, how to record execution, and how to verify completion.
```

As AI coding tools multiply, many users will face this same operational problem:

- choosing among coding agents;
- separating Director judgment from Producer execution;
- creating task contracts before mutation;
- routing work by complexity and risk;
- managing approvals for push/deploy/delete/secrets/paid actions;
- preserving run logs and evidence;
- resuming work across sessions;
- applying independent review before claiming completion;
- wrapping project-specific harnesses without losing safety gates.

That is broader than a personal automation script and narrower than a full general-purpose Agent OS. The likely public niche is:

```text
Agent Operations Control Plane for AI development workflows.
```

## Do not publish the private JARVIS repo as-is

The current JARVIS workspace is a private operating instance. It contains or references user-specific context such as:

- local paths and usernames;
- private project registry entries;
- internal project wiki/status/decisions;
- RFP/business ideas and project-specific notes;
- Hermes profile assumptions;
- memory/skills/session-history-derived operating preferences;
- Telegram/CLI continuity assumptions;
- approval and security policy tuned for one user;
- run artifacts and local research folders.

Public release must extract a generic framework into a separate repository rather than exposing the private control plane.

## Public architecture principle

The public system should separate core from host runtime.

```text
Public core:
  no Hermes tool imports
  no user-specific profile assumptions
  no private paths
  no secrets
  no fixed executor default

Adapters:
  Hermes
  Codex
  OMX
  OpenCode
  Gajae-Code
  LazyCodex
  Claude Code / OMC
  shell / dry-run

Private JARVIS instance:
  may remain Hermes-first
  may use user's specific policies, memory, wiki, registry, and executors
```

Core must expose interfaces. Host runtimes implement them.

Bad public-core pattern:

```python
from hermes_tools import terminal, read_file
```

Good public-core pattern:

```python
class RuntimeAdapter(Protocol):
    def run_command(...): ...
    def read_text(...): ...
    def launch_producer(...): ...
    def collect_result(...): ...
```

Hermes can then implement the adapter without making the core Hermes-only.

## Suggested public positioning

Avoid using `JARVIS` as the public product name unless trademark/name risk is resolved. Keep JARVIS as the user's private instance name if needed.

Possible public descriptions:

```text
A control-plane runtime for AI coding agents:
route work, create task contracts, run producers, collect evidence,
manage approvals, and verify results across multiple agent runtimes.
```

```text
An agent-operations framework for selecting, delegating, verifying,
and recording AI-assisted development work across coding agents and harnesses.
```

Potential naming directions:

- AgentOps Harness
- Agent Director
- DirectorOS
- AgentRunway
- SpecOps Agent
- AI Agent Control Plane

## Public core modules

A public framework should start with these runtime-independent modules.

```text
core/
  task_contract
  run_ledger
  approval_queue
  event_log
  status_model
  evidence_model

routing/
  task_classifier
  routing_ontology
  policy_engine
  decision_record

harnesses/
  manifest_schema
  registry
  compatibility

adapters/
  base_protocol
  shell_dry_run
  hermes
  codex
  omx
  opencode
  gajae
  lazycodex
  claude_code

verification/
  mechanical_gate
  semantic_review_contract
  consensus_gate_optional

cli/
  init
  route
  run
  status
  approve
  verify
  manifest
```

## Minimal public MVP

The first public version does not need every executor adapter. It should prove the operating contract.

Minimum viable release:

1. `task-contract.yaml` schema and generator.
2. File-first run ledger with `events.jsonl`.
3. Approval queue with decision ids.
4. Harness manifest schema.
5. Base executor adapter protocol.
6. Shell/dry-run adapter for safe demos.
7. Optional Hermes adapter or documentation as first integration.
8. Simple mechanical verification gate.
9. `status` command for active/completed/blocked runs.
10. Toy example repository or synthetic task.
11. Tests and secret/path scrub checks.
12. README explaining the problem and separation from host agents.

Do not wait for Gajae-Code, LazyCodex, OpenCode, OMX, and Hermes adapters to be perfect before publishing an MVP.

## Recommended repository shape

```text
agent-ops-control-plane/
  README.md
  LICENSE
  pyproject.toml
  docs/
    getting-started.md
    concepts/
      task-contract.md
      run-ledger.md
      approval-queue.md
      executor-adapters.md
      harness-manifests.md
      verification-gates.md
      hermes-first-not-hermes-only.md
    integrations/
      hermes.md
      codex.md
      omx.md
      opencode.md

  src/agentops/
    core/
    routing/
    harnesses/
    adapters/
    verification/
    cli/

  examples/
    toy-code-task/
    docs-update-task/
    pr-review-task/

  tests/
```

## Relationship to Hermes

For the user's private system, Hermes remains the best main Director host because it provides memory, skills, session search, tools, cron, gateway, wiki operations, and orchestration.

For the public project, Hermes should be:

```text
first-class adapter
recommended host for users who want a JARVIS-like operating loop
not required by the core library
```

This keeps the private JARVIS workflow strong while making the public project useful to users of Claude Code, Codex, OpenCode, local shells, or other runtimes.

## Relationship to Ouroboros

Ouroboros remains a reference for specification-first AI coding workflows. The public JARVIS-derived project should not try to clone Ouroboros or compete on the same exact axis.

Suggested distinction:

```text
Ouroboros:
  vague idea -> interview -> seed -> execute -> evaluate -> evolve

JARVIS-derived AgentOps core:
  task/request -> route decision -> run ledger -> executor/harness adapter
  -> approval queue -> producer/reviewer -> verification -> status/resume
```

The projects can be complementary: Ouroboros patterns inform task contracts and evaluation, while the JARVIS-derived project focuses on operational control across heterogeneous harnesses and agents.

## Extraction strategy from private JARVIS

1. Keep `$HOME/jarvis` private as the dogfood control-plane instance.
2. Create a separate public-candidate repository under `$HOME/projects/<public-name>`.
3. Extract only generic schemas, protocols, and CLI code.
4. Replace user-specific examples with synthetic examples.
5. Keep Hermes integration behind an adapter boundary.
6. Add automated checks for private paths and secrets.
7. Dogfood the public core from the private JARVIS instance.
8. Only then create/publish a GitHub repository.

## Public release gates

Before public release, verify:

- no personal usernames or private local paths in public files;
- no `.env`, tokens, keys, auth files, session transcripts, or private run logs;
- no private project names that should remain internal;
- license selected;
- README explains scope and non-goals;
- tests pass;
- CLI smoke works on a toy example;
- Hermes adapter is optional;
- issue templates and contribution guidelines exist;
- the public repo does not imply affiliation with Hermes, Nous, OpenAI, Ouroboros, or other tools unless explicitly correct.

## Non-goals

- Do not publish the current private JARVIS repo unchanged.
- Do not make public core depend on Hermes tools.
- Do not make Hermes memory/skills/session search required for basic operation.
- Do not include private project wiki/status/decisions in the public repo.
- Do not promise autonomous push/deploy/delete behavior.
- Do not compete by claiming to replace every coding agent; the project coordinates agents and harnesses.

## Next design step

The next useful artifact is a public-core extraction plan:

```text
JARVIS public-core MVP plan
  - package name candidates
  - module boundaries
  - initial schemas
  - CLI command surface
  - adapter protocol
  - private-data scrub checklist
  - dogfood plan from $HOME/jarvis
```

## See also

- [[concepts/jarvis-office-runtime-direction|JARVIS Office Runtime Direction]]
- [[concepts/jarvis-vnext-executor-ontology|JARVIS vNext Executor Ontology]]
- [[concepts/ouroboros-adoption-review|Ouroboros Adoption Review for JARVIS vNext]]
- [[concepts/executor-routing|Executor Routing]]
