# Hermes Slide Director Architecture

## Core architecture decision

The system is a director loop, not a deterministic renderer.

```text
materials + design reference
  -> criteria proposal
  -> user approval
  -> Claude Design generation
  -> render/export
  -> QA critics
  -> revision planner
  -> next generation iteration
  -> final deck
```

## Roles

- Hermes Orchestrator: state machine, approval gates, iteration control.
- Criteria Proposer: extracts content/design/readability/export criteria for user approval.
- Claude Design Generator: creates/revises 1920x1080 self-contained HTML decks.
- Renderer: opens HTML, captures console/runtime errors, exports PDF and screenshots.
- QA Critics: evaluate approved criteria against the rendered deck.
- Revision Planner: turns QA failures into concrete generator instructions.
- Dashboard Cockpit: later UI for criteria approval, iteration timeline, QA findings, and final artifacts.

## First implementation principle

Prove the loop in CLI first. Do not repeat the prior mistake of making the dashboard/form the product center before the generation-quality loop exists.
