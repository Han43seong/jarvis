#!/usr/bin/env python3
"""Acceptance checks for the Hermes-main just-chill dogfood harness."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from just_chill_hermes_harness import build_hermes_main_harness

ROOT = Path(__file__).resolve().parents[1]
HERMES_HARNESS_SCRIPT = ROOT / "scripts" / "just_chill_hermes_harness.py"


def require(name: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle: Any, haystack: Any) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


def require_truthy(name: str, value: Any) -> None:
    if not value:
        raise AssertionError(f"{name}: expected truthy, got {value!r}")


def run_json(argv: list[str]) -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(HERMES_HARNESS_SCRIPT), *argv], cwd=ROOT, text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def assert_top_boundary(label: str, report: dict[str, Any]) -> None:
    boundary = report["authorityBoundary"]
    require(f"{label} execution", boundary["executionAllowedHere"], False)
    for key in [
        "justChillExecutesGjc",
        "justChillWritesHermes",
        "justChillOwnsCanonicalMemory",
        "justChillRunsShaclEngine",
        "justChillSearchesVectorStore",
        "justChillCallsCoordinator",
        "justChillCallsDelegateTools",
    ]:
        require(f"{label} {key}", boundary[key], False)


cases: list[str] = []

report = build_hermes_main_harness(cwd=str(ROOT))
require("report status", report["status"], "passed")
require("hermes main", report["hermesMain"]["userFacingLayer"], "Hermes")
require("cli debug", report["hermesMain"]["cliRole"], "debug/test/fixture surface only")
require("validation", report["validationIssues"], [])
assert_top_boundary("report", report)
cases.append("hermes-main-happy-path")

flows = report["flows"]
require("route tool", flows["routeDevelopment"]["tool"], "just_chill.route")
require("route dev", flows["routeDevelopment"]["decoded"]["routerPacket"]["classification"]["isDevelopment"], True)
require("handoff ready", flows["gjcHandoff"]["decoded"]["status"], "handoff-plan-ready")
require("consent visible", flows["consent"]["decoded"]["status"], "visible-session-preferred")
require("remember ready", flows["remember"]["decoded"]["status"], "memory-candidate-ready")
require("recall allowed", flows["recall"]["decoded"]["status"], "recall-allowed")
require("status user layer", flows["status"]["decoded"]["userFacingLayer"], "Hermes")
require("status bridge mode", flows["status"]["decoded"]["executionBridge"]["mode"], "visible-session-only")
require("bad mcp error", flows["malformedMcp"]["result"]["isError"], True)
cases.append("flow-contracts")

for name, passed in report["assertions"].items():
    require(f"assertion {name}", passed, True)
cases.append("assertion-map")

stale = build_hermes_main_harness(cwd=str(ROOT), recall_source_hash_override="sha256:stale")
require("stale status", stale["status"], "blocked")
require("stale recall", stale["flows"]["recall"]["decoded"]["status"], "recall-blocked")
require_in("stale assertion", "assertion failed: recallAllowed", stale["validationIssues"])
require_in("stale blocker", "current canonical source hash is stale relative to sidecar", stale["flows"]["recall"]["decoded"]["blockedReasons"])
cases.append("stale-recall-blocks")

deleted = build_hermes_main_harness(cwd=str(ROOT), current_deletion_state="deleted")
require("deleted status", deleted["status"], "blocked")
require("deleted recall", deleted["flows"]["recall"]["decoded"]["status"], "recall-blocked")
require_in("deleted blocker", "deleted source cannot be recalled", deleted["flows"]["recall"]["decoded"]["blockedReasons"])
cases.append("deleted-recall-blocks")

redacted = build_hermes_main_harness(cwd=str(ROOT), current_redaction_state="redacted")
require("redacted status", redacted["status"], "blocked")
require("redacted recall", redacted["flows"]["recall"]["decoded"]["status"], "recall-blocked")
require_in("redacted blocker", "redacted source cannot be recalled", redacted["flows"]["recall"]["decoded"]["blockedReasons"])
cases.append("redacted-recall-blocks")

sensitive = build_hermes_main_harness(cwd=str(ROOT), sensitive_memory=True)
require("sensitive status", sensitive["status"], "blocked")
require("sensitive remember", sensitive["flows"]["remember"]["decoded"]["status"], "memory-candidate-blocked")
require_in("sensitive assertion", "assertion failed: memoryContractsReady", sensitive["validationIssues"])
require("sensitive positive assertion", sensitive["assertions"]["sensitiveMemoryBlocks"], True)
cases.append("sensitive-memory-blocks")

cli = run_json(["--cwd", str(ROOT)])
require("CLI status", cli["status"], "passed")
require("CLI main", cli["hermesMain"]["userFacingLayer"], "Hermes")
require("CLI no exec", cli["authorityBoundary"]["executionAllowedHere"], False)
cases.append("cli-json")

cli_sensitive = run_json(["--cwd", str(ROOT), "--sensitive-memory"])
require("CLI sensitive blocked", cli_sensitive["status"], "blocked")
require("CLI sensitive memory", cli_sensitive["flows"]["remember"]["decoded"]["status"], "memory-candidate-blocked")
cases.append("cli-sensitive-json")

for idx, item in enumerate([report, stale, deleted, redacted, sensitive, cli, cli_sensitive], start=1):
    assert_top_boundary(f"report-{idx}", item)
    for flow_name, flow in item["flows"].items():
        if flow_name == "malformedMcp":
            continue
        decoded = flow["decoded"]
        require(f"report {idx} flow {flow_name} execution", decoded["executionAllowedHere"], False)
        boundary = decoded["authorityBoundary"]
        for key in ["justChillExecutesGjc", "justChillWritesHermes", "justChillOwnsCanonicalMemory"]:
            require(f"report {idx} flow {flow_name} {key}", boundary[key], False)
cases.append("authority-boundary-invariant")

print(f"PASS: {len(cases)} just-chill Hermes-main harness cases passed")
