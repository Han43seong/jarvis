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
- `src/hermes_slide_director/cli.py` — CLI scaffold with doctor, loop description, criteria proposal/approval, generation preparation, dry-run deck production, local render-check, local QA, revision-brief, apply-revision, local loop, and optional browser-render commands.
- `src/hermes_slide_director/models.py` — Phase 0 Pydantic models for criteria, jobs, iterations, artifacts, QA reports, and reviewer verdicts.
- `src/hermes_slide_director/phase1.py` — Phase 1 source ingestion and deterministic baseline criteria proposal utilities.
- `src/hermes_slide_director/phase2.py` — Phase 2 dry-run producer contract and Claude Design-style producer brief preparation utilities.
- `src/hermes_slide_director/phase3.py` — Phase 3 local dry-run deck producer adapter that writes placeholder iteration artifacts.
- `src/hermes_slide_director/phase4.py` — Phase 4 deterministic local render-contract checker and report writer.
- `src/hermes_slide_director/phase5.py` — Phase 5 deterministic local criteria QA reviewer and report writer.
- `src/hermes_slide_director/phase6.py` — Phase 6 deterministic revision brief planner for REQUEST_CHANGES findings.
- `src/hermes_slide_director/phase7.py` — Phase 7 deterministic local revision-iteration applicator for next-iteration artifacts.
- `src/hermes_slide_director/phase8.py` — Phase 8 deterministic local max-iteration loop orchestrator and report writer.
- `src/hermes_slide_director/phase9.py` — Phase 9 optional Playwright browser-render/export checks with screenshot/PDF/report artifacts.
- `tests/test_models.py` — schema alignment and model validation tests.
- `tests/test_phase1.py` — CLI/source-ingestion/propose/approve artifact tests.
- `tests/test_phase2.py` — prepare-generation contract/brief/failure-path tests.
- `tests/test_phase3.py` — dry-run deck production artifact/job-status tests.
- `tests/test_phase4.py` — local render-check report/status/failure-path tests.
- `tests/test_phase5.py` — local criteria QA verdict/report/status tests.
- `tests/test_phase6.py` — deterministic revision brief generation/status/failure-path tests.
- `tests/test_phase7.py` — deterministic revision application/iteration-2 render-QA PASS tests.
- `tests/test_phase8.py` — deterministic local max-iteration loop/report tests.
- `tests/test_phase9.py` — optional browser-render report/artifact/failure-path tests using fake Playwright.

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
- `2026-05-14`: Built Phase 5 deterministic local criteria QA reports.
  - Command added: `review-qa --run <run_dir> [--iteration <n>]`.
  - Artifacts: `iterations/<NNN>/qa-report.json` and `qa-report.md`.
  - QA evaluates approved criteria with local filesystem/text checks only: export depends on render PASS and artifacts; design/readability depend on structural markers; content/narrative/risk require literal acceptance evidence until semantic critics are added.
  - Dry-run placeholder decks intentionally produce `REQUEST_CHANGES`, moving `job.json` to `revising` and setting the iteration verdict/`qa_report_path`.
  - Producer/Reviewer loop: separate reviewer verdict `PASS`.
  - Verification: `PYTHONPATH=src python -m pytest -q` -> `28 passed`; doctor OK; propose -> approve -> prepare-generation -> produce-deck -> check-render -> review-qa smoke OK.
  - Commit: `e2bc616 feat: add local criteria QA CLI`.
- `2026-05-14`: Built Phase 6 deterministic revision brief generation.
  - Command added: `plan-revision --run <run_dir> [--iteration <n>]`.
  - Artifacts: `iterations/<NNN>/revision-brief.md` and `revision-brief.json`.
  - The brief groups REQUEST_CHANGES findings by category, carries required fixes into producer instructions, preserves approved-criteria/source-trace/16:9/artifact-contract/no-unsupported-claims constraints, and declares expected outputs for the next iteration.
  - PASS QA verdicts fail clearly with `no revision needed`; missing QA reports instruct the user to run `review-qa` first.
  - `job.json` stays `revising` and source iteration receives `revision_brief_path`.
  - Producer/Reviewer loop: separate reviewer verdict `PASS`.
  - Verification: `PYTHONPATH=src python -m pytest -q` -> `32 passed`; doctor OK; full CLI smoke through `plan-revision` OK.
  - Commit: `f52238c feat: add deterministic revision brief CLI`.
- `2026-05-14`: Built Phase 7 deterministic local revision application.
  - Command added: `apply-revision --run <run_dir> [--source-iteration <n>]`.
  - Artifacts: `iterations/<next>/deck.html`, `speaker-notes.md`, `artifact-manifest.json`, and `revision-applied.json`.
  - The next-iteration deck is a deterministic `DRY-RUN REVISION STUB` that consumes required fixes/producer instructions and embeds approved acceptance bullets as local QA evidence; it is not real Claude/LLM revision generation.
  - `job.json` keeps the source iteration `revising`, adds/replaces the next iteration as `rendering`, and the follow-on local render/QA commands can bring iteration 2 to PASS.
  - Producer/Reviewer loop: separate reviewer verdict `PASS`.
  - Verification: `PYTHONPATH=src python -m pytest -q` -> `35 passed`; doctor OK; full CLI smoke through `apply-revision`, `check-render --iteration 2`, and `review-qa --iteration 2` -> PASS.
  - Commit: `9b28aa7 feat: add deterministic revision iteration CLI`.
- `2026-05-14`: Built Phase 8 deterministic local max-iteration loop orchestration.
  - Command added: `run-local-loop --run <run_dir> [--max-iterations <n>]`; default max iterations is 3.
  - Artifacts: `loop/local-loop-report.json` and `loop/local-loop-report.md`.
  - The orchestrator requires `prepare-generation`, starts at iteration 1, runs local produce/check/review, plans/applies revisions on REQUEST_CHANGES, and stops at PASS or `MAX_ITERATIONS_REACHED` without external generation.
  - `job.json` reaches `passed` when the final local QA verdict is PASS; max-iteration unresolved loops remain non-passed and report `REQUEST_CHANGES/MAX_ITERATIONS_REACHED`.
  - Producer/Reviewer loop: separate reviewer verdict `PASS`.
  - Verification: `PYTHONPATH=src python -m pytest -q` -> `40 passed`; doctor OK; propose -> approve -> prepare-generation -> `run-local-loop --max-iterations 2` smoke -> PASS at iteration 2.
  - Commit: `95eb057 feat: add deterministic local loop CLI`.
- `2026-05-14`: Built Phase 9 optional Playwright browser-render/export checks.
  - Command added: `browser-render --run <run_dir> [--iteration <n>] [--viewport WIDTHxHEIGHT] [--no-pdf] [--no-screenshot]`; default viewport is `1280x720`.
  - Optional dependency extra added: `hermes-slide-director[browser]`; Chromium install remains manual via `python -m playwright install chromium`.
  - Artifacts on success: `iterations/<NNN>/browser-render-report.json`, `browser-render-report.md`, `deck-screenshot.png` unless disabled, and `deck.pdf` unless disabled.
  - Checks capture console/page errors, deck load, `.slide` presence, approximate 16:9 slide boxes, horizontal overflow, obvious element/text overflow, screenshot export, and PDF export.
  - Missing Playwright or Chromium fails clearly without automatic install/download.
  - `job.json` records browser-render artifacts on the current iteration and moves/remains `qa_reviewing`.
  - Producer/Reviewer loop: separate reviewer verdict `PASS`.
  - Verification: `PYTHONPATH=src python -m pytest -q` -> `45 passed`; doctor OK; propose -> approve -> prepare-generation -> produce-deck -> browser-render negative smoke failed clearly in current environment because Playwright is not installed.
  - Commit: `0b6e038 feat: add optional browser render checks`.

## Next steps

1. Add semantic critic hook / LLM-agent critic contract for content, narrative, risk, and design review beyond deterministic local checks.
2. Add dashboard only after the CLI proof, quality loop, browser-render path, and semantic critic contract are stable.
