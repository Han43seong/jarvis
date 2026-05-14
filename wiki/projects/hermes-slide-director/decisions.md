# Hermes Slide Director Decisions

## 2026-05-14 - Create clean-start project instead of continuing slide-harness

- Decision: create `/home/hskim/projects/hermes-slide-director` as a new repository.
- Rationale: the prior `slide-harness` work drifted toward a structured JSON/requirements dashboard. The clarified goal is a Claude Design-style slide production loop with QA/rejection/revision, driven by user-provided research material and design references.
- Consequences: keep `slide-harness` as reference, but do not force its architecture into the new project. Start from contracts, loop architecture, and CLI proof.
- Verification/source: user clarified the scenario in conversation; repository and JARVIS registry were created/updated in this session.

## 2026-05-14 - Criteria approval is the primary gate

- Decision: Hermes must propose verification criteria before generation, and the user reviews/edits/approves those criteria.
- Rationale: the criteria become the contract for the generator, critics, and revision planner.
- Consequences: first schemas model verification criteria and job state before renderer or dashboard implementation.

## 2026-05-14 - HTML-first, Claude Design-style deck as canonical artifact

- Decision: the canonical deck artifact is a designed HTML deck; PDF/screenshots are derived outputs.
- Rationale: Claude Design's strength is high-fidelity HTML artifact design, and browser rendering enables visual QA loops.
- Consequences: PPTX support remains optional/later.
