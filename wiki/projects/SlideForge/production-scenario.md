# SlideForge production scenario

- status: active operating runbook
- updated: 2026-05-21
- project: SlideForge
- owner: JARVIS / Hermes Director

## Purpose

This runbook defines the default user-facing workflow for producing evidence-first slide decks with SlideForge.

The key design choice is that ComfyUI asset prompts/briefs are mostly internal implementation artifacts. The user should normally review actual visual candidates, not only text briefs.

## Operating principle

SlideForge delivery is not just “make a deck.” A completed job should produce:

```text
artifact + visual evidence + QA result + final delivery package
```

Default artifact set:

```text
- deck.html
- deck.pptx when PPTX delivery is requested
- generated-assets/
- browser screenshots
- PPTX render screenshots when PPTX is requested
- run-summary.md / run-summary.json
- fidelity-report.md / fidelity-score.json when applicable
- evidence-pack.zip
```

## Roles

```text
User
  Provides goal, source material, design preference/template, and approval decisions.

JARVIS / Hermes Director
  Intake, decomposition, source/design analysis, approval gates, QA rubric, evidence verification, final reporting.

SlideForge
  Deterministic artifact pipeline for deck.json, HTML, PPTX export, screenshot/render evidence, summaries, and evidence packs.

ComfyUI
  Graphical asset forge only. It does not compose final slides.

HTML producer route
  Primary high-fidelity visual/presentation route.

PPTX producer route
  Delivery/template-native route when editable or PowerPoint-compatible output is required.

Reviewer
  Independent review loop for quality-sensitive decks before final delivery.
```

## Default workflow

### 1. Intake

Collect the minimum information needed to route and scope the job.

Ask or infer:

```text
- purpose: proposal, pitch, executive report, education, internal briefing, etc.
- audience: evaluator, customer, executive, practitioner, public audience
- format: HTML, PPTX, PDF/images, or all
- slide count / presentation length
- editable PPTX requirement
- source material: files, text, URLs, notes, RFP, meeting log
- design reference: PPTX template, image/link reference, brand guide, or none
- security constraints: external research allowed, private-source handling, citation expectations
- deadline / quality mode
```

Routing:

```text
PPTX template file exists:
  prefer PPTX/template-native route plus render evidence.

Only image/link/gallery reference exists:
  use style-reference analysis; do not copy or redistribute original template assets.

No design reference exists:
  create a topic-informed design spec.

No source material or weak source material:
  run research/content repair before deck production.
```

### 2. Source and design collection

Normalize inputs into durable working artifacts.

Typical artifacts:

```text
source.md or extracted-source.md
research-supplement.md when needed
observations.json when a design reference exists
design-spec.json
sections.json
deck-plan.md
```

If provided material is weak, stale, or inconsistent, JARVIS should repair it before production:

```text
- identify unsupported claims
- fill missing context with allowed research
- separate facts, assumptions, and recommendations
- cite or record source basis where appropriate
- flag unresolved claims instead of hiding them
```

### 3. Slide plan and QA rubric approval

Before heavy generation, present the user with a compact plan.

Approval package:

```text
- slide-by-slide outline
- purpose of each slide
- intended visual type per slide
- required source/research assumptions
- output format route: HTML/PPTX/both
- QA rubric and pass/fail gates
```

Recommended approval prompt:

```text
검토 요청: Slide Plan & QA Rubric

1. 이 슬라이드 구성으로 진행할까요?
2. 검증 기준은 아래대로 적용할까요?
3. 수정할 슬라이드나 강조점이 있으면 알려주세요.
```

Gate result:

```text
APPROVED:
  proceed to asset generation and deck production.

REQUEST_CHANGES:
  revise outline/rubric and ask again if direction changed materially.

FAST/AUTONOMOUS MODE:
  JARVIS may self-approve routine plans, but must still report the chosen rubric.
```

### 4. Internal asset brief generation

After plan approval, JARVIS creates internal ComfyUI asset briefs.

These are mostly for the pipeline, not for default user review.

Artifact:

```text
asset-briefs.json
```

Each brief should include:

```text
- target slide id
- purpose in the slide
- desired composition
- style constraints
- required motifs
- forbidden elements
- text-free requirement unless deterministic diagram rendering is intended
- negative prompt hints
```

Default policy:

```text
Do not ask the user to approve text-only asset briefs unless the deck is high-risk, brand-sensitive, expensive to regenerate, or the user asks to review prompts first.
```

### 5. Visual candidate generation

Generate visual candidates from the internal briefs.

Typical candidate count:

```text
routine deck: 2 candidates per key visual
important cover/key visual: 3-4 candidates
large deck/autonomous mode: 1 best candidate + regenerate only if QA fails
```

Artifacts:

```text
generated-assets/candidates/
asset-generation-report.json
```

Each candidate should preserve evidence:

```text
- file path
- target slide id
- generation source: ComfyUI / deterministic SVG-HTML / other local forge
- prompt/workflow/seed when safe and useful
- generated_at
- status
- known issues
```

When exact labels, arrows, or Korean text are required, prefer deterministic diagram rendering over pure diffusion output:

```text
architecture diagrams, process flows, org charts, KPI diagrams:
  create deterministic SVG/HTML/diagram assets and render to PNG.

cinematic backgrounds, abstract motifs, photo-like visual bands:
  use ComfyUI.
```

### 6. Visual Candidate Board

This is the default user-facing asset approval artifact.

The user should see actual images, not just asset briefs.

Artifacts:

```text
asset-review-board.html
asset-review-board.md
```

Board contents:

```text
- slide id / slide title
- intended use of the asset
- candidate images A/B/C
- JARVIS quick QA notes per candidate
- JARVIS recommendation
- simple approval choices
```

Candidate QA checklist:

```text
- topic relevance
- visual fit with design spec/template
- adequate text-safe area
- no broken anatomy or distracting artifacts
- no random unreadable text unless intentionally blurred/background-only
- no logos/trademarks unless explicitly provided and allowed
- no sensitive or misleading imagery
- works when cropped/placed into target slide
```

Recommended user prompt:

```text
Visual Asset Approval 요청입니다.

아래 review board에서 실제 이미지 후보를 확인해주세요.
추천안은 JARVIS 기준으로 표시했습니다.

선택지:
- Slide 1: A/B/C 승인
- 재생성: 어떤 방향으로 바꿀지 한 줄 지시
- 자동선택: JARVIS 추천안으로 진행
```

CLI delivery pattern:

```text
- provide Windows-friendly paths to asset-review-board.html and candidate images
- include JARVIS recommendation in the terminal response
- do not use MEDIA tags in CLI
```

Telegram/Discord delivery pattern:

```text
- send image candidates directly when practical
- include slide id, recommendation, and decision options
```

### 7. Visual asset approval gate

Only approved assets should enter final deck production.

Artifact:

```text
approved-assets.json
```

Suggested schema:

```json
{
  "run_id": "...",
  "approval_status": "approved",
  "approved_assets": [
    {
      "slide_id": "slide-01-cover",
      "selected_candidate": "B",
      "asset_path": "generated-assets/slide-01-cover-b.png",
      "approved_by": "user_or_jarvis",
      "approval_mode": "explicit_user|jarvis_recommended|autonomous",
      "notes": "left-side text space is best"
    }
  ],
  "rejected_assets": [],
  "regeneration_requests": []
}
```

Gate behavior:

```text
APPROVED:
  attach selected asset_path values to deck.json and proceed.

REQUEST_REGENERATION:
  regenerate only the affected assets, update the board, and request approval again.

AUTO_APPROVE:
  JARVIS selects recommended candidates and records approval_mode=jarvis_recommended or autonomous.
```

### 8. Deck production

Use approved assets only.

Steps:

```text
- bind approved asset paths into deck.json
- generate HTML deck
- export PPTX if requested
- ensure visual assets are embedded or referenced according to output type
```

Current route expectations:

```text
HTML:
  generated asset paths render in visual slides.
  architecture_visual with asset_path can render as clean full-slide diagram.

PPTX:
  generated assets are embedded into ppt/media.
  architecture_visual with asset_path can render as full-slide image without overlay title/subtitle/chips.
```

### 9. Evidence-first QA revision loop

Run QA against the approved rubric.

HTML evidence:

```text
- browser screenshot capture
- console errors
- slide count match
- visual overlap/clipping/readability check
```

PPTX evidence:

```text
- PPTX export report
- static package/media checks
- renderer evidence with PNG/SVG outputs when available
- Korean glyph/tofu check
- clipping/overlap/readability check
```

Content evidence:

```text
- slide count/order matches plan
- claims align with source/research
- no placeholders or TODOs
- terminology consistency
```

Revision rules:

```text
blocker:
  must fix before delivery.

request_changes:
  fix in a bounded loop or escalate if tradeoff requires user decision.

minor warning:
  may ship if user accepts or deadline/quality mode allows.
```

Common rollback targets:

```text
content issue:
  return to source/research or slide plan.

design issue:
  revise design spec or layout.

asset issue:
  return to visual candidate generation and approval.

export/render issue:
  fix HTML/PPTX route and rerender.
```

### 10. Final delivery package

Final response should include:

```text
- final artifact paths
- evidence pack path
- summary status
- blockers count
- warnings count and meaning
- verification commands
- remaining risks or optional polish
```

Delivery should not claim completion until:

```text
- requested artifacts exist
- evidence has been generated
- blockers are zero or explicitly accepted by the user
- final status is reported honestly
```

## Approval modes

### Strict mode

Use for customer delivery, public-sector/RFP submissions, executive decks, brand-sensitive work.

```text
Gate 1: Slide Plan & QA Rubric approval required
Gate 2: Visual Asset approval required
Gate 3: Final Delivery approval required
```

### Fast mode

Use for drafts and internal working versions.

```text
Gate 1 required
Gate 2 can use JARVIS recommended assets unless the user asks to inspect them
Gate 3 report required, approval optional
```

### Autonomous mode

Use when the user says to continue unless review is necessary.

```text
JARVIS self-approves routine choices.
Escalate only for:
- new design direction
- weak/contradictory source claims
- visual candidates with meaningful ambiguity
- blocker or material REQUEST_CHANGES
- paid/cloud/external-risk actions
- secrets/auth/deploy/delete/sudo or other safety-gated actions
```

## Recommended user-facing checkpoint wording

### Plan checkpoint

```text
[Gate 1: Plan & QA]
구성안과 검증 기준입니다.
승인하면 에셋 후보 생성으로 넘어가겠습니다.
수정할 슬라이드/강조점이 있으면 알려주세요.
```

### Visual asset checkpoint

```text
[Gate 2: Visual Asset]
실제 이미지 후보 review board를 만들었습니다.
추천안은 표시해두었습니다.
선택해주세요: A/B/C, 재생성, JARVIS 추천안으로 진행.
```

### Final checkpoint

```text
[Gate 3: Final Delivery]
최종 산출물과 evidence pack이 준비되었습니다.
blockers=0, warnings=N입니다.
승인하면 이 버전을 납품본으로 고정하겠습니다.
```

## Minimal file contract for future implementation

```text
runs/<run_id>/
  source.md
  design-spec.json
  sections.json
  deck.json
  asset-briefs.json
  asset-review-board.html
  asset-review-board.md
  approved-assets.json
  generated-assets/
  deck.html
  deck.pptx
  browser-capture/
  pptx-render-*/
  run-summary.json
  run-summary.md
  evidence-pack-manifest.json

runs/<run_id>-evidence-pack.zip
```

## Current implementation note

As of 2026-05-21, SlideForge already has the core production/evidence primitives:

```text
- source/design local run preparation
- HTML deck generation
- Playwright screenshot capture
- PPTX export
- generated asset embedding into HTML/PPTX
- full-slide architecture diagram asset rendering
- supplemental PPTX visual render QA
- run summary
- evidence pack export
```

The next implementation gap is turning candidate discovery/review-board generation into first-class commands/artifacts. The source-of-truth approval/application step is now implemented:

```text
- approve-assets
- apply-approved-assets
```

Remaining candidate helper commands:

```text
- generate-asset-candidates
- build-asset-review-board
```
