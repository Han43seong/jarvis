#!/usr/bin/env python3
"""Acceptance checks for the host-owned just-chill GJC execution bridge."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from just_chill_gjc_execution_bridge import BRIDGE_NAME, prepare_visible_execution, stable_session_name, verify_completion
from just_chill_harness import gjc_handoff_plan

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_SCRIPT = ROOT / "scripts" / "just_chill_gjc_execution_bridge.py"


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
    result = subprocess.run([sys.executable, str(BRIDGE_SCRIPT), *argv], cwd=ROOT, text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def assert_boundary(label: str, output: dict[str, Any]) -> None:
    require(f"{label} execution", output["executionAllowedHere"], False)
    boundary = output["authorityBoundary"]
    for key in [
        "executionAllowedHere",
        "justChillExecutesGjc",
        "justChillCallsCoordinator",
        "justChillCallsDelegateTools",
        "justChillWritesHermes",
        "hostBridgeExecutesCommands",
        "hostBridgeStartsGjc",
        "hostBridgeInjectsPrompt",
        "scrollbackIsCompletion",
    ]:
        require(f"{label} {key}", boundary[key], False)
    require(f"{label} durable evidence", boundary["durableEvidenceRequired"], True)


cases: list[str] = []

with TemporaryDirectory() as tmp:
    request = "fix src/hooks/bridge.ts and run the focused test"
    bridge_dir = str(Path(tmp) / "bridge")
    state_dir = str(Path(tmp) / "sessions")
    prepared = prepare_visible_execution(
        request,
        cwd=str(ROOT),
        session_name="jc-test-session",
        bridge_dir=bridge_dir,
        state_dir=state_dir,
        gjc_command=sys.executable,
    )
    require("prepared bridge", prepared["bridge"], BRIDGE_NAME)
    require("prepared status", prepared["status"], "visible-execution-prepared")
    require("session", prepared["sessionName"], "jc-test-session")
    require("session ok", prepared["sessionRecord"]["ok"], True)
    require("prompt ok", prepared["promptRecord"]["ok"], True)
    require("task hash prefix", prepared["taskFileHash"].startswith("sha256:"), True)
    task_text = Path(prepared["taskFile"]).read_text(encoding="utf-8")
    require_in("task request", request, task_text)
    require_in("task scrollback warning", "tmux pane capture / scrollback alone", task_text)
    require("session no hidden", prepared["sessionRecord"]["hiddenExecutionStarted"], False)
    require("prompt not injected", prepared["promptRecord"]["session"]["promptInjectedByHelper"], False)
    assert_boundary("prepared", prepared)
    cases.append("prepare-visible-session-artifacts")

    valid = verify_completion(
        "jc-test-session",
        bridge_dir=bridge_dir,
        state_dir=state_dir,
        evidence={"kind": "turn_id", "turn_id": "turn-123", "description": "GJC returned a durable turn receipt"},
    )
    require("valid evidence status", valid["status"], "completion-evidence-accepted")
    require("valid evidence accepted", valid["evidenceAccepted"], True)
    require("valid source", valid["completionSource"], "durable-evidence")
    require("tail debug only", valid["tailReport"]["debugOnly"], True)
    assert_boundary("valid", valid)
    cases.append("verify-durable-evidence")

    scrollback = verify_completion(
        "jc-test-session",
        bridge_dir=bridge_dir,
        state_dir=state_dir,
        evidence={"kind": "scrollback", "description": "pane says done"},
    )
    require("scrollback status", scrollback["status"], "completion-evidence-blocked")
    require_in("scrollback blocker", "scrollback is debug-only and cannot prove completion", scrollback["blockedReasons"])
    require("scrollback accepted", scrollback["scrollbackAccepted"], False)
    cases.append("reject-scrollback-completion")

with TemporaryDirectory() as tmp:
    missing = verify_completion(
        "jc-missing-session",
        bridge_dir=str(Path(tmp) / "bridge"),
        state_dir=str(Path(tmp) / "sessions"),
        evidence={"kind": "turn_id", "turn_id": "turn-missing"},
    )
    require("missing session status", missing["status"], "completion-evidence-blocked")
    require_in("missing session blocker", "session metadata record does not exist; run create-gjc-session first", missing["blockedReasons"])
    cases.append("missing-session-blocked")

with TemporaryDirectory() as tmp:
    request = "fix src/hooks/bridge.ts"
    handoff = gjc_handoff_plan(request, cwd=str(ROOT))
    handoff["bridgePlan"]["bridgePlan"]["bridgePath"] = "coordinator-mcp"
    blocked = prepare_visible_execution(
        request,
        cwd=str(ROOT),
        handoff_plan=handoff,
        bridge_dir=str(Path(tmp) / "bridge"),
        state_dir=str(Path(tmp) / "sessions"),
    )
    require("coordinator blocked", blocked["status"], "blocked")
    require_in("coordinator blocker", "execution bridge MVP supports only 'visible-routed-session'; got 'coordinator-mcp'", blocked["blockedReasons"])
    assert_boundary("blocked", blocked)
    cases.append("block-non-visible-bridge")

with TemporaryDirectory() as tmp:
    bridge_dir = str(Path(tmp) / "bridge")
    state_dir = str(Path(tmp) / "sessions")
    cli_prepared = run_json([
        "prepare",
        "--cwd", str(ROOT),
        "--session-name", "jc-cli-session",
        "--bridge-dir", bridge_dir,
        "--state-dir", state_dir,
        "--gjc-command", sys.executable,
        "fix src/hooks/bridge.ts",
    ])
    require("CLI prepare status", cli_prepared["status"], "visible-execution-prepared")
    cli_verify = run_json([
        "verify",
        "--session-name", "jc-cli-session",
        "--bridge-dir", bridge_dir,
        "--state-dir", state_dir,
        "--evidence-json", json.dumps({"kind": "test", "command": ["python3", "scripts/check_just_chill_gjc_execution_bridge.py"]}, sort_keys=True),
    ])
    require("CLI verify status", cli_verify["status"], "completion-evidence-accepted")
    assert_boundary("cli", cli_verify)
    cases.append("cli-prepare-verify")

with TemporaryDirectory() as tmp:
    malformed = run_json([
        "prepare",
        "--cwd", str(ROOT),
        "--bridge-dir", str(Path(tmp) / "bridge"),
        "--handoff-plan-json", "{bad-json}",
        "fix src/hooks/bridge.ts",
    ])
    require("malformed status", malformed["status"], "blocked")
    require_truthy("malformed blockers", malformed["blockedReasons"])
    cases.append("malformed-handoff-blocked")

name_a = stable_session_name("same request", str(ROOT))
name_b = stable_session_name("same request", str(ROOT))
require("stable session", name_a, name_b)
cases.append("stable-session-name")

print(f"PASS: {len(cases)} just-chill GJC execution bridge cases passed")
