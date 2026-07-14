# Background Executor Hygiene Follow-up — 2026-05-14

## Cleanup implementation status

Implemented in the JARVIS control-plane repo after `hermes-slide-director` Phase 13 was committed as `e4e6666`.

Changes made:

- `.gitignore` now explicitly ignores root `.omx/` runtime state and the standardized executor runtime directories under `tmp/`.
- `harnesses/producer-reviewer-rejection-loop.md` now distinguishes short synchronous `delegate_task` slices from durable background Producer/Reviewer execution.
- `harnesses/execute-codex-omx.md` now defines ignored runtime prompt/log paths, stdin/file-prompt preference, short argv fallback, early background poll/preflight, and `.omx/` handling.
- `config/routing.yaml` now records standard background executor runtime paths and hygiene notes for prompt handling and early interactive prompt detection.
- `wiki/projects/jarvis/background-executor-runbook-2026-05-14.md` records the reusable launch/check/cleanup procedure.

Remaining follow-up:

- Investigate whether current OMX provides a native stdin or prompt-file option for `omx exec`.
- Patch reusable Hermes skills only if future executor runs show the same procedure should be surfaced as an operator command.

## Context

During `hermes-slide-director` Phase 13, JARVIS switched from synchronous `delegate_task` to background Codex/OMX execution so the main Hermes/JARVIS conversation channel stays responsive while implementation/review work continues.

Current in-flight work at time of note:

- App repo: `$HOME/projects/hermes-slide-director`
- Phase 13 Producer: background OMX session `proc_9aa1f245e781`, completed exit 0
- Phase 13 Reviewer: background Codex read-only session `proc_6a5f8ece29e5`, running when this note was created
- Main channel remained responsive after switching to background processes

## What worked

- `terminal(background=true, notify_on_complete=true)` kept the main conversation available.
- Hermes could poll background work using `process poll` and verify with `git status`/`git diff`/tests.
- Producer and Reviewer were separated:
  - Producer: OMX/Codex-family implementation
  - Reviewer: Codex read-only background review
  - Hermes/JARVIS: Director, verifier, integrator
- The Phase 13 Producer completed without blocking the main channel after launch.

## Problems observed

### 1. Control-plane repo got runtime artifacts

`$HOME/jarvis` showed untracked runtime files:

```text
?? .omx/
?? executor-prompts/
```

Cause:

- `omx exec -C $HOME/projects/hermes-slide-director ...` was launched with shell working directory `$HOME/jarvis`.
- OMX correctly used the app repo as target, but its own `.omx/` runtime state was written under the shell cwd.
- The first Producer prompt was written to `$HOME/jarvis/executor-prompts/`, which is not ignored.

Recommended fix:

- Do not run executor processes from the tracked JARVIS repo root.
- Standardize an ignored runtime workdir, for example:
  - `$HOME/jarvis/tmp/executor-runs/`
  - or `$HOME/jarvis/runs/executor-runs/`
- Store prompts/logs under ignored runtime paths, not root-level tracked paths.
- Add ignore rules if appropriate:
  - `/.omx/`
  - `/executor-prompts/` only if keeping the existing root folder local-only
  - or migrate root `executor-prompts/` into `/tmp/executor-prompts/` and avoid tracking it

### 2. Prompt was exposed in process command line

The first OMX Producer was launched as:

```bash
omx exec --sandbox workspace-write -C $HOME/projects/hermes-slide-director "$(cat $HOME/jarvis/executor-prompts/hermes-slide-director-phase13-final-package-omx.md)"
```

This expanded the full prompt into argv, making it visible in `ps` and process logs.

Risk:

- Current prompt had no secrets, so no incident.
- As a general system pattern, this is poor hygiene.

Recommended fix:

- Prefer stdin/file-based prompt passing when supported.
- Codex supports stdin:

```bash
codex exec -C <repo> - < prompt.md
```

- Investigate whether `omx exec` supports stdin prompt (`-`) or prompt-file options.
- If OMX cannot read stdin/file directly, use a short argv prompt that references an ignored prompt file path and contains no secrets.
- Never include secrets or sensitive material in executor prompts.

### 3. OMX update prompt can stall background execution

Initial OMX run paused at:

```text
[omx] Update available: v0.16.0 → v0.17.2. Update now? [Y/n]
```

Action taken:

- Responded `n` manually via `process submit` because tool/global updates require user approval.

Recommended fix:

- Add preflight step before long background OMX runs:
  - launch
  - immediate `process poll`
  - detect update/auth/interactive prompts
  - answer safe defaults only when policy allows, otherwise ask user
- Investigate OMX environment variable or flag to disable update prompt.

### 4. Some harness docs still understate `delegate_task` caveat

Policy is mostly aligned in:

- `AGENTS.md`
- `config/routing.yaml`
- `jarvis-core` skill
- `jarvis-executor-router` skill
- `hermes-agent` skill

But some harness text still lists `delegate_task` as a Producer option without strong responsiveness warnings.

Files to audit/update:

- `$HOME/jarvis/harnesses/producer-reviewer-rejection-loop.md`
- `$HOME/jarvis/harnesses/execute-codex-omx.md`
- possibly `$HOME/jarvis/harnesses/executor-router.md`

Recommended wording:

- `delegate_task` is synchronous and non-durable.
- Do not use it for long Producer/Reviewer/documentation work when the main JARVIS channel must remain responsive.
- Prefer background Codex/OMX/Claude processes, `/background`, cron, or kanban for long work.

### 5. Active implementation pipeline isolation

Do not change workflow/routing/harness defaults while `hermes-slide-director` Phase 13 is still mid-review/integration.

Safe sequence:

1. Finish Phase 13 review.
2. Verify app repo tests/smoke.
3. Commit/push Phase 13.
4. Update JARVIS wiki/status for Phase 13.
5. Then perform background executor hygiene cleanup as a separate control-plane task.

## Proposed cleanup task after Phase 13

Task name:

`JARVIS background executor hygiene cleanup`

Scope:

- JARVIS control-plane repo only: `$HOME/jarvis`
- No app repo changes unless needed for status links

Acceptance criteria:

1. Runtime executor state does not dirty `$HOME/jarvis` root.
2. Executor prompt/log paths are standardized under ignored runtime directories.
3. `.gitignore` covers only intended runtime artifacts without hiding tracked wiki/project files.
4. Harness docs clearly distinguish:
   - synchronous `delegate_task`
   - background external executors
   - Hermes `/goal`
   - cron/kanban durability
5. Codex/OMX launch templates avoid placing long prompts in argv when possible.
6. Safe preflight/poll procedure handles update/auth prompts.
7. `git status`, `git diff --check`, and YAML checks pass.
8. If behavior becomes reusable, patch/create a Hermes skill.

## Suggested verification commands

```bash
git -C $HOME/jarvis status -sb
git -C $HOME/jarvis diff --check
python3 - <<'PY'
from pathlib import Path
import yaml
root = Path.home() / "jarvis"
for p in [root / "config/routing.yaml", root / "config/projects.yaml"]:
    yaml.safe_load(p.read_text())
    print('YAML OK:', p)
PY
```

## Current known cleanup candidates

- Move or ignore `$HOME/jarvis/executor-prompts/`.
- Decide whether to ignore or remove local `$HOME/jarvis/.omx/` after Phase 13 is fully integrated.
- Prefer future executor prompt files under `$HOME/jarvis/tmp/executor-prompts/` or `$HOME/jarvis/runs/executor-runs/`.
- Investigate OMX stdin/prompt-file support.
- Strengthen harness docs around main-channel responsiveness.
