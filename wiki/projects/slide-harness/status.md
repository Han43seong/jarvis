---
title: Slide Harness Project Status
created: 2026-05-12
updated: 2026-05-12
type: project-status
project: slide-harness
status: active
tags: [jarvis, slides, html, pdf, claude-design, qa-loop]
sources: [wiki/concepts/slide-generation-harness.md]
confidence: medium
---

# Slide Harness Project Status

## Summary

`slide-harness` is an HTML-first presentation/deck generation harness under `/home/hskim/projects/slide-harness`.

It uses a neutral brief/slide-plan model, a Claude Design-style HTML renderer, static QA, and Playwright CLI export to produce a PDF and preview image.

## Current MVP

Implemented:

- JSON brief intake
- Requirement selector with audience/purpose-specific criteria
- User-reviewable `requirements.md` and machine-readable `requirements.json`
- Deterministic slide plan generation
- Fixed 16:9 HTML deck renderer
- Keyboard navigation and slide counter
- Print/PDF CSS for 7-page deck export
- Static QA for slide count, placeholders, density, and visual elements
- Playwright CLI export to `deck.pdf` and `preview.png`
- Example run at `/home/hskim/projects/slide-harness/runs/demo`
- Pytest suite with 6 passing tests

## Verification

Latest verified commands:

```bash
cd /home/hskim/projects/slide-harness
python3 -m slide_harness.cli run --brief examples/brief.json --out runs/demo
python3 -m pytest -q
file runs/demo/final/deck.pdf runs/demo/final/preview.png
pdfinfo runs/demo/final/deck.pdf | grep Pages
```

Observed:

- `6 passed`
- `deck.pdf`: PDF document, 7 pages
- `preview.png`: PNG image, 1920x1080
- Browser visual check: cover slide centered/readable after alignment fix
- Browser console: no errors

## Next Work

Recommended next phases:

1. Add explicit requirement approval gate before final generation.
2. Add slide-by-slide screenshot/contact sheet export.
3. Add iterative revision loop from QA issues.
4. Add design token files and named style presets.
5. Add template/theme import path.
6. Add PPTX renderer/export adapter only if editable PowerPoint output is required.
