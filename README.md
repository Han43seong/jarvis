# JARVIS Control Plane

> A Hermes-centered operating workspace for planning, routing, verifying, and documenting AI-assisted software work.

JARVIS is not an application repository. It is a control plane: a small, durable workspace that keeps project registry, routing policy, operating rules, wiki notes, execution harnesses, and verification records in one place.

## Operating model

```text
User intent
   │
   ▼
Hermes / JARVIS control plane
   ├─ plans and decomposes work
   ├─ routes to the right executor
   ├─ verifies diffs, tests, and repo state
   ├─ updates durable wiki/status notes
   └─ preserves reusable procedures as skills
        │
        ├─ Codex CLI + OMX          primary coding executor line
        ├─ Claude Code + OMC        secondary executor line for review, planning, refactoring, and Claude-strength reasoning
        ├─ Hermes direct tools      quick edits, docs, checks, wiki maintenance
        ├─ background workers       research, comparison, long inspections
        └─ cron / kanban            recurring or durable multi-step work
```

## Core roles

| Component | Role |
| --- | --- |
| Hermes Agent | Main orchestrator, planner, verifier, memory/skill manager, and wiki maintainer. |
| Codex CLI + OMX | Primary external implementation executor for medium and large coding work. |
| Claude Code + OMC | Secondary external executor for review, planning, refactoring, and Claude-specific reasoning strengths. |
| JARVIS Wiki | Human-readable long-term knowledge: status, decisions, architecture notes, research, and runbooks. |
| Project Registry | Tracks active projects, paths, repo metadata, executor defaults, and status. |

## Repository layout

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Standing operating rules for JARVIS sessions launched from this repository. |
| `config/projects.yaml` | Project registry. |
| `config/routing.yaml` | Executor routing policy. |
| `harnesses/` | Reusable execution procedures and verification harnesses. |
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

## Executor routing policy

Default routing is intentionally conservative:

- Use Hermes direct work for quick documentation, config, checks, small edits, and wiki maintenance.
- Use Codex CLI + OMX for primary medium/large implementation work.
- Use Claude Code + OMC when a second executor is useful for review, design critique, refactoring, planning, or Claude-strength reasoning.
- Use background workers for non-trivial research, comparison, and long inspections so the main session stays responsive.
- Use cron for recurring monitoring/reporting.
- Use kanban for durable multi-worker backlogs.
- Ask the user before destructive operations, deploys, pushes to protected targets, auth/secret changes, broad rewrites, or unclear scope.

## Typical workflow

```text
1. Capture the request and identify the target project.
2. Inspect current repo state and relevant project/wiki context.
3. Select an executor mode.
4. Prepare a bounded prompt or direct edit plan.
5. Execute with the selected tool or external CLI executor.
6. Verify with git status, git diff, tests, lint, or targeted checks.
7. Record durable decisions/status in the wiki.
8. Commit only the intended files.
```

## Safety baseline

JARVIS is designed for high autonomy with explicit safety gates.

Expected baseline:

- Smart approvals for low-risk local automation.
- Secret redaction enabled.
- No API keys, OAuth tokens, private keys, auth files, or credential contents stored in this repository.
- No permanent deletion without explicit confirmation naming the exact target.
- No git push, deployment, secrets/auth modification, or broad rewrite unless the user clearly requests it.

## Documentation policy

Use the right durability layer:

- `README.md`: public orientation and operating model.
- `AGENTS.md`: active operating instructions for agents launched in this workspace.
- `wiki/`: durable human-readable knowledge, decisions, status, and research.
- Hermes memory: compact durable facts and preferences only.
- Hermes skills: reusable procedures that should guide future agent behavior.

---

# JARVIS 컨트롤 플레인

> Hermes를 중심으로 AI 보조 개발 작업을 계획, 라우팅, 검증, 문서화하기 위한 운영 워크스페이스입니다.

JARVIS는 애플리케이션 소스 저장소가 아닙니다. 여러 프로젝트를 관리하기 위한 컨트롤 플레인입니다. 프로젝트 레지스트리, 라우팅 정책, 운영 규칙, 위키, 실행 하네스, 검증 기록을 한곳에서 관리합니다.

## 운영 모델

```text
사용자 요청
   │
   ▼
Hermes / JARVIS 컨트롤 플레인
   ├─ 작업 계획 및 분해
   ├─ 적절한 실행자 선택
   ├─ diff, 테스트, 저장소 상태 검증
   ├─ 장기 위키/상태 문서 업데이트
   └─ 재사용 가능한 절차는 skill로 보존
        │
        ├─ Codex CLI + OMX          주 실행자 라인
        ├─ Claude Code + OMC        리뷰, 설계, 리팩터링, Claude 강점 작업용 보조 실행자 라인
        ├─ Hermes direct tools      빠른 수정, 문서, 점검, 위키 관리
        ├─ background workers       조사, 비교, 장시간 분석
        └─ cron / kanban            반복 모니터링 또는 지속형 작업
```

## 핵심 역할

| 구성요소 | 역할 |
| --- | --- |
| Hermes Agent | 메인 관제탑, 계획자, 검증자, 메모리/스킬 관리자, 위키 관리자. |
| Codex CLI + OMX | 중대형 구현 작업의 기본 외부 실행자. |
| Claude Code + OMC | 리뷰, 설계, 리팩터링, Claude 특화 추론 작업을 위한 보조 외부 실행자. |
| JARVIS Wiki | 상태, 결정사항, 아키텍처, 리서치, 런북을 보관하는 장기 지식 저장소. |
| Project Registry | 활성 프로젝트, 저장소 메타데이터, 기본 실행자, 상태를 관리하는 레지스트리. |

## 저장소 구조

| 경로 | 목적 |
| --- | --- |
| `AGENTS.md` | 이 저장소에서 시작되는 JARVIS 세션의 상시 운영 규칙. |
| `config/projects.yaml` | 프로젝트 레지스트리. |
| `config/routing.yaml` | 실행자 라우팅 정책. |
| `harnesses/` | 재사용 가능한 실행 절차와 검증 하네스. |
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

## 실행자 라우팅 정책

기본 라우팅은 보수적으로 운영합니다.

- 빠른 문서 수정, 설정 점검, 작은 변경, 위키 관리는 Hermes가 직접 처리합니다.
- 중대형 구현 작업은 기본적으로 Codex CLI + OMX 라인에 맡깁니다.
- 리뷰, 설계 비평, 리팩터링, Claude 강점 추론이 필요하면 Claude Code + OMC를 보조 실행자로 사용합니다.
- 조사, 비교, 장시간 분석은 background worker로 분리해 메인 세션 응답성을 유지합니다.
- 반복 모니터링/보고는 cron을 사용합니다.
- 지속형 다중 작업 백로그는 kanban을 사용합니다.
- 파괴적 작업, 배포, 보호 대상 push, 인증/시크릿 변경, 광범위한 rewrite, 범위가 불명확한 작업은 사용자 확인 후 진행합니다.

## 일반 작업 흐름

```text
1. 요청과 대상 프로젝트를 파악합니다.
2. 현재 저장소 상태와 관련 문서/위키 맥락을 확인합니다.
3. 실행자 모드를 선택합니다.
4. 제한된 프롬프트 또는 직접 수정 계획을 준비합니다.
5. 선택한 도구 또는 외부 CLI 실행자로 작업합니다.
6. git status, git diff, 테스트, lint, 표적 점검으로 검증합니다.
7. 장기적으로 남길 결정/상태는 위키에 기록합니다.
8. 의도한 파일만 커밋합니다.
```

## 안전 기준

JARVIS는 높은 자율성을 목표로 하지만 명시적인 안전 게이트를 둡니다.

기본 기준:

- 저위험 로컬 자동화는 smart approval 기반으로 처리합니다.
- 시크릿 redaction을 유지합니다.
- API key, OAuth token, private key, auth file, credential 내용은 저장소에 보관하지 않습니다.
- 영구 삭제는 정확한 대상 경로를 명시한 사용자 확인 없이는 수행하지 않습니다.
- git push, 배포, 인증/시크릿 변경, 광범위한 rewrite는 사용자의 명확한 요청이 있을 때만 진행합니다.

## 문서화 정책

정보의 성격에 따라 저장 위치를 분리합니다.

- `README.md`: 공개 가능한 개요와 운영 모델.
- `AGENTS.md`: 이 워크스페이스에서 실행되는 에이전트의 실제 운영 지침.
- `wiki/`: 장기 지식, 결정사항, 상태, 리서치.
- Hermes memory: 앞으로도 유용한 압축된 사실과 선호도.
- Hermes skills: 향후 에이전트 행동을 직접 안내해야 하는 재사용 절차.
