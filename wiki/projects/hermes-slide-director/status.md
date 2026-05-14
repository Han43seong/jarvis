# Hermes Slide Director Status

## Current state

- Project created as a clean-start repository at `/home/hskim/projects/hermes-slide-director`.
- Purpose: Hermes-orchestrated Claude Design loop harness for high-fidelity slide decks.
- The project intentionally starts from product/architecture contracts before implementing a dashboard or generator.
- Existing `slide-harness` remains as prior experiment/reference; this project is the new direction.

## Active product model

User supplies:

1. Research material: reports, RFPs, notes, PDFs/text extracts, URLs, or proposal drafts.
2. Design reference: template link, Claude Design reference, website/brand reference, screenshot, or style brief.
3. Optional constraints: audience, purpose, slide count, tone, language, must-include/must-exclude items.

Hermes then:

1. Analyzes material and design reference.
2. Proposes verification criteria.
3. Waits for user review/edit/approval.
4. Directs Claude Design-style HTML deck generation.
5. Renders PDF/screenshots.
6. Runs content/design/readability/export QA.
7. Creates revision briefs and loops until pass or max iteration.

## Initial repository contents

- `README.md` — product definition and canonical pipeline.
- `docs/product-vision.md` — what this is and is not.
- `docs/architecture.md` — orchestrator/generator/renderer/critic/reviser/dashboard components.
- `docs/mvp-plan.md` — phased MVP plan, starting with CLI proof before dashboard.
- `schemas/verification-criteria.schema.json` — approved criteria contract.
- `schemas/job.schema.json` — job state contract.
- `examples/user-scenario.md` — representative use case.
- `src/hermes_slide_director/cli.py` — minimal CLI scaffold.

## Next steps

1. Implement Phase 0 contracts in code: Pydantic models for jobs, criteria, iterations, and QA reports.
2. Build a CLI-only proof before any dashboard work.
3. Add material/design-reference ingestion for Markdown/text first.
4. Add generator prompt contract for Claude Design-style HTML decks.
5. Add renderer checks for HTML/PDF/screenshots.
6. Add critic report schema and one QA loop.
