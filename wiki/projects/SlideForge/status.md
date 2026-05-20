# SlideForge status

- status: active
- updated: 2026-05-20
- repo: `/home/hskim/projects/SlideForge`
- remote: `https://github.com/Han43seong/SlideForge.git`
- visibility: private

## Purpose

`SlideForge` is the clean-start successor direction after `hermes-slide-director` Phase 42.

It narrows the production architecture to:

```text
Design analysis / planning:
  JARVIS + hermes-slide-director learnings

High-quality graphical assets:
  ComfyUI

Primary slide production:
  codex-guizang-html

PPTX delivery:
  codex-presentation-pptx
```

## Initial repository state

Initial commits:

```text
b428a46 chore: initialize Hermes Slide Forge
10fa069 chore: rename project to oh-my-side-design
7865a20 chore: rename project to SlideForge
```

Initial files:

- `README.md`
- `docs/architecture.md`
- `pyproject.toml`
- `src/slideforge/__init__.py`
- `src/slideforge/toolchain.py`
- `tests/test_toolchain.py`

Initial validation:

```text
PYTHONPATH=src python -m pytest -q
# 1 passed
```

## Production route decision

Production slide-making tools are fixed to:

- `codex-guizang-html` — primary high-fidelity HTML/presentation composer.
- `codex-presentation-pptx` — PPTX delivery/template-native route.

Supporting/fallback tools:

- ComfyUI — graphical asset forge, not slide composer.
- `codex-reveal-playwright` — fallback/export experiments only.
- `codex-editable-html-slides` — excluded.

## Current implementation state

Synced implementation commits include:

```text
6f0edfa feat: add design spec and fidelity pipeline primitives
975f297 feat: add SlideForge artifact CLI
0de907c feat: generate ComfyUI asset briefs
a762242 feat: add run evidence manifest writer
3693a7e feat: add guizang HTML presentation composer
0706bf0 feat: add HTML smoke run artifact writer
37f92cc feat: add fidelity markdown report
dbe924b feat: render archetype-specific HTML sections
af85dab feat: support structured slide content
48e56e5 feat: add browser regression evidence plan
841c99f feat: add ComfyUI asset placeholder seam
5fd4cac feat: add PPTX delivery gate contract
3d113d8 feat: add chart and comparison slide schemas
1cb4c27 feat: add Playwright screenshot runner
3f50fbd feat: add ComfyUI handoff report
6f32791 feat: add PPTX export seam
279d2e6 refactor: extract slide schemas
6153d5b feat: add run evidence summary
0ac331b feat: add local run orchestrator
2b9df84 feat: add deck preparation command
b531a35 feat: add source section preparation
9c3132a feat: add source local run command
81d9746 feat: add evidence pack export
d7ed0b2 feat: add design source local runner
```

Implemented primitives:

- `slideforge.design_spec` — colors, typography, slide archetypes, background layers, graphic motifs.
- `slideforge.template_analyzer` — template observations to design spec.
- `slideforge.archetype_mapper` — content sections to template-like slide archetype mappings.
- `slideforge.asset_brief` — text-free ComfyUI asset brief schema.
- `slideforge.asset_brief_generator` — design spec + mappings to ComfyUI-ready briefs.
- `slideforge.comfyui_handoff` — evidence-first ComfyUI handoff/report seam for generated asset briefs; checks an already-running endpoint, records blockers/status, optionally submits workflow API prompts, and never claims generated assets unless output files exist.
- `slideforge.run_manifest` — run/evidence manifest and markdown evidence index writer.
- `slideforge.schemas` — reusable deck/slide content dataclasses and validation (`HtmlDeck`, `HtmlSlide`, `VisualChip`, `AssetPlaceholder`, `TimelineStep`, `MetricRow`, `ChartDatum`, `ComparisonColumn`, `ComparisonRow`); legacy imports remain re-exported from `guizang_html_composer`.
- `slideforge.guizang_html_composer` — deterministic 16:9 HTML presentation shell with keyboard navigation, counter, progress bar, print CSS, escaped user content, archetype-specific visual-band/timeline/table/chart/comparison-matrix sections, structured content, and placeholder-only ComfyUI `AssetPlaceholder` cards for visual archetypes.
- `slideforge.smoke_run` — end-to-end compose-html smoke run writer that emits `deck.json`, `deck.html`, `browser-regression-plan.json`, `manifest.json`, and `evidence-index.md`.
- `slideforge.browser_regression` — dependency-free browser regression checklist/plan contract with expected slide count, slide ids, archetypes, and explicit `not_captured` screenshot status.
- `slideforge.browser_capture` — optional Playwright Chromium screenshot runner that captures per-slide PNGs and writes `browser-regression-report.json` with detected slide count, screenshots, viewport, browser name, console errors, and capture status.
- `slideforge.pptx_delivery_gate` — dependency-free PPTX delivery/render strategy contract with local tool availability, static/visual check plans, blockers, and explicit no-export/no-render validation claim.
- `slideforge.pptx_export` — optional `python-pptx` PPTX generation seam exposed through `export-pptx`; imports the dependency lazily, writes an honest unavailable report when the optional extra is missing, records stale-output/generation-failure blockers, and attaches `pptx-glimpse` renderer evidence only as availability/blocker metadata unless a renderer is actually approved and present.
- `slideforge.evidence_summary` — dependency-free operator summary over a run directory exposed through `summarize-run`; aggregates manifest/deck/browser/PPTX/ComfyUI/fidelity artifacts into honest JSON/Markdown readiness evidence with warnings, blockers, and next actions.
- `slideforge.run_pipeline` — dependency-free local operator handoff runner exposed through `run-local`; turns an existing HtmlDeck-compatible JSON deck into a smoke run plus `run-summary.json`/`run-summary.md`, validates run ids to avoid path-like escapes, and records missing external evidence honestly.
- `slideforge.deck_preparer` — dependency-free upstream deck preparation seam exposed through `prepare-deck`; validates structured user sections, maps intents/design-spec archetypes conservatively, and writes HtmlDeck-compatible JSON that `run-local` can consume.
- `slideforge.section_preparer` — dependency-free extractive source-material preparation seam exposed through `prepare-sections`; converts local plain text/Markdown-like outlines into structured section JSON with conservative intent aliases, duplicate-safe ids, and no semantic/provider summarization claims.
- `slideforge.source_pipeline` — dependency-free all-in-one source-material handoff exposed through `run-source-local`; composes `prepare-sections`, `prepare-deck`, and `run-local`, writes intermediate `sections.json`/`deck.json`, prints compact JSON, and preserves honest missing-evidence status.
- `slideforge.design_source_pipeline` — dependency-free all-in-one design-reference/source handoff exposed through `run-design-source-local`; builds `design-spec.json` from local observations, then runs the source-local path with that DesignSpec and preserves honest missing-evidence status.
- `slideforge.evidence_pack` — dependency-free evidence-pack exporter exposed through `export-evidence-pack`; zips existing run artifacts with embedded/optional sidecar manifest, per-file SHA-256 checksums, honest summary status, symlink skipping, and output-inside-run-dir protection.
- `slideforge.fidelity_scorer` — 100-point template-fidelity scoring.
- `slideforge.fidelity_report` — markdown report renderer with PASS/PASS_WITH_WARNINGS/WEAK_PASS/FAIL verdicts.
- `slideforge.cli` — `prepare-sections`, `prepare-deck`, `build-spec`, `generate-asset-briefs`, `compose-html`, `comfyui-handoff`, `smoke-html`, `capture-screenshots`, `export-pptx`, `pptx-delivery-gate`, `export-evidence-pack`, `run-source-local`, `run-design-source-local`, `run-local`, `summarize-run`, and `score-fidelity --markdown-output` artifact commands.

Validation:

```text
PYTHONPATH=src python -m pytest -q
# 98 passed

PYTHONPATH=src python -m slideforge.cli --help
# prepare-sections, prepare-deck, build-spec, generate-asset-briefs, compose-html, comfyui-handoff, smoke-html, capture-screenshots, export-pptx, pptx-delivery-gate, export-evidence-pack, run-source-local, run-design-source-local, run-local, summarize-run, score-fidelity

PYTHONPATH=src python -m slideforge.cli capture-screenshots --deck-html runs/jarvis-browser-runner-smoke/deck.html --output-dir runs/jarvis-browser-runner-smoke/browser-capture --expected-slide-count 2
# wrote browser-regression-report.json and slide-01.png/slide-02.png with screenshot_capture.status=captured

PYTHONPATH=src python -m slideforge.cli comfyui-handoff --asset-briefs runs/jarvis-comfyui-handoff-hermes-smoke/asset-briefs.json --output-dir runs/jarvis-comfyui-handoff-hermes-smoke --endpoint http://127.0.0.1:8188 --timeout 0.5
# wrote comfyui-handoff-report.json with status=unavailable, server_available=false, generated_assets=0, pending_assets=2, failed_assets=0 because local ComfyUI was not running

PYTHONPATH=src python -m slideforge.cli export-pptx --deck runs/jarvis-pptx-real-render-smoke/deck.json --output runs/jarvis-pptx-real-render-smoke/deck.pptx --report-output runs/jarvis-pptx-real-render-smoke/pptx-export-report.json --run-id jarvis-pptx-real-render-smoke
# after approved repo-local optional extra install: report status=available, output_exists=true, generated_this_run=true, slide_count_generated=3; temp-local pptx-glimpse rendered 3 PNG + 3 SVG files at 1280x720 with Malgun Gothic font mapping and visual inspection PASS for Korean glyphs/no clipping/no overlap

PYTHONPATH=src python -m slideforge.cli summarize-run --run-dir runs/jarvis-evidence-summary-smoke --output runs/jarvis-evidence-summary-smoke/hermes-verified-run-summary.json --markdown-output runs/jarvis-evidence-summary-smoke/hermes-verified-run-summary.md
# wrote operator summary with status=ready_with_warnings, sections=[browser_capture, comfyui, fidelity, html, pptx], warnings=1, blockers=0

PYTHONPATH=src python -m slideforge.cli prepare-sections --source runs/jarvis-prepare-sections-hermes-input/source.md --output runs/jarvis-prepare-sections-hermes-input/sections-postfix.json
# wrote 4 structured sections; ids=[폐쇄망-ai-운영-전략, kpi-metrics-table, architecture-flow, 비교-기준]; intents=[policy, table, architecture, comparison]; reviewer-requested false-positive fix verified for 사업 목표/성과 목표/Geometric Ecosystem

PYTHONPATH=src python -m slideforge.cli prepare-deck --title "Hermes Prepare Sections Postfix" --sections runs/jarvis-prepare-sections-hermes-input/sections-postfix.json --output runs/jarvis-prepare-sections-hermes-input/deck-postfix.json
# consumed prepared sections and wrote HtmlDeck-compatible deck.json

PYTHONPATH=src python -m slideforge.cli run-design-source-local --source /tmp/jarvis-runtime/slideforge/design-source-local-smoke/source.md --observations /tmp/jarvis-runtime/slideforge/design-source-local-smoke/observations.json --design-name "Hermes Design Source Verification" --title "Hermes Design Source Verification" --runs-dir runs --run-id jarvis-run-design-source-local-hermes
# wrote design-spec/sections/deck handoff at runs/jarvis-run-design-source-local-hermes-input/{design-spec.json,sections.json,deck.json}; wrote run artifacts at runs/jarvis-run-design-source-local-hermes/; design_spec.name=Hermes Design Source Verification; section_count=2; deck_slides=2; first_archetype=policy_card; summary_status=needs_visual_evidence; blockers=0; warnings=4; missing external evidence=[browser screenshot capture, PPTX export/render, ComfyUI generated asset, fidelity score/report]
```

## Next work

1. For production PPTX delivery, keep the `python-pptx` seam as first-pass static/native evidence and continue requiring renderer or manual QA before final visual acceptance; temp-local `pptx-glimpse` smoke passed for the 3-slide harness sample after Malgun Gothic font mapping.
2. Use `run-design-source-local` when local design-reference observations are available, or `run-source-local` when only source text/Markdown-like outlines are available; both preserve honest missing-evidence status, and `export-evidence-pack` packages existing run artifacts for sharing/archive without generating or claiming missing evidence.
3. Next product phase should integrate real visual/PPTX/ComfyUI/fidelity evidence capture where approved, while preserving evidence-first and no-provider/no-install boundaries unless explicitly approved.
