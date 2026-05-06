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

## Next steps

1. Restart Hermes from `/home/hskim/jarvis` so config/context changes are loaded cleanly.
2. Create JARVIS-specific Hermes skills if needed:
   - `jarvis-core`
   - `jarvis-executor-router`
   - `jarvis-codex-omx-executor`
   - `jarvis-wiki-manager`
3. Register the first real project in `config/projects.yaml`.
4. Test executor routing on a small repo-local task.
