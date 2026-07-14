#!/usr/bin/env python3
"""Acceptance checks for the Hermes-facing just-chill harness adapter."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from just_chill_approval_registry import issue_approval
from just_chill_harness import (
    call_operation,
    consent_evaluate,
    gjc_handoff_plan,
    handle,
    recall_gate,
    remember_plan,
    route,
    status,
)
from just_chill_memory_contracts import build_raw_artifact_record, build_summary_memory_record
from just_chill_router import classify_request
from just_chill_vector_recall import build_retrieval_evidence, build_vector_sidecar_candidate

ROOT = Path(__file__).resolve().parents[1]
HARNESS_SCRIPT = ROOT / "scripts" / "just_chill_harness.py"


def require(name: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle: Any, haystack: Any) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


def require_truthy(name: str, value: Any) -> None:
    if not value:
        raise AssertionError(f"{name}: expected truthy, got {value!r}")


def run_json(operation: str, arguments: dict[str, Any]) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(HARNESS_SCRIPT), "--operation", operation, "--arguments", json.dumps(arguments, ensure_ascii=False, sort_keys=True)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def canonical_ref(summary: dict[str, Any]) -> dict[str, Any]:
    memory = summary["summaryMemory"]
    return {
        "sourceKind": "summary-memory",
        "canonicalSourceId": memory["id"],
        "canonicalContentHash": memory["summaryHash"],
        "observedContentHash": memory["summaryHash"],
        "receiptRef": "host-hermes-receipt://harness-summary-001",
        "receiptKind": "host-owned-summary-memory-receipt",
        "readBackHashMatches": True,
        "canonicalInHermes": True,
        "deletionState": memory["deletionState"],
        "redactionState": memory["redactionState"],
    }


def assert_boundary(label: str, output: dict[str, Any]) -> None:
    require(f"{label} execution", output["executionAllowedHere"], False)
    boundary = output["authorityBoundary"]
    for key in [
        "executionAllowedHere",
        "justChillExecutesGjc",
        "justChillWritesHermes",
        "justChillOwnsCanonicalMemory",
        "justChillRunsShaclEngine",
        "justChillSearchesVectorStore",
        "justChillCallsCoordinator",
        "justChillCallsDelegateTools",
    ]:
        require(f"{label} boundary {key}", boundary[key], False)


cases: list[str] = []

route_dev = route("fix src/hooks/bridge.ts and run tests", cwd=str(ROOT))
require("route op", route_dev["operation"], "route")
require("route status", route_dev["status"], "route-ready")
require("route dev", route_dev["routerPacket"]["classification"]["isDevelopment"], True)
require("route bridge", route_dev["bridgePlan"]["bridgePlan"]["bridgePath"], "visible-routed-session")
assert_boundary("route", route_dev)
cases.append("route-dev-contract")

memory = remember_plan(
    "remember that just-chill is a Hermes-facing harness",
    summary="just-chill is a Hermes-facing harness, not the main user CLI.",
)
require("memory status", memory["status"], "memory-candidate-ready")
require("memory raw", memory["rawArtifactContract"]["recordKind"], "raw-artifact-contract")
require("memory summary", memory["summaryMemoryContract"]["recordKind"], "summary-memory-contract")
assert_boundary("remember", memory)
cases.append("remember-plan-ready")

sensitive = remember_plan("remember my API key <example-api-key> for later")
require("sensitive blocked", sensitive["status"], "memory-candidate-blocked")
require_in("sensitive approval", "sensitive memory requires explicit approval before host-owned persistence", sensitive["blockedReasons"])
require("sensitive redacted", sensitive["rawArtifactContract"]["artifact"]["contentPreview"], "[redacted-sensitive]")
assert_boundary("sensitive", sensitive)
cases.append("sensitive-memory-blocked")
with TemporaryDirectory() as tmp:
    sensitive_request = "remember my API key <example-api-key> for later"
    issued = issue_approval(
        scope="memory.write",
        subject=sensitive_request,
        actor="example-user",
        reason="harness registry acceptance test",
        registry=str(Path(tmp) / "approvals.jsonl"),
    )
    registry_memory = remember_plan(
        sensitive_request,
        approval_token=issued["approvalToken"],
        approval_registry=str(Path(tmp) / "approvals.jsonl"),
    )
    require("registry memory ready", registry_memory["status"], "memory-candidate-ready")
    require("registry verification mode", registry_memory["approvalVerification"]["mode"], "registry")
    require("registry approval accepted", registry_memory["approvalTokenAccepted"], True)
    assert_boundary("registry-memory", registry_memory)
    cases.append("sensitive-memory-registry-approved")


recall_default = recall_gate("How should dev work route?", cwd=str(ROOT))
require("recall default", recall_default["status"], "host-retrieval-required")
require("recall probe default", recall_default["vectorBoundary"]["probeMode"], "availability-only")
require("recall decision", recall_default["recallGateDecision"], None)
assert_boundary("recall-default", recall_default)
cases.append("recall-default-host-evidence-required")

packet = classify_request("remember that development routes to GJC visible sessions first")
raw = build_raw_artifact_record(packet, content="Development routes to GJC visible sessions first.")
summary = build_summary_memory_record(raw, "Development routes to GJC visible sessions first.")
reference = canonical_ref(summary)
candidate = build_vector_sidecar_candidate(
    summary,
    canonical_reference=reference,
    embedding_model="harness-test-embedding",
    embedding_dimensions=384,
)
retrieval = build_retrieval_evidence(candidate, query="How should dev work route?", score=0.94)
recall_allowed = recall_gate(
    "How should dev work route?",
    candidate=candidate,
    retrieval_evidence=retrieval,
    current_source_hash=reference["observedContentHash"],
    current_deletion_state=reference["deletionState"],
    current_redaction_state=reference["redactionState"],
)
require("recall allowed", recall_allowed["status"], "recall-allowed")
require("recall allow bool", recall_allowed["recallGateDecision"]["allowRecall"], True)
require("recall blockers", recall_allowed["blockedReasons"], [])
cases.append("recall-admitted-with-host-evidence")

recall_malformed = recall_gate("How should dev work route?", candidate="{nope}", retrieval_evidence=retrieval)
require("malformed recall", recall_malformed["status"], "blocked")
require_in("malformed blocker", "candidate JSON must decode to an object", recall_malformed["blockedReasons"])
cases.append("recall-malformed-json-blocked")

recall_deleted = recall_gate(
    "How should dev work route?",
    candidate=candidate,
    retrieval_evidence=retrieval,
    current_source_hash=reference["observedContentHash"],
    current_deletion_state="deleted",
    current_redaction_state=reference["redactionState"],
)
require("deleted recall", recall_deleted["status"], "recall-blocked")
require_in("deleted blocker", "deleted source cannot be recalled", recall_deleted["blockedReasons"])
cases.append("recall-deleted-blocked")

handoff = gjc_handoff_plan("fix src/hooks/bridge.ts and run tests", cwd=str(ROOT), allow_mutation=True)
require("handoff status", handoff["status"], "handoff-plan-ready")
require("handoff target", handoff["bridgePlan"]["target"], "GJC")
require("handoff local mutation", handoff["mutationConsent"]["allowedHere"], False)
assert_boundary("handoff", handoff)
cases.append("gjc-handoff-plan")

consent_visible = consent_evaluate(bridge_plan=handoff["bridgePlan"], surfaces={
    "visibleRoutedSession": {"status": "orchestration-plan-ready", "scrollbackIsCompletion": False, "evidencePolicy": {"durableEvidenceRequired": True, "scrollbackIsCompletion": False}},
    "operatorConsent": {"allowMutation": False, "source": "not-needed-visible", "requiredPerMutatingCall": True},
    "coordinatorMcp": {"status": "not-used", "missingTools": [], "mutationClassesEnabled": [], "mutationClassesRequiredForExecution": ["sessions", "questions", "reports"]},
    "gjcDelegation": {"delegateTools": {}},
}, evidence_payload={"kind": "test", "command": ["python3", "scripts/check_just_chill_harness.py"]})
require("consent visible", consent_visible["status"], "visible-session-preferred")
require("consent blockers", consent_visible["blockedReasons"], [])
assert_boundary("consent", consent_visible)
cases.append("consent-visible-first")
consent_no_durable = consent_evaluate(bridge_plan=handoff["bridgePlan"], surfaces={
    "visibleRoutedSession": {"status": "orchestration-plan-ready", "scrollbackIsCompletion": False, "evidencePolicy": {"durableEvidenceRequired": False, "scrollbackIsCompletion": False}},
    "operatorConsent": {"allowMutation": False, "source": "not-needed-visible", "requiredPerMutatingCall": True},
    "coordinatorMcp": {"status": "not-used", "missingTools": [], "mutationClassesEnabled": [], "mutationClassesRequiredForExecution": ["sessions", "questions", "reports"]},
    "gjcDelegation": {"delegateTools": {}},
}, evidence_payload={"kind": "test", "command": ["python3", "scripts/check_just_chill_harness.py"]})
require("consent no durable", consent_no_durable["status"], "mutation-blocked")
require_in("consent no durable blocker", "durable completion evidence is required", consent_no_durable["blockedReasons"])
cases.append("consent-durable-evidence-required")

consent_scrollback = consent_evaluate(bridge_plan=handoff["bridgePlan"], surfaces={
    "visibleRoutedSession": {"status": "orchestration-plan-ready", "scrollbackIsCompletion": True, "evidencePolicy": {"durableEvidenceRequired": True, "scrollbackIsCompletion": True}},
    "operatorConsent": {"allowMutation": False, "source": "not-needed-visible", "requiredPerMutatingCall": True},
    "coordinatorMcp": {"status": "not-used", "missingTools": [], "mutationClassesEnabled": [], "mutationClassesRequiredForExecution": ["sessions", "questions", "reports"]},
    "gjcDelegation": {"delegateTools": {}},
}, evidence_payload={"kind": "test", "command": ["python3", "scripts/check_just_chill_harness.py"]})
require("consent scrollback", consent_scrollback["status"], "mutation-blocked")
require_in("consent scrollback blocker", "tmux scrollback must be explicitly rejected as completion evidence", consent_scrollback["blockedReasons"])
cases.append("consent-scrollback-rejected")

coordinator_bridge = json.loads(json.dumps(handoff["bridgePlan"], sort_keys=True))
coordinator_bridge["bridgePlan"]["bridgePath"] = "coordinator-mcp"
coordinator_blocked = consent_evaluate(bridge_plan=coordinator_bridge, surfaces={
    "visibleRoutedSession": {"status": "orchestration-plan-ready", "scrollbackIsCompletion": False, "evidencePolicy": {"durableEvidenceRequired": True, "scrollbackIsCompletion": False}},
    "operatorConsent": {"allowMutation": False, "source": "missing", "requiredPerMutatingCall": True},
    "coordinatorMcp": {"status": "not-used", "missingTools": [], "mutationClassesEnabled": [], "mutationClassesRequiredForExecution": ["sessions", "questions", "reports"]},
    "gjcDelegation": {"delegateTools": {}},
}, evidence_payload={"kind": "test", "command": ["python3", "scripts/check_just_chill_harness.py"]})
require("coordinator blocked", coordinator_blocked["status"], "mutation-blocked")
require_in("coordinator smoke blocker", "coordinator MCP smoke check is not clean", coordinator_blocked["blockedReasons"])
require_in("coordinator class blocker", "GJC coordinator/delegation mutation requires classes: sessions, questions, reports", coordinator_blocked["blockedReasons"])
require_in("coordinator consent blocker", "GJC coordinator/delegation mutation requires explicit per-call allow_mutation consent", coordinator_blocked["blockedReasons"])
cases.append("consent-coordinator-mutation-blocked")

coordinator_ready = consent_evaluate(
    bridge_plan=coordinator_bridge,
    surfaces={
        "visibleRoutedSession": {"status": "orchestration-plan-ready", "scrollbackIsCompletion": False, "evidencePolicy": {"durableEvidenceRequired": True, "scrollbackIsCompletion": False}},
        "operatorConsent": {"allowMutation": True, "source": "host-approval://gjc-coordinator-test", "requiredPerMutatingCall": True},
        "coordinatorMcp": {"status": "smoke-ok", "missingTools": [], "mutationClassesEnabled": ["sessions", "questions", "reports"], "mutationClassesRequiredForExecution": ["sessions", "questions", "reports"]},
        "gjcDelegation": {"delegateTools": {}},
    },
    allow_mutation=True,
    mutation_classes=["sessions", "questions", "reports"],
    evidence_payload={"kind": "test", "command": ["python3", "scripts/check_just_chill_harness.py"]},
)
require("coordinator ready", coordinator_ready["status"], "host-mutation-consent-ready")
require("coordinator approved", coordinator_ready["consentPolicyDecision"]["mutationConsentGate"]["approvedForHostMutation"], True)
require("coordinator blockers", coordinator_ready["blockedReasons"], [])
cases.append("consent-coordinator-mutation-ready")

consent_missing = consent_evaluate()
require("consent missing", consent_missing["status"], "blocked")
require_in("consent missing blocker", "request or bridge plan is required", consent_missing["blockedReasons"])
cases.append("consent-missing-bridge-blocked")

consent_bad_bridge = consent_evaluate(bridge_plan="{bad-json}")
require("consent bad bridge", consent_bad_bridge["status"], "blocked")
require_in("consent bad bridge blocker", "bridge plan JSON must decode to an object", consent_bad_bridge["blockedReasons"])
cases.append("consent-malformed-bridge-blocked")


handled_dev = handle("fix src/hooks/bridge.ts and run tests", cwd=str(ROOT))
require("handle dev status", handled_dev["status"], "handled-contract-ready")
require_truthy("handle handoff", handled_dev["gjcHandoffPlan"])
require_truthy("handle consent", handled_dev["consentEvaluation"])
require("handle memory none", handled_dev["memoryPlan"], None)
require_in("handle bridge next step", "Hermes or a host bridge may prepare visible-session-only execution through scripts/just_chill_gjc_execution_bridge.py", handled_dev["hostOwnedNextSteps"])
assert_boundary("handle-dev", handled_dev)
cases.append("handle-development")

handled_memory = handle("remember that Hermes is the user-facing main layer", summary="Hermes is the user-facing main layer.")
require("handle memory status", handled_memory["status"], "handled-contract-ready")
require_truthy("handle memory plan", handled_memory["memoryPlan"])
require("handle memory no handoff", handled_memory["gjcHandoffPlan"], None)
cases.append("handle-memory")
with TemporaryDirectory() as tmp:
    sensitive_request = "remember my API key <example-api-key> for later"
    registry_path = str(Path(tmp) / "approvals.jsonl")
    issued = issue_approval(
        scope="memory.write",
        subject=sensitive_request,
        actor="example-user",
        reason="handle registry acceptance test",
        registry=registry_path,
    )
    handled_registry_memory = handle(
        sensitive_request,
        approval_token=issued["approvalToken"],
        approval_registry=registry_path,
    )
    require("handle registry memory status", handled_registry_memory["status"], "handled-contract-ready")
    require("handle registry verification", handled_registry_memory["memoryPlan"]["approvalVerification"]["mode"], "registry")
    assert_boundary("handle-registry-memory", handled_registry_memory)
    cases.append("handle-sensitive-memory-registry-approved")

handled_memory_blocked = handle("remember my API key <example-api-key>")
require("handle blocked memory status", handled_memory_blocked["status"], "handled-contract-blocked")
require_truthy("handle blocked memory plan", handled_memory_blocked["memoryPlan"])
require_in("handle blocked memory reason", "sensitive memory requires explicit approval before host-owned persistence", handled_memory_blocked["blockedReasons"])
cases.append("handle-sensitive-memory-blocked")

handled_external = handle("search the web for Hermes MCP docs")
require("handle external status", handled_external["status"], "handled-contract-ready")
require("handle external no memory", handled_external["memoryPlan"], None)
require("handle external no handoff", handled_external["gjcHandoffPlan"], None)
require_in("handle external next step", "Hermes should route to the appropriate non-development external tool or direct response lane", handled_external["hostOwnedNextSteps"])
cases.append("handle-non-development-external")


status_report = status(cwd=str(ROOT))
require("status ready", status_report["status"], "ready")
require("status user layer", status_report["userFacingLayer"], "Hermes")
require("status cli role", status_report["cliRole"], "debug/test/fixture surface only")
require_in("status route tool", "just_chill.route", status_report["mcpTools"])
require("status bridge enabled", status_report["executionBridge"]["enabled"], True)
require("status bridge mode", status_report["executionBridge"]["mode"], "visible-session-only")
require("status bridge no prompt injection", status_report["executionBridge"]["injectsPromptHere"], False)
assert_boundary("status", status_report)
cases.append("status-contract")

cli_handle = run_json("handle", {"request": "remember that just-chill is a Hermes harness", "summary": "just-chill is a Hermes harness"})
require("CLI handle status", cli_handle["status"], "handled-contract-ready")
require_truthy("CLI memory", cli_handle["memoryPlan"])
assert_boundary("cli-handle", cli_handle)
cases.append("cli-handle-json")

bad_args = subprocess.run(
    [sys.executable, str(HARNESS_SCRIPT), "--operation", "route", "--arguments", "{bad-json}"],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=True,
)
bad_output = json.loads(bad_args.stdout)
require("bad args blocked", bad_output["status"], "blocked")
require_in("bad args reason", "arguments JSON must decode to an object", bad_output["blockedReasons"])
cases.append("cli-malformed-arguments-blocked")

for idx, output in enumerate([
    route_dev,
    memory,
    sensitive,
    registry_memory,
    recall_default,
    recall_allowed,
    recall_malformed,
    recall_deleted,
    handoff,
    consent_visible,
    consent_no_durable,
    consent_scrollback,
    coordinator_blocked,
    coordinator_ready,
    consent_missing,
    consent_bad_bridge,
    handled_dev,
    handled_memory,
    handled_registry_memory,
    handled_memory_blocked,
    handled_external,
    status_report,
    cli_handle,
    bad_output,
], start=1):
    assert_boundary(f"output-{idx}", output)
cases.append("authority-boundary-invariant")

print(f"PASS: {len(cases)} just-chill Hermes harness cases passed")
