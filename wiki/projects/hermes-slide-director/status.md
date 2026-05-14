# Hermes Slide Director Status

## Current state

- Project created as a clean-start repository at `/home/hskim/projects/hermes-slide-director`.
- GitHub private repo created and pushed at `https://github.com/Han43seong/hermes-slide-director`; local `origin` tracks `origin/main`.
- Purpose: Hermes-orchestrated Claude Design loop harness for high-fidelity slide decks.
- The project intentionally centers on the Hermes conversation-first flow before implementing any dashboard.
- Existing `slide-harness` remains as prior experiment/reference; this project is the new direction.

## Active product model

User supplies:

1. Research material: reports, RFPs, notes, PDFs/text extracts, URLs, or proposal drafts.
2. Design reference: template link, Claude Design reference, website/brand reference, screenshot, or style brief.
3. Optional constraints: audience, purpose, slide count, tone, language, must-include/must-exclude items.

Hermes then:

1. Converts the conversation into operator intake artifacts.
2. Proposes verification criteria.
3. Waits for user review/edit/approval.
4. Prepares generation from approved criteria.
5. Directs Claude Design-style HTML deck generation.
6. Renders PDF/screenshots.
7. Runs content/design/readability/export QA.
8. Creates revision briefs and loops until pass or max iteration.

## Repository contents

- `README.md` — product definition and canonical pipeline.
- `docs/product-vision.md` — what this is and is not.
- `docs/architecture.md` — orchestrator/generator/renderer/critic/reviser/dashboard components.
- `docs/mvp-plan.md` — phased MVP plan, starting with CLI proof before dashboard.
- `schemas/verification-criteria.schema.json` — approved criteria contract.
- `schemas/job.schema.json` — job state contract.
- `examples/user-scenario.md` — representative use case.
- `src/hermes_slide_director/cli.py` — CLI scaffold with doctor, loop description, conversation-first intake, criteria proposal/approval, generation preparation, dry-run deck production, local render-check, local QA, revision-brief, apply-revision, local loop, optional browser-render, critic, and finalization commands.
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
- `src/hermes_slide_director/phase10.py` — Phase 10 critic hook contract preparation for future semantic/design/combined external critic handoff; writes durable contract/brief artifacts without invoking an external critic.
- `src/hermes_slide_director/phase11.py` — Phase 11 critic report ingestion for file-only external critic reports, with schema validation and job-status mapping.
- `src/hermes_slide_director/phase12.py` — Phase 12 dry-run critic report producer adapter for Phase 11-compatible reports.
- `src/hermes_slide_director/phase13.py` — Phase 13 deterministic local final package manifest writer for finalized runs.
- `src/hermes_slide_director/phase14.py` — Phase 14 conversation-first slide job intake and proposed-criteria artifact writer.
- `src/hermes_slide_director/phase15.py` — Phase 15 Hermes-authored Claude Design producer prompt/contract preparation from operator intake plus approved criteria.
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
- `tests/test_phase10.py` — critic contract/brief/job-artifact tests, local-QA prerequisite checks, optional browser-report behavior, critic-kind validation, and CLI parsing tests.
- `tests/test_phase11.py` — critic report ingestion validation, artifact writing, status mapping, confidence/finding schema, and CLI parsing tests.
- `tests/test_phase12.py` — dry-run critic report producer validation, default artifact path, Phase 11-compatible shape, scope guards, and CLI parsing tests.
- `tests/test_phase13.py` — final package manifest/report tests, source-artifact reference behavior, optional browser artifact warnings, and CLI parsing tests.
- `tests/test_phase14.py` — conversation-first intake artifact, proposed criteria, validation, and CLI parsing tests.
- `tests/test_phase15.py` — design producer contract, brief, Claude Design prompt, approved-criteria gate, allow-proposed behavior, and CLI parsing tests.

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
- `2026-05-14`: Built Phase 10 critic hook contract CLI.
  - Command added: `prepare-critic --run <run_dir> [--iteration <n>] [--critic-kind semantic|design|combined] [--include-browser-report]`.
  - Artifacts: `iterations/<NNN>/critic-contract.json` and `critic-brief.md`.
  - Scope is contract-only: prepares durable handoff artifacts and does not call an external critic, LLM, browser, network API, or paid service.
  - Requires local QA (`review-qa`) first; `--include-browser-report` includes `browser-render-report.json` only when that optional report already exists, otherwise it fails clearly.
  - Producer/Reviewer loop: separate reviewer verdict `PASS`.
  - Verification: `PYTHONPATH=src python -m pytest -q` -> `52 passed`; doctor OK; smoke through `run-local-loop` -> `prepare-critic` OK.
  - Commit: `dfea114 feat: add critic hook contract CLI`.
- `2026-05-14`: Built Phase 11 critic report ingestion CLI.
  - Command added: `ingest-critic-report --run <run_dir> --report <path> [--iteration <n>]`.
  - Artifacts: `iterations/<NNN>/critic-report.json` and `critic-report.md`.
  - Scope is file-only report ingestion: validates and records an already-produced critic report; it does not call an external critic, LLM, browser, network API, or paid service.
  - Prerequisite: `prepare-critic` must have created `iterations/<NNN>/critic-contract.json` for the target iteration.
  - Validation requires verdict `PASS`, `REQUEST_CHANGES`, `ESCALATE_TO_USER`, or `ABORT`; numeric confidence in `0..1`; and findings with `criterion_id`, `passed`, `evidence`, and `required_fixes` fields.
  - Job status mapping: `PASS` -> `passed`, `REQUEST_CHANGES` -> `revising`, `ESCALATE_TO_USER` -> `user_review`, `ABORT` -> `failed`.
  - Producer/Reviewer loop: final reviewer verdict `PASS` after two `REQUEST_CHANGES` fixes aligning Phase 10/11 confidence and finding schema.
  - Verification: `PYTHONPATH=src python -m pytest -q` -> `68 passed`; doctor OK; smoke through `run-local-loop` -> `prepare-critic` -> `ingest-critic-report` OK.
  - Commit: `b3c1182 feat: add critic report ingestion CLI`.
- `2026-05-14`: Built Phase 12 dry-run critic report producer adapter.
  - Command added: `produce-critic-report --run <run_dir> [--iteration <n>] [--mode dry-run] [--verdict PASS|REQUEST_CHANGES|ESCALATE_TO_USER|ABORT] [--out <path>]`.
  - Default artifact: `iterations/<NNN>/external-critic-report.dry-run.json`.
  - Scope is dry-run-only: no external critic call, no automatic ingestion, and no job mutation.
  - Prerequisite: `prepare-critic` must have created `iterations/<NNN>/critic-contract.json` first.
  - Produces a Phase 11-compatible report shape for follow-up `ingest-critic-report`.
  - Producer/Reviewer loop: `PASS`.
  - Verification: `PYTHONPATH=src python -m pytest -q` -> `75 passed`; doctor OK; smoke through `run-local-loop` -> `prepare-critic` -> `produce-critic-report` -> `ingest-critic-report` OK.
  - Commit: `39dfef9 feat: add dry-run critic report producer`.
- `2026-05-14`: Built Phase 13 deterministic local final package CLI.
  - Command added: `finalize-run --run <run_dir> [--iteration <n>]`.
  - Artifacts: `final/final-package.json` and `final/final-package.md`.
  - Scope is local finalization only: the final package references source artifacts instead of copying every deck/report/source file.
  - Optional browser/PDF/screenshot artifacts are recorded as warnings when absent, not as hard failures.
  - `job.json` moves to `finalized`; corrected smoke selected iteration `001` for job id `phase13-verify`.
  - Producer/Reviewer separation: background OMX producer returned exit 0; independent read-only background Codex reviewer returned `PASS`, while Hermes/JARVIS ran full verification separately. This kept the main channel responsive during implementation and review.
  - Verification: `PYTHONPATH=src python -m pytest -q` -> `81 passed in 0.36s`; doctor OK with `11 job statuses, 4 reviewer verdicts`; corrected finalize smoke through propose/approve/prepare-generation/produce-deck/check-render/review-qa/prepare-critic/produce-critic-report PASS/ingest-critic-report/finalize-run produced the final package artifacts.
  - Commit: `b0778d4 feat: add final package manifest CLI`; branch `main` synced with `origin/main` after push (`ahead/behind 0/0`).
- `2026-05-14`: Built Phase 14 conversation-first slide job intake.
  - User decision: dashboard is deferred; Hermes conversation-first flow is the product center.
  - Command added: `start-slide-job`.
  - Purpose: Hermes/JARVIS can convert user-provided materials, design reference/template, audience, purpose, slide count, language, output format, and constraints into stable run artifacts without requiring the user to handle internal JSON/brief paths directly.
  - Artifacts: `inputs/operator-intake.json`, `inputs/operator-intake.md`, `criteria/proposed.json`, and `criteria/proposed.md`.
  - Product model: conversation -> operator intake -> proposed criteria -> user approval -> prepare-generation -> Producer/Reviewer generation loop.
  - Reviewer: independent background Codex read-only session `proc_3050402e2460` returned no blocking findings or required changes; read-only pytest limitation was covered by Hermes full test run.
  - Verification: Phase 14 tests -> `10 passed`; full suite -> `91 passed`; doctor OK; Hermes smoke under `/tmp/hermes-phase14-hermes-verify.W7Z0LB/run` created intake and proposed criteria artifacts.
  - Commit pushed: `656fd4b feat: add conversation-first slide job intake`; GitHub repo remains `https://github.com/Han43seong/hermes-slide-director`.
- `2026-05-14`: Built Phase 15 Hermes-authored Claude Design producer prompt/contract generation.
  - Command added: `prepare-design-producer`.
  - Purpose: convert Phase 14 operator intake plus approved criteria into durable, structured, offline/local Producer artifacts for a future Claude Design/OMC/HTML deck Producer.
  - Product decision confirmed: Hermes writes the production prompt; raw user input is source material, not the final Claude Design prompt.
  - Artifacts: `generation/design-producer-contract.json`, `generation/design-producer-brief.md`, and `generation/claude-design-prompt.md`.
  - Behavior: requires approved criteria by default; supports explicit allow-proposed/dry-run-style behavior; no real Claude, OMC, provider, or network call.
  - Reviewer: independent background Codex read-only session `proc_ed26aed5e6fc` returned `PASS` with no required changes; read-only pytest limitation was covered by Hermes full test run.
  - Verification: Phase 15 tests -> `7 passed`; full suite -> `98 passed`; doctor OK; Hermes smoke under `/tmp/hermes-phase15-hermes-verify.XwmUPu/run` created all three generation artifacts and verified required structured sections.
  - Commit pushed: `4921e32 feat: add design producer prompt preparation`; GitHub repo remains `https://github.com/Han43seong/hermes-slide-director`.

## Next steps

1. Next likely phase: real background Producer adapter/handoff that can consume the Phase 15 contract.
   - Still gate before provider, secrets, cost, or actual external generation.
2. Keep dashboard work deferred until the conversation-first flow and Producer/Reviewer generation loop are stronger.
3. Background executor hygiene cleanup is already completed and recorded in the JARVIS wiki/status history.
