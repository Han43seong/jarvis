#!/usr/bin/env python3
"""Acceptance checks for JARVIS executor-routing policy text.

This is intentionally stdlib-only because the JARVIS control-plane should be
checkable in a minimal WSL environment without PyYAML or project dependencies.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "AGENTS.md": ROOT / "AGENTS.md",
    "config/routing.yaml": ROOT / "config/routing.yaml",
    "harnesses/executor-router.md": ROOT / "harnesses/executor-router.md",
    "harnesses/executor-router-test-cases.md": ROOT / "harnesses/executor-router-test-cases.md",
    "wiki/projects/jarvis/status.md": ROOT / "wiki/projects/jarvis/status.md",
}

checks = []

def require(name: str, text: str, needle: str) -> None:
    checks.append((name, needle in text, needle))

texts = {name: path.read_text(encoding="utf-8") for name, path in FILES.items()}

# Core executor presence and default routing.
require("AGENTS executor list", texts["AGENTS.md"], "`hermes-background`")
require("AGENTS background rule", texts["AGENTS.md"], "Use `hermes-background` for research, market analysis, comparison, report drafting, long inspections")
require("AGENTS durable mechanisms", texts["AGENTS.md"], "terminal(background=true, notify_on_complete=true)")
require("AGENTS delegate_task warning", texts["AGENTS.md"], "over synchronous `delegate_task` when interruption would lose work")

# Structured routing config.
require("routing executor block", texts["config/routing.yaml"], "  hermes_background:")
for key in [
    "research_over_one_minute: hermes_background",
    "market_analysis: hermes_background",
    "comparison_or_scouting: hermes_background",
    "report_drafting: hermes_background",
    "long_inspection: hermes_background",
]:
    require("routing default " + key, texts["config/routing.yaml"], key)
for mechanism in [
    "terminal_background_notify_on_complete",
    "slash_background",
    "one_shot_cron",
    "kanban_for_durable_backlog",
]:
    require("routing durable mechanism " + mechanism, texts["config/routing.yaml"], mechanism)
require("routing delegate_task non-durable", texts["config/routing.yaml"], "delegate_task is synchronous and is cancelled if the parent is interrupted; do not use it as durable background work.")

# Human harness and acceptance matrix.
require("harness background default", texts["harnesses/executor-router.md"], "use `hermes-background` by default")
require("harness delegate_task warning", texts["harnesses/executor-router.md"], "Do not treat `delegate_task` as durable background execution")
for case in ["R1", "R2", "R5", "R8"]:
    require("acceptance case " + case, texts["harnesses/executor-router-test-cases.md"], "| " + case + " |")
require("acceptance background durability", texts["harnesses/executor-router-test-cases.md"], "`delegate_task` must not be described or relied on as durable background execution")

# Durable status note.
require("status note", texts["wiki/projects/jarvis/status.md"], "Added `hermes-background` to the routing pipeline")

failures = [(name, needle) for name, ok, needle in checks if not ok]
if failures:
    print("FAIL: executor routing policy checks failed")
    for name, needle in failures:
        print(f"- {name}: missing {needle!r}")
    sys.exit(1)

print(f"PASS: {len(checks)} executor routing policy checks passed")
