---
title: Codex CLI
created: 2026-05-07
updated: 2026-05-07
type: entity
entity_type: executor
status: active
tags: [codex, jarvis, executor-routing, automation, verification]
sources: [AGENTS.md, harnesses/execute-codex-omx.md]
confidence: high
relations:
  - type: executes_in
    target: project-repositories
  - type: governed_by
    target: executor-routing
  - type: verified_by
    target: hermes-agent
---

# Codex CLI

Codex CLI is an implementation executor available to [[entities/jarvis|JARVIS]], especially for repo-local iterative cleanup and tasks where the user's Codex OAuth/subscription path is preferred.

## JARVIS Usage

Codex should run inside a selected target repository under `$HOME/projects/<project>`, not in the JARVIS control-plane repo unless the task explicitly targets JARVIS docs/config.

## Guardrails

- Do not push.
- Do not edit secrets or auth files.
- Do not delete unrelated files.
- Report changed files, commands run, verification results, and residual risks.

## See also

- [[concepts/executor-routing|Executor Routing]]
- [[entities/hermes-agent|Hermes Agent]]
- [[entities/omx|OMX]]
