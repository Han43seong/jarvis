# Hermes Slide Director Status

## Current state

- Project created as a clean-start repository at `/home/hskim/projects/hermes-slide-director`.
- GitHub private repo created and pushed at `https://github.com/Han43seong/hermes-slide-director`; local `origin` tracks `origin/main`.
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

## Repository contents

- `README.md` — product definition and canonical pipeline.
- `docs/product-vision.md` — what this is and is not.
- `docs/architecture.md` — orchestrator/generator/renderer/critic/reviser/dashboard components.
- `docs/mvp-plan.md` — phased MVP plan, starting with CLI proof before dashboard.
- `schemas/verification-criteria.schema.json` — approved criteria contract.
- `schemas/job.schema.json` — job state contract.
- `examples/user-scenario.md` — representative use case.
- `src/hermes_slide_director/cli.py` — CLI scaffold with doctor, loop description, criteria proposal/approval, generation preparation, dry-run deck production, and local render-check commands.
- `src/hermes_slide_director/models.py` — Phase 0 Pydantic models for criteria, jobs, iterations, artifacts, QA reports, and reviewer verdicts.
- `src/hermes_slide_director/phase1.py` — Phase 1 source ingestion and deterministic baseline criteria proposal utilities.
- `src/hermes_slide_director/phase2.py` — Phase 2 dry-run producer contract and Claude Design-style producer brief preparation utilities.
- `src/hermes_slide_director/phase3.py` — Phase 3 local dry-run deck producer adapter that writes placeholder iteration artifacts.
- `src/hermes_slide_director/phase4.py` — Phase 4 deterministic local render-contract checker and report writer.
- `tests/test_models.py` — schema alignment and model validation tests.
- `tests/test_phase1.py` — CLI/source-ingestion/propose/approve artifact tests.
- `tests/test_phase2.py` — prepare-generation contract/brief/failure-path tests.
- `tests/test_phase3.py` — dry-run deck production artifact/job-status tests.
- `tests/test_phase4.py` — local render-check report/status/failure-path tests.

## Recent progress

- `2026-05-14`: Dogfooded the new JARVIS Producer/Reviewer rejection loop on Phase 0 domain models.
  - Producer: delegate_task implementation agent.
  - Reviewer: separate delegate_task critic.
  - Reviewer verdict: `PASS`.
  - Verification: `PYTHONPATH=src python -m pytest -q` -> `6 passed`; `PYTHONPATH=src python -m hermes_slide_director.cli doctor` -> OK; `python -m py_compile src/hermes_slide_director/*.py` -> OK.
  - Commit: `f8433f1 feat: add Phase 0 domain models`.
- `2026-05-14`: Built Phase 1 CLI-only source ingestion and deterministic criteria proposal.
  - GitHub initial project push completed.
  - Commands added: `propose-criteria` and `approve-criteria`.
  - Artifacts: `job.json`, `inputs/metadata.json`, copied material/design-reference inputs, `criteria/proposed.json`, `criteria/proposed.md`, `criteria/approved.json`, `criteria/approved.md`.
  - Baseline criteria cover content, narrative, design, readability, export, and risk.
  - Producer/Reviewer loop: initial reviewer requested path-only `--materials` enforcement and README correction; fixes applied; final reviewer verdict `PASS`.
  - Verification: `PYTHONPATH=src python -m pytest -q` -> `10 passed`; doctor OK; propose/approve smoke OK; missing-material smoke exits non-zero with expected message.
  - Commit: `34bb0d0 feat: add Phase 1 criteria proposal CLI`.
- `2026-05-14`: Built Phase 2 dry-run generation prompt contract.
  - Command added: `prepare-generation --run <run_dir> [--deck-title ...] [--audience ...] [--language ...] [--slide-count ...]`.
  - Artifacts: `generation/producer-contract.json` and `generation/producer-brief.md`.
  - The contract records job id, run marker, title/audience/language/slide count, source materials, design references, approved criteria path, required producer outputs, constraints, and QA inputs.
  - `job.json` status moves to `generating` to mark generation preparation; no deck/renderer/LLM call is performed yet.
  - Producer/Reviewer loop: separate reviewer verdict `PASS`.
  - Verification: `PYTHONPATH=src python -m pytest -q` -> `14 passed`; doctor OK; propose -> approve -> prepare-generation smoke OK.
  - Commit: `3f257a0 feat: add Phase 2 generation brief CLI`.
- `2026-05-14`: Built Phase 3 local dry-run deck producer adapter.
  - Command added: `produce-deck --run <run_dir> [--iteration <n>] [--mode dry-run]`.
  - Artifacts: `iterations/<NNN>/deck.html`, `speaker-notes.md`, and `artifact-manifest.json`.
  - The placeholder HTML deck is deterministic, self-contained, 16:9-friendly, visibly watermarked as dry-run output, and includes source/criteria trace notices.
  - `job.json` receives an `Iteration` entry and moves to `rendering` because renderer checks are next.
  - Producer/Reviewer loop: separate reviewer verdict `PASS`.
  - Verification: `PYTHONPATH=src python -m pytest -q` -> `19 passed`; doctor OK; propose -> approve -> prepare-generation -> produce-deck smoke OK.
  - Commit: `1a5e9a6 feat: add dry-run deck producer adapter`.
- `2026-05-14`: Built Phase 4 deterministic local render-check reports.
  - Command added: `check-render --run <run_dir> [--iteration <n>]`.
  - Artifacts: `iterations/<NNN>/render-report.json` and `render-report.md`.
  - Checks cover deck/manifest existence, doctype, 16:9 marker, dry-run watermark, slide sections, manifest artifact path existence, manifest iteration consistency, and approved criteria path existence.
  - This remains local deterministic contract checking only; no browser, Playwright, PDF, screenshots, network, or LLM calls.
  - `job.json` moves to `qa_reviewing` because renderer-contract checks are complete and criteria QA is next.
  - Producer/Reviewer loop: separate reviewer verdict `PASS`.
  - Verification: `PYTHONPATH=src python -m pytest -q` -> `24 passed`; doctor OK; propose -> approve -> prepare-generation -> produce-deck -> check-render smoke OK.
  - Commit: `7c2a467 feat: add local render check CLI`.

## Next steps

1. Add criteria QA report persistence and one local critic loop against approved criteria and render reports.
2. Add revision brief generation for `REQUEST_CHANGES` findings.
3. Add real browser/Playwright rendering, screenshot/PDF export, console capture, and layout overflow checks after the local QA loop is stable.
4. Add dashboard only after CLI proof and quality loop are stable.
