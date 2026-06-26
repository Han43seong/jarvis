#!/usr/bin/env python3
"""Hermes-main dogfood harness for just-chill.

This harness models Hermes as the user-facing agent and just-chill as a policy
MCP/harness dependency. It exercises real harness/MCP code paths without
starting GJC, writing Hermes memory, running SHACL, or searching a vector store.
"""
from __future__ import annotations

import argparse
import json
from typing import Any

from just_chill_harness_mcp import (
    TOOL_CONSENT,
    TOOL_GJC_HANDOFF,
    TOOL_HANDLE,
    TOOL_RECALL,
    TOOL_REMEMBER,
    TOOL_ROUTE,
    TOOL_STATUS,
    handle_mcp_request,
    tool_names,
)
from just_chill_memory_contracts import build_raw_artifact_record, build_summary_memory_record
from just_chill_router import classify_request
from just_chill_vector_recall import build_retrieval_evidence, build_vector_sidecar_candidate

SCHEMA_VERSION = 1
HARNESS_NAME = "just-chill-hermes-main-dogfood-v1"
DEFAULT_DEV_REQUEST = "fix src/hooks/bridge.ts and run focused checks"
DEFAULT_MEMORY_REQUEST = "remember that Hermes is the user-facing layer and just-chill is its policy harness"
DEFAULT_SUMMARY = "Hermes is user-facing; just-chill is the routing and memory policy harness."


def authority_boundary() -> dict[str, Any]:
    return {
        "executionAllowedHere": False,
        "hermesIsUserFacingLayer": True,
        "justChillIsHarness": True,
        "justChillExecutesGjc": False,
        "justChillWritesHermes": False,
        "justChillOwnsCanonicalMemory": False,
        "justChillRunsShaclEngine": False,
        "justChillSearchesVectorStore": False,
        "justChillCallsCoordinator": False,
        "justChillCallsDelegateTools": False,
    }


def mcp_tool_call(name: str, arguments: dict[str, Any], request_id: str) -> dict[str, Any]:
    response = handle_mcp_request({
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    if response is None:
        raise AssertionError("MCP response unexpectedly omitted")
    result = response.get("result", {})
    content = result.get("content", [])
    decoded: dict[str, Any] = {}
    if content:
        decoded = json.loads(content[0]["text"])
    return {
        "requestId": request_id,
        "tool": name,
        "response": response,
        "isError": result.get("isError", False),
        "decoded": decoded,
    }


def canonical_ref(summary_record: dict[str, Any]) -> dict[str, Any]:
    memory = summary_record["summaryMemory"]
    return {
        "sourceKind": "summary-memory",
        "canonicalSourceId": memory["id"],
        "canonicalContentHash": memory["summaryHash"],
        "observedContentHash": memory["summaryHash"],
        "receiptRef": "host-hermes-receipt://hermes-main-summary-001",
        "receiptKind": "host-owned-summary-memory-receipt",
        "readBackHashMatches": True,
        "canonicalInHermes": True,
        "deletionState": memory["deletionState"],
        "redactionState": memory["redactionState"],
    }


def recall_fixture(summary_text: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    packet = classify_request("remember that Hermes is user-facing and just-chill is a harness")
    raw = build_raw_artifact_record(packet, content="Hermes is user-facing and just-chill is a harness.")
    summary_record = build_summary_memory_record(raw, summary_text, confidence=0.92)
    reference = canonical_ref(summary_record)
    candidate = build_vector_sidecar_candidate(
        summary_record,
        canonical_reference=reference,
        embedding_model="hermes-main-dogfood-exact-hash",
        embedding_dimensions=384,
    )
    retrieval = build_retrieval_evidence(candidate, query="What is the main user-facing layer?", score=0.95)
    return candidate, retrieval, reference


def build_hermes_main_harness(
    *,
    dev_request: str = DEFAULT_DEV_REQUEST,
    memory_request: str = DEFAULT_MEMORY_REQUEST,
    summary: str = DEFAULT_SUMMARY,
    cwd: str | None = None,
    recall_source_hash_override: str | None = None,
    current_deletion_state: str | None = None,
    current_redaction_state: str | None = None,
    sensitive_memory: bool = False,
) -> dict[str, Any]:
    initialize = handle_mcp_request({"jsonrpc": "2.0", "id": "init", "method": "initialize", "params": {}})
    tools_list = handle_mcp_request({"jsonrpc": "2.0", "id": "tools", "method": "tools/list"})
    route_dev = mcp_tool_call(TOOL_ROUTE, {"request": dev_request, "cwd": cwd, "caller": "hermes"}, "route-dev")
    handoff = mcp_tool_call(TOOL_GJC_HANDOFF, {"request": dev_request, "cwd": cwd, "caller": "hermes"}, "handoff-dev")
    consent = mcp_tool_call(TOOL_CONSENT, {
        "bridgePlan": handoff["decoded"].get("bridgePlan"),
        "surfaces": {
            "visibleRoutedSession": {"status": "orchestration-plan-ready", "scrollbackIsCompletion": False, "evidencePolicy": {"durableEvidenceRequired": True, "scrollbackIsCompletion": False}},
            "operatorConsent": {"allowMutation": False, "source": "not-needed-visible", "requiredPerMutatingCall": True},
            "coordinatorMcp": {"status": "not-used", "missingTools": [], "mutationClassesEnabled": [], "mutationClassesRequiredForExecution": ["sessions", "questions", "reports"]},
            "gjcDelegation": {"delegateTools": {}},
        },
        "evidencePayload": {"kind": "test", "command": ["python3", "scripts/check_just_chill_hermes_harness.py"]},
        "caller": "hermes",
    }, "consent-visible")

    selected_memory_request = "remember my API key sk-test-1234567890" if sensitive_memory else memory_request
    selected_summary = "API key sk-test-1234567890" if sensitive_memory else summary
    remember = mcp_tool_call(TOOL_REMEMBER, {"request": selected_memory_request, "summary": selected_summary, "caller": "hermes"}, "remember")
    handled = mcp_tool_call(TOOL_HANDLE, {"request": selected_memory_request, "summary": selected_summary, "caller": "hermes"}, "handle")
    candidate, retrieval, reference = recall_fixture(summary)
    recall = mcp_tool_call(TOOL_RECALL, {
        "query": "What is the main user-facing layer?",
        "candidate": candidate,
        "retrievalEvidence": retrieval,
        "currentSourceHash": recall_source_hash_override or reference["observedContentHash"],
        "currentDeletionState": current_deletion_state or reference["deletionState"],
        "currentRedactionState": current_redaction_state or reference["redactionState"],
        "caller": "hermes",
    }, "recall")
    status = mcp_tool_call(TOOL_STATUS, {"cwd": cwd, "caller": "hermes"}, "status")
    malformed = handle_mcp_request({"jsonrpc": "2.0", "id": "bad", "method": "tools/call", "params": {"name": "just_chill.nope", "arguments": {}}})

    validation_issues: list[str] = []
    tool_names_list = [tool["name"] for tool in tools_list["result"]["tools"]]
    assertions = {
        "mcpInitializes": initialize["result"]["serverInfo"]["name"] == "just-chill-harness",
        "toolManifestComplete": tool_names_list == tool_names(),
        "devRoutesToGjc": route_dev["decoded"].get("routerPacket", {}).get("classification", {}).get("isDevelopment") is True,
        "handoffDoesNotExecute": handoff["decoded"].get("executionAllowedHere") is False and handoff["decoded"].get("bridgePlan", {}).get("authorityBoundary", {}).get("noExecutionInThisPlan") is True,
        "consentKeepsVisibleFirst": consent["decoded"].get("status") == "visible-session-preferred",
        "memoryContractsReady": remember["decoded"].get("status") == "memory-candidate-ready" and not sensitive_memory,
        "sensitiveMemoryBlocks": sensitive_memory is False or remember["decoded"].get("status") == "memory-candidate-blocked",
        "handleUsesMemoryPlan": handled["decoded"].get("memoryPlan") is not None,
        "recallAllowed": recall["decoded"].get("status") == "recall-allowed" and recall["decoded"].get("recallGateDecision", {}).get("allowRecall") is True,
        "malformedMcpFailsClosed": malformed["id"] == "bad" and malformed["result"]["isError"] is True,
        "statusSaysHermesMain": status["decoded"].get("userFacingLayer") == "Hermes" and status["decoded"].get("cliRole") == "debug/test/fixture surface only",
        "noHiddenExecution": all(
            call["decoded"].get("executionAllowedHere") is False
            for call in [route_dev, handoff, consent, remember, handled, recall, status]
        ),
    }
    failed = [name for name, passed in assertions.items() if not passed]
    validation_issues.extend(f"assertion failed: {name}" for name in failed)

    return {
        "schemaVersion": SCHEMA_VERSION,
        "harness": HARNESS_NAME,
        "status": "passed" if not validation_issues else "blocked",
        "authorityBoundary": authority_boundary(),
        "hermesMain": {
            "userFacingLayer": "Hermes",
            "justChillRole": "policy/routing/memory/GJC-handoff harness",
            "cliRole": "debug/test/fixture surface only",
        },
        "initialize": initialize,
        "toolsList": tools_list,
        "flows": {
            "routeDevelopment": route_dev,
            "gjcHandoff": handoff,
            "consent": consent,
            "remember": remember,
            "handle": handled,
            "recall": recall,
            "status": status,
            "malformedMcp": malformed,
        },
        "assertions": assertions,
        "validationIssues": validation_issues,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Hermes-main just-chill dogfood harness without executing GJC or writing Hermes.")
    parser.add_argument("--dev-request", default=DEFAULT_DEV_REQUEST)
    parser.add_argument("--memory-request", default=DEFAULT_MEMORY_REQUEST)
    parser.add_argument("--summary", default=DEFAULT_SUMMARY)
    parser.add_argument("--cwd", default=None)
    parser.add_argument("--recall-source-hash-override", default=None)
    parser.add_argument("--current-deletion-state", default=None)
    parser.add_argument("--current-redaction-state", default=None)
    parser.add_argument("--sensitive-memory", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_hermes_main_harness(
        dev_request=args.dev_request,
        memory_request=args.memory_request,
        summary=args.summary,
        cwd=args.cwd,
        recall_source_hash_override=args.recall_source_hash_override,
        current_deletion_state=args.current_deletion_state,
        current_redaction_state=args.current_redaction_state,
        sensitive_memory=args.sensitive_memory,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
