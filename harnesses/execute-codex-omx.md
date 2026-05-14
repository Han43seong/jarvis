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
- For long Producer/Reviewer tasks where the main Hermes/JARVIS channel must stay responsive, use a background process such as `terminal(background=true, notify_on_complete=true)` or an equivalent tmux/background runner. Do not use synchronous `delegate_task` as a durability or responsiveness substitute.

## Runtime paths

Keep executor runtime files out of the tracked JARVIS root.

- Store generated executor prompts under `/home/hskim/jarvis/tmp/executor-prompts/`.
- Store captured logs, pid files, and run metadata under `/home/hskim/jarvis/tmp/executor-runs/`.
- Run long executor processes from an ignored runtime work directory when practical.
- Treat `.omx/` created under `/home/hskim/jarvis` as ignored local runtime state. Future launches should still prefer ignored work directories so the root stays visually clean.
- Do not place prompt files at repo root or under tracked wiki/project documentation unless the prompt is intentionally curated documentation.

## Prompt handling

Avoid placing long or sensitive prompts directly in process argv.

- Prefer stdin/file-prompt patterns where supported.
- Codex supports stdin prompts:

```bash
codex exec -C <target_repo> - < /home/hskim/jarvis/tmp/executor-prompts/<task>.md
```

- If an executor cannot read stdin or a prompt file directly, pass a short argv prompt that points to an ignored prompt file path.
- Never include secrets, credentials, auth tokens, private keys, or `.env` content in executor prompts.

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
omx exec -C <target_repo> "<short prompt that references /home/hskim/jarvis/tmp/executor-prompts/<task>.md>"
```

For long-running work, run in background or tmux and capture output under `/home/hskim/jarvis/tmp/executor-runs/`.

Immediately after launching a background Codex/OMX process, poll it once before stepping away:

```text
1. Launch the background executor with notify-on-complete.
2. Poll early for update prompts, auth prompts, sandbox prompts, or other interactive blockers.
3. Answer only safe defaults allowed by JARVIS policy. For example, decline optional tool updates unless the user approved an update.
4. If credentials, auth, paid actions, destructive actions, or production access are requested, pause and ask the user.
5. Record the process id, prompt path, log path, target repo, and verification commands in the Director notes.
```

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
