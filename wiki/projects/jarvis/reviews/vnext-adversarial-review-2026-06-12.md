# JARVIS vNext 설계 적대적 검토 리포트

- 작성: 2026-06-12 | 검토 계약: `.gjc/plans/ralplan/2026-06-12-0815-213a/pending-approval.md` | 입력 스펙: `.gjc/specs/deep-interview-jarvis-vnext-design-review.md`
- 검토 대상: `wiki/concepts/jarvis-vnext-intent-to-contract-director.md`(C1), `wiki/projects/jarvis/decisions.md` 2026-06-11자 결정 4건(D1~D4) + 교차 코퍼스(`jarvis-vnext-meta-control-plane.md`(C2), executor-ontology, ouroboros-adoption-review, office-runtime-direction, open-source-strategy)
- 근거: 코퍼스 전문 + 외부 심층 리서치 3건(`evidence-brief-2a/2c/2d.md`, 출처 합계 24건, 전부 확인일 2026-06-12, top_claim 3건 원출처 직접 대조 완료)
- baseline: commit `6eee2a43cb596c83aa6a3d091004d0a44f38d2e8`, wiki/ 클린 시작 (`tmp/design-reviews/baseline-2026-06-12.txt`)

---

## §0 Severity 정의표

| 등급 | 의미 |
|------|------|
| BLOCK | 핵심 전제 붕괴 또는 방향 변경 필요 |
| MAJOR | 설계 수정 필요 |
| MINOR | 문서 수정 수준 |
| NOTE | 관찰·참고 |

**judgment 라벨 규칙**: 인용된 사실로부터의 명시적 추론 사슬을 갖춘 전략적 판단 Finding은 `[judgment]` 라벨을 달고 MAJOR 이상 severity를 가질 수 있다. 인용 불가능한 인상 비평은 NOTE 이하로만 허용된다.

---

## §1 Executive Verdict: **수정 (방향 조건부 유지)**

**판정: 유지/수정/부정 중 "수정".** BLOCK급 발견은 없다. vNext 방향의 뼈대 — `Understand → Contract → Delegate → Verify → Report` 기본 워크플로, backend-native 시스템 위의 Director 포지셔닝, 4계층(지침/계약/강제/증거) 분리, harness/loop 위의 Governor — 는 외부 현실 대조에서도 생존한다. 경쟁 control-plane 6곳 중 어디에도 intent→contract 컴파일 계층이 없고(2C C1), 증거 기반 완료 판정(completion gate)을 네이티브로 제공하는 backend도 없다(2D C3). 설계가 차지하려는 자리는 실제로 비어 있다.

그러나 **현재 서술 그대로는 18개월을 버티지 못한다.** 세 가지 이유다:

1. **차별화 서사(P2)의 절반은 이미 상품화됐다.** AWS Kiro와 GitHub Spec Kit이 "의도→수용기준 있는 spec" 컴파일을 제품화했고(2A C7), Codex best-of-N은 원시적 결과 선별을 내장했다(2A C4). "intent-to-contract 컴파일러"라는 명사 단독으로는 차별화가 성립하지 않는다.
2. **검증 잔존성(P1)의 서술이 공격면을 넓게 열어둔다.** Claude Code dynamic workflows는 "독립 에이전트 간 적대적 교차검증"을 공식 GA 기능으로 명문화했다(2A top_claim, 원출처 직접 확인). "검증은 JARVIS에 남는다"는 문장은 이 사실 앞에서 절반만 참이다.
3. **enforcement 전제(P3)는 backend별 강도 편차를 등급화해야만 성립한다.** Codex는 workspace 내부 파일 단위 deny가 불가하고(2D C2), completion_gates는 어떤 backend도 네이티브로 제공하지 않는다(2D C3). "가장 강한 네이티브 메커니즘으로 번역"은 등급 명시 없이는 silent downgrade를 낳는다.

**생존 공식**: 차별화 주장을 "컴파일러"에서 **"contract-파생 판정 폐루프"**(의도→계약 컴파일 → 위임 → 계약에서 파생된 scope/금지/수용기준 검사 → 이해관계 분리된 최종 판정)로 좁히고, P1을 "검증"이 아니라 **"이해관계 분리된 contract-기준 최종 판정"**으로 재정의하며, 가드레일에 **필드별 enforcement 등급**을 도입하면, 설계는 외부 근거 위에서 방어 가능하다. 이 세 가지가 §4의 핵심 수정안이다.

---

## §2 CorePremise 찬반 논증과 판정

### P1. 검증 잔존성 — "backend가 강해져도 검증은 JARVIS에 남는다"

**찬성 논거:**
- completion_gates(증거 요구 기반 완료 판정)는 Claude Code(Stop hook 근사), Codex(부재), 일반 wrapper(본질적으로 외부 영역) 어디서도 완전 네이티브가 아니다 — 최종 판정 계층이 backend로 내려갈 수 없음이 enforcement 수준에서 확인된다(2D C3, top_claim).
- 시장 다수(Golutra, Agor, CodeMachine)는 검증 책임을 명시적으로 인간 또는 사용자 정의 workflow에 떠넘긴다(2C C5). OpenAI Symphony조차 "humans review the results"로 최종 판정을 인간에 위임한다(2C C4).

**반대 논거:**
- Claude Code workflows는 "independent agents adversarially review each other's findings before they're reported"를 공식 기능으로 제공하며, ultracode는 이해→변경→검증 3-workflow 자동 분해를 수행한다(2A C3, 원출처 직접 확인). Cursor 클라우드 에이전트는 비디오/스크린샷/로그 증거를 자가생성한다(2A C5). OpenHands는 critic 결과 표시를 제품화했다(2A C6). "검증"이라는 일반 명사의 영역은 이미 침식 중이다.

**판정: 조건부 생존 — 재정의 필수.** backend의 검증은 (a) 동일 벤더·동일 세션 권한계 내부의 자가교차검증이고, (b) 사용자 의도에서 컴파일된 명시적 계약을 판정 기준으로 삼지 않으며, (c) 실행 주체와 이해관계가 분리되지 않았다. P1은 "검증 잔존"이 아니라 **"이해관계 분리된, contract-파생 기준의 최종 판정 잔존"**으로 좁혀 써야 생존한다. → F-A2

### P2. 차별화 방어력 — "intent-to-contract 컴파일러는 backend-native가 흡수하지 못한다"

**찬성 논거:**
- 경쟁 control-plane 5+1곳 전부에 intent→contract 컴파일 계층(scope/금지행위/수용기준 스키마)이 없다 — 입력 단위는 모두 issue/ticket/자유 프롬프트다(2C C1, 매트릭스 6/6).
- 컴파일된 계약 기준의 독립 검증 폐루프를 닫는 제품은 확인되지 않았다(2A C7 후반, confidence low로 한정).

**반대 논거:**
- intent→spec 절반은 이미 상품화됐다: Kiro(요구사항→user story→acceptance criteria), Spec Kit(SPECIFY/PLAN/TASKS, 30+ 에이전트 호환)(2A C7). backend plan mode들도 동일 방향으로 확장 중이다.
- Symphony는 backend 벤더가 orchestration 계층을 "SPEC.md 한 장"으로 흡수 가능함을 시연했다(2C C4) — 컴파일러가 가치 있다면 벤더가 더 빨리 만든다는 반론이 성립한다.

**판정: 수정 필요.** 컴파일러 **단독**으로는 약화가 사실이다. 차별화는 컴파일러가 아니라 **폐루프** — 컴파일된 계약이 검증 기준으로 연결되고, 그 판정이 실행 주체와 분리되어 있다는 결합 — 에 있다. 정체성 문장을 이 폐루프로 재서술해야 한다. → F-A1

### P3. Markdown/가드레일 분리의 실현 가능성 — "가드레일은 backend 네이티브로 실제 강제 가능하다"

**찬성 논거:**
- Claude Code: deny rules 평가 1순위, PreToolUse hook deny는 `--dangerously-skip-permissions`에서도 유효, sandbox는 OS(Seatbelt/bubblewrap) 수준에서 자식 프로세스까지 강제(2D C1, 공식 문서 3건 교차). 5필드 중 4필드 네이티브.
- Codex: `workspace-write`+`writable_roots` 쓰기 경계와 `prefix_rule(decision="forbidden")` 명령 차단이 실재(2D C2, 원출처 직접 확인).

**반대 논거:**
- Codex는 workspace 내부 파일 단위 쓰기 deny(`**/.env`)와 per-path read-deny가 없고, rules는 "experimental and may change"로 명시된다(2D C2, 원출처 직접 확인: 리다이렉션/치환 포함 스크립트는 분해 없이 통째 평가).
- completion_gates는 전 backend 네이티브 부재(2D C3). 일반 CLI wrapper는 명령 차단·승인 게이트가 구조적으로 불가(2D C4).
- 매트릭스 15셀 중 네이티브 차단은 8셀에 그친다(2D 종합 메모).

**판정: 조건부 성립.** "어댑터가 가장 강한 네이티브 메커니즘으로 번역한다"는 설계 문장은 Claude Code·Codex 한정으로 근거가 실재하나, **필드×backend 강도 편차를 등급화하지 않으면 과대 주장**이다. denied_paths를 Codex에 보내면 secret 보호가 조용히 사후 검사로 강등된다. → F-A3

### P4. 경쟁 부재 — "경쟁 control-plane은 contract+verification 계층을 제공하지 않는다" (06-10 결정)

**찬성 논거:** contract 계층은 6/6 부재(2C C1). 실행 메커니즘(worktree/병렬/PR)은 3곳에서 동일 패턴으로 반복되는 commodity(2C C2) — "오케스트레이션은 차별화 안 됨" 전반부는 강하게 지지된다.

**반대 논거:** Optio는 "isolated environment → agent → PR → CI 모니터링 → 리뷰 에이전트 → 전부 통과 시 자동 머지"의 evidence 게이트를 이미 출하했다(2C C3, top_claim 원출처 직접 확인). 게다가 multi-vendor(Claude Code/Codex/Copilot/Gemini/OpenCode) A/B 실행까지 제공한다 — Level 3 아비트레이션의 원시형이 경쟁 제품에 이미 존재한다.

**판정: 부분 반증 — 결정문 재서술 필요.** 엄격 정의(contract 스키마 + contract-파생 verification)에서는 생존, 완화 정의(아무 verification 게이트)에서는 깨졌다. 06-10 결정의 해당 서술은 "경쟁의 verification은 외부 CI/리뷰 통과 위임이며 contract-파생 판정이 아니다"로 좁혀야 한다. → F-B2

### P5. 어댑터 추적 가능성 — "어댑터 모델이 backend 진화 속도를 따라갈 수 있다"

**찬성 논거:** 어댑터 계약(capability/contract/launch/status/result)은 얇고, MVP는 수동/CLI 어댑터(통합 레벨 1~2)부터 시작하므로 초기 표면적은 작다(C2 통합 레벨).

**반대 논거:** Codex rules는 experimental 명시(2D C2), Claude Code는 dynamic workflows를 v2.1.154에서 GA로 추가하며 표면을 스크립트 런타임 단위로 확장(2A C2), OpenAI는 Symphony로 orchestration에 직접 진입(2C C4). 어댑터가 추적해야 할 표면이 분기·고속 확장 중이라는 실측 근거가 셋 모두에서 나왔다.

**판정: 리스크 확인 — 완화 장치 필요.** 전제 자체는 부정되지 않으나 설계 문서에 capability staleness 대응(검증일, smoke 계약, 강등 규칙)이 없다. → F-A6

---

## §3 축별 Finding 목록

### 축 1: architecture-soundness (8건)

| ID | Severity | Finding |
|----|----------|---------|
| F-A1 | **MAJOR** [judgment] | 차별화 정체성 문장이 "컴파일러" 단독에 걸려 있음 — Kiro/Spec Kit이 컴파일 절반을 상품화(2A C7), 정체성 그대로면 18개월 내 서사 붕괴. 추론 사슬: 컴파일 단독 상품화 사실 + 폐루프 미상품화 사실 → 차별화 위치 이동 |
| F-A2 | **MAJOR** [judgment] | P1 서술 과대 — backend 자가교차검증(2A C3 원문 확인)과 "JARVIS 검증"의 구분 기준(이해관계 분리, contract-파생 기준)이 문서에 명문화되어 있지 않음 |
| F-A3 | **MAJOR** | enforcement silent downgrade — 가드레일 필드×backend 강도 편차(2D 매트릭스: 네이티브 8/15셀)를 설계가 등급화하지 않아, Codex로 보낸 denied_paths의 secret 보호가 조용히 사후 검사로 강등됨 |
| F-A4 | **MAJOR** [judgment] | 최종 판정의 자기참조 약점 — D2의 논리("Markdown은 모델이 해석하므로 강제가 아니다")를 JARVIS 자신에 적용하면, "JARVIS makes the final PASS/... decision" 역시 모델 판단임. 문서는 completion_gates(기계 검사)와 Director judgment(모델 판단)를 한 문장에 섞어 씀 — 판정의 결정론적 부분과 판단적 부분의 경계 미명시 |
| F-A5 | MINOR | Level 2.5의 분류 과잉 — deep workflow는 `backend_capabilities.native_features.deep_workflow`로 이미 모델링되는데 별도 워크플로 레벨로도 존재. 레벨 체계(0/1/2/2.5/3/4)와 capability 플래그의 역할 중복 |
| F-A6 | MINOR [judgment] | 어댑터 유지비 리스크(P5) 실측 — Codex rules experimental(2D), Claude 표면 고속 확장(2A C2), 벤더 직접 진입(2C C4). capability 기록의 신선도 관리 장치 부재 |
| F-A7 | NOTE | `denied_paths: "**/*key*"` glob은 `keyboard.ts`, `monkey.py` 류 오탐 가능 — 예시 패턴 정밀화 필요 |
| F-A8 | NOTE | 긍정 확인 — 5단계 기본 워크플로와 "routine 작업에 deep workflow 기본 사용 금지" 원칙은 외부 비용 구조(workflows 문서의 토큰 경고)와 정확히 부합 |

### 축 2: decision-consistency (5건)

| ID | Severity | Finding |
|----|----------|---------|
| F-B1 | MINOR | MVP 우선순위 이중화 — C1은 10항목 스키마-우선, C2는 4항목(run ledger/route CLI/완료게이트/메모리) 우선. 둘 다 06-11 갱신본인데 canonical 선언과 상호 정렬이 없어 구현 에이전트가 상충 지시를 받음 |
| F-B2 | **MAJOR** | 06-10 결정의 P4 서술이 외부 사실로 부분 반증됨 — Optio의 CI+리뷰+자동머지 게이트(2C top_claim), Symphony의 orchestration 진입. 결정문 그대로 인용하면 미래 설계 논증이 틀린 전제 위에 서게 됨 |
| F-B3 | MINOR | executor-ontology 문서가 06-10의 역할 용어 결정(Director/Runtime/Producer/Verifier, `executor:` 단일 필드 회피)을 미반영 — 여전히 `executor:` 스키마와 executor 명칭 체계 유지 |
| F-B4 | NOTE | decisions.md 항목 정렬 비단조 — 06-08이 05-12 앞에, 06-11이 06-10 앞에 위치. 로그 가독성 문제 |
| F-B5 | NOTE | 인용 사실성 통과 — 'Dynamic workflows'와 'ultracode'는 공식 명칭으로 실재 확인(2A C2, 원출처 대조). 단 D2가 인용한 `docs.anthropic.com/.../workflows` URL은 현재 `code.claude.com/docs/en/workflows`로 이동 — 링크 갱신 권장 |

**정합성 매트릭스 (06-11자 결정 4건 × concept 2건 = 8셀):**

| 결정 | × C1 (intent-to-contract) | × C2 (meta-control-plane) |
|------|---------------------------|---------------------------|
| D1 intent-to-contract 최적화 | **일치** — 문서 전체가 D1의 본문 (워크플로·계약 스키마·모호성 규칙·레벨) | **드리프트** — "Revised MVP priority"가 D1을 수용했으나 우선순위 목록이 C1과 불일치 (F-B1) |
| D2 Markdown/가드레일 분리 | **일치** — "Instruction layer vs enforcement layer" 절 + 기계검사 필드 | **일치** — "Policy enforcement model" 절, dynamic workflow≠enforcement 구분 동일 |
| D3 harness/loop 위 Director | **일치** — "Harness engineering and loop engineering" 절 + loop_contract | **일치** — "Harness and loop model" 절, 동일 계층 뷰 |
| D4 agent implementation brief | **일치** — "Agent implementation brief" 절 (invariants/non-goals/first artifacts) | **일치** — "Greenfield implementation use" 절 ("deliberately not a line-by-line build manual") |

D4 단독 판정 가능성: **가능** — D4는 C1·C2 양쪽에 독립 절로 실재하므로 composite(③+④) 처리 없이 단독 행 판정이 성립한다. 8셀 중 일치 7, 드리프트 1, 충돌 0, 누락 0.

확장 교차 검증: 06-08 Hermes-agnostic 원칙 ↔ C1 non_goals("Hermes 하드 의존 금지") **일치**; 06-10 역할 용어 ↔ C2 **일치**, ↔ executor-ontology **드리프트**(F-B3); 05-28 office-runtime ↔ C2 Runtime 책임 분담 **일치**.

### 축 3: gaps-and-risks (4건)

| ID | Severity | Finding |
|----|----------|---------|
| F-C1 | **MAJOR** | contract 품질 평가 루프 부재 — 설계의 근거 자체가 "병목은 요구사항 품질로 이동"(D1 rationale)인데, 정작 계약이 좋았는지 나빴는지 측정·개선하는 메커니즘이 스키마·MVP 어디에도 없음 (open Q6이 미해결로 방치) |
| F-C2 | **MAJOR** [judgment] | "엄격 contract" 베팅의 반대 논증 부재 — Symphony는 "objectives instead of strict transitions"로 정반대 설계를 명시 채택(2C C4 원문). 문서는 over-specification을 비목표로 두면서도 contract 필수 필드의 최소형(open Q1)을 미정의 — 강모델에 어느 강도의 계약이 최적인지에 대한 논거가 설계에 없음 |
| F-C3 | MINOR | 비용·지연 모델 부재 — 레벨 라우팅과 deep workflow 호출 판단이 전부 정성적. ultracode류 고비용 모드의 호출 기준(예상 토큰/시간 대비 가치)이 미정량 |
| F-C4 | MINOR | Level 3 아비트레이션 가치 조건 미정(open Q5) — 경쟁(Optio)이 multi-vendor A/B를 이미 제공하는 상황에서, "언제 아비트레이션이 비용을 정당화하는가"의 부재는 차별화 주장의 공백 |

**집계: BLOCK 0 · MAJOR 7 · MINOR 6 · NOTE 4 (총 17건)**

---

## §4 BLOCK/MAJOR별 설계 수정안

| 대상 | 수정안 |
|------|--------|
| F-A1 | 정체성 문장 재서술 — C1 "Revised JARVIS identity"를 다음 취지로 교체: "JARVIS는 모호한 의도를 backend-native 계약으로 컴파일하고, **그 계약에서 파생된 기준으로, 실행 주체와 이해관계가 분리된 최종 판정**을 내리는 Agent Operations Director다. 차별화는 컴파일러 단독이 아니라 컴파일→위임→contract-파생 판정의 폐루프에 있다." Kiro/Spec Kit/plan mode를 '컴파일 절반의 경쟁자'로 명시 인정 |
| F-A2 | C1 "QA and verification model"에 구분 기준 명문화: backend 자가검증(같은 벤더·세션 권한계·계약 비참조)은 evidence로만 취급하고, JARVIS 판정의 정의를 "contract-파생 기준 + 이해관계 분리" 2조건으로 고정. backend_capabilities에 `self_verification: none|self_check|cross_agent_review` 필드 추가해 Claude Code workflows급 자가교차검증을 증거 등급에 반영 |
| F-A3 | task_contract 가드레일에 필드별 `enforcement_level: native | wrapper | post_hoc` 주석을 어댑터가 기록하고, **native 미만 필드는 completion_gates의 사후 검사 항목으로 자동 승격**하는 규칙 추가 (2D 권고 채택). 어댑터 책임에 "기본 credential read 허용 등 backend 기본값에 deny 명시 주입" 명문화 |
| F-A4 | 최종 판정을 2단으로 분리 명문화: ① mechanical gate(diff scope, secret diff, 검증 로그 존재, 금지명령 흔적) = 결정론적 필요조건, 코드로 강제 ② Director judgment(아키텍처 드리프트, 의도 부합) = 모델 판단, mechanical 통과 후에만. "JARVIS의 판정도 모델 판단이므로 mechanical 게이트가 우회 불가능한 바닥"임을 설계 원칙으로 명시 |
| F-B2 | decisions.md에 후속 결정 추가(기존 항목 수정 아님): "06-10의 '경쟁은 contract+verification 미제공' 서술을 '경쟁의 verification은 외부 CI/리뷰 위임이며 contract-파생 판정 계층은 공백'으로 정정. 근거: Optio/Symphony (2026-06-12 확인)" |
| F-C1 | contract 품질 피드백 루프를 MVP 스키마에 추가: run ledger에 `contract_id ↔ outcome`(REQUEST_CHANGES율, 재작업 횟수, scope 위반, 판정 뒤집힘) 연계 필드 + 실패 원인 분류(`contract_defect | execution_defect | verification_defect`). open Q6의 답으로 §6 참조 |
| F-C2 | contract 필드를 `must`(objective, forbidden_actions, acceptance_criteria, approval_gates) / `should`(scope, qa_checklist) / `optional`(나머지) 3등급으로 구분하고, backend 강도별 프로파일(강모델=objectives 중심 얇은 계약 + 강한 판정, 약모델=두꺼운 계약)을 명시 — Symphony의 반대 베팅을 "판정 없는 objectives는 인간 리뷰로 회귀한다"는 논거로 정면 반박하는 절 추가 |

---

## §5 정합성 매트릭스

§3 축 2에 포함 (8셀 표 + 확장 교차 검증). 요약: **일치 7 / 드리프트 1(D1×C2, MVP 우선순위) / 충돌 0 / 누락 0** — 2026-06-11 결정 3~4건과 concept 문서의 정합성은 전반적으로 양호하며, 유일한 드리프트는 MVP 우선순위 목록의 이중화다(F-B1).

---

## §6 Open Questions 8건 재분류

| # | 질문 | 분류 | 처리 |
|---|------|------|------|
| Q5 | Level 3 아비트레이션이 언제 비용을 정당화하는가 | **설계-치명** | **답 제안 (아래)** |
| Q6 | contract 품질을 시간에 걸쳐 어떻게 평가하는가 | **설계-치명** | **답 제안 (아래)** |
| Q1 | 최소 task-contract.yaml 스키마 | 구현-시-결정 | 우선순위 1 (F-C2의 must/should/optional 등급이 선행 입력) |
| Q2 | 최소 backend-result.json 스키마 | 구현-시-결정 | 우선순위 2 |
| Q7 | 최소 harness manifest 스키마 | 구현-시-결정 | 우선순위 3 |
| Q3 | 첫 어댑터: Codex CLI vs Claude Code | 구현-시-결정 | 우선순위 4 — 단 2D 근거상 **Claude Code가 enforcement 네이티브 매핑(4/5필드)이 가장 강해 가드레일 검증용 첫 어댑터로 우세**, Codex는 현 운영 경로라 실용 우세. 양자 모두 합리적 |
| Q8 | 1급 루프 타입 선정 | 구현-시-결정 | 우선순위 5 — test-fix 루프 우선 권장 (stop 조건·증거가 가장 기계적) |
| Q4 | 모델/데이터보존/비용 정책 기록 방법 | 구현-시-결정 | 우선순위 6 |

**Q5 답 제안**: 아비트레이션은 세 조건의 합집합이 아니라 **교집합**일 때만 기동한다 — (a) 결과 우열을 기계 판정 가능(테스트/벤치마크 등 객관 기준 존재), (b) 실패·재작업 비용 > N배 실행 비용, (c) 접근 다양성이 실재(다른 모델 계열 또는 상이한 아키텍처 접근). 기본값 OFF, route 기록에 기동 사유 필수. 경쟁(Optio A/B)과의 차별화는 "병렬 실행"이 아니라 "contract-파생 기준의 기계 판정으로 승자를 고르는 것"에 둔다.

**Q6 답 제안**: contract 품질은 산출물이 아니라 **결과로 측정**한다 — run ledger에 계약별 REQUEST_CHANGES율/재작업 횟수/scope 위반/판정 뒤집힘을 기록하고, 실패 원인을 `contract_defect | execution_defect | verification_defect`로 분류해 contract_defect 비율을 컴파일러 품질 지표로 삼는다. 주기 리뷰에서 결함 패턴(누락 필드, 모호 수용기준)을 컴파일 프롬프트/스키마에 역반영한다.

---

## §7 외부 근거 부록

전체 출처는 evidence-brief 3건에 수록 (합계 24건, 전부 확인일 2026-06-12). 판정에 직접 인용된 핵심 출처:

**2A — backend-native 범위** (`evidence-brief-2a.md`, 출처 10건):
- https://code.claude.com/docs/en/workflows — dynamic workflows GA(v2.1.154+), adversarial cross-review, ultracode **[top_claim 원출처 — 종합 판정자 직접 열람·대조 완료, 인용 일치]**
- https://code.claude.com/docs/en/permissions , /sub-agents — permission/hook/sandbox/subagent 거버넌스
- https://developers.openai.com/codex/cli/features , /codex/subagents — best-of-N, subagent GA
- https://cursor.com/blog/cloud-agent-lessons , https://www.openhands.dev/blog/openhands-product-update---may-2026
- https://kiro.dev/docs/specs/ , https://github.com/github/spec-kit — intent→spec 상품화

**2C — 경쟁 control-plane** (`evidence-brief-2c.md`, 출처 7건):
- https://github.com/jonwiggins/optio — CI+리뷰에이전트+자동머지, multi-vendor A/B **[top_claim 원출처 — 직접 열람·대조 완료, 인용 일치 + "A/B agents on the same task" 추가 확인]**
- https://github.com/ComposioHQ/agent-orchestrator , golutra/golutra , moazbuilds/CodeMachine-CLI , preset-io/agor
- https://openai.com/index/open-source-codex-orchestration-symphony/ + https://github.com/openai/symphony

**2D — 가드레일 실현성** (`evidence-brief-2d.md`, 출처 7건):
- https://developers.openai.com/codex/rules — prefix_rule/forbidden, experimental, 셸 분해 한계 **[top_claim 원출처 — 직접 열람·대조 완료, 인용 일치]**
- https://code.claude.com/docs/en/sandboxing , /hooks , /hooks-guide , /permissions
- https://developers.openai.com/codex/concepts/sandboxing , /codex/agent-approvals-security
- https://github.com/anthropic-experimental/sandbox-runtime

---

## 검수 기록

- Non-Goals 준수: 구현 착수 게이트 판정 없음, wiki/decisions 반영 지시 없음(F-B2 수정안도 "후속 결정 추가 제안"으로 한정 — 실행은 사용자 disposition 결정 대기), Ouroboros 심층 조사 없음(경량 대조만).
- AC 검수와 wiki 무변경 2중 게이트 결과는 검토 종료 시 별도 확인.
