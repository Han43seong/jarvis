<div align="center">

# JARVIS Control Plane

**A Hermes-centered control plane for AI-assisted software work.**

Plan work, route it to the right executor, verify results, and preserve durable knowledge.

<br />

![Status](https://img.shields.io/badge/status-active-10b981?style=for-the-badge)
![Control Plane](https://img.shields.io/badge/role-control--plane-7170ff?style=for-the-badge)
![Hermes](https://img.shields.io/badge/orchestrator-Hermes-5e6ad2?style=for-the-badge)
![Codex OMX](https://img.shields.io/badge/primary-Codex%20%2B%20OMX-111827?style=for-the-badge)
![Claude OMC](https://img.shields.io/badge/secondary-Claude%20Code%20%2B%20OMC-191a1b?style=for-the-badge)

<br />

[Overview](#overview) · [Why](#why-this-exists) · [Methodology](#methodology) · [Architecture](#architecture) · [History](#build-history-and-lessons-learned) · [Korean](#jarvis-컨트롤-플레인)

</div>

---

## Overview

JARVIS is not an application repository. It is a **control plane**: a compact, durable workspace for project registry, routing policy, operating rules, wiki notes, execution harnesses, and verification records.

It exists to make AI-assisted work more operationally reliable:

- choose the right executor for each task,
- keep application code outside the control-plane repository,
- separate production from review for quality-sensitive work,
- verify every meaningful change with git state, diffs, tests, or targeted checks,
- preserve durable decisions in the wiki,
- promote reusable procedures into skills.

## Why this exists

The initial idea was to build a practical personal JARVIS: **not a single all-powerful coding bot**, but a control plane that can coordinate multiple AI executors, remember durable context, and keep work verifiable.

The core design assumption is that AI work becomes safer and more useful when responsibilities are separated:

| Concern | Owner | Purpose |
| --- | --- | --- |
| Planning and routing | Hermes / JARVIS | Choose the smallest capable execution path. |
| Production | Producer agents | Implement code, create artifacts, or generate designs inside bounded scope. |
| Independent review | Reviewer/Critic agents | Judge producer output against the original spec and return pass/change/escalate/abort. |
| Revision planning | Hermes / JARVIS | Convert reviewer findings into bounded producer instructions. |
| Verification | Hermes / JARVIS | Check repo state, diffs, tests, lint, artifacts, and completion criteria. |
| Durable knowledge | Wiki | Preserve decisions, status, architecture, and research. |
| Reusable procedure | Skills | Turn proven workflows into repeatable operating knowledge. |
| Source of truth | Git | Record exactly what changed. |

## Methodology

JARVIS follows a control-plane methodology:

1. Keep the control plane small and focused on documentation, configuration, routing, and verification.
2. Keep application source code in independent project repositories.
3. Route each task to the smallest capable executor.
4. Use a Producer/Reviewer rejection loop for non-trivial implementation, design, and quality-sensitive artifacts.
5. Give executors bounded prompts, allowed scope, forbidden actions, and clear completion criteria.
6. Verify results with repo state, diffs, tests, lint, or targeted checks before reporting success.
7. Promote recurring workflows into skills; promote durable knowledge into the wiki; keep memory compact.
8. Prefer reversible, inspectable changes over hidden automation.

## Architecture

```text
User intent
   │
   ▼
Hermes / JARVIS control plane
   ├─ plans and decomposes work
   ├─ routes to the right executor
   ├─ runs Producer/Reviewer rejection loops when quality warrants it
   ├─ verifies diffs, tests, and repo state
   ├─ updates durable wiki/status notes
   └─ preserves reusable procedures as skills
        │
        ├─ Codex CLI + OMX          Codex-family producer line
        ├─ Claude Code + OMC        Claude-family producer/reviewer line
        ├─ Hermes direct tools      quick edits, docs, checks, wiki maintenance
        ├─ background workers       research, comparison, long inspections
        └─ cron / kanban            recurring or durable multi-step work
```

## Executor matrix

| Executor path | Best for | Notes |
| --- | --- | --- |
| **Hermes direct** | Small edits, docs, config checks, wiki maintenance | Fastest path for low-risk control-plane work. |
| **Codex CLI + OMX** | Codex-family production work: medium/large implementation, bounded repo-local edits | `omx` is the oh-my-codex orchestration layer on top of Codex CLI. |
| **Claude Code + OMC** | Claude-family production/review work: planning, refactoring, design-heavy artifacts, independent critique | `omc` is the oh-my-claudecode orchestration layer on top of Claude Code. |
| **Producer/Reviewer loop** | Non-trivial implementation, design, and quality-sensitive artifacts | Producer and Reviewer are separate; reviewer returns `PASS`, `REQUEST_CHANGES`, `ESCALATE_TO_USER`, or `ABORT`. |
| **Background workers** | Research, comparison, long inspections | Keeps the main JARVIS session responsive. |
| **cron** | Recurring monitoring/reporting | For scheduled checks and reports. |
| **kanban** | Durable multi-worker backlog | For longer-running coordinated work. |

## Producer/Reviewer rejection loop

For non-trivial work, JARVIS separates creation from review:

```text
User request
  -> JARVIS Director defines scope, criteria, allowed paths, forbidden actions, and verification commands
  -> Producer agent creates or modifies the artifact
  -> JARVIS runs basic git/test/artifact checks
  -> Reviewer/Critic agent independently evaluates against the original criteria
  -> JARVIS accepts, escalates, aborts, or turns findings into a bounded revision prompt
  -> repeat until pass or max iteration
```

This loop is selective. It is used for medium/large implementation, design/deck generation, quality-sensitive artifacts, explicit rejection-loop requests, and `hermes-slide-director` development. It is skipped for quick reads, simple status checks, one-line docs/config edits, and local server start/stop.

The durable protocol lives at `harnesses/producer-reviewer-rejection-loop.md`, with routing policy in `config/routing.yaml` and active agent instructions in `AGENTS.md`.

## Repository layout

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Standing operating rules for JARVIS sessions launched from this repository. |
| `config/projects.yaml` | Project registry. |
| `config/routing.yaml` | Executor routing policy, including selective Producer/Reviewer loop triggers. |
| `harnesses/` | Reusable execution procedures and verification harnesses, including the Producer/Reviewer rejection-loop protocol. |
| `plans/` | Implementation and migration plans. |
| `runs/` | Run logs and executor summaries. |
| `scripts/` | Helper scripts for control-plane checks and automation. |
| `wiki/` | Obsidian-readable long-term project knowledge. |
| `logs/` | Local workflow logs. |
| `tmp/` | Temporary control-plane files. |

## Project repository model

Application source code should stay outside this control-plane repository.

Each application project should normally be:

1. created as its own directory,
2. initialized as its own git repository,
3. optionally connected to its own GitHub repository,
4. registered in `config/projects.yaml`, and
5. documented under `wiki/projects/<project>/` when durable notes are useful.

This separation keeps orchestration history, project source, CI, remotes, and executor activity cleanly isolated.

## Typical workflow

```text
1. Capture the request and identify the target project.
2. Inspect current repo state and relevant project/wiki context.
3. Select an executor mode.
4. Decide whether the Producer/Reviewer loop is warranted.
5. Prepare a bounded prompt or direct edit plan.
6. Execute with the selected tool or external CLI executor.
7. If looped, run an independent reviewer and convert findings into bounded revision instructions.
8. Verify with git status, git diff, tests, lint, or targeted checks.
9. Record durable decisions/status in the wiki.
10. Commit only the intended files.
```

## Safety baseline

JARVIS is designed for high autonomy with explicit safety gates.

| Guardrail | Policy |
| --- | --- |
| Low-risk local automation | Allowed with smart approval. |
| Secrets | Never store API keys, OAuth tokens, private keys, auth files, or credential contents in this repository. |
| Permanent deletion | Requires explicit confirmation naming the exact target. |
| Push/deploy/auth changes | Requires a clear user request. |
| Broad rewrites | Require clear scope and confirmation. |

## Documentation policy

Use the right durability layer:

| Layer | Use it for |
| --- | --- |
| `README.md` | Public orientation and operating model. |
| `AGENTS.md` | Active operating instructions for agents launched in this workspace. |
| `wiki/` | Durable human-readable knowledge, decisions, status, and research. |
| Hermes memory | Compact durable facts and preferences only. |
| Hermes skills | Reusable procedures that should guide future agent behavior. |

## Build history and lessons learned

The workflow was assembled iteratively. Important decisions and fixes include:

| Area | What happened | Lesson |
| --- | --- | --- |
| Control-plane boundary | Established this repository as a management workspace rather than an application repository. | Keep orchestration separate from application source. |
| Routing | Added a project registry and routing policy so JARVIS can choose between Hermes direct work, Codex/OMX, Claude Code/OMC, background workers, cron, kanban, and selective Producer/Reviewer loops. | Routing should be explicit, not improvised. |
| Producer/Reviewer loop | Wired the loop into `AGENTS.md`, `config/routing.yaml`, `harnesses/producer-reviewer-rejection-loop.md`, README, and relevant JARVIS skills. | Quality-sensitive work needs independent critique, but loop overhead should remain selective. |
| Primary executor | Verified the Codex CLI + OMX line with smoke tests before treating it as the primary implementation path. | Executor trust should be earned by live verification. |
| Safety | Added sandbox and approval hardening so routine automation can proceed while destructive operations remain gated. | Autonomy needs guardrails. |
| Wiki | Built an ontology-informed markdown wiki for decisions, research, status, and architecture notes. | Durable knowledge should be human-readable and git-friendly. |
| Research | Added background/research-worker conventions after long research tasks began blocking the main chat. | Long-running reasoning belongs outside the foreground loop. |
| MCP bridge | Deferred the OMX Hermes MCP bridge after investigation showed it was promising but not yet stable enough for the default path. | Do not promote unstable integration paths into core workflow. |
| Claude Code auth | Refreshed Claude Code OAuth through an interactive terminal session after print mode returned an authentication error. | Interactive login status and print-mode auth must be verified separately. |
| OMC setup | Confirmed the correct package/repository naming before installation. | Similar package names should be verified before installing. |
| Commit hygiene | Avoided committing large or unrelated research artifacts during setup and README commits. | Stage only intended files. |

---

<div align="center">

# JARVIS 컨트롤 플레인

**Hermes 중심의 AI 보조 개발 작업 관제 워크스페이스.**

작업을 계획하고, 적절한 실행자에게 라우팅하고, 결과를 검증하며, 장기 지식을 보존합니다.

</div>

## 개요

JARVIS는 애플리케이션 소스 저장소가 아닙니다. 프로젝트 레지스트리, 라우팅 정책, 운영 규칙, 위키, 실행 하네스, 검증 기록을 관리하는 **컨트롤 플레인**입니다.

목표는 AI 보조 작업을 더 안정적으로 운영하는 것입니다.

- 작업마다 적절한 실행자를 선택합니다.
- 애플리케이션 코드는 컨트롤 플레인 저장소 밖에 둡니다.
- 중요한 작업에서는 제작자와 검토자를 분리해 품질을 안정화합니다.
- 중요한 변경은 git 상태, diff, 테스트, 표적 점검으로 검증합니다.
- 장기 결정사항은 위키에 남깁니다.
- 반복 가능한 절차는 skill로 승격합니다.

## 왜 만들었는가

초기 구상은 실무적으로 쓸 수 있는 개인용 JARVIS를 만드는 것이었습니다. 하나의 만능 코딩 봇이 아니라, 여러 AI 실행자를 조율하고, 중요한 맥락을 기억하고, 결과를 검증 가능한 형태로 남기는 컨트롤 플레인을 만드는 것이 핵심입니다.

기본 전제는 명확합니다. AI 작업은 계획, 실행, 검증, 기억을 분리할수록 더 안전하고 유용해집니다.

| 관심사 | 담당 | 목적 |
| --- | --- | --- |
| 계획과 라우팅 | Hermes / JARVIS | 처리 가능한 가장 작은 실행 경로를 선택합니다. |
| 제작 | Producer 에이전트 | 제한된 범위 안에서 코드, 산출물, 디자인을 만듭니다. |
| 독립 검토 | Reviewer/Critic 에이전트 | 원래 기준에 비춰 통과/수정/에스컬레이션/중단을 판정합니다. |
| 수정 계획 | Hermes / JARVIS | 반려 사유를 다음 제작자가 실행 가능한 지시로 바꿉니다. |
| 검증 | Hermes / JARVIS | 저장소 상태, diff, 테스트, lint, 산출물, 완료 기준을 확인합니다. |
| 장기 지식 | Wiki | 결정사항, 상태, 아키텍처, 리서치를 보관합니다. |
| 재사용 절차 | Skills | 검증된 워크플로우를 반복 가능한 운영 지식으로 만듭니다. |
| 변경 기준 | Git | 실제 변경 사항을 기록합니다. |

## 방법론

JARVIS는 컨트롤 플레인 방법론을 따릅니다.

1. 컨트롤 플레인은 작고 명확하게 유지하며 주로 문서, 설정, 라우팅, 검증을 담당합니다.
2. 애플리케이션 소스코드는 독립 프로젝트 저장소에 둡니다.
3. 각 작업은 처리 가능한 가장 작은 실행자에게 라우팅합니다.
4. 중대형 구현, 디자인, 품질 민감 산출물에는 Producer/Reviewer 반려 루프를 사용합니다.
5. 실행자에게는 제한된 프롬프트, 허용 범위, 금지 행동, 완료 기준을 함께 제공합니다.
6. 성공 보고 전에는 저장소 상태, diff, 테스트, lint, 표적 점검으로 검증합니다.
7. 반복되는 절차는 skill로, 장기 지식은 wiki로, 아주 압축된 사실만 memory로 보존합니다.
8. 숨겨진 자동화보다 되돌릴 수 있고 검토 가능한 변경을 우선합니다.

## 아키텍처

```text
사용자 요청
   │
   ▼
Hermes / JARVIS 컨트롤 플레인
   ├─ 작업 계획 및 분해
   ├─ 적절한 실행자 선택
   ├─ 필요 시 Producer/Reviewer 반려 루프 실행
   ├─ diff, 테스트, 저장소 상태 검증
   ├─ 장기 위키/상태 문서 업데이트
   └─ 재사용 가능한 절차는 skill로 보존
        │
        ├─ Codex CLI + OMX          Codex 계열 제작자 라인
        ├─ Claude Code + OMC        Claude 계열 제작/검토 라인
        ├─ Hermes direct tools      빠른 수정, 문서, 점검, 위키 관리
        ├─ background workers       조사, 비교, 장시간 분석
        └─ cron / kanban            반복 모니터링 또는 지속형 작업
```

## 실행자 매트릭스

| 실행 경로 | 적합한 작업 | 비고 |
| --- | --- | --- |
| **Hermes direct** | 작은 수정, 문서, 설정 점검, 위키 관리 | 저위험 컨트롤 플레인 작업에 가장 빠른 경로입니다. |
| **Codex CLI + OMX** | Codex 계열 제작 작업: 중대형 구현, 제한된 저장소 수정 | `omx`는 Codex CLI 위의 oh-my-codex 오케스트레이션 계층입니다. |
| **Claude Code + OMC** | Claude 계열 제작/검토 작업: 계획, 리팩터링, 디자인 중심 산출물, 독립 비평 | `omc`는 Claude Code 위의 oh-my-claudecode 오케스트레이션 계층입니다. |
| **Producer/Reviewer 루프** | 중대형 구현, 디자인, 품질 민감 산출물 | 제작자와 검토자를 분리하고 `PASS`, `REQUEST_CHANGES`, `ESCALATE_TO_USER`, `ABORT`로 판정합니다. |
| **Background workers** | 조사, 비교, 장시간 분석 | 메인 JARVIS 세션의 응답성을 유지합니다. |
| **cron** | 반복 모니터링/보고 | 예약 점검과 보고에 사용합니다. |
| **kanban** | 지속형 다중 작업 백로그 | 긴 협업형 작업에 사용합니다. |

## Producer/Reviewer 반려 루프

비사소한 작업에서는 JARVIS가 제작과 검토를 분리합니다.

```text
사용자 요청
  -> JARVIS Director가 범위, 기준, 허용 경로, 금지 행동, 검증 명령을 정의
  -> Producer 에이전트가 산출물을 생성/수정
  -> JARVIS가 기본 git/test/artifact 점검
  -> Reviewer/Critic 에이전트가 원래 기준에 따라 독립 평가
  -> JARVIS가 승인, 에스컬레이션, 중단, 또는 제한된 수정 지시 생성
  -> 통과 또는 최대 반복까지 반복
```

이 루프는 선택적으로 사용합니다. 중대형 구현, 디자인/슬라이드 생성, 품질 민감 산출물, 명시적 반려 루프 요청, `hermes-slide-director` 개발에 적용합니다. 빠른 읽기, 단순 상태 확인, 한 줄 문서/설정 수정, 로컬 서버 시작/중지는 제외합니다.

구체 프로토콜은 `harnesses/producer-reviewer-rejection-loop.md`, 라우팅 정책은 `config/routing.yaml`, 실제 에이전트 운영 지침은 `AGENTS.md`에 있습니다.

## 저장소 구조

| 경로 | 목적 |
| --- | --- |
| `AGENTS.md` | 이 저장소에서 시작되는 JARVIS 세션의 상시 운영 규칙. |
| `config/projects.yaml` | 프로젝트 레지스트리. |
| `config/routing.yaml` | 실행자 라우팅 정책과 선택적 Producer/Reviewer 루프 트리거. |
| `harnesses/` | 재사용 가능한 실행 절차와 검증 하네스. Producer/Reviewer 반려 루프 프로토콜을 포함합니다. |
| `plans/` | 구현 및 마이그레이션 계획. |
| `runs/` | 실행 로그와 executor 요약. |
| `scripts/` | 컨트롤 플레인 점검 및 자동화 보조 스크립트. |
| `wiki/` | Obsidian에서도 읽을 수 있는 장기 프로젝트 지식. |
| `logs/` | 로컬 워크플로 로그. |
| `tmp/` | 임시 작업 파일. |

## 프로젝트 저장소 모델

애플리케이션 소스코드는 이 컨트롤 플레인 저장소 안에 넣지 않는 것을 원칙으로 합니다.

각 애플리케이션 프로젝트는 일반적으로 다음 흐름을 따릅니다.

1. 별도 디렉터리로 생성합니다.
2. 독립 git 저장소로 초기화합니다.
3. 필요하면 별도 GitHub 저장소에 연결합니다.
4. `config/projects.yaml`에 등록합니다.
5. 장기 문서가 필요하면 `wiki/projects/<project>/` 아래에 정리합니다.

이 구조는 관제 기록, 프로젝트 소스, CI, remote, executor 작업 이력을 깔끔하게 분리하기 위한 것입니다.

## 일반 작업 흐름

```text
1. 요청과 대상 프로젝트를 파악합니다.
2. 현재 저장소 상태와 관련 문서/위키 맥락을 확인합니다.
3. 실행자 모드를 선택합니다.
4. Producer/Reviewer 루프가 필요한지 판단합니다.
5. 제한된 프롬프트 또는 직접 수정 계획을 준비합니다.
6. 선택한 도구 또는 외부 CLI 실행자로 작업합니다.
7. 루프 대상이면 독립 reviewer를 실행하고 반려 사유를 제한된 수정 지시로 변환합니다.
8. git status, git diff, 테스트, lint, 표적 점검으로 검증합니다.
9. 장기적으로 남길 결정/상태는 위키에 기록합니다.
10. 의도한 파일만 커밋합니다.
```

## 안전 기준

JARVIS는 높은 자율성을 목표로 하지만 명시적인 안전 게이트를 둡니다.

| 기준 | 정책 |
| --- | --- |
| 저위험 로컬 자동화 | smart approval 기반으로 처리합니다. |
| 시크릿 | API key, OAuth token, private key, auth file, credential 내용은 저장소에 보관하지 않습니다. |
| 영구 삭제 | 정확한 대상 경로를 명시한 사용자 확인이 필요합니다. |
| push/deploy/auth 변경 | 사용자의 명확한 요청이 필요합니다. |
| 광범위한 rewrite | 명확한 범위와 확인이 필요합니다. |

## 문서화 정책

정보의 성격에 따라 저장 위치를 분리합니다.

| 계층 | 용도 |
| --- | --- |
| `README.md` | 공개 가능한 개요와 운영 모델. |
| `AGENTS.md` | 이 워크스페이스에서 실행되는 에이전트의 실제 운영 지침. |
| `wiki/` | 장기 지식, 결정사항, 상태, 리서치. |
| Hermes memory | 앞으로도 유용한 압축된 사실과 선호도. |
| Hermes skills | 향후 에이전트 행동을 직접 안내해야 하는 재사용 절차. |

## 구축 이력과 해결한 문제

이 워크플로우는 한 번에 만든 것이 아니라 단계적으로 구축했습니다.

| 영역 | 발생한 일 | 배운 점 |
| --- | --- | --- |
| 컨트롤 플레인 경계 | 이 저장소를 애플리케이션 저장소가 아니라 관리 워크스페이스로 정의했습니다. | 관제와 애플리케이션 소스는 분리해야 합니다. |
| 라우팅 | Hermes direct, Codex/OMX, Claude Code/OMC, background worker, cron, kanban, 선택적 Producer/Reviewer 루프 중 선택할 수 있도록 레지스트리와 라우팅 정책을 추가했습니다. | 라우팅은 즉흥적으로 정하지 않고 명시해야 합니다. |
| Producer/Reviewer 루프 | `AGENTS.md`, `config/routing.yaml`, `harnesses/producer-reviewer-rejection-loop.md`, README, 관련 JARVIS skill에 루프 정책을 연결했습니다. | 품질 민감 작업에는 독립 비평이 필요하지만, 루프 비용은 선택적으로 써야 합니다. |
| 기본 실행자 | Codex CLI + OMX 라인을 smoke test로 검증한 뒤 기본 구현 경로로 채택했습니다. | 실행자 신뢰는 실제 검증으로 확보해야 합니다. |
| 안전성 | sandbox와 approval 정책을 정리했습니다. | 자율성에는 안전 게이트가 필요합니다. |
| 위키 | ontology-informed markdown wiki를 구축했습니다. | 장기 지식은 사람이 읽기 쉽고 git 친화적이어야 합니다. |
| 리서치 | 긴 조사 작업은 background/research-worker로 분리했습니다. | 장시간 추론은 foreground loop 밖에서 처리하는 편이 좋습니다. |
| MCP bridge | OMX Hermes MCP bridge는 안정화 부족으로 기본 경로 도입을 보류했습니다. | 불안정한 통합은 core workflow로 승격하지 않습니다. |
| Claude Code 인증 | print mode 인증 오류를 interactive OAuth 갱신과 별도 smoke test로 해결했습니다. | interactive 로그인과 print-mode 인증은 별도로 검증해야 합니다. |
| OMC 설치 | 정확한 패키지/저장소 이름을 확인한 뒤 설치했습니다. | 유사 패키지명은 설치 전 검증해야 합니다. |
| 커밋 위생 | 대용량 또는 관련 없는 리서치 산출물은 README/세팅 커밋에서 제외했습니다. | 의도한 파일만 stage합니다. |
