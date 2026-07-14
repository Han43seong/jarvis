---
title: Slide Generation Harness
created: 2026-05-12
updated: 2026-05-12
type: concept
concept_type: agent-harness
status: draft
tags: [jarvis, hermes, slides, powerpoint, harness, qa-loop, presentation]
sources: [user-request]
confidence: medium
relations:
  - type: extends
    target: learning-harness
  - type: produces
    target: pptx-deck
  - type: uses
    target: powerpoint-qa-loop
---

# Slide Generation Harness

## 목적

템플릿, 주제, 목적, 발표 대상자, 분량, 톤, 참고자료를 입력받아 발표/자료용 슬라이드를 생성하고, 자동 평가 루프를 통해 요구사항을 충족할 때까지 생성-검토-수정-검증을 반복하는 JARVIS 하네스.

핵심 방향은 “한 번에 예쁘게 만들기”가 아니라 “명시 요구사항 + 자동 선별 QA 기준 + 사용자 검토 게이트”를 만족할 때까지 반복하는 제작 시스템이다.

## 기본 사용자 경험

1. 사용자가 입력한다.
   - 템플릿: pptx 템플릿 파일 또는 스타일 프리셋
   - 주제: 발표/자료 주제
   - 목적: 설득, 보고, 교육, 제안, 투자유치, 영업 등
   - 발표 대상자: 의사결정자, 실무자, 개발자, 고객, 공공기관, 임원 등
   - 사용 맥락: 발표 시간, 배포용 여부, 언어, 출력 형식
   - 참고자료: 문서, URL, 메모, 기존 슬라이드, 이미지
2. Hermes가 요구사항 체크리스트를 자동 선별한다.
3. 사용자가 체크리스트를 검토/수정/승인한다.
4. 하네스가 슬라이드 아웃라인, 스토리라인, 디자인 시스템을 생성한다.
5. 초안 deck을 생성한다.
6. 자동 QA가 내용/구조/시각/템플릿 준수/발표 적합성을 평가한다.
7. 실패 항목을 수정 프롬프트로 변환해 deck을 수정한다.
8. 최소 1회 이상의 수정-재검증 루프를 수행한다.
9. 기준 통과 후 사용자에게 preview, QA report, 최종 pptx를 제공한다.

## 입력 스키마 초안

```yaml
job:
  id: string
  mode: presentation | handout | proposal | training | pitch | report
  language: ko | en | ja | vi | mixed
  output:
    format: pptx
    aspect_ratio: 16:9
    audience_delivery: live_presentation | reading_deck | both

template:
  type: pptx_file | style_preset | generated_theme
  path: optional string
  preserve:
    layouts: true
    fonts: true
    colors: true
    master_slides: true
  allowed_deviation: low | medium | high

brief:
  topic: string
  purpose: string
  audience:
    primary: string
    knowledge_level: executive | expert | practitioner | beginner | mixed
    decision_power: high | medium | low
    concerns: [string]
  duration_minutes: number
  slide_count:
    min: number
    max: number
  key_messages: [string]
  call_to_action: string
  constraints: [string]
  references:
    files: [path]
    urls: [url]
    notes: string

style:
  tone: executive | technical | persuasive | educational | premium | public-sector
  density: sparse | balanced | detailed
  visual_style: light_engineering | dark_premium | public_proposal | startup_pitch | custom
  source_policy: title_only_images | citations_required | internal_only

loop:
  max_iterations: 5
  require_user_review_of_requirements: true
  require_fix_and_verify_cycle: true
  stop_when_score_at_least: 90
```

## Hermes가 선별할 요구사항 카테고리

사용자가 모두 직접 정하지 않아도, Hermes가 주제/목적/대상자에 따라 아래 기준을 자동 선택하고 초안으로 제시한다.

### 1. 목적 적합성

- 발표 목적이 각 슬라이드의 역할과 연결되는가?
- 첫 3장 안에 왜 지금 이 주제가 중요한지 설명되는가?
- 마지막 장에 명확한 결론, 요청사항, 다음 액션이 있는가?
- 의사결정형 발표라면 선택지, 근거, 리스크, 요청 결정사항이 분리되어 있는가?

### 2. 대상자 적합성

- 대상자의 지식 수준에 맞는 용어와 설명 깊이인가?
- 임원/의사결정자 대상이면 요약, 비용/효과, 리스크, 일정이 빠지지 않았는가?
- 개발자/실무자 대상이면 아키텍처, 워크플로우, 제약, 구현 포인트가 충분한가?
- 공공/제안 대상이면 신뢰성, 보안, 운영성, 검증 지표가 강조되는가?

### 3. 스토리라인

- 문제 → 통찰 → 해결안 → 실행계획 → 기대효과 흐름이 있는가?
- 각 슬라이드가 하나의 메시지만 전달하는가?
- 중복 슬라이드나 논리 점프가 없는가?
- 섹션 전환이 자연스러운가?

### 4. 콘텐츠 완성도

- 필수 항목이 누락되지 않았는가?
- 주장마다 근거/예시/데이터가 있는가?
- 불확실한 내용은 가정 또는 검증 필요로 표시했는가?
- 참고자료 기반 내용과 생성된 추론이 구분되는가?

### 5. 슬라이드 디자인 품질

- 텍스트-only 슬라이드를 피했는가?
- 모든 슬라이드에 이미지, 다이어그램, 차트, 아이콘, 카드, 콜아웃 중 하나 이상의 시각 요소가 있는가?
- 제목 36-44pt, 본문 14-16pt 수준의 계층감이 있는가?
- 0.5인치 이상 외곽 여백과 0.3-0.5인치 요소 간격을 지켰는가?
- 색상은 주제에 맞고, 한 가지 dominant 색상이 있는가?
- 저대비 텍스트/아이콘이 없는가?

### 6. 템플릿 준수

- 마스터/레이아웃/폰트/색상을 보존했는가?
- 템플릿 placeholder가 남아 있지 않은가?
- 로고, footer, 페이지 번호, 출처 위치가 일관적인가?
- 템플릿의 톤에서 벗어난 장식이 없는가?

### 7. 발표 가능성

- 발표 시간 대비 슬라이드 수와 밀도가 적절한가?
- 발표자 노트가 필요한 슬라이드에 포함되어 있는가?
- 한 슬라이드당 설명 포인트가 1-3개로 제한되는가?
- 청중 질문이 예상되는 리스크/반론이 백업 또는 부록에 있는가?

### 8. 자료 배포 가능성

배포용 deck인 경우 추가 적용한다.

- 발표자가 없어도 핵심 맥락을 이해할 수 있는가?
- 약어/전문용어 설명이 충분한가?
- 출처, 날짜, 버전, 작성자 정보가 포함되어 있는가?
- 민감정보/내부정보가 제거되었는가?

### 9. 기술적 QA

- 텍스트 잘림, 겹침, overflow가 없는가?
- PDF/이미지 렌더링 시 깨짐이 없는가?
- placeholder/lorem/xxxx 같은 잔여 텍스트가 없는가?
- PPTX 파일이 열리고, markitdown으로 텍스트 추출이 되는가?

## 루프 구조

```text
[Input Brief]
   ↓
[Requirement Selector]
   ↓ user review gate
[Approved Requirement Checklist]
   ↓
[Outline + Storyline Generator]
   ↓
[Design System Extractor/Builder]
   ↓
[Deck Generator]
   ↓
[Render to PDF/JPG]
   ↓
[QA Evaluators]
   ├─ Content QA
   ├─ Structure QA
   ├─ Audience/Purpose QA
   ├─ Template QA
   ├─ Visual QA
   └─ Technical QA
   ↓
[Issue Prioritizer]
   ↓
[Revision Planner]
   ↓
[Deck Editor]
   ↓
[Re-render + Re-verify]
   ↓
[Pass?] no → loop / yes → final package
```

## 주요 컴포넌트 설계

### 1. Brief Intake

역할: 사용자 입력을 정규화하고 누락된 핵심 항목을 추론 또는 질문한다.

출력:
- normalized_brief.yaml
- missing_info_questions.md
- assumptions.md

원칙:
- 분량, 대상자, 목적, 템플릿이 있으면 시작 가능하다.
- 애매한 세부사항은 가정으로 표시하고 진행한다.
- 결과 품질에 큰 영향을 주는 누락만 질문한다.

### 2. Requirement Selector

역할: 발표 목적/대상자/자료 형태에 맞는 요구사항 체크리스트를 선별한다.

출력:
- requirements.md
- requirements.yaml
- acceptance_thresholds.yaml

사용자 검토 게이트:
- Hermes가 초안을 제안한다.
- 사용자가 항목 추가/삭제/가중치 조정한다.
- 승인된 checklist를 루프의 판정 기준으로 고정한다.

### 3. Storyline Planner

역할: 메시지 아키텍처와 슬라이드별 역할을 만든다.

출력:
- outline.md
- slide_plan.yaml

slide_plan 예시:

```yaml
slides:
  - no: 1
    role: title
    message: 핵심 한 줄
    visual: hero image or abstract motif
    notes: 발표 opening
  - no: 2
    role: problem
    message: 왜 지금 중요한가
    visual: 3-stat callout
```

### 4. Design System Adapter

역할: 템플릿에서 색상, 폰트, 레이아웃, 로고/footer 규칙을 추출하거나 스타일 프리셋을 만든다.

출력:
- design_tokens.yaml
- layout_rules.yaml

규칙:
- 템플릿이 있으면 템플릿 우선.
- 템플릿이 없으면 주제 기반 팔레트와 반복 motif 생성.
- title-only sourced robot imagery 등 사용자 선호 정책 반영 가능.

### 5. Deck Generator

역할: slide_plan과 design_tokens를 기반으로 pptx 초안을 생성한다.

구현 후보:
- pptxgenjs: scratch 생성에 적합
- python-pptx/open XML patching: 기존 템플릿 수정에 적합
- LibreOffice headless: 렌더링 검증
- markitdown: 텍스트 추출 검증

### 6. QA Evaluators

각 evaluator는 score, pass/fail, issue list, evidence, suggested_fix를 반환한다.

```yaml
issue:
  id: VQA-003
  severity: high
  slide: 7
  category: visual_overflow
  evidence: 오른쪽 카드 본문이 footer와 8px 간격으로 너무 가까움
  suggested_fix: 본문 1줄 축약 또는 카드 높이 확대
```

권장 evaluator:
- `content_evaluator`: 누락, 사실성, 주장-근거 연결
- `story_evaluator`: 흐름, 중복, 논리 점프
- `audience_evaluator`: 대상자 적합성
- `purpose_evaluator`: 목적 달성 여부
- `template_evaluator`: 템플릿/브랜드 준수
- `visual_evaluator`: 이미지 렌더 기반 시각 QA
- `technical_evaluator`: 파일 열림, 렌더링, placeholder, overflow
- `speaker_evaluator`: 발표 시간/노트/말하기 흐름

### 7. Issue Prioritizer

역할: 모든 이슈를 중요도와 수정 비용 기준으로 정렬한다.

우선순위:
1. 파일/렌더링 실패
2. 요구사항 필수 항목 누락
3. 시각적 치명 오류: 겹침, 잘림, 저대비
4. 목적/대상자 부적합
5. 스토리라인 중복/논리 점프
6. 미세 정렬/문구 개선

### 8. Revision Planner + Deck Editor

역할: 이슈를 수정 작업으로 묶고 deck을 수정한다.

수정 전략:
- 같은 슬라이드의 여러 이슈는 한 번에 수정한다.
- 템플릿/레이아웃 문제는 design_tokens 또는 layout_rules부터 수정한다.
- 내용 누락은 outline/slide_plan에 먼저 반영한 뒤 deck을 재생성 또는 부분 수정한다.
- 수정 후 영향받은 슬라이드만 우선 재검증하되, 마지막에는 전체 검증한다.

## 점수 모델 초안

총점 100점, 기본 통과 기준 90점.

```yaml
weights:
  purpose_fit: 15
  audience_fit: 15
  storyline: 15
  content_completeness: 15
  visual_quality: 15
  template_compliance: 10
  presentation_readiness: 10
  technical_integrity: 5
hard_fail:
  - pptx_not_openable
  - missing_required_section
  - severe_text_overlap_or_cutoff
  - leftover_placeholder
  - unsafe_or_unverified_claim_presented_as_fact
```

통과 조건:
- 총점 >= threshold
- hard_fail 0개
- high severity issue 0개
- 최소 1회 fix-and-verify cycle 완료
- 사용자 승인 요구 모드라면 final preview 승인

## 반복 종료 조건

성공 종료:
- 점수 기준 충족
- hard fail 없음
- 전체 QA pass
- 최종 파일, preview 이미지/PDF, QA report 생성

중단 종료:
- max_iterations 도달
- 필수 입력 부족으로 더 이상 개선 불가
- 템플릿 손상 또는 렌더링 도구 실패
- 사용자 수동 검토 필요 항목 발생

중단 시에도 산출물은 남긴다.
- latest.pptx
- qa_report.md
- unresolved_issues.md
- next_actions.md

## 산출물 구조 제안

```text
$HOME/projects/slide-harness/runs/<job-id>/
  input/
    brief.yaml
    references/
    template.pptx
  planning/
    requirements.md
    requirements.yaml
    outline.md
    slide_plan.yaml
    design_tokens.yaml
  drafts/
    iter-01.pptx
    iter-02.pptx
  render/
    iter-01/slide-01.jpg
    iter-02/slide-01.jpg
  qa/
    iter-01-report.md
    iter-02-report.md
    final-report.md
  final/
    deck.pptx
    deck.pdf
    preview-contact-sheet.jpg
    handoff.md
```

## MVP 범위

1. CLI 기반 job 생성
2. YAML brief 입력
3. 템플릿 없이 pptxgenjs로 scratch deck 생성
4. 요구사항 체크리스트 자동 생성 및 사용자 승인 파일 생성
5. markitdown 텍스트 QA
6. LibreOffice + pdftoppm 렌더링
7. 이미지 기반 visual QA는 Hermes/delegate subagent 또는 vision tool로 수행
8. issue list 기반 1-3회 수정 루프
9. final pptx/pdf/QA report 저장

MVP에서 제외:
- 완전한 템플릿 마스터 편집
- 복잡한 이미지 생성 파이프라인
- 웹 UI
- 실시간 공동 편집
- 외부 유료 API 의존 고정

## 구현 단계 제안

### Phase 1: Harness Skeleton

- `slide_harness/cli.py`
- `slide_harness/schemas.py`
- `slide_harness/requirements.py`
- `slide_harness/run_state.py`
- run directory 생성
- brief validation

### Phase 2: Requirement Gate

- 목적/대상자 기반 체크리스트 생성
- `requirements.md` 출력
- 사용자가 승인 파일에 `approved: true` 표시하면 다음 단계 진행

### Phase 3: Outline and Deck Draft

- outline/slide_plan 생성
- pptxgenjs 또는 python-pptx 기반 deck 생성
- 디자인 토큰 적용

### Phase 4: Render and QA

- pptx → pdf → jpg 변환
- markitdown 텍스트 검사
- placeholder 검사
- visual QA 프롬프트 생성
- issue schema 저장

### Phase 5: Revision Loop

- issue prioritization
- slide_plan 또는 deck 수정
- 재렌더링 및 재검증
- max_iterations/score 기준 적용

### Phase 6: Template Support

- 기존 pptx 템플릿 분석
- master/layout 추출
- placeholder 매핑
- 템플릿 기반 슬라이드 작성

## 첫 번째 요구사항 체크리스트 초안

사용자 검토용 기본안:

1. 입력 brief에는 주제, 목적, 대상자, 발표 시간, 예상 슬라이드 수가 있어야 한다.
2. Hermes가 생성한 requirements.md는 사용자가 승인해야 루프에 들어간다.
3. 모든 슬라이드는 하나의 핵심 메시지를 가져야 한다.
4. 첫 3장 안에 문제의 중요성과 발표의 결론 방향이 드러나야 한다.
5. 마지막 장에는 명확한 결론/요청/다음 액션이 있어야 한다.
6. 각 슬라이드에는 텍스트 외 시각 요소가 하나 이상 있어야 한다.
7. 템플릿이 제공되면 폰트/색상/footer/logo 규칙을 유지해야 한다.
8. 텍스트 잘림, 겹침, placeholder 잔여물은 hard fail이다.
9. 임원/의사결정자 대상이면 비용/효과/리스크/일정 중 해당 항목을 포함해야 한다.
10. 기술/개발자 대상이면 구조/워크플로우/제약/검증 방법을 포함해야 한다.
11. 공공/제안 대상이면 보안/운영성/검증 KPI/도입 절차를 포함해야 한다.
12. 최소 1회 수정-재검증 루프를 수행해야 한다.
13. 최종 산출물에는 pptx, pdf, preview, QA report가 포함되어야 한다.

## 사용자 검토 필요 항목

다음 항목은 확정이 필요하다.

1. 이 하네스를 JARVIS control-plane helper로 둘지, 독립 프로젝트 `$HOME/projects/slide-harness`로 만들지.
2. 초기 생성 엔진을 pptxgenjs로 할지, python-pptx로 할지.
3. visual QA를 Hermes vision/subagent 기반으로 할지, 로컬 규칙 기반 screenshot 검사부터 시작할지.
4. 사용자가 요구사항을 승인하는 방식: markdown 체크박스, YAML approved flag, CLI interactive prompt 중 선택.
5. 첫 MVP의 주요 사용 사례: 제안서, 임원 보고, 교육자료, 영업자료 중 우선순위.

## 포맷 전략

권장 전략은 `HTML-first canonical deck`이다. PPTX를 첫 번째 내부 포맷으로 삼기보다, 슬라이드 구조를 YAML/JSON의 중립 모델로 유지하고 HTML 렌더러를 MVP 기본 출력으로 둔다.

이유:
- HTML/CSS는 반복 생성과 수정이 빠르고 diff/review가 쉽다.
- Playwright/Chromium 기반 PDF export와 screenshot QA가 안정적이다.
- CSS token, theme, layout component를 코드로 관리할 수 있어 템플릿/스타일 변형이 쉽다.
- visual QA가 slide image 기반으로 단순해진다.
- PDF가 최종 사용물이라면 PPTX 편집 호환성보다 렌더 품질과 재현성이 더 중요하다.

PPTX는 다음 경우에 renderer 또는 export adapter로 지원한다.
- 사용자가 PowerPoint에서 후편집해야 하는 경우
- 고객/기관이 pptx 원본 제출을 요구하는 경우
- 기존 기업/기관 PPT 템플릿을 반드시 써야 하는 경우

## 권장 결정

- 프로젝트 위치: `$HOME/projects/slide-harness` 독립 repo
- JARVIS에는 wiki와 라우팅/하네스 실행 문서만 유지
- MVP 기본 포맷: HTML deck → PDF export
- 내부 모델: slide_plan.yaml 또는 deck.json 같은 중립 slide spec
- MVP 렌더러: HTML/CSS fixed 16:9 canvas + Playwright PDF/screenshot export
- PPTX 지원: Phase 2 이후 별도 renderer/export adapter로 추가
- 사용자 승인 방식: `requirements.md` 체크리스트 + `requirements.yaml.approved: true`
- QA는 content/structure는 LLM, technical/render는 로컬 도구, visual은 이미지 기반 fresh-eye subagent로 분리
- Claude Design 스타일의 HTML artifact 생성 방식을 기본 deck renderer 품질 기준으로 활용

## Claude Design 활용 전략

Claude Design은 `HTML-first slide harness`와 잘 맞는다. PPTX보다 HTML deck을 기본 포맷으로 둘 경우, Claude Design식 산출물 생성 방식을 슬라이드 renderer의 핵심 엔진/패턴으로 활용할 수 있다.

활용 포인트:
- 고정 16:9 HTML canvas 기반 slide deck 생성
- CSS token 기반 디자인 시스템 생성
- theme/style preset 변형 생성
- keyboard navigation, slide count, localStorage 같은 deck UX 기본 탑재
- print/PDF friendly layout 적용
- 브라우저 렌더링 후 screenshot/visual QA 수행
- 사용자가 고른 스타일 방향을 HTML/CSS component로 고정

권장 역할 분리:
- Hermes/JARVIS: 요구사항 선별, 루프 제어, 산출물 검증, 파일/프로젝트 관리
- Claude Design 패턴: HTML deck의 시각 디자인, 레이아웃 시스템, component/tokens 생성
- Playwright/Chromium: PDF export, screenshot, technical render QA
- Fresh-eye evaluator: visual QA와 수정 제안

주의점:
- Claude Design을 단순히 “예쁜 HTML 생성기”로 쓰면 generic SaaS deck이 되기 쉽다.
- 먼저 brief, 대상자, 목적, 요구사항, style constraints를 고정한 뒤 디자인 생성에 투입해야 한다.
- interior slide에는 반복적인 AI/robot 이미지를 남발하지 않고, 다이어그램/루브릭/워크플로우/비교표 중심으로 설계한다.
- 최종 품질은 Claude Design 단독 판단이 아니라 harness QA 기준으로 판정한다.
