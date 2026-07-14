# Background Executor Runbook - 2026-05-14

## Purpose

Use this runbook when JARVIS launches Codex/OMX/Claude-family Producer or Reviewer work that may run long enough to block the main Hermes conversation.

## Standard

- Use durable background execution when main-channel responsiveness matters: `terminal(background=true, notify_on_complete=true)`, `/background`, tmux, cron, kanban, or an equivalent process runner.
- Use synchronous `delegate_task` only for short slices where interruption/cancellation is acceptable.
- Store generated prompts under `$HOME/jarvis/tmp/executor-prompts/`.
- Store logs, pids, and run metadata under `$HOME/jarvis/tmp/executor-runs/`.
- Treat `$HOME/jarvis/.omx/` as ignored local runtime state if OMX creates it from the control-plane root.
- Prefer launching from ignored runtime work directories so `git status` stays focused on intentional source/doc changes.

## Prompt Handling

- Never put secrets, tokens, private keys, auth files, or `.env` content in executor prompts.
- Prefer stdin or file-prompt patterns where supported.
- For Codex, prefer:

```bash
codex exec -C <target_repo> - < $HOME/jarvis/tmp/executor-prompts/<task>.md
```

- If an executor only accepts argv prompts, keep argv short and point it to an ignored prompt file:

```text
Read and execute the approved task prompt at $HOME/jarvis/tmp/executor-prompts/<task>.md. Follow the JARVIS execution contract. Do not push, delete unrelated files, or edit secrets.
```

## Launch Checklist

1. Confirm target repo, allowed paths, forbidden actions, acceptance criteria, and verification commands.
2. Write the prompt under `$HOME/jarvis/tmp/executor-prompts/`.
3. Start the executor in a background process with completion notification.
4. Poll immediately for update prompts, auth prompts, sandbox prompts, or other interactive blockers.
5. Decline optional tool updates unless the user has approved the update.
6. Pause and ask the user for credential, auth, paid, destructive, deployment, or production-access requests.
7. Record process id, prompt path, log path, target repo, and verification commands in the Director notes.

## Completion Checklist

1. Poll until the executor exits or reports a clear blocker.
2. Run `git status`, `git diff --stat`, and relevant tests/checks in the target repo.
3. Inspect for unexpected files, secret/auth edits, broad rewrites, or runtime artifacts outside ignored paths.
4. Run reviewer/critic pass when the Producer/Reviewer loop applies.
5. Update wiki/status when the run changes JARVIS operating knowledge.
