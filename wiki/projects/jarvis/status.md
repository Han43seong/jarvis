# JARVIS Status

## Current state

- WSL environment cleaned and ready.
- Codex CLI and OMX installed and smoke-tested.
- Codex OAuth/ChatGPT Pro Personal workspace verified previously.
- Bubblewrap installed and Codex sandbox warning removed.
- Hermes approval policy set to smart.
- Secret redaction enabled for future sessions.
- JARVIS control-plane root created at `/home/hskim/jarvis`.
- Project root created at `/home/hskim/projects`.

## Active operating model

- Hermes is the control-plane/orchestrator/verifier/memory manager.
- OMX `$ralph` is the default medium/large implementation executor.
- Codex `/goal` is available for repo-local iterative cleanup when useful.
- Harness documents define automatic routing and completion rules.

## Recent changes

- 2026-05-06: Created user-local JARVIS Hermes skills:
  - `jarvis-core`
  - `jarvis-executor-router`
  - `jarvis-codex-omx-executor`
  - `jarvis-wiki-manager`

## Next steps

1. Register the first real project in `config/projects.yaml`.
2. Test executor routing on a small repo-local task.
3. Promote or refine JARVIS skills after a few real routing/executor runs.
