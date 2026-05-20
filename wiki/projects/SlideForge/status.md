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

Local commits ahead of origin as of this update:

```text
6f0edfa feat: add design spec and fidelity pipeline primitives
975f297 feat: add SlideForge artifact CLI
0de907c feat: generate ComfyUI asset briefs
```

Implemented primitives:

- `slideforge.design_spec` — colors, typography, slide archetypes, background layers, graphic motifs.
- `slideforge.template_analyzer` — template observations to design spec.
- `slideforge.archetype_mapper` — content sections to template-like slide archetype mappings.
- `slideforge.asset_brief` — text-free ComfyUI asset brief schema.
- `slideforge.asset_brief_generator` — design spec + mappings to ComfyUI-ready briefs.
- `slideforge.fidelity_scorer` — 100-point template-fidelity scoring.
- `slideforge.cli` — `build-spec`, `generate-asset-briefs`, and `score-fidelity` artifact commands.

Validation:

```text
PYTHONPATH=src python -m pytest -q
# 15 passed

PYTHONPATH=src python -m slideforge.cli --help
# build-spec, generate-asset-briefs, score-fidelity
```

## Next work

1. Implement a run manifest/evidence directory writer so every analysis/generation pass leaves durable artifacts.
2. Add a deterministic HTML presentation skeleton for the `codex-guizang-html` route.
3. Add visual-fidelity report markdown generation from score JSON.
4. Add PPTX delivery gate and visual-render strategy.
