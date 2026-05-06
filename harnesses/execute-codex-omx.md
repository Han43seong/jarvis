# Execute Codex/OMX Harness

Use this harness when Hermes delegates implementation to Codex CLI or OMX.

## Preconditions

- Target project path is known.
- Target project exists.
- Target project is preferably a git repository.
- Current git status has been inspected.
- The user has approved high-risk scope if required.
- The prompt includes clear completion criteria.

## Executor selection

- Use `omx exec` for one-shot ralph-style execution with OMX overlays.
- Use interactive `omx --madmax --high` plus `$ralplan`/`$ralph` for complex long-running sessions.
- Use Codex `/goal` in an interactive Codex session for repo-local iterative cleanup when OMX is not needed or the user specifically asks for Codex goal.

## Standard OMX exec prompt structure

```text
You are executing an approved JARVIS implementation task.

Target repo: <absolute path>
Task: <task summary>

Scope:
- Work only inside this repository.
- Allowed files/areas: <list or "repo-local implementation files">

Forbidden:
- Do not push to remote.
- Do not edit secrets, .env files, auth files, OAuth tokens, SSH keys, or credentials.
- Do not delete unrelated files.
- Do not run sudo.
- Do not modify files outside the target repo.
- Do not redefine the requirements.

Implementation requirements:
- <requirements>

Verification:
- Run: <test/lint/build commands if known>
- If a command cannot run, explain why.

Report exactly:
- Files changed
- Commands run
- Test results
- Remaining risks or follow-ups
```

## Standard command

```bash
omx exec -C <target_repo> "<generated prompt>"
```

For long-running work, run in background or tmux and capture output to `runs/`.

## Hermes post-check

After the executor finishes, Hermes must run:

```bash
git -C <target_repo> status --short
git -C <target_repo> diff --stat
git -C <target_repo> diff
```

Then run relevant tests/build/lint if feasible.

## Completion criteria

The task is complete only when:

- The executor reports completion or a clear block.
- Hermes has inspected git status/diff.
- Tests/verification were run or skipped with a reason.
- No secrets or unexpected broad changes are present.
- Wiki/status notes are updated when appropriate.
