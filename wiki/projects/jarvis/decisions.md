# JARVIS Decisions

## 2026-05-06 — Hermes-first hybrid architecture

Decision:
- Use Hermes Agent as the JARVIS control plane.
- Use Codex CLI + OMX as implementation executors.
- Keep Hermes available for direct small coding, docs, validation, wiki updates, and orchestration.

Rationale:
- User wants to use Codex subscription/OAuth path for coding workflows.
- Hermes provides memory, skills, session search, cron, tool orchestration, and gateway features.
- OMX provides stronger coding execution loops for medium/large implementation.

## 2026-05-06 — Workspace layout

Decision:
- JARVIS root: `/home/hskim/jarvis`
- Active WSL project root: `/home/hskim/projects`
- Application project source stays outside the JARVIS control-plane repo.
- Each project is managed as an independent git repository and can map to its own GitHub repository.
- If `/home/hskim/jarvis/projects/` is created locally as a root-level folder or symlink, it is ignored by `.gitignore`.

Rationale:
- Keeps the control plane separate from application repositories.
- Allows Hermes to manage many projects from one place.
- Allows Codex/OMX to run inside specific target repos with `-C <repo>`.
- Keeps project history, remotes, CI, and executor work isolated per project.

## 2026-05-06 — Permission policy

Decision:
- `approvals.mode: smart`
- `approvals.cron_mode: deny`
- `security.tirith_enabled: true`
- `security.redact_secrets: true`

Rationale:
- Allows low-risk automation while keeping high-risk actions gated.
