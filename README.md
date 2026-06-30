<div align="center">

# just-chill

**Hermes와 GJC 사이의 라우팅·메모리 정책·승인 검증 하네스**

![Status](https://img.shields.io/badge/status-active-10b981?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3-3776ab?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-3b82f6?style=for-the-badge)

</div>

---

## 목적

Hermes(사용자 대면 에이전트)와 GJC(개발 실행기) 사이에서 정책 레이어 역할을 한다.

- **Hermes**가 요청을 받으면 → **just-chill**이 분류·라우팅·승인 검증·GJC 핸드오프 계획을 생성
- **GJC**가 실제 구현·검증을 수행하고 내구성 있는 증거를 Hermes에 반환

just-chill은 독립형 CLI 제품도, 숨겨진 실행기도, 메모리 데이터베이스도 아니다. Hermes와 GJC의 권한 경계를 지키는 정책 하네스다.

---

## 원리 / 동작 방식

```text
User
  → Hermes
       → just-chill 하네스
            → 요청 분류 (dev / non-dev / 고위험)
            → 메모리·회수·승인 게이트 구성
            → GJC 핸드오프 계획 생성 (개발 작업인 경우)
       → 호스트 소유 브리지
            → 가시 GJC 세션 또는 승인된 coordinator/delegate 경로
            → 내구성 있는 증거 (turn_id, 아티팩트, 테스트 결과 등) 반환
       → Hermes 메모리·아티팩트 도구
            → 정식 저장·회수·감사·사용자 연속성 관리
```

**권한 경계**

| 레이어 | 소유 | 소유 불가 |
|---|---|---|
| Hermes | 사용자 UX, 정식 메모리/아티팩트, 도구 호출 | GJC 내부 또는 just-chill 정책 결정 |
| just-chill | 라우팅, 정책, 승인 검증, 회수 게이트, GJC 핸드오프 계약 | GJC 실행, Hermes 쓰기, 벡터 검색 |
| GJC | 개발 실행, 계획 워크플로, 검증 구현 | 개인 메모리 권한 또는 Hermes UX |

라우팅은 `scripts/just_chill_router.py`의 키워드·신호 기반 결정론적 분류기로 수행되며, `gjc-direct` / `gjc-deep-interview` / `gjc-ralplan` / `gjc-ultragoal` 등의 경로로 분기한다. 실행 브리지(`scripts/just_chill_gjc_execution_bridge.py`)는 **가시 세션 전용**으로 제한되며 숨겨진 GJC 실행은 허용하지 않는다.

---

## 주요 기능

| 표면 | 파일 |
|---|---|
| 요청 라우터 및 GJC 브리지 계약 | `scripts/just_chill_router.py`, `scripts/just_chill_bridge.py` |
| Hermes 대면 하네스 (MCP 래퍼 포함) | `scripts/just_chill_harness.py`, `scripts/just_chill_harness_mcp.py` |
| Hermes 메인 도그푸드 하네스 | `scripts/just_chill_hermes_harness.py` |
| 승인 레지스트리 (토큰 해시·스코프·만료·취소 검증) | `scripts/just_chill_approval_registry.py` |
| 메모리 계약 및 마이그레이션 픽스처 | `scripts/just_chill_memory_contracts.py`, `scripts/just_chill_memory_migration_fixture.py` |
| 원시 아티팩트 스테이징 | `scripts/just_chill_raw_artifact_store.py` |
| 벡터 사이드카 및 회수 게이트 | `scripts/just_chill_vector_recall.py` |
| 온톨로지/RDF/SHACL 계약 | `scripts/just_chill_ontology_contracts.py`, `scripts/just_chill_rdf_persistence_receipts.py` |
| Hermes 메모리 MCP API | `scripts/just_chill_hermes_memory_mcp.py` |
| coordinator/delegate 동의 정책 | `scripts/just_chill_gjc_consent_policy.py` |
| 가시 GJC 세션 헬퍼 | `scripts/create-gjc-session`, `scripts/prompt-gjc-session`, `scripts/tail-gjc-session` |
| 디버그/테스트 CLI | `scripts/just_chill_cli.py`, `scripts/just-chill` |

Hermes MCP 등록 상태: `just_chill_memory_api`와 `just_chill_harness`가 등록·활성화됨. 신선한 Hermes 세션에서 `just_chill.status: ready` 확인됨.

---

## 설치 & 사용법

**전체 회귀 검사 실행** (권장)

```sh
python3 scripts/check_all.py
```

`check_all.py`는 모든 `scripts/check_*.py`를 서브프로세스로 실행하고 PASS/FAIL 요약을 출력한다.

**개별 표면 검사 예시**

```sh
python3 scripts/check_just_chill_router.py
python3 scripts/check_just_chill_harness.py
python3 scripts/check_just_chill_approval_registry.py
```

**디버그 CLI**

```sh
scripts/just-chill classify "GJC로 인증 모듈 구현해줘"
```

---

## 요구사항 / 의존성

- Python 3.11+
- `pyproject.toml` 참조 (외부 패키지 의존성 최소화)
- Hermes 세션과 GJC가 실행 중인 JARVIS 컨트롤 플레인 환경 필요

---

## 주요 변경 이력

| 시기 | 내용 |
|---|---|
| 2026-05-06 | JARVIS 컨트롤 플레인 초기화 — 삭제 명시적 확인 정책 포함 |
| 2026-05-11 | 라우팅 스모크 테스트 완료, 온톨로지 기반 LLM 위키 및 Hermes 백그라운드 라우팅 점검 기초 수립 |
| 2026-05-12 | executor 모델 정립 및 README 재정비, JARVIS 근거·빌드 이력 정의 |
| 2026-06-11~12 | vNext 아키텍처 설계 — 실행 가드레일·권한 경계·에이전트 역할 정의, 적대적 설계 검토 반영 |
| 2026-06-26 | Hermes 하네스 구현 완료, LICENSE·CI·패키징 메타데이터 및 `check_all` 집계기 추가 |

---

## 라이선스

[MIT License](LICENSE) — Copyright (c) 2026 Han43seong
