#!/usr/bin/env python3
"""Deterministic GJC coordinator/delegation mutation-consent policy for just-chill.

The policy keeps visible routed sessions as the default path and only admits
coordinator/delegation mutation plans when the host has explicitly enabled the
required mutation classes and supplied per-call allow_mutation consent. It never
executes GJC, never calls coordinator/delegate tools, and never accepts tmux
scrollback as completion evidence.
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Any

from just_chill_bridge import build_bridge_plan
from just_chill_live_bindings import discover_live_surfaces
from just_chill_router import classify_request
from just_chill_visible_session_helpers import validate_visible_evidence_payload

SCHEMA_VERSION = 1
POLICY_NAME = "just-chill-gjc-mutation-consent-policy-v1"
REQUIRED_MUTATION_CLASSES = ["sessions", "questions", "reports"]
MUTATING_BRIDGE_PATHS = {"coordinator-mcp", "gjc-delegation"}
VISIBLE_FIRST_DEFAULT = "visible-routed-session"


def parse_mutation_classes(raw: str | list[str] | None) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        parts = raw
    else:
        parts = raw.split(",")
    normalized: list[str] = []
    for part in parts:
        value = str(part).strip()
        if value and value not in normalized:
            normalized.append(value)
    return normalized


def _surfaces_mutation_classes(surfaces: dict[str, Any] | None, mutation_classes: list[str] | None) -> list[str]:
    if mutation_classes is not None:
        return parse_mutation_classes(mutation_classes)
    if surfaces:
        return parse_mutation_classes(surfaces.get("coordinatorMcp", {}).get("mutationClassesEnabled", []))
    return parse_mutation_classes(os.environ.get("GJC_COORDINATOR_MCP_MUTATIONS"))


def _operator_consent(surfaces: dict[str, Any] | None, allow_mutation: bool) -> dict[str, Any]:
    surface_consent = surfaces.get("operatorConsent", {}) if surfaces else {}
    return {
        "allowMutation": bool(allow_mutation or surface_consent.get("allowMutation")),
        "source": "explicit-policy-input" if allow_mutation else surface_consent.get("source", "not-provided"),
        "requiredPerMutatingCall": surface_consent.get("requiredPerMutatingCall", True),
    }


def _coordinator_tools_ready(surfaces: dict[str, Any] | None) -> tuple[bool, list[str]]:
    if not surfaces:
        return False, ["live coordinator surfaces were not supplied"]
    coordinator = surfaces.get("coordinatorMcp", {})
    if coordinator.get("status") != "smoke-ok":
        return False, ["coordinator MCP smoke check is not clean"]
    missing = list(coordinator.get("missingTools", []))
    if missing:
        return False, [f"coordinator MCP is missing required tools: {', '.join(missing)}"]
    return True, []


def _delegate_tool_ready(bridge: dict[str, Any], surfaces: dict[str, Any] | None) -> tuple[bool, list[str]]:
    if bridge.get("bridgePath") != "gjc-delegation":
        return True, []
    delegate_tool = bridge.get("delegateTool")
    if not delegate_tool:
        return False, ["delegation bridge has no delegate tool"]
    if not surfaces:
        return False, ["live delegation surfaces were not supplied"]
    delegate_status = surfaces.get("gjcDelegation", {}).get("delegateTools", {}).get(delegate_tool, {})
    if delegate_status.get("availableViaCoordinator") is not True:
        return False, [f"delegate tool {delegate_tool!r} is not available via coordinator"]
    return True, []


def _durable_evidence_policy(bridge_plan: dict[str, Any], surfaces: dict[str, Any] | None) -> dict[str, Any]:
    evidence_required = list(bridge_plan.get("completionEvidenceRequired", []))
    forbidden = list(bridge_plan.get("forbiddenActions", []))
    visible = surfaces.get("visibleRoutedSession", {}) if surfaces else {}
    evidence_policy = visible.get("evidencePolicy", {})
    durable_required = bool(evidence_required) and evidence_policy.get("durableEvidenceRequired", True) is True
    scrollback_rejected = (
        any("scrollback" in str(item).lower() for item in forbidden + evidence_required)
        and visible.get("scrollbackIsCompletion", False) is False
        and evidence_policy.get("scrollbackIsCompletion", False) is False
    )
    return {
        "durableEvidenceRequired": durable_required,
        "scrollbackIsCompletion": False,
        "scrollbackRejected": scrollback_rejected,
        "completionEvidenceRequired": evidence_required,
        "forbiddenActions": forbidden,
    }


def build_consent_policy_decision(
    bridge_plan: dict[str, Any],
    *,
    surfaces: dict[str, Any] | None = None,
    allow_mutation: bool = False,
    mutation_classes: list[str] | None = None,
    evidence_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bridge = bridge_plan.get("bridgePlan", {})
    path = bridge.get("bridgePath")
    is_mutating_path = path in MUTATING_BRIDGE_PATHS
    consent = _operator_consent(surfaces, allow_mutation)
    enabled_classes = _surfaces_mutation_classes(surfaces, mutation_classes)
    class_set = set(enabled_classes)
    required_set = set(REQUIRED_MUTATION_CLASSES)
    missing_classes = [name for name in REQUIRED_MUTATION_CLASSES if name not in class_set]
    blockers: list[str] = []

    coordinator_ready, coordinator_issues = _coordinator_tools_ready(surfaces)
    delegate_ready, delegate_issues = _delegate_tool_ready(bridge, surfaces)
    evidence_policy = _durable_evidence_policy(bridge_plan, surfaces)
    evidence_issues = validate_visible_evidence_payload(evidence_payload) if evidence_payload is not None else []

    if bridge.get("executionAllowedHere") is not False:
        blockers.append("bridge plan must keep executionAllowedHere false")
    if bridge_plan.get("authorityBoundary", {}).get("noExecutionInThisPlan") is not True:
        blockers.append("bridge plan must preserve noExecutionInThisPlan")
    if not evidence_policy["durableEvidenceRequired"]:
        blockers.append("durable completion evidence is required")
    if not evidence_policy["scrollbackRejected"]:
        blockers.append("tmux scrollback must be explicitly rejected as completion evidence")
    if evidence_issues:
        blockers.extend(evidence_issues)

    if is_mutating_path:
        blockers.extend(coordinator_issues)
        blockers.extend(delegate_issues)
        if missing_classes:
            blockers.append(f"GJC coordinator/delegation mutation requires classes: {', '.join(REQUIRED_MUTATION_CLASSES)}")
        if consent["allowMutation"] is not True:
            blockers.append("GJC coordinator/delegation mutation requires explicit per-call allow_mutation consent")
        if consent["requiredPerMutatingCall"] is not True:
            blockers.append("per-call mutation consent must remain required")
    elif path == VISIBLE_FIRST_DEFAULT:
        pass
    else:
        blockers.append(f"unsupported or non-GJC mutation bridge path {path!r}")

    mutation_ready = is_mutating_path and not blockers and coordinator_ready and delegate_ready and required_set.issubset(class_set) and consent["allowMutation"] is True
    if path == VISIBLE_FIRST_DEFAULT and not blockers:
        status = "visible-session-preferred"
    elif mutation_ready:
        status = "host-mutation-consent-ready"
    else:
        status = "mutation-blocked"

    return {
        "schemaVersion": SCHEMA_VERSION,
        "policy": POLICY_NAME,
        "status": status,
        "bridgePath": path,
        "routeHint": bridge_plan.get("developmentHandoff", {}).get("routeHint"),
        "authorityBoundary": {
            "executionAllowedHere": False,
            "justChillExecutesGjc": False,
            "justChillCallsCoordinator": False,
            "justChillCallsDelegateTools": False,
            "justChillWritesHermes": False,
        },
        "visibleFirst": {
            "defaultBridgePath": VISIBLE_FIRST_DEFAULT,
            "selectedBridgePath": path,
            "visibleSessionPreferred": path == VISIBLE_FIRST_DEFAULT,
            "mutationBridgeRequiresJustification": is_mutating_path,
            "justification": "router selected a machine-control or whole-workflow GJC bridge path" if is_mutating_path else "visible routed session is the default path",
        },
        "mutationConsentGate": {
            "mutatingBridgePath": is_mutating_path,
            "approvedForHostMutation": mutation_ready,
            "allowMutation": consent["allowMutation"],
            "consentSource": consent["source"],
            "requiredMutationClasses": REQUIRED_MUTATION_CLASSES,
            "enabledMutationClasses": enabled_classes,
            "missingMutationClasses": missing_classes,
            "perCallConsentRequired": consent["requiredPerMutatingCall"],
            "coordinatorReady": coordinator_ready,
            "delegateReady": delegate_ready,
        },
        "completionEvidenceGate": {
            **evidence_policy,
            "providedEvidenceValidated": evidence_payload is not None and not evidence_issues,
            "providedEvidenceIssues": evidence_issues,
        },
        "blockers": blockers,
    }


def validate_consent_policy_decision(decision: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if decision.get("schemaVersion") != SCHEMA_VERSION:
        issues.append("schemaVersion mismatch")
    if decision.get("policy") != POLICY_NAME:
        issues.append("policy name mismatch")
    boundary = decision.get("authorityBoundary", {})
    for key in ["executionAllowedHere", "justChillExecutesGjc", "justChillCallsCoordinator", "justChillCallsDelegateTools", "justChillWritesHermes"]:
        if boundary.get(key) is not False:
            issues.append(f"authority boundary must keep {key} false")
    if decision.get("completionEvidenceGate", {}).get("scrollbackIsCompletion") is not False:
        issues.append("scrollback cannot be completion evidence")
    gate = decision.get("mutationConsentGate", {})
    if gate.get("approvedForHostMutation"):
        if decision.get("blockers"):
            issues.append("approved mutation decisions must have no blockers")
        if gate.get("allowMutation") is not True:
            issues.append("approved mutation decisions require allowMutation true")
        if gate.get("missingMutationClasses"):
            issues.append("approved mutation decisions require all mutation classes")
        if gate.get("perCallConsentRequired") is not True:
            issues.append("per-call consent must remain required")
    if decision.get("status") == "visible-session-preferred" and decision.get("bridgePath") != VISIBLE_FIRST_DEFAULT:
        issues.append("visible-session-preferred status requires visible bridge path")
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate just-chill GJC coordinator/delegation mutation consent without executing it.")
    parser.add_argument("request", nargs="*", help="Request text; ignored when --bridge-plan-json is supplied.")
    parser.add_argument("--bridge-plan-json", help="Existing bridge plan JSON.")
    parser.add_argument("--cwd", default=None, help="Repo/workdir for optional read-only live discovery.")
    parser.add_argument("--probe", action="store_true", help="Run allowlisted read-only discovery probes.")
    parser.add_argument("--allow-mutation", action="store_true", help="Record explicit per-call allow_mutation consent; does not execute anything.")
    parser.add_argument("--mutation-classes", help="Comma-separated enabled coordinator mutation classes for deterministic evaluation.")
    parser.add_argument("--evidence-json", help="Optional completion evidence JSON to validate against durable evidence policy.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.bridge_plan_json:
        bridge_plan = json.loads(args.bridge_plan_json)
    else:
        packet = classify_request(" ".join(args.request))
        bridge_plan = build_bridge_plan(packet, cwd=args.cwd)
    surfaces = discover_live_surfaces(cwd=args.cwd, probe=args.probe)
    evidence = json.loads(args.evidence_json) if args.evidence_json else None
    decision = build_consent_policy_decision(
        bridge_plan,
        surfaces=surfaces,
        allow_mutation=args.allow_mutation,
        mutation_classes=parse_mutation_classes(args.mutation_classes),
        evidence_payload=evidence,
    )
    print(json.dumps(decision, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
