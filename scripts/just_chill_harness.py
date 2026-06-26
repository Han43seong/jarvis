#!/usr/bin/env python3
"""Hermes-facing just-chill harness adapter.

Hermes is the user-facing agent. This module is the policy/routing/memory/GJC
handoff harness Hermes can call before it chooses a host-owned tool. It composes
existing just-chill contracts and deliberately does not execute GJC, write
Hermes memory, run SHACL, or search vector stores.
"""
from __future__ import annotations

import argparse
import json
from typing import Any

from just_chill_cli import handoff_gjc_command, recall_command, remember_command, route_command
from just_chill_gjc_consent_policy import build_consent_policy_decision, parse_mutation_classes, validate_consent_policy_decision
from just_chill_live_bindings import discover_live_surfaces

SCHEMA_VERSION = 1
HARNESS_NAME = "just-chill-hermes-harness-v1"
DEFAULT_CALLER = "hermes"

OP_ROUTE = "route"
OP_REMEMBER = "remember.plan"
OP_RECALL = "recall.gate"
OP_GJC_HANDOFF = "gjc_handoff.plan"
OP_CONSENT = "consent.evaluate"
OP_HANDLE = "handle"
OP_STATUS = "status"
OPERATIONS = [OP_ROUTE, OP_REMEMBER, OP_RECALL, OP_GJC_HANDOFF, OP_CONSENT, OP_HANDLE, OP_STATUS]
VISIBLE_SESSION_ONLY_EXECUTION_BRIDGE = {
    "enabled": True,
    "mode": "visible-session-only",
    "bridge": "scripts/just_chill_gjc_execution_bridge.py",
    "hostOwned": True,
    "startsGjcHere": False,
    "injectsPromptHere": False,
    "coordinatorDelegateAutoMutation": False,
    "requiresDurableEvidence": True,
    "scrollbackAcceptedAsCompletion": False,
}



class HarnessInputError(ValueError):
    """Fail-closed host input error."""


def json_text(data: Any, *, pretty: bool = False) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2 if pretty else None, sort_keys=True)


def authority_boundary() -> dict[str, Any]:
    return {
        "executionAllowedHere": False,
        "justChillExecutesGjc": False,
        "justChillWritesHermes": False,
        "justChillOwnsCanonicalMemory": False,
        "justChillRunsShaclEngine": False,
        "justChillSearchesVectorStore": False,
        "justChillCallsCoordinator": False,
        "justChillCallsDelegateTools": False,
        "hostOwnedToolsMayExecuteLater": True,
    }


def base_envelope(operation: str, *, caller: str = DEFAULT_CALLER, request_id: str | None = None) -> dict[str, Any]:
    envelope = {
        "schemaVersion": SCHEMA_VERSION,
        "harness": HARNESS_NAME,
        "operation": operation,
        "caller": caller,
        "authorityBoundary": authority_boundary(),
        "executionAllowedHere": False,
    }
    if request_id is not None:
        envelope["requestId"] = request_id
    return envelope




def _json_object_or_issue(raw_json: str | None, label: str) -> tuple[dict[str, Any] | None, str | None]:
    if raw_json is None:
        return None, None
    try:
        decoded = json.loads(raw_json)
    except json.JSONDecodeError:
        return None, f"{label} JSON must decode to an object"
    if not isinstance(decoded, dict):
        return None, f"{label} JSON must decode to an object"
    return decoded, None


def _object_or_issue(value: Any, label: str) -> tuple[dict[str, Any] | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, dict):
        return value, None
    if isinstance(value, str):
        return _json_object_or_issue(value, label)
    return None, f"{label} must be an object"


def blocked(operation: str, reasons: list[str], *, caller: str = DEFAULT_CALLER, request_id: str | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    output = base_envelope(operation, caller=caller, request_id=request_id)
    output.update({"status": "blocked", "blockedReasons": reasons})
    if payload:
        output.update(payload)
    return output


def route(request: str, *, cwd: str | None = None, include_bridge: bool = True, caller: str = DEFAULT_CALLER, request_id: str | None = None) -> dict[str, Any]:
    routed = route_command(request, cwd=cwd, include_bridge=include_bridge)
    output = base_envelope(OP_ROUTE, caller=caller, request_id=request_id)
    output.update({
        "status": routed.get("status", "route-ready"),
        "request": request,
        "routerPacket": routed.get("routerPacket"),
        "nextStep": routed.get("nextStep"),
        "bridgePlan": routed.get("bridgePlan"),
        "hostOwnedNextSteps": [
            "Hermes decides whether to call memory tools, external tools, or a host-owned GJC bridge",
            "just-chill output is policy and contract evidence only",
        ],
    })
    return output


def remember_plan(
    request: str,
    *,
    summary: str | None = None,
    approval_token: str | None = None,
    approval_registry: str | None = None,
    approval_scope: str = "memory.write",
    approval_subject: str | None = None,
    source_channel: str = "hermes:just-chill-harness",
    caller: str = DEFAULT_CALLER,
    request_id: str | None = None,
) -> dict[str, Any]:
    plan = remember_command(
        request,
        summary=summary,
        approval_token=approval_token,
        source_channel=source_channel,
        approval_registry=approval_registry,
        approval_scope=approval_scope,
        approval_subject=approval_subject,
    )
    output = base_envelope(OP_REMEMBER, caller=caller, request_id=request_id)
    output.update({
        "status": plan.get("status"),
        "request": request,
        "routerPacket": plan.get("routerPacket"),
        "rawArtifactContract": plan.get("rawArtifactContract"),
        "summaryMemoryContract": plan.get("summaryMemoryContract"),
        "approvalTokenPresent": plan.get("approvalTokenPresent", False),
        "approvalTokenAccepted": plan.get("approvalTokenAccepted", False),
        "approvalVerification": plan.get("approvalVerification"),
        "blockedReasons": list(plan.get("blockedReasons", [])),
        "hostOwnedNextSteps": list(plan.get("hostOwnedNextSteps", [])),
    })
    return output


def recall_gate(
    query: str,
    *,
    cwd: str | None = None,
    candidate: dict[str, Any] | str | None = None,
    retrieval_evidence: dict[str, Any] | str | None = None,
    current_source_hash: str | None = None,
    current_deletion_state: str | None = None,
    current_redaction_state: str | None = None,
    approval_token: str | None = None,
    approval_registry: str | None = None,
    approval_scope: str = "memory.recall",
    approval_subject: str | None = None,
    probe: bool = False,
    caller: str = DEFAULT_CALLER,
    request_id: str | None = None,
) -> dict[str, Any]:
    candidate_obj, candidate_issue = _object_or_issue(candidate, "candidate")
    evidence_obj, evidence_issue = _object_or_issue(retrieval_evidence, "retrieval evidence")
    json_issues = [issue for issue in [candidate_issue, evidence_issue] if issue]
    if json_issues:
        return blocked(OP_RECALL, json_issues, caller=caller, request_id=request_id, payload={"query": query})
    plan = recall_command(
        query,
        cwd=cwd,
        candidate_json=json.dumps(candidate_obj, ensure_ascii=False, sort_keys=True) if candidate_obj is not None else None,
        retrieval_evidence_json=json.dumps(evidence_obj, ensure_ascii=False, sort_keys=True) if evidence_obj is not None else None,
        current_source_hash=current_source_hash,
        current_deletion_state=current_deletion_state,
        current_redaction_state=current_redaction_state,
        approval_token=approval_token,
        approval_registry=approval_registry,
        approval_scope=approval_scope,
        approval_subject=approval_subject,
        probe=probe,
    )
    output = base_envelope(OP_RECALL, caller=caller, request_id=request_id)
    output.update({
        "status": plan.get("status"),
        "query": query,
        "vectorBoundary": plan.get("vectorBoundary"),
        "approvalTokenPresent": plan.get("approvalTokenPresent", False),
        "approvalTokenAccepted": plan.get("approvalTokenAccepted", False),
        "approvalVerification": plan.get("approvalVerification"),
        "blockedReasons": list(plan.get("blockedReasons", [])),
        "recallGateDecision": plan.get("recallGateDecision"),
        "hostOwnedNextSteps": list(plan.get("hostOwnedNextSteps", [])),
    })
    return output


def gjc_handoff_plan(
    request: str,
    *,
    cwd: str | None = None,
    allow_mutation: bool = False,
    caller: str = DEFAULT_CALLER,
    request_id: str | None = None,
) -> dict[str, Any]:
    handoff = handoff_gjc_command(request, cwd=cwd, allow_mutation=allow_mutation)
    output = base_envelope(OP_GJC_HANDOFF, caller=caller, request_id=request_id)
    output.update({
        "status": handoff.get("status"),
        "request": request,
        "routerPacket": handoff.get("routerPacket"),
        "mutationConsent": handoff.get("mutationConsent"),
        "blockedReasons": list(handoff.get("blockedReasons", [])),
        "bridgePlan": handoff.get("bridgePlan"),
        "operatorReminder": list(handoff.get("operatorReminder", [])),
    })
    return output


def consent_evaluate(
    *,
    bridge_plan: dict[str, Any] | str | None = None,
    request: str | None = None,
    surfaces: dict[str, Any] | str | None = None,
    allow_mutation: bool = False,
    mutation_classes: list[str] | str | None = None,
    evidence_payload: dict[str, Any] | str | None = None,
    cwd: str | None = None,
    probe: bool = False,
    caller: str = DEFAULT_CALLER,
    request_id: str | None = None,
) -> dict[str, Any]:
    bridge_obj, bridge_issue = _object_or_issue(bridge_plan, "bridge plan")
    surfaces_obj, surfaces_issue = _object_or_issue(surfaces, "surfaces")
    evidence_obj, evidence_issue = _object_or_issue(evidence_payload, "evidence")
    issues = [issue for issue in [bridge_issue, surfaces_issue, evidence_issue] if issue]
    if issues:
        return blocked(OP_CONSENT, issues, caller=caller, request_id=request_id)
    if bridge_obj is None:
        if not request:
            return blocked(OP_CONSENT, ["request or bridge plan is required"], caller=caller, request_id=request_id)
        handoff = handoff_gjc_command(request, cwd=cwd, allow_mutation=allow_mutation)
        bridge_obj = handoff.get("bridgePlan")
        if bridge_obj is None:
            return blocked(OP_CONSENT, list(handoff.get("blockedReasons", ["GJC bridge plan is unavailable"])), caller=caller, request_id=request_id, payload={"request": request})
    if surfaces_obj is None:
        surfaces_obj = discover_live_surfaces(cwd=cwd, probe=probe)
    classes = parse_mutation_classes(mutation_classes)
    decision = build_consent_policy_decision(
        bridge_obj,
        surfaces=surfaces_obj,
        allow_mutation=allow_mutation,
        mutation_classes=classes,
        evidence_payload=evidence_obj,
    )
    validation_issues = validate_consent_policy_decision(decision)
    output = base_envelope(OP_CONSENT, caller=caller, request_id=request_id)
    status_value = "blocked" if validation_issues else decision.get("status")
    output.update({
        "status": status_value,
        "request": request,
        "consentPolicyDecision": decision,
        "validationIssues": validation_issues,
        "blockedReasons": list(decision.get("blockers", [])) + validation_issues,
    })
    return output


def status(*, cwd: str | None = None, probe: bool = False, caller: str = DEFAULT_CALLER, request_id: str | None = None) -> dict[str, Any]:
    surfaces = discover_live_surfaces(cwd=cwd, probe=probe)
    output = base_envelope(OP_STATUS, caller=caller, request_id=request_id)
    output.update({
        "status": "ready",
        "entrypointRole": "Hermes-facing harness adapter",
        "userFacingLayer": "Hermes",
        "cliRole": "debug/test/fixture surface only",
        "operations": OPERATIONS,
        "mcpTools": [
            "just_chill.route",
            "just_chill.remember.plan",
            "just_chill.recall.gate",
            "just_chill.gjc_handoff.plan",
            "just_chill.consent.evaluate",
            "just_chill.handle",
            "just_chill.status",
        ],
        "executionBridge": VISIBLE_SESSION_ONLY_EXECUTION_BRIDGE,
        "liveSurfaces": surfaces,
        "registration": {
            "hermesMcpRegistrationRequired": True,
            "registeredByThisHarness": False,
            "requiresExplicitApproval": True,
        },
    })
    return output


def handle(
    request: str,
    *,
    cwd: str | None = None,
    summary: str | None = None,
    approval_token: str | None = None,
    approval_registry: str | None = None,
    approval_scope: str = "memory.write",
    approval_subject: str | None = None,
    allow_mutation: bool = False,
    mutation_classes: list[str] | str | None = None,
    evidence_payload: dict[str, Any] | str | None = None,
    probe: bool = False,
    caller: str = DEFAULT_CALLER,
    request_id: str | None = None,
) -> dict[str, Any]:
    routed = route(request, cwd=cwd, include_bridge=True, caller=caller, request_id=request_id)
    output = base_envelope(OP_HANDLE, caller=caller, request_id=request_id)
    output.update({
        "status": "handled-contract-ready",
        "request": request,
        "route": routed,
        "memoryPlan": None,
        "gjcHandoffPlan": None,
        "consentEvaluation": None,
        "hostOwnedNextSteps": [],
        "blockedReasons": [],
    })
    packet = routed.get("routerPacket") or {}
    classification = packet.get("classification", {})
    if classification.get("isDevelopment") is True:
        handoff = gjc_handoff_plan(request, cwd=cwd, allow_mutation=allow_mutation, caller=caller, request_id=request_id)
        output["gjcHandoffPlan"] = handoff
        if handoff.get("bridgePlan"):
            output["consentEvaluation"] = consent_evaluate(
                bridge_plan=handoff["bridgePlan"],
                allow_mutation=allow_mutation,
                mutation_classes=mutation_classes,
                evidence_payload=evidence_payload,
                cwd=cwd,
                probe=probe,
                caller=caller,
                request_id=request_id,
            )
        output["hostOwnedNextSteps"].extend([
            "Hermes or a host bridge may prepare visible-session-only execution through scripts/just_chill_gjc_execution_bridge.py",
            "Mutating coordinator/delegation paths remain disabled unless consentEvaluation is host-mutation-consent-ready",
        ])
    elif classification.get("category") == "memory":
        memory = remember_plan(
            request,
            summary=summary,
            approval_token=approval_token,
            approval_registry=approval_registry,
            approval_scope=approval_scope,
            approval_subject=approval_subject,
            caller=caller,
            request_id=request_id,
        )
        output["memoryPlan"] = memory
        output["blockedReasons"].extend(memory.get("blockedReasons", []))
        output["hostOwnedNextSteps"].extend([
            "Hermes may persist only through host-owned memory tools after approval and read-back evidence",
            "just-chill memoryPlan is not a write operation",
        ])
        if memory.get("status") != "memory-candidate-ready":
            output["status"] = "handled-contract-blocked"
    else:
        output["hostOwnedNextSteps"].append("Hermes should route to the appropriate non-development external tool or direct response lane")
    return output


def call_operation(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    args = arguments or {}
    if name == OP_ROUTE:
        return route(str(args.get("request", "")), cwd=args.get("cwd"), include_bridge=bool(args.get("includeBridge", True)), caller=args.get("caller", DEFAULT_CALLER), request_id=args.get("requestId"))
    if name == OP_REMEMBER:
        return remember_plan(
            str(args.get("request", "")),
            summary=args.get("summary"),
            approval_token=args.get("approvalToken"),
            source_channel=args.get("sourceChannel", "hermes:just-chill-harness"),
            approval_registry=args.get("approvalRegistry"),
            approval_scope=args.get("approvalScope", "memory.write"),
            approval_subject=args.get("approvalSubject"),
            caller=args.get("caller", DEFAULT_CALLER),
            request_id=args.get("requestId"),
        )
    if name == OP_RECALL:
        return recall_gate(
            str(args.get("query", "")),
            cwd=args.get("cwd"),
            candidate=args.get("candidate"),
            retrieval_evidence=args.get("retrievalEvidence"),
            current_source_hash=args.get("currentSourceHash"),
            current_deletion_state=args.get("currentDeletionState"),
            current_redaction_state=args.get("currentRedactionState"),
            approval_token=args.get("approvalToken"),
            approval_registry=args.get("approvalRegistry"),
            approval_scope=args.get("approvalScope", "memory.recall"),
            approval_subject=args.get("approvalSubject"),
            probe=bool(args.get("probe", False)),
            caller=args.get("caller", DEFAULT_CALLER),
            request_id=args.get("requestId"),
        )
    if name == OP_GJC_HANDOFF:
        return gjc_handoff_plan(str(args.get("request", "")), cwd=args.get("cwd"), allow_mutation=bool(args.get("allowMutation", False)), caller=args.get("caller", DEFAULT_CALLER), request_id=args.get("requestId"))
    if name == OP_CONSENT:
        return consent_evaluate(
            bridge_plan=args.get("bridgePlan"),
            request=args.get("request"),
            surfaces=args.get("surfaces"),
            allow_mutation=bool(args.get("allowMutation", False)),
            mutation_classes=args.get("mutationClasses"),
            evidence_payload=args.get("evidencePayload"),
            cwd=args.get("cwd"),
            probe=bool(args.get("probe", False)),
            caller=args.get("caller", DEFAULT_CALLER),
            request_id=args.get("requestId"),
        )
    if name == OP_HANDLE:
        return handle(
            str(args.get("request", "")),
            cwd=args.get("cwd"),
            summary=args.get("summary"),
            approval_token=args.get("approvalToken"),
            approval_registry=args.get("approvalRegistry"),
            approval_scope=args.get("approvalScope", "memory.write"),
            approval_subject=args.get("approvalSubject"),
            allow_mutation=bool(args.get("allowMutation", False)),
            mutation_classes=args.get("mutationClasses"),
            evidence_payload=args.get("evidencePayload"),
            probe=bool(args.get("probe", False)),
            caller=args.get("caller", DEFAULT_CALLER),
            request_id=args.get("requestId"),
        )
    if name == OP_STATUS:
        return status(cwd=args.get("cwd"), probe=bool(args.get("probe", False)), caller=args.get("caller", DEFAULT_CALLER), request_id=args.get("requestId"))
    raise HarnessInputError(f"unknown harness operation: {name}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes-facing just-chill harness adapter; emits contracts without executing them.")
    parser.add_argument("--operation", choices=OPERATIONS, default=OP_HANDLE)
    parser.add_argument("--arguments", default="{}", help="JSON object arguments for the selected operation.")
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    parsed, issue = _json_object_or_issue(args.arguments, "arguments")
    if issue:
        output = blocked(args.operation, [issue])
    else:
        try:
            output = call_operation(args.operation, parsed)
        except Exception as exc:
            output = blocked(args.operation, [str(exc)])
    print(json_text(output, pretty=args.pretty))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
