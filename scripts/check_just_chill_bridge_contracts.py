#!/usr/bin/env python3
"""Acceptance checks for just-chill bridge and Hermes contract skeletons."""
from __future__ import annotations

from just_chill_bridge import build_bridge_plan, validate_router_packet
from just_chill_memory_contracts import (
    build_raw_artifact_record,
    build_summary_memory_record,
    validate_contract_record,
)
from just_chill_router import classify_request


def require(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle, haystack) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


def require_truthy(name: str, value) -> None:
    if not value:
        raise AssertionError(f"{name}: expected truthy value, got {value!r}")

def require_raises(name: str, func, expected_substring: str) -> None:
    try:
        func()
    except Exception as exc:
        if expected_substring not in str(exc):
            raise AssertionError(f"{name}: expected {expected_substring!r} in {exc!r}") from exc
        return
    raise AssertionError(f"{name}: expected exception containing {expected_substring!r}")



cases: list[str] = []

packet = classify_request("fix TypeError in src/hooks/bridge.ts and run bun test")
plan = build_bridge_plan(packet, cwd="/home/hskim/projects/demo")
require("dev direct target", plan["target"], "GJC")
require("dev direct bridge", plan["bridgePlan"]["bridgePath"], "visible-routed-session")
require("dev direct no execution", plan["bridgePlan"]["executionAllowedHere"], False)
require("dev direct no state mirroring", plan["authorityBoundary"]["doesNotMirrorGjcState"], True)
require("dev direct contract-only", plan["liveBinding"]["status"], "contract-only")
require("dev direct plan no execution", plan["authorityBoundary"]["noExecutionInThisPlan"], True)
require_in("visible evidence", "real GJC work signal; tmux scrollback alone is insufficient", plan["completionEvidenceRequired"])
cases.append("visible-routed-session")

packet = classify_request("Refine this auth architecture plan before implementation")
plan = build_bridge_plan(packet, cwd="/home/hskim/projects/demo")
require("ralplan route", plan["developmentHandoff"]["routeHint"], "gjc-ralplan")
require("ralplan delegation bridge", plan["bridgePlan"]["bridgePath"], "gjc-delegation")
require("ralplan delegate tool", plan["bridgePlan"]["delegateTool"], "gjc_delegate_plan")
require("ralplan approval gate", plan["approvalGate"]["required"], True)
cases.append("gjc-delegate-plan")

packet = classify_request("Execute the approved pending-approval plan with ultragoal")
plan = build_bridge_plan(packet, cwd="/home/hskim/jarvis")
require("ultragoal route", plan["developmentHandoff"]["routeHint"], "gjc-ultragoal")
require("ultragoal delegate tool", plan["bridgePlan"]["delegateTool"], "gjc_delegate_execute")
require_in("turn evidence", "terminal GJC turn_id state", plan["completionEvidenceRequired"])
require("ultragoal no local execution", plan["bridgePlan"]["executionAllowedHere"], False)
cases.append("gjc-delegate-execute")

packet = classify_request("Use team tmux workers to implement independent modules in parallel")
plan = build_bridge_plan(packet, cwd="/home/hskim/jarvis")
require("team route", plan["developmentHandoff"]["routeHint"], "gjc-team")
require("team delegate tool", plan["bridgePlan"]["delegateTool"], "gjc_delegate_team")
cases.append("gjc-delegate-team")

packet = classify_request("Use coordinator MCP machine control and poll the turn_id artifact state for this repo task")
plan = build_bridge_plan(packet, cwd="/home/hskim/jarvis")
require("coordinator bridge", plan["bridgePlan"]["bridgePath"], "coordinator-mcp")
require("coordinator command", plan["bridgePlan"]["server"]["args"], ["mcp-serve", "coordinator"])
require("coordinator mutation consent", plan["bridgePlan"]["server"]["perCallConsentRequired"], "allow_mutation: true for mutating calls")
cases.append("coordinator-mcp")

packet = classify_request("Implement repo diagnostics; GJC needs Hermes host tools via RPC customTools for memory recall")
plan = build_bridge_plan(packet, cwd="/home/hskim/jarvis")
require("rpc bridge", plan["bridgePlan"]["bridgePath"], "rpc-host-tools")
require_in("rpc forbidden import", "/mcp", plan["bridgePlan"]["rpcBoundary"]["forbiddenImports"])
require_in("rpc host tool", "hermes_memory_recall", plan["bridgePlan"]["rpcBoundary"]["allowedFirstTools"])
cases.append("rpc-host-tools")

packet = classify_request("remember my API key for later")
plan = build_bridge_plan(packet, cwd="/home/hskim/jarvis")
require("sensitive memory nondev", packet["classification"]["isDevelopment"], False)
require("sensitive memory no gjc handoff", plan["bridgePlan"]["gjcHandoff"], None)
require("sensitive memory approval", plan["approvalGate"]["required"], True)
raw = build_raw_artifact_record(packet)
require("sensitive memory sensitivity", raw["artifact"]["sensitivity"], "sensitive")
require("sensitive memory no auto persist", raw["artifact"]["retention"]["autoPersistAllowed"], False)
require("sensitive memory no candidate", raw["artifact"]["memoryPolicy"]["candidateCreationAllowed"], False)
require("sensitive preview redacted", raw["artifact"]["contentPreview"], "[redacted-sensitive]")
require("raw validation", validate_contract_record(raw), [])

token_packet = classify_request("remember my API key sk-test-1234567890 for later")
token_plan = build_bridge_plan(token_packet, cwd="/home/hskim/jarvis")
token_raw = build_raw_artifact_record(token_packet)
require("token-shaped sensitive memory nondev", token_packet["classification"]["isDevelopment"], False)
require("token-shaped sensitive memory no gjc handoff", token_plan["bridgePlan"]["gjcHandoff"], None)
require("token-shaped sensitive preview redacted", token_raw["artifact"]["contentPreview"], "[redacted-sensitive]")
require("token-shaped sensitive no auto persist", token_raw["artifact"]["retention"]["autoPersistAllowed"], False)
cases.append("token-shaped-sensitive-memory-blocked")
cases.append("sensitive-memory-contract")

packet = classify_request("remember that GJC should use visible routed sessions first")
raw = build_raw_artifact_record(packet)
summary = build_summary_memory_record(raw, "User prefers visible routed GJC sessions first for just-chill integration.")
require("policy memory remains nondev", packet["classification"]["isDevelopment"], False)
require("policy memory internal", raw["artifact"]["sensitivity"], "internal")
require("summary validation", validate_contract_record(summary), [])
require_truthy("summary source refs", summary["summaryMemory"]["sourceArtifactRefs"])
require("summary promotion blocked pending confirmation", summary["summaryMemory"]["promotionPolicy"]["canonicalPromotionAllowed"], False)
cases.append("summary-memory-contract")

packet = classify_request("새 개발 아이디어가 모호한데 요구사항을 정리해서 명세로 만들어줘")
plan = build_bridge_plan(packet, cwd="/home/hskim/jarvis")
require("deep interview route", plan["developmentHandoff"]["routeHint"], "gjc-deep-interview")
require("deep interview skill", plan["developmentHandoff"]["skillEntrypoint"], "/skill:deep-interview")
require("deep interview visible bridge", plan["bridgePlan"]["bridgePath"], "visible-routed-session")
cases.append("deep-interview-visible-route")

bad_packet = classify_request("fix TypeError in src/hooks/bridge.ts")
bad_packet["routing"]["target"] = "Hermes"
require_in("bad packet validation", "development packets must target GJC", validate_router_packet(bad_packet))
require_raises("bad packet rejected", lambda: build_bridge_plan(bad_packet, cwd="/home/hskim/jarvis"), "development packets must target GJC")
cases.append("malformed-packet-rejected")

packet = classify_request("메일 초안을 작성해서 요약해줘")
plan = build_bridge_plan(packet, cwd="/home/hskim/jarvis")
require("mail nondev", packet["classification"]["isDevelopment"], False)
require("mail category", plan["bridgePlan"]["nonDevelopmentPlan"]["category"], "mail")
require_in("draft allowed", "draft", plan["bridgePlan"]["nonDevelopmentPlan"]["allowedBeforeApproval"])
cases.append("nondev-draft")

print(f"PASS: {len(cases)} just-chill bridge/memory contract cases passed")
