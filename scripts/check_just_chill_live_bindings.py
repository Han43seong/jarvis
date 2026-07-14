#!/usr/bin/env python3
"""Acceptance checks for just-chill live-binding helpers."""
from __future__ import annotations
import copy

import os
from pathlib import Path

from just_chill_bridge import build_bridge_plan
from just_chill_hermes_adapter import build_hermes_adapter_stub, validate_adapter_stub
from just_chill_visible_session_helpers import helper_contract
from just_chill_live_bindings import (
    build_live_binding_report,
    build_visible_session_handoff,
    discover_live_surfaces,
    validate_bridge_live_readiness,
)
from just_chill_memory_contracts import build_raw_artifact_record, build_summary_memory_record
from just_chill_router import classify_request

ROOT = Path(__file__).resolve().parents[1]
ROOT_CWD = str(ROOT)


def require(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle, haystack) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


def require_truthy(name: str, value) -> None:
    if not value:
        raise AssertionError(f"{name}: expected truthy value, got {value!r}")


COORDINATOR_TOOLS = [
    "gjc_coordinator_list_sessions",
    "gjc_coordinator_read_status",
    "gjc_coordinator_read_tail",
    "gjc_coordinator_list_questions",
    "gjc_coordinator_list_artifacts",
    "gjc_coordinator_read_artifact",
    "gjc_coordinator_read_coordination_status",
    "gjc_coordinator_watch_events",
    "gjc_coordinator_register_session",
    "gjc_coordinator_start_session",
    "gjc_coordinator_send_prompt",
    "gjc_coordinator_submit_question_answer",
    "gjc_coordinator_read_turn",
    "gjc_coordinator_await_turn",
    "gjc_coordinator_report_status",
    "gjc_delegate_plan",
    "gjc_delegate_execute",
    "gjc_delegate_team",
]


def fake_runner(argv, cwd, timeout):
    if len(argv) >= 3 and list(argv[1:]) == ["--contract", "--json"]:
        helper_name = os.path.basename(str(argv[0]))
        if helper_name in {"create-gjc-session", "prompt-gjc-session", "tail-gjc-session"}:
            return {
                "argv": list(argv),
                "exitCode": 0,
                "ok": True,
                "stdout": "",
                "stderr": "",
                "json": {"ok": True, "contract": helper_contract(helper_name)},
            }
    if argv[:4] == ["gjc", "mcp-serve", "coordinator", "--check"]:
        return {
            "argv": list(argv),
            "exitCode": 0,
            "ok": True,
            "stdout": "",
            "stderr": "",
            "json": {"ok": True, "server": {"name": "gjc-coordinator-mcp"}, "tools": COORDINATOR_TOOLS},
        }
    if argv[:4] == ["gjc", "setup", "hermes", "--root"]:
        return {
            "argv": list(argv),
            "exitCode": 0,
            "ok": True,
            "stdout": "",
            "stderr": "",
            "json": {"ok": True, "mode": "smoke", "files_written": [], "smoke": {"missingTools": []}},
        }
    if list(argv) == ["hermes", "memory", "status"]:
        return {
            "argv": list(argv),
            "exitCode": 0,
            "ok": True,
            "stdout": "Memory status\n  Built-in: always active\n  Provider: (none — built-in only)",
            "stderr": "",
            "json": None,
        }
    if list(argv) == ["hermes", "mcp", "list"]:
        return {
            "argv": list(argv),
            "exitCode": 0,
            "ok": True,
            "stdout": "No MCP servers configured.",
            "stderr": "",
            "json": None,
        }
    raise AssertionError(f"unexpected probe argv: {argv!r}")
def fake_runner_holographic(argv, cwd, timeout):
    result = fake_runner(argv, cwd, timeout)
    if list(argv) == ["hermes", "memory", "status"]:
        result["stdout"] = (
            "Memory status\n"
            "  Built-in: always active\n"
            "  Provider: holographic\n"
            "  Plugin: installed ✓\n"
            "  Status: available ✓"
        )
    return result


def fake_runner_bad_contract(argv, cwd, timeout):
    result = fake_runner(argv, cwd, timeout)
    if len(argv) >= 3 and list(argv[1:]) == ["--contract", "--json"]:
        helper_name = os.path.basename(str(argv[0]))
        contract = copy.deepcopy(result["json"]["contract"])
        if helper_name == "create-gjc-session":
            contract["orchestrationPlanning"]["helperRunsTmux"] = True
        elif helper_name == "prompt-gjc-session":
            contract["orchestrationPlanning"].pop("emitsArgvPlan", None)
        elif helper_name == "tail-gjc-session":
            contract["helper"] = "wrong-helper"
            contract["rejectedEvidenceKinds"] = []
        result["json"]["contract"] = contract
    return result




def fake_which_full(name: str) -> str | None:
    return f"/fake/bin/{name}"


def fake_which_core_only(name: str) -> str | None:
    return f"/fake/bin/{name}" if name in {"gjc", "hermes", "tmux"} else None
def fake_which_no_tmux(name: str) -> str | None:
    return None if name == "tmux" else f"/fake/bin/{name}"




cases: list[str] = []
old_mutations = os.environ.get("GJC_COORDINATOR_MCP_MUTATIONS")
try:
    os.environ.pop("GJC_COORDINATOR_MCP_MUTATIONS", None)

    surfaces = discover_live_surfaces(cwd=ROOT_CWD, probe=False, which=fake_which_core_only, runner=fake_runner)
    require("availability-only visible status", surfaces["visibleRoutedSession"]["status"], "host-helpers-present-unverified")
    require("availability-only visible readiness issue", validate_bridge_live_readiness(build_bridge_plan(classify_request("fix TypeError in src/hooks/bridge.ts"), cwd=ROOT_CWD), surfaces), ["visible routed-session helper contracts were not probed"])
    require("availability-only coordinator status", surfaces["coordinatorMcp"]["status"], "not-probed")
    cases.append("availability-only-map")

    surfaces = discover_live_surfaces(cwd=ROOT_CWD, probe=True, which=fake_which_full, runner=fake_runner)
    require("coordinator smoke ok", surfaces["coordinatorMcp"]["status"], "smoke-ok")
    require("delegates present", surfaces["gjcDelegation"]["status"], "delegate-tools-present")
    require("hermes storage write unavailable", surfaces["hermes"]["liveStorageWriteAvailable"], False)
    cases.append("read-only-smoke-map")
    holographic_surfaces = discover_live_surfaces(cwd=ROOT_CWD, probe=True, which=fake_which_full, runner=fake_runner_holographic)
    require("holographic provider parsed", holographic_surfaces["hermes"]["memoryProvider"], "holographic")
    require("holographic summary api mapped", holographic_surfaces["hermes"]["summaryMemoryApi"], "hermes.summary_memory.provider_tool.fact_store.add")
    require("holographic memory tool available", holographic_surfaces["hermes"]["memoryToolWriteAvailable"], True)
    require("holographic raw api still unmapped", holographic_surfaces["hermes"]["rawArtifactApi"], "unmapped")
    require("holographic raw read api still unmapped", holographic_surfaces["hermes"]["rawArtifactReadApi"], "unmapped")
    require("holographic raw delete api still unmapped", holographic_surfaces["hermes"]["rawArtifactDeleteApi"], "unmapped")
    require("holographic surface boundary", holographic_surfaces["hermes"]["memoryProviderSurface"]["tool"]["name"], "fact_store")
    cases.append("holographic-provider-tool-map")

    packet = classify_request("fix TypeError in src/hooks/bridge.ts and run bun test")
    plan = build_bridge_plan(packet, cwd=ROOT_CWD)
    handoff = build_visible_session_handoff(plan, surfaces)
    require("visible handoff ready", handoff["status"], "ready-for-host-execution")
    require("visible no local execution", handoff["executionAllowedHere"], False)
    require("visible scrollback rejected", handoff["scrollbackIsCompletion"], False)
    require_in("visible command helper", "create-gjc-session", [cmd["helper"] for cmd in handoff["commands"]])
    require("visible orchestration mode", handoff["orchestration"]["mode"], "tmux-orchestration-plan-v1")
    require("visible orchestration status", handoff["orchestration"]["status"], "orchestration-plan-ready")
    cases.append("visible-handoff-ready")

    missing_surfaces = discover_live_surfaces(cwd="/tmp/just-chill-no-helper-repo", probe=True, which=fake_which_core_only, runner=fake_runner)
    missing_handoff = build_visible_session_handoff(plan, missing_surfaces)
    require("visible handoff blocked", missing_handoff["status"], "blocked-missing-host-helpers")
    require_in("visible readiness issue", "visible routed-session helpers are not all available", validate_bridge_live_readiness(plan, missing_surfaces))
    cases.append("visible-handoff-fail-closed")
    metadata_only_surfaces = discover_live_surfaces(cwd=ROOT_CWD, probe=True, which=fake_which_no_tmux, runner=fake_runner)
    metadata_only_handoff = build_visible_session_handoff(plan, metadata_only_surfaces)
    require("metadata-only visible status", metadata_only_surfaces["visibleRoutedSession"]["status"], "metadata-only-ready")
    require("metadata-only handoff blocked", metadata_only_handoff["status"], "blocked-missing-orchestration-tools")
    require_in("tmux missing readiness issue", "visible routed-session orchestration requires tmux and gjc availability", validate_bridge_live_readiness(plan, metadata_only_surfaces))
    cases.append("visible-orchestration-fail-closed")
    invalid_contract_surfaces = discover_live_surfaces(cwd=ROOT_CWD, probe=True, which=fake_which_full, runner=fake_runner_bad_contract)
    invalid_contract_handoff = build_visible_session_handoff(plan, invalid_contract_surfaces)
    require("invalid contract visible status", invalid_contract_surfaces["visibleRoutedSession"]["status"], "invalid-host-helper-contracts")
    require("invalid contract handoff blocked", invalid_contract_handoff["status"], "blocked-host-helper-contract")
    require_in("invalid contract readiness issue", "visible routed-session helper contracts are invalid", validate_bridge_live_readiness(plan, invalid_contract_surfaces))
    cases.append("visible-invalid-contract-fail-closed")

    coordinator_packet = classify_request("Use coordinator MCP machine control and poll the turn_id artifact state for this repo task")
    coordinator_plan = build_bridge_plan(coordinator_packet, cwd=ROOT_CWD)
    require_in("coordinator mutation issue", "coordinator MCP execution requires sessions, questions, reports mutation classes", validate_bridge_live_readiness(coordinator_plan, surfaces))
    os.environ["GJC_COORDINATOR_MCP_MUTATIONS"] = "sessions,questions,reports"
    mutation_surfaces = discover_live_surfaces(cwd=ROOT_CWD, probe=True, which=fake_which_full, runner=fake_runner)
    require_in("coordinator per-call consent issue", "coordinator MCP execution requires explicit per-call allow_mutation consent", validate_bridge_live_readiness(coordinator_plan, mutation_surfaces))
    mutation_surfaces["operatorConsent"] = {"allowMutation": True, "source": "test", "requiredPerMutatingCall": True}
    require("coordinator ready with mutations and consent", validate_bridge_live_readiness(coordinator_plan, mutation_surfaces), [])
    cases.append("coordinator-readiness")

    delegate_packet = classify_request("Execute the approved pending-approval plan with ultragoal")
    delegate_plan = build_bridge_plan(delegate_packet, cwd=ROOT_CWD)
    require("delegation ready with mutations and consent", validate_bridge_live_readiness(delegate_plan, mutation_surfaces), [])
    cases.append("delegation-readiness")

    rpc_packet = classify_request("Implement repo diagnostics; GJC needs Hermes host tools via RPC customTools for memory recall")
    rpc_plan = build_bridge_plan(rpc_packet, cwd=ROOT_CWD)
    require_in("rpc blocked without registry", "RPC host customTools registry is not mapped", validate_bridge_live_readiness(rpc_plan, mutation_surfaces))
    cases.append("rpc-fail-closed")

    memory_packet = classify_request("remember my API key <example-api-key> for later")
    raw = build_raw_artifact_record(memory_packet)
    raw_stub = build_hermes_adapter_stub(raw, surfaces=mutation_surfaces)
    require("adapter storage authority", raw_stub["storageAuthority"], "Hermes")
    require("adapter no local write", raw_stub["writePlan"]["allowedHere"], False)
    require("adapter writes disabled", raw_stub["writePlan"]["enabled"], False)
    require_in("adapter sensitive blocked", "sensitive memory requires explicit approval before any Hermes write", raw_stub["writePlan"]["blockedReasons"])
    require("adapter validation", validate_adapter_stub(raw_stub), [])
    sensitive_report = build_live_binding_report(memory_packet, cwd=ROOT_CWD, probe=False)
    require("sensitive report packet redacted", sensitive_report["packet"]["request"], "[redacted-sensitive]")
    require("sensitive report bridge redacted", sensitive_report["bridgePlan"]["request"], "[redacted-sensitive]")
    cases.append("sensitive-live-report-redacted")
    cases.append("hermes-adapter-sensitive-block")

    summary = build_summary_memory_record(raw, "User provided <example-api-key>; do not persist without approval.")
    summary_stub = build_hermes_adapter_stub(summary, surfaces=mutation_surfaces)
    require("sensitive summary redacted", summary["summaryMemory"]["summary"], "[redacted-sensitive]")
    require("summary adapter no write", summary_stub["writePlan"]["enabled"], False)
    require_in("summary future binding", "SHACL validation before canonical promotion", summary_stub["requiredFutureBinding"])
    require("summary adapter validation", validate_adapter_stub(summary_stub), [])
    cases.append("hermes-adapter-summary-block")

    report = build_live_binding_report(packet, cwd=ROOT_CWD, probe=False)
    require("report bridge path", report["bridgePlan"]["bridgePlan"]["bridgePath"], "visible-routed-session")
    require_truthy("report includes handoff", report.get("visibleSessionHandoff"))
    cases.append("live-binding-report")
finally:
    if old_mutations is None:
        os.environ.pop("GJC_COORDINATOR_MCP_MUTATIONS", None)
    else:
        os.environ["GJC_COORDINATOR_MCP_MUTATIONS"] = old_mutations

print(f"PASS: {len(cases)} just-chill live-binding cases passed")
