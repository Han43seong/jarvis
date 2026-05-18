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
- `src/hermes_slide_director/phase16.py` — Phase 16 local/dry-run Producer handoff package preparation before any real Claude/OMC/provider generation.
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
- `tests/test_phase16.py` — local Producer handoff package, safety booleans, expected output directory, launch-template, and CLI parsing tests.

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
- `2026-05-14`: Built Phase 16 local/dry-run Producer handoff adapter.
  - Command added: `prepare-producer-handoff`.
  - Purpose: package the Phase 15 Claude Design prompt/contract/brief into a local handoff package before any real Claude/OMC/provider generation. This is the safe bridge between the Hermes-authored prompt and a future real Producer launch.
  - Artifacts: `generation/producer-handoff.json`, `generation/producer-handoff.md`, and `generation/producer-launch-command.txt`.
  - Safety behavior: `external_call_made=false`, `approval_required_before_real_launch=true`; expected output directory is `iterations/001/`; expected outputs are `deck.html`, `producer-report.md`, and `asset-manifest.json`.
  - Launch command template avoids putting the full prompt in argv.
  - Scope: no real Claude, OMC, provider, browser, network, dashboard, or deck generation was added.
  - Reviewer: independent reviewer `proc_73754be86170` returned `PASS` with no required changes.
  - Verification: Phase 16 tests -> `7 passed`; full suite -> `105 passed`; doctor OK; Hermes smoke under `/tmp/hermes-phase16-hermes-verify.Ge4ImX/run` created all three handoff artifacts and verified the safety booleans/path.
  - Note: Hermes smoke initially checked the wrong key name `expected_output_dir`; actual JSON key is `expected_output_directory`, and verification was rerun successfully before commit.
  - Commit pushed: `f09b437 feat: add dry-run producer handoff preparation`; GitHub repo remains `https://github.com/Han43seong/hermes-slide-director`.
- `2026-05-15`: Built Phase 17 Producer path quality bake-off preparation.
  - Commit: `3b49eb7 feat: add producer quality bakeoff harness`.
  - Command added: `prepare-bakeoff`.
  - Purpose: prepare equal-budget, quality-first Producer candidate packages and a weighted ranking rubric without executing candidates.
  - Scope remains local/preparation-only; candidate execution, provider calls, browser, network, and paid services remain gated.
- `2026-05-15`: Built Phase 18 content-locked design bake-off preparation.
  - Commits: `1210b28 feat: add content-locked design bakeoff harness`, `046b17b feat: require browser layout gate before design ranking`, `8e8e447 feat: require fresh companion artifacts for final ranking`.
  - Command added: `prepare-content-locked-bakeoff`.
  - Purpose: Hermes locks slide content so Producer comparison ranks design execution only after content compliance passes.
  - Artifacts include `generation/locked-content-plan.*`, `generation/design-only-rubric.*`, `generation/content-compliance-gate.*`, `generation/browser-layout-gate.*`, `generation/companion-artifact-freshness-gate.*`, candidate content-locked prompts, and `reviews/design-only-ranking-template.md`.
  - Hard gates now block ranking on browser layout defects such as clipping, overflow, and overlap, and on stale companion artifacts such as manifests/reports/self-checks that do not describe the current deck.
  - Verification: `PYTHONPATH=src python -m pytest -q` -> `122 passed in 0.56s`; local repo clean and `main...origin/main [ahead 4]`.
- `2026-05-18`: Built Phase 19 candidate execution adapter.
  - Commits: `33630da docs: plan Phase 19 candidate execution adapter`, `4407953 feat: add Phase 19 candidate execution adapter`.
  - Commands added: `run-candidate` and `inspect-candidate`.
  - Purpose: record dry-run execution metadata for a Phase 18 candidate and inspect candidate outputs plus browser-layout/freshness gate evidence before ranking.
  - Safety behavior: Phase 19 remains dry-run/inspection only; it does not execute Producers, call Claude/OMC/Codex/provider/network/paid services, install browsers/tools, or push.
  - Reviewer loop: independent reviewer first returned `REQUEST_CHANGES` because a companion freshness override could pass without a deduction; Hermes added a regression test and fixed `_override_recorded` to require an override marker/status plus a deduction field. Re-review verdict: `PASS`.
  - Verification: `tests/test_phase19.py` -> `13 passed`; full suite -> `135 passed in 0.49s`; CLI smoke for `run-candidate` and `inspect-candidate` emitted stable JSON and returned `ranking_ready=true` only after required outputs plus PASS gate artifacts existed; staged diff hygiene/security scans were clean.
  - Local repo status after commit: `main...origin/main [ahead 6]`.
- `2026-05-18`: Built Phase 20 Codex/OMX OSS Producer candidate registry.
  - Commit: `59a1edb feat: add Phase 20 Codex OSS producer registry`.
  - Command added: `prepare-codex-oss-candidates`.
  - User decision: exclude `claude-code-html-native` and `slidev-native` as primary automation candidates; keep `hosted-claude-design-benchmark` only as a manual quality benchmark reference.
  - New default candidates: `codex-presentation-pptx`, `codex-guizang-html`, `codex-reveal-playwright`, and `codex-editable-html-slides`; PptxGenJS is recorded as a lower-level engine/reference.
  - Purpose: write a deterministic Codex/OMX OSS candidate registry, candidate exclusion record, and per-candidate dry-run launch contracts without installing, cloning, running Codex/OMX/Claude, calling network/provider/paid services, or generating slides.
  - Verification: `tests/test_phase20.py` -> `6 passed`; full suite -> `141 passed in 0.53s`; CLI smoke for `prepare-codex-oss-candidates` verified default candidates, benchmark-only hosted Claude Design, exclusions, and `external_call_made=false`; independent reviewer verdict: `PASS`.
  - Pushed to `origin/main` after user approval.
- `2026-05-18`: Built Phase 21A codex-presentation-pptx source inspection and isolated smoke planning.
  - Commit: `4e1ea75 feat: add Phase 21A PPTX smoke planning`.
  - Command added: `prepare-codex-presentation-pptx-smoke`.
  - Purpose: inspect a local `appautomaton/presentation` source tree for `deck-design-ppt` metadata and produce a Phase 21B smoke plan without installing, cloning, running Codex/OMX/Claude/provider/browser, generating PPTX, or mutating global config.
  - Real local source smoke: read-only inspection against `/home/hskim/jarvis/research_codex_omx/ext/appautomaton__presentation` found `pptxgenjs`, `playwright-core`, `sharp`, 21 pattern JS files, and 21 slot markdown files.
  - Reviewer loop: first review returned `REQUEST_CHANGES` because `--run-dir` could be equal to or nested inside `--source-dir`; Hermes added resolved-path validation and tests to preserve source-tree read-only guarantees. Re-review verdict: `PASS`.
  - Verification: `tests/test_phase21.py` -> `7 passed`; full suite -> `148 passed in 0.51s`; `git diff --check` clean; CLI smoke emitted `source inspected: true`, `candidate execution: not_run`, and `external call made: false`.
  - Pushed to `origin/main` after user approval.
- `2026-05-18`: Ran and recorded Phase 21B isolated `codex-presentation-pptx` native PPTX smoke.
  - Commit: `1640150 feat: record Phase 21B PPTX smoke evidence`.
  - User approval: npm install was explicitly allowed if needed.
  - Manual smoke: copied `appautomaton/presentation` into `/tmp/hermes-slide-director-phase21b.kr8k6Z`, ran `npm install` only inside the temp `deck-design-ppt` copy (`33 packages`, `0 vulnerabilities`), then generated `/tmp/hermes-slide-director-phase21b.kr8k6Z/outputs/codex-presentation-pptx-smoke.pptx`.
  - Smoke result: native PPTX generated successfully (`92916` bytes, 3 slide XML files) using `consulting-mckinsey` palette and patterns `p01-cover`, `p04-scorecard`, `p08-closer`; zip/text extraction confirmed expected cover and closer text.
  - Command added: `record-codex-presentation-pptx-smoke` to record existing PPTX smoke evidence without running npm, generating decks, invoking Codex/OMX/Claude/provider/browser/LibreOffice, copying the temp PPTX, or mutating global config.
  - Verification: `tests/test_phase21.py` -> `14 passed`; full suite -> `155 passed in 0.53s`; CLI smoke against the real generated PPTX produced `pptx valid zip: true`, `slide xml count: 3`, `deck generated: true`, `ranking ready: false`; independent reviewer verdict: `PASS`.
  - Limitation: no visual QA yet because `soffice` and Python `markitdown` were unavailable in the environment; Phase 21B proves native PPTX generation only, not design quality or ranking readiness.
  - Pushed to `origin/main` after user approval.
- `2026-05-18`: Built Phase 22A no-sudo PPTX candidate ingestion and static layout gate.
  - Commit: `c3879ec feat: add Phase 22A PPTX static gate`.
  - Command added: `inspect-pptx-candidate`.
  - Purpose: ingest an existing `codex-presentation-pptx` PPTX by path, validate the Phase 21B smoke result, inspect PPTX zip/XML/text, and run python-pptx static geometry heuristics without rendering, copying PPTX artifacts, installing packages, invoking providers, or mutating global config.
  - Real smoke: inspected `/tmp/hermes-slide-director-phase21b.kr8k6Z/outputs/codex-presentation-pptx-smoke.pptx` with the recorded Phase 21B smoke result; verdict `PASS_WITH_LIMITATIONS`, `slide_xml_count=3`, `static_layout_inspection_performed=true`, `visual_inspection_performed=false`, `render_performed=false`, `ranking_ready=false`, and no static issues.
  - Verification: `tests/test_phase22.py` -> `6 passed`; full suite -> `161 passed in 4.43s`; `git diff --check` clean; independent reviewer verdict: `PASS`.
  - Limitation: Phase 22A is static-only and does not prove rendered visual quality, clipping/overflow absence, or ranking readiness. Phase 22B still needs real render/visual/reviewer gates.
  - Pushed to `origin/main` after user approval.
- `2026-05-18`: Built Phase 22B PPTX render/visual gate evidence recorder.
  - Commit: `443cdc8 feat: add Phase 22B PPTX render gate recorder`.
  - User approval: installing needed dependencies while proceeding was allowed; sudo/system installs remain user-run only.
  - Manual render smoke: installed `pptx-glimpse` only in isolated temp workspace `/tmp/hermes-slide-director-phase22b.PfLDCt`; rendered the Phase 21B native PPTX to 3 PNG and 3 SVG files at 1280x720 without LibreOffice/sudo.
  - Visual QA: Hermes vision inspection of all 3 rendered PNGs found no blocking clipping, overflow, text overlap, missing content, or obvious rendering defects. Non-blocking warnings remain: small/low-contrast detail text, sparse spacing, one awkward title wrap, and a bullet punctuation issue.
  - Command added: `record-pptx-render-gate` to record existing rendered PNG/SVG evidence and optional visual-review JSON. The command validates image inventory, render-report counts, visual-review blockers/warnings, and emits `PASS`, `PASS_WITH_WARNINGS`, `NEEDS_VISUAL_REVIEW`, or `REQUEST_CHANGES` without installing, rendering, invoking providers, generating decks, or copying temp images/PPTX into the repo.
  - Real smoke: CLI against `/tmp/hermes-slide-director-phase22b.PfLDCt/rendered`, `render-report.json`, and `visual-review.json` produced `PASS_WITH_WARNINGS`, `png_count=3`, `svg_count=3`, `visual_inspection_performed=true`, `render_performed=true`, `ranking_ready=true`, and no blocking issues.
  - Verification: `tests/test_phase22.py` -> `11 passed`; full suite -> `166 passed in 4.39s`; `git diff --check` clean; independent reviewer verdict: `PASS`.
  - Limitation: Phase 22B proves render/visual evidence for the smoke deck only. Next phases should connect this gate into candidate bakeoff/ranking and test additional content/styling cases.
  - Push: `443cdc8` pushed to `origin/main`; local/remote ahead-behind `0 0`.

- `2026-05-18`: Built Phase 23 PPTX ranking evidence integration.
  - Commit: `ea38365 feat: add Phase 23 PPTX ranking integration`.
  - Command added: `integrate-pptx-candidate-ranking`.
  - Behavior: reads existing `phase21b-smoke-result.json`, `phase22a-static-layout-gate.json`, and `phase22b-render-gate.json` for `codex-presentation-pptx`; validates hard gates; rejects missing/failed evidence; carries Phase 22B warnings forward into deterministic ranking penalty/review notes; writes ranking integration/evidence artifacts under `generation/` and `reviews/`.
  - Safety: Phase 23 itself does not install packages, render slides, generate decks, call network APIs, invoke providers, or use browsers/LibreOffice. It records `external_call_made=false`, `install_performed=false`, `network_access_used=false`, `deck_generated=false`, and `render_invoked_by_command=false`.
  - Real smoke: replayed Phase 21B/22A/22B recorders against the existing PPTX/render evidence, then ran Phase 23. Result: `ranking_candidate_ready`, `ranking_ready=true`, `ranking_score=0.75`, `ranking_penalty=0.25`, `warnings=9`, artifacts present.
  - Verification: `tests/test_phase23.py` -> `6 passed`; full suite -> `172 passed in 4.14s`; `git diff --check` clean; independent reviewer verdict: `PASS`. Reviewer suggested phase-field validation as a minor improvement; Hermes added it and reran tests successfully.
  - Limitation: `ranking_ready=true` means eligible for the next bakeoff/ranking comparison, not final deck/design acceptance.
  - Push: `ea38365` pushed to `origin/main`; local/remote ahead-behind `0 0`.

- `2026-05-18`: Built Phase 24 PPTX ranking/bakeoff readiness report.
  - Commit: `1385d74 feat: add Phase 24 PPTX ranking report`.
  - Command added: `prepare-pptx-ranking-report`.
  - Behavior: reads Phase 23 ranking integration/evidence, validates candidate id, `ranking_candidate_ready`, score/penalty bounds, hard-gate pass status, expected gate phases (`phase21b`, `phase22a`, `phase22b`), and Phase 23 safety flags. Writes a ranking report plus next-candidate decision gate.
  - Outcome semantics: marks `codex-presentation-pptx` as `shortlist_ready_single_candidate`; does not claim it is a bakeoff winner, final design acceptance, or final product acceptance.
  - Real smoke: replayed Phase 21B/22A/22B/23/24 on existing PPTX/render evidence. Result: `shortlist_ready_single_candidate`, `shortlist_ready=true`, `bakeoff_winner=false`, `ranking_score=0.75`, `ranking_penalty=0.25`, `warnings=9`, and `requires_user_decision_before_next_candidate_install_or_execution=true`.
  - Safety: Phase 24 itself does not install packages, render, generate decks, call network APIs/providers, invoke producers, or use browsers/LibreOffice.
  - Verification: `tests/test_phase24.py` -> `11 passed`; full suite -> `183 passed in 4.45s`; `git diff --check` clean; independent reviewer verdict: `PASS`. Reviewer suggested exact hard-gate phase validation as a minor improvement; Hermes added it and reran tests successfully.
  - Local repo status after commit: `main...origin/main [ahead 1]`.

## Next steps

1. Push the Phase 24 `hermes-slide-director` commit after verification.
2. Decide the next candidate path before running installs/execution: `run_next_candidate_pipeline` is recommended, but it may require user-approved installs/execution for the selected OSS candidate.
3. Candidate options remain `codex-guizang-html`, `codex-reveal-playwright`, and `codex-editable-html-slides`; pick one and request approval before any install/execution.
4. Keep hosted Claude Design as a separate design quality benchmark only, not an automation path.
5. Keep dashboard work deferred until the conversation-first flow and Producer/Reviewer generation loop are stronger.
6. Update JARVIS registry/status hygiene for the completed legacy `slide-harness` when convenient.
