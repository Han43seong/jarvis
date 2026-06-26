#!/usr/bin/env python3
"""Contract-level GJC bridge plan builder for just-chill.

This module consumes the deterministic route packet from ``just_chill_router``
and emits an execution-safe bridge plan. It never starts GJC, never mutates
Hermes state, and never claims GJC workflow ownership; it only prepares the
handoff contract that a host/operator layer can execute later.
"""
from __future__ import annotations

import argparse
import json
from typing import Any

from just_chill_router import BRIDGE_REFERENCE, classify_request

SCHEMA_VERSION = 1
BRIDGE_PLANNER = "just-chill-gjc-bridge-v1"

DELEGATE_TOOLS = {
    "gjc-ralplan": "gjc_delegate_plan",
    "gjc-ultragoal": "gjc_delegate_execute",
    "gjc-team": "gjc_delegate_team",
}

GJC_ROUTES = {"gjc-direct", "gjc-deep-interview", "gjc-ralplan", "gjc-ultragoal", "gjc-team"}

DEV_BRIDGE_PATHS = {"visible-routed-session", "coordinator-mcp", "gjc-delegation", "rpc-host-tools"}
NONDEV_BRIDGE_PATHS = {"host-tool-or-direct", "coordinator-mcp", "rpc-host-tools"}



def _skill_prompt(packet: dict[str, Any]) -> str:
    skill = packet["routing"].get("skillEntrypoint")
    request = packet.get("request", "")
    if skill:
        return f"{skill}\n\n{request}"
    return request


def _route_label(packet: dict[str, Any]) -> str:
    return packet["routing"].get("routeHint") or "unknown"

def validate_router_packet(packet: dict[str, Any]) -> list[str]:
    """Return packet invariant violations that would make bridge output unsafe."""
    issues: list[str] = []
    for key in ["classification", "routing", "handoff"]:
        if not isinstance(packet.get(key), dict):
            issues.append(f"missing object: {key}")

    classification = packet.get("classification", {})
    routing = packet.get("routing", {})
    is_dev = classification.get("isDevelopment")
    route = routing.get("routeHint")
    target = routing.get("target")
    bridge_path = routing.get("bridgePath")

    if not isinstance(is_dev, bool):
        issues.append("classification.isDevelopment must be boolean")

    if is_dev is True:
        if target != "GJC":
            issues.append("development packets must target GJC")
        if route not in GJC_ROUTES:
            issues.append(f"development packets require a GJC route hint, got {route!r}")
        if bridge_path not in DEV_BRIDGE_PATHS:
            issues.append(f"development packets have unsupported bridge path {bridge_path!r}")
    elif is_dev is False:
        if target == "GJC":
            issues.append("non-development packets must not target GJC")
        if route != "non-development-tool-or-direct":
            issues.append(f"non-development packets require non-development route hint, got {route!r}")
        if bridge_path not in NONDEV_BRIDGE_PATHS:
            issues.append(f"non-development packets have unsupported bridge path {bridge_path!r}")

    evidence = packet.get("handoff", {}).get("completionEvidenceRequired")
    if not isinstance(evidence, list) or not evidence:
        issues.append("handoff.completionEvidenceRequired must be a non-empty list")

    return issues



def _base_plan(packet: dict[str, Any], cwd: str | None) -> dict[str, Any]:
    classification = packet["classification"]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "planner": BRIDGE_PLANNER,
        "bridgeReference": BRIDGE_REFERENCE,
        "sourceRouter": packet.get("router"),
        "sourceRouterSchemaVersion": packet.get("schemaVersion"),
        "request": packet.get("request", ""),
        "target": packet["routing"].get("target"),
        "workdir": cwd,
        "authorityBoundary": {
            "justChillOwns": [
                "request intake",
                "risk and route classification",
                "handoff packet assembly",
                "completion evidence policy",
                "memory promotion policy",
            ],
            "gjcOwns": [
                "development workflow state",
                "development clarification/planning/execution skills",
                "implementation verification loops",
            ],
            "hermesOwns": [
                "state storage",
                "artifact storage and retrieval",
                "memory access infrastructure",
                "retention and deletion infrastructure",
            ],
            "noExecutionInThisPlan": True,
            "doesNotMirrorGjcState": True,
        },
        "approvalGate": {
            "required": bool(classification.get("approvalRequired")),
            "risk": classification.get("risk"),
            "reasonSignals": packet.get("signals", {}).get("risk", []),
            "blockedUntilApproved": bool(classification.get("approvalRequired")),
        },
        "completionEvidenceRequired": list(packet.get("handoff", {}).get("completionEvidenceRequired", [])),
        "forbiddenActions": list(packet.get("handoff", {}).get("forbiddenActions", [])),
        "liveBinding": {
            "status": "contract-only",
            "unresolved": [
                "operator-executed tmux/TUI bridge beyond dry-run orchestration plans",
                "installed coordinator MCP profile and mutation classes",
                "installed gjc_delegate_* host plugin availability",
                "host RPC customTools registry",
            ],
        },
    }


def _visible_routed_session_plan(packet: dict[str, Any], cwd: str | None) -> dict[str, Any]:
    return {
        "bridgePath": "visible-routed-session",
        "executionAllowedHere": False,
        "sessionPlan": {
            "hostOwnedHelpers": ["create-gjc-session", "prompt-gjc-session", "tail-gjc-session"],
            "worktreeRequired": True,
            "workdir": cwd,
            "skillPrompt": _skill_prompt(packet),
            "acceptanceSignal": "real GJC work signal such as a tool call, todo/plan update, diff, test, report, PR, or durable artifact",
            "scrollbackIsCompletion": False,
        },
        "operatorSteps": [
            "create or verify a dedicated worktree",
            "start a visible routed GJC tmux session",
            "wait for GJC TUI readiness",
            "inject the skill-based prompt separately",
            "collect durable evidence before reporting completion",
        ],
    }


def _coordinator_mcp_plan(packet: dict[str, Any], cwd: str | None) -> dict[str, Any]:
    return {
        "bridgePath": "coordinator-mcp",
        "executionAllowedHere": False,
        "server": {
            "command": "gjc",
            "args": ["mcp-serve", "coordinator"],
            "requiredEnv": {
                "GJC_COORDINATOR_MCP_WORKDIR_ROOTS": cwd or "<repo-root>",
            },
            "mutationClassesRequiredForStart": ["sessions", "questions", "reports"],
            "perCallConsentRequired": "allow_mutation: true for mutating calls",
        },
        "turnModel": {
            "start": "gjc_coordinator_start_session",
            "send": "gjc_coordinator_send_prompt",
            "poll": ["gjc_coordinator_read_turn", "gjc_coordinator_await_turn", "gjc_coordinator_watch_events"],
            "questions": ["gjc_coordinator_list_questions", "gjc_coordinator_submit_question_answer"],
            "report": "gjc_coordinator_report_status",
            "taskPrompt": _skill_prompt(packet),
            "completionSourceOfTruth": "terminal GJC turn_id state plus report/artifact evidence",
        },
    }


def _delegation_plan(packet: dict[str, Any], cwd: str | None) -> dict[str, Any]:
    route = _route_label(packet)
    delegate_tool = DELEGATE_TOOLS.get(route)
    return {
        "bridgePath": "gjc-delegation",
        "executionAllowedHere": False,
        "delegateTool": delegate_tool,
        "delegateAvailable": delegate_tool is not None,
        "delegateInput": {
            "cwd": cwd,
            "task": packet.get("request", ""),
            "allow_mutation": "required only after explicit approval and enabled mutation class",
        },
        "fallbackWhenNoDelegateTool": "use visible-routed-session or coordinator MCP with the skill prompt",
        "completionSourceOfTruth": "returned turn_id polled through coordinator turn state, not terminal scrollback",
    }


def _rpc_host_tools_plan(packet: dict[str, Any], cwd: str | None) -> dict[str, Any]:
    return {
        "bridgePath": "rpc-host-tools",
        "executionAllowedHere": False,
        "rpcBoundary": {
            "mode": "gjc --mode rpc",
            "hostExportsTools": True,
            "gjcCallsHostVia": "host_tool_call / host_tool_result frames",
            "allowedFirstTools": [
                "hermes_route_message",
                "hermes_artifact_read",
                "hermes_memory_recall",
                "just_chill_policy_check",
            ],
            "forbiddenImports": [
                "@gajae-code/coding-agent/runtime-mcp",
                "/mcp",
                "/capability/mcp",
                "/config/mcp-schema",
                "/discovery/mcp-json",
            ],
            "workdir": cwd,
            "taskPrompt": _skill_prompt(packet),
        },
    }


def _nondev_plan(packet: dict[str, Any], cwd: str | None) -> dict[str, Any]:
    return {
        "bridgePath": packet["routing"].get("bridgePath"),
        "executionAllowedHere": False,
        "gjcHandoff": None,
        "nonDevelopmentPlan": {
            "category": packet["classification"].get("category"),
            "target": packet["routing"].get("target"),
            "workdir": cwd,
            "allowedBeforeApproval": [
                "draft",
                "summarize",
                "prepare memory candidate",
                "prepare external-tool route packet",
            ],
            "requiresApprovalFor": [
                "external send",
                "payment or purchase",
                "delete/redact/broad overwrite",
                "sensitive memory",
                "canonical Decision/Policy assertion promotion",
            ],
        },
    }


def build_bridge_plan(packet: dict[str, Any], cwd: str | None = None) -> dict[str, Any]:
    """Build a deterministic bridge plan from a just_chill_router packet."""
    issues = validate_router_packet(packet)
    if issues:
        raise ValueError("invalid router packet: " + "; ".join(issues))
    plan = _base_plan(packet, cwd)
    is_dev = bool(packet["classification"].get("isDevelopment"))
    route = _route_label(packet)
    bridge_path = packet["routing"].get("bridgePath")

    if is_dev:
        plan["developmentHandoff"] = {
            "routeHint": route,
            "skillEntrypoint": packet["routing"].get("skillEntrypoint"),
            "originalRequestPreserved": True,
            "justChillDoesNotInterview": True,
            "justChillDoesNotPlanImplementation": True,
        }
        if bridge_path == "visible-routed-session":
            plan["bridgePlan"] = _visible_routed_session_plan(packet, cwd)
        elif bridge_path == "coordinator-mcp":
            plan["bridgePlan"] = _coordinator_mcp_plan(packet, cwd)
        elif bridge_path == "gjc-delegation":
            plan["bridgePlan"] = _delegation_plan(packet, cwd)
        elif bridge_path == "rpc-host-tools":
            plan["bridgePlan"] = _rpc_host_tools_plan(packet, cwd)
        else:
            raise ValueError(f"unsupported bridge path: {bridge_path}")
    else:
        plan["bridgePlan"] = _nondev_plan(packet, cwd)

    return plan


def packet_from_json(raw: str) -> dict[str, Any]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("packet JSON must decode to an object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a just-chill GJC/Hermes bridge plan without executing it.")
    parser.add_argument("request", nargs="*", help="User request text. Ignored when --packet-json is provided.")
    parser.add_argument("--packet-json", help="Existing just_chill_router packet JSON.")
    parser.add_argument("--cwd", default=None, help="Target workdir for handoff planning.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    if args.packet_json:
        packet = packet_from_json(args.packet_json)
    else:
        packet = classify_request(" ".join(args.request))

    plan = build_bridge_plan(packet, cwd=args.cwd)
    print(json.dumps(plan, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
