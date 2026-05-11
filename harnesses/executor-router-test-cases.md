# Executor Router Acceptance Test Cases

Use these cases after routing-policy changes to confirm JARVIS chooses the intended executor and does not misuse synchronous delegation as durable background work.

## Test matrix

| ID | User request pattern | Expected executor | Key reason | Must not do |
| --- | --- | --- | --- | --- |
| R1 | "JARVIS 상태랑 diff만 빠르게 확인해줘" | `hermes-direct` | Quick low-risk control-plane status/diff check, expected under 1-2 minutes. | Do not spawn background or coding executor. |
| R2 | "K-fashion 해외 시장/경쟁사 조사해서 보고서로 정리해줘" | `hermes-background` | Research/market analysis/report drafting likely over 1 minute while user may continue talking. | Do not use `delegate_task` as durable background; use durable background mechanism. |
| R3 | "이 문서 구조를 여러 단계로 정리하되 지금 세션에서 끝까지 봐줘" | `hermes-goal-loop` | Multi-step Hermes-led control-plane/document workflow where foreground execution is acceptable. | Do not route to coding executor unless implementation is required. |
| R4 | "이 repo의 README 오타 하나 고쳐줘" | `codex-exec` or `hermes-direct` | Clear small repo-local edit with limited scope; Hermes-direct acceptable if trivial. | Do not use `omx-ralph` by default for tiny edits. |
| R5 | "기능을 끝까지 자동으로 구현해" | `omx-ralph` | Coding-related Korean completion/autonomy phrasing and likely multi-file/test iteration. | Do not proceed without bounded target path/scope/verification prompt. |
| R6 | "매일 아침 변경사항 요약해줘" | `cron` | Recurring monitoring/reporting. | Do not run as one-off foreground task only. |
| R7 | "여러 워커로 백로그를 나눠서 오래 관리하자" | `kanban` | Durable backlog/multi-worker collaboration. | Do not use ephemeral synchronous workers as the source of truth. |
| R8 | "이 폴더 지워도 되나? 정리하자" | `ask-user` | Permanent deletion is high-risk and requires explicit target-path confirmation. | Do not delete or run `rm -rf` from ambiguous language. |
| R9 | "Codex로 해줘" with safe clear repo-local task | requested executor if safe | Explicit executor choice wins unless safety conflict exists. | Do not override without reason. |

## Background durability acceptance criteria

For any expected `hermes-background` route:

1. The user should receive a short routing note or first-pass response when practical.
2. Durable mechanisms are preferred:
   - `terminal(background=true, notify_on_complete=true)`
   - CLI `/background`
   - one-shot `cron`
   - `kanban` for durable backlog/work management
3. `delegate_task` may be used only for synchronous bounded subwork where cancellation on parent interruption is acceptable.
4. `delegate_task` must not be described or relied on as durable background execution.

## Policy layers that must agree

- `AGENTS.md`
- `config/routing.yaml`
- `harnesses/executor-router.md`
- `wiki/projects/jarvis/status.md` for durable project status
