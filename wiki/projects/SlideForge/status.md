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
```

Implemented primitives:

- `slideforge.design_spec` — colors, typography, slide archetypes, background layers, graphic motifs.
- `slideforge.template_analyzer` — template observations to design spec.
- `slideforge.archetype_mapper` — content sections to template-like slide archetype mappings.
- `slideforge.asset_brief` — text-free ComfyUI asset brief schema.
- `slideforge.asset_brief_generator` — design spec + mappings to ComfyUI-ready briefs.
- `slideforge.run_manifest` — run/evidence manifest and markdown evidence index writer.
- `slideforge.guizang_html_composer` — deterministic 16:9 HTML presentation shell with keyboard navigation, counter, progress bar, print CSS, escaped user content, archetype-specific visual-band/timeline/table sections, structured `VisualChip`/`TimelineStep`/`MetricRow` content, and placeholder-only ComfyUI `AssetPlaceholder` cards for visual archetypes.
- `slideforge.smoke_run` — end-to-end compose-html smoke run writer that emits `deck.json`, `deck.html`, `browser-regression-plan.json`, `manifest.json`, and `evidence-index.md`.
- `slideforge.browser_regression` — dependency-free browser regression checklist/plan contract with expected slide count, slide ids, archetypes, and explicit `not_captured` screenshot status.
- `slideforge.pptx_delivery_gate` — dependency-free PPTX delivery/render strategy contract with local tool availability, static/visual check plans, blockers, and explicit no-export/no-render validation claim.
- `slideforge.fidelity_scorer` — 100-point template-fidelity scoring.
- `slideforge.fidelity_report` — markdown report renderer with PASS/PASS_WITH_WARNINGS/WEAK_PASS/FAIL verdicts.
- `slideforge.cli` — `build-spec`, `generate-asset-briefs`, `compose-html`, `smoke-html`, `pptx-delivery-gate`, and `score-fidelity --markdown-output` artifact commands.

Validation:

```text
PYTHONPATH=src python -m pytest -q
# 36 passed

PYTHONPATH=src python -m slideforge.cli --help
# build-spec, generate-asset-briefs, compose-html, smoke-html, pptx-delivery-gate, score-fidelity
```

## Next work

1. Extend content schema for charts and comparison matrices.
2. Add optional real screenshot runner once browser automation dependencies are explicitly approved.
3. Add real ComfyUI output handoff once ComfyUI/provider execution is explicitly approved.
4. Add real PPTX export/render integration once a renderer path such as LibreOffice or pptx-glimpse is explicitly approved.
