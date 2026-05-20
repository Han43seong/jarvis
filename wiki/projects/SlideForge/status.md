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
- `slideforge.fidelity_scorer` — 100-point template-fidelity scoring.
- `slideforge.fidelity_report` — markdown report renderer with PASS/PASS_WITH_WARNINGS/WEAK_PASS/FAIL verdicts.
- `slideforge.cli` — `build-spec`, `generate-asset-briefs`, `compose-html`, `comfyui-handoff`, `smoke-html`, `capture-screenshots`, `export-pptx`, `pptx-delivery-gate`, and `score-fidelity --markdown-output` artifact commands.

Validation:

```text
PYTHONPATH=src python -m pytest -q
# 57 passed

PYTHONPATH=src python -m slideforge.cli --help
# build-spec, generate-asset-briefs, compose-html, comfyui-handoff, smoke-html, capture-screenshots, export-pptx, pptx-delivery-gate, score-fidelity

PYTHONPATH=src python -m slideforge.cli capture-screenshots --deck-html runs/jarvis-browser-runner-smoke/deck.html --output-dir runs/jarvis-browser-runner-smoke/browser-capture --expected-slide-count 2
# wrote browser-regression-report.json and slide-01.png/slide-02.png with screenshot_capture.status=captured

PYTHONPATH=src python -m slideforge.cli comfyui-handoff --asset-briefs runs/jarvis-comfyui-handoff-hermes-smoke/asset-briefs.json --output-dir runs/jarvis-comfyui-handoff-hermes-smoke --endpoint http://127.0.0.1:8188 --timeout 0.5
# wrote comfyui-handoff-report.json with status=unavailable, server_available=false, generated_assets=0, pending_assets=2, failed_assets=0 because local ComfyUI was not running

PYTHONPATH=src python -m slideforge.cli export-pptx --deck runs/jarvis-pptx-real-render-smoke/deck.json --output runs/jarvis-pptx-real-render-smoke/deck.pptx --report-output runs/jarvis-pptx-real-render-smoke/pptx-export-report.json --run-id jarvis-pptx-real-render-smoke
# after approved repo-local optional extra install: report status=available, output_exists=true, generated_this_run=true, slide_count_generated=3; temp-local pptx-glimpse rendered 3 PNG + 3 SVG files at 1280x720 with Malgun Gothic font mapping and visual inspection PASS for Korean glyphs/no clipping/no overlap
```

## Next work

1. For production PPTX delivery, keep the `python-pptx` seam as first-pass static/native evidence and continue requiring renderer or manual QA before final visual acceptance; temp-local `pptx-glimpse` smoke passed for the 3-slide harness sample after Malgun Gothic font mapping.
2. Next product phase is no longer schema extraction; choose the next operator-facing capability or production-route hardening target before proceeding.
