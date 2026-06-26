#!/usr/bin/env python3
"""Focused checks for host-owned visible routed-session helper scripts."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from just_chill_bridge import build_bridge_plan
from just_chill_live_bindings import (
    build_visible_session_handoff,
    discover_live_surfaces,
    validate_bridge_live_readiness,
    validate_visible_completion_evidence,
)
from just_chill_router import classify_request
from just_chill_visible_session_helpers import (
    build_tail_report,
    build_tmux_orchestration_plan,
    create_session_record,
    helper_contract,
    prepare_prompt_record,
    validate_visible_evidence_payload,
)

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"


def require(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle, haystack) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


def run_json(argv: list[str]) -> dict:
    completed = subprocess.run(argv, cwd=REPO, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise AssertionError(f"command failed {argv!r}: {completed.stdout}\n{completed.stderr}")
    return json.loads(completed.stdout)


cases: list[str] = []

for helper in ["create-gjc-session", "prompt-gjc-session", "tail-gjc-session"]:
    contract = helper_contract(helper)
    require(f"{helper} no hidden GJC", contract["executesGjc"], False)
    require(f"{helper} no product work", contract["executesProductWork"], False)
    require(f"{helper} rejects scrollback", contract["scrollbackIsCompletion"], False)
    require(f"{helper} durable evidence", contract["durableEvidenceRequired"], True)
    require(f"{helper} planning supported", contract["orchestrationPlanning"]["supported"], True)
    require(f"{helper} planning no execution", contract["orchestrationPlanning"]["executesCommands"], False)
    cli_contract = run_json([str(SCRIPTS / helper), "--contract", "--json"])
    require(f"{helper} cli contract ok", cli_contract["ok"], True)
    require(f"{helper} cli contract helper", cli_contract["contract"]["helper"], helper)
cases.append("helper-contracts")

with tempfile.TemporaryDirectory(prefix="just-chill-visible-helper-") as temp_root:
    root = Path(temp_root)
    state_dir = root / "state"
    worktree = root / "worktree"
    worktree.mkdir()
    task_file = root / "task.md"
    task_file.write_text("/skill:ultragoal\n\nRun a focused no-op verification task.\n", encoding="utf-8")

    invalid = create_session_record("bad/../../name", str(worktree), state_dir=state_dir)
    require("invalid create rejected", invalid["ok"], False)
    require_in("invalid issue", "session name must be 3-96 chars of letters, numbers, dot, underscore, or dash and start alphanumeric", invalid["issues"])

    created = create_session_record("just-chill-test-001", str(worktree), state_dir=state_dir)
    require("create ok", created["ok"], True)
    require("create no execution", created["hiddenExecutionStarted"], False)
    require("create no product work", created["productWorkStarted"], False)
    plan = build_tmux_orchestration_plan(
        "just-chill-test-001",
        str(worktree),
        tmux_session="just-chill-test-001",
        tmux_window="gjc",
        tmux_pane="0",
    )
    require("tmux plan status", plan["status"], "orchestration-plan-ready")
    require("tmux plan no execution", plan["executesCommands"], False)
    require("tmux target", plan["tmuxTarget"]["target"], "just-chill-test-001:gjc.0")

    bad_plan_create = create_session_record(
        "just-chill-test-002",
        str(worktree),
        state_dir=state_dir,
        orchestration_plan=True,
        tmux_session="../bad",
    )
    require("invalid tmux target rejected", bad_plan_create["ok"], False)
    require_in("invalid tmux issue", "tmux session must be 1-96 chars of letters, numbers, dot, underscore, or dash and start alphanumeric", bad_plan_create["issues"])

    planned = create_session_record(
        "just-chill-test-003",
        str(worktree),
        state_dir=state_dir,
        orchestration_plan=True,
        tmux_session="just-chill-test-003",
    )
    require("planned create ok", planned["ok"], True)
    require("planned create status", planned["status"], "orchestration-plan-recorded")
    require("planned create no execution", planned["orchestrationPlan"]["executesCommands"], False)


    prepared = prepare_prompt_record("just-chill-test-001", f"@{task_file}", tui_ready=True, state_dir=state_dir)
    require("prompt ok", prepared["ok"], True)
    require("prompt not injected", prepared["session"]["promptInjectedByHelper"], False)
    require("prompt prepared", prepared["session"]["promptPrepared"], True)
    planned_prompt = prepare_prompt_record(
        "just-chill-test-003",
        f"@{task_file}",
        tui_ready=True,
        state_dir=state_dir,
        orchestration_plan=True,
        tmux_session="just-chill-test-003",
    )
    require("planned prompt ok", planned_prompt["ok"], True)
    require("planned prompt no injection", planned_prompt["session"]["promptInjectedByHelper"], False)
    require("planned prompt task in plan", planned_prompt["session"]["orchestrationPlan"]["argvPlan"][3]["argv"][-1].startswith("just-chill prompt ready at @"), True)


    scrollback_only = {"signals": [{"kind": "tmux-scrollback", "source": "pane text shows prompt"}]}
    scrollback_issues = validate_visible_evidence_payload(scrollback_only)
    require_in("scrollback rejected", "tmux-scrollback is debug-only and cannot prove completion", scrollback_issues)
    require_in("scrollback not durable", "at least one non-scrollback durable evidence signal is required", scrollback_issues)
    vague_description = {"signals": [{"kind": "artifact", "description": "done"}]}
    require_in("vague description rejected", "artifact evidence description must be concrete, not a vague completion word", validate_visible_evidence_payload(vague_description))
    bad_command = {"signals": [{"kind": "tool_call", "command": "pytest"}]}
    require_in("command shape rejected", "tool_call evidence command must be a non-empty argv array", validate_visible_evidence_payload(bad_command))


    durable = {"signals": [{"kind": "artifact", "path": str(root / "report.json"), "description": "terminal GJC turn report"}]}
    require("durable accepted", validate_visible_evidence_payload(durable), [])
    require("live binding evidence wrapper", validate_visible_completion_evidence(durable), [])
    command_evidence = {"signals": [{"kind": "tool_call", "command": ["python3", "scripts/check_just_chill_visible_helpers.py"]}]}
    require("argv command evidence accepted", validate_visible_evidence_payload(command_evidence), [])
    tail = build_tail_report("just-chill-test-001", evidence=durable, state_dir=state_dir)
    require("tail helper debug only", tail["debugOnly"], True)
    require("tail no scrollback completion", tail["scrollbackIsCompletion"], False)
    require("tail evidence accepted", tail["evidenceValidation"]["accepted"], True)

    cli_created = run_json([str(SCRIPTS / "create-gjc-session"), "just-chill-cli-001", str(worktree), "--state-dir", str(state_dir)])
    require("cli create ok", cli_created["ok"], True)
    cli_prompt = run_json([str(SCRIPTS / "prompt-gjc-session"), "just-chill-cli-001", f"@{task_file}", "--state-dir", str(state_dir), "--tui-ready"])
    require("cli prompt ok", cli_prompt["ok"], True)
    cli_tail = run_json([
        str(SCRIPTS / "tail-gjc-session"),
        "just-chill-cli-001",
        "50",
        "--state-dir",
        str(state_dir),
        "--evidence-json",
        json.dumps(durable),
    ])
    require("cli tail ok", cli_tail["ok"], True)
    cli_planned = run_json([
        str(SCRIPTS / "create-gjc-session"),
        "just-chill-cli-plan-001",
        str(worktree),
        "--state-dir",
        str(state_dir),
        "--tmux-plan",
        "--tmux-session",
        "just-chill-cli-plan-001",
    ])
    require("cli planned create ok", cli_planned["ok"], True)
    require("cli planned mode", cli_planned["orchestrationPlan"]["mode"], "tmux-orchestration-plan-v1")
    require("cli tail evidence accepted", cli_tail["evidenceValidation"]["accepted"], True)

cases.append("helper-state-and-evidence")

# Real repo-local helper discovery: the helpers do not have to be globally on PATH.
def fake_which_core_only(name: str) -> str | None:
    return f"/fake/bin/{name}" if name in {"gjc", "hermes", "tmux"} else None


def fake_runner(argv, cwd, timeout):
    if len(argv) >= 3 and list(argv[1:]) == ["--contract", "--json"]:
        helper_name = os.path.basename(str(argv[0]))
        return {
            "argv": list(argv),
            "exitCode": 0,
            "ok": True,
            "stdout": "",
            "stderr": "",
            "json": {"ok": True, "contract": helper_contract(helper_name)},
        }
    if argv[:4] == ["gjc", "mcp-serve", "coordinator", "--check"]:
        return {"argv": list(argv), "exitCode": 0, "ok": True, "stdout": "", "stderr": "", "json": {"ok": True, "tools": []}}
    if argv[:4] == ["gjc", "setup", "hermes", "--root"]:
        return {"argv": list(argv), "exitCode": 0, "ok": True, "stdout": "", "stderr": "", "json": {"ok": True, "files_written": []}}
    if list(argv) == ["hermes", "memory", "status"]:
        return {"argv": list(argv), "exitCode": 0, "ok": True, "stdout": "Provider: (none — built-in only)", "stderr": "", "json": None}
    if list(argv) == ["hermes", "mcp", "list"]:
        return {"argv": list(argv), "exitCode": 0, "ok": True, "stdout": "No MCP servers configured.", "stderr": "", "json": None}
    raise AssertionError(f"unexpected argv: {argv!r}")

surfaces = discover_live_surfaces(cwd=str(REPO), probe=True, which=fake_which_core_only, runner=fake_runner)
require("repo-local helpers ready", surfaces["visibleRoutedSession"]["status"], "orchestration-plan-ready")
packet = classify_request("fix TypeError in src/hooks/bridge.ts and run bun test")
plan = build_bridge_plan(packet, cwd=str(REPO))
require("visible readiness clean", validate_bridge_live_readiness(plan, surfaces), [])
handoff = build_visible_session_handoff(plan, surfaces)
require("handoff ready", handoff["status"], "ready-for-host-execution")
require("handoff no local execution", handoff["executionAllowedHere"], False)
require("handoff uses repo helper path", str(SCRIPTS / "create-gjc-session"), handoff["commands"][0]["argv"][0])
require("handoff orchestration target", handoff["orchestration"]["target"], f"{handoff['sessionName']}:gjc.0")
cases.append("repo-local-live-readiness")

print(f"PASS: {len(cases)} just-chill visible helper cases passed")
