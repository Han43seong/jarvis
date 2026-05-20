# oh-my-side-design status

- status: active
- updated: 2026-05-20
- repo: `/home/hskim/projects/oh-my-side-design`
- remote: `https://github.com/Han43seong/oh-my-side-design.git`
- visibility: private

## Purpose

`oh-my-side-design` is the clean-start successor direction after `hermes-slide-director` Phase 42.

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
```

Initial files:

- `README.md`
- `docs/architecture.md`
- `pyproject.toml`
- `src/oh_my_side_design/__init__.py`
- `src/oh_my_side_design/toolchain.py`
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

## Next work

1. Build the template deep-analyzer/design-spec skeleton.
2. Define asset-brief schema for ComfyUI text-free graphics.
3. Implement guizang HTML composer with custom presentation mode.
4. Add fidelity scoring rubric and evidence report format.
5. Add PPTX delivery gate and visual-render strategy.
