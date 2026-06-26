#!/usr/bin/env python3
"""Acceptance checks for just-chill GJC coordinator/delegation consent policy."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from just_chill_bridge import build_bridge_plan
from just_chill_gjc_consent_policy import (
    REQUIRED_MUTATION_CLASSES,
    build_consent_policy_decision,
    parse_mutation_classes,
    validate_consent_policy_decision,
)
from just_chill_router import classify_request

ROOT = Path(__file__).resolve().parents[1]
POLICY_SCRIPT = ROOT / "scripts" / "just_chill_gjc_consent_policy.py"


def require(name: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle: Any, haystack: Any) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


def run_json(argv: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(POLICY_SCRIPT), *argv],
        text=True,
        capture_output=True,
        check=True,
        cwd=ROOT,
    )
    return json.loads(result.stdout)


def surfaces(*, classes: list[str] | None = None, allow: bool = False, coordinator_status: str = "smoke-ok", delegate_available: bool = True, durable: bool = True, scrollback: bool = False) -> dict[str, Any]:
    return {
        "operatorConsent": {
            "allowMutation": allow,
            "source": "test" if allow else "not-provided",
            "requiredPerMutatingCall": True,
        },
        "visibleRoutedSession": {
            "status": "orchestration-plan-ready",
            "scrollbackIsCompletion": scrollback,
            "evidencePolicy": {
                "durableEvidenceRequired": durable,
                "scrollbackIsCompletion": scrollback,
            },
        },
        "coordinatorMcp": {
            "status": coordinator_status,
            "missingTools": [],
            "mutationClassesEnabled": classes or [],
            "mutationClassesRequiredForExecution": REQUIRED_MUTATION_CLASSES,
        },
        "gjcDelegation": {
            "delegateTools": {
                "gjc_delegate_plan": {"availableViaCoordinator": delegate_available},
                "gjc_delegate_execute": {"availableViaCoordinator": delegate_available},
                "gjc_delegate_team": {"availableViaCoordinator": delegate_available},
            }
        },
    }


def plan_for(request: str) -> dict[str, Any]:
    return build_bridge_plan(classify_request(request), cwd=str(ROOT))


cases: list[str] = []

require("parse classes", parse_mutation_classes(" sessions,questions,reports,sessions "), REQUIRED_MUTATION_CLASSES)
cases.append("mutation-class-normalization")

visible_plan = plan_for("fix TypeError in src/hooks/bridge.ts")
visible = build_consent_policy_decision(visible_plan, surfaces=surfaces(), evidence_payload={"kind": "test", "command": ["python3", "scripts/check_just_chill_cli.py"]})
require("visible status", visible["status"], "visible-session-preferred")
require("visible approved mutation", visible["mutationConsentGate"]["approvedForHostMutation"], False)
require("visible first", visible["visibleFirst"]["visibleSessionPreferred"], True)
require("visible no blockers", visible["blockers"], [])
require("visible validation", validate_consent_policy_decision(visible), [])
cases.append("visible-session-first")
unsupported_plan = json.loads(json.dumps(visible_plan))
unsupported_plan["bridgePlan"]["bridgePath"] = "hidden-gjc-worker"
unsupported = build_consent_policy_decision(unsupported_plan, surfaces=surfaces(), evidence_payload={"kind": "test", "command": ["python3", "scripts/check_just_chill_gjc_consent_policy.py"]})
require("unsupported path blocked", unsupported["status"], "mutation-blocked")
require_in("unsupported path reason", "unsupported or non-GJC mutation bridge path 'hidden-gjc-worker'", unsupported["blockers"])
require("unsupported validation", validate_consent_policy_decision(unsupported), [])
cases.append("unsupported-bridge-path-blocked")


coordinator_plan = plan_for("Use coordinator MCP machine control and poll the turn_id artifact state for this repo task")
coordinator_blocked = build_consent_policy_decision(coordinator_plan, surfaces=surfaces())
require("coordinator status blocked", coordinator_blocked["status"], "mutation-blocked")
require_in("coordinator class blocker", "GJC coordinator/delegation mutation requires classes: sessions, questions, reports", coordinator_blocked["blockers"])
require_in("coordinator consent blocker", "GJC coordinator/delegation mutation requires explicit per-call allow_mutation consent", coordinator_blocked["blockers"])
require("coordinator validation", validate_consent_policy_decision(coordinator_blocked), [])
cases.append("coordinator-blocked-without-classes-or-consent")

classes_only = build_consent_policy_decision(coordinator_plan, surfaces=surfaces(classes=REQUIRED_MUTATION_CLASSES))
require("classes only blocked", classes_only["status"], "mutation-blocked")
require("classes only missing", classes_only["mutationConsentGate"]["missingMutationClasses"], [])
require_in("classes only consent blocker", "GJC coordinator/delegation mutation requires explicit per-call allow_mutation consent", classes_only["blockers"])
cases.append("per-call-consent-required")

coordinator_ready = build_consent_policy_decision(
    coordinator_plan,
    surfaces=surfaces(classes=REQUIRED_MUTATION_CLASSES, allow=True),
    allow_mutation=True,
    evidence_payload={"kind": "turn_id", "turn_id": "turn-123"},
)
require("coordinator ready", coordinator_ready["status"], "host-mutation-consent-ready")
require("coordinator approved", coordinator_ready["mutationConsentGate"]["approvedForHostMutation"], True)
require("coordinator blockers", coordinator_ready["blockers"], [])
require("coordinator evidence validated", coordinator_ready["completionEvidenceGate"]["providedEvidenceValidated"], True)
require("coordinator validation", validate_consent_policy_decision(coordinator_ready), [])
cases.append("coordinator-ready-with-classes-consent-evidence")

delegate_plan = plan_for("Execute the approved pending-approval plan with ultragoal")
delegate_ready = build_consent_policy_decision(delegate_plan, surfaces=surfaces(classes=REQUIRED_MUTATION_CLASSES, allow=True), allow_mutation=True)
require("delegate route", delegate_ready["routeHint"], "gjc-ultragoal")
require("delegate ready", delegate_ready["status"], "host-mutation-consent-ready")
require("delegate approved", delegate_ready["mutationConsentGate"]["approvedForHostMutation"], True)
require("delegate validation", validate_consent_policy_decision(delegate_ready), [])
cases.append("delegation-ready-with-tool-classes-consent")

delegate_missing = build_consent_policy_decision(delegate_plan, surfaces=surfaces(classes=REQUIRED_MUTATION_CLASSES, allow=True, delegate_available=False), allow_mutation=True)
require("delegate missing blocked", delegate_missing["status"], "mutation-blocked")
require_in("delegate missing reason", "delegate tool 'gjc_delegate_execute' is not available via coordinator", delegate_missing["blockers"])
cases.append("delegation-tool-required")

coordinator_down = build_consent_policy_decision(coordinator_plan, surfaces=surfaces(classes=REQUIRED_MUTATION_CLASSES, allow=True, coordinator_status="unavailable-or-incomplete"), allow_mutation=True)
require("coordinator down blocked", coordinator_down["status"], "mutation-blocked")
require_in("coordinator smoke blocker", "coordinator MCP smoke check is not clean", coordinator_down["blockers"])
cases.append("coordinator-smoke-required")

scrollback_only = build_consent_policy_decision(
    coordinator_plan,
    surfaces=surfaces(classes=REQUIRED_MUTATION_CLASSES, allow=True),
    allow_mutation=True,
    evidence_payload={"kind": "tmux-scrollback", "description": "looks done from pane"},
)
require("scrollback blocked", scrollback_only["status"], "mutation-blocked")
require_in("scrollback debug blocker", "tmux-scrollback is debug-only and cannot prove completion", scrollback_only["blockers"])
require_in("scrollback durable blocker", "at least one non-scrollback durable evidence signal is required", scrollback_only["blockers"])
cases.append("scrollback-only-rejected")

mixed_evidence = build_consent_policy_decision(
    coordinator_plan,
    surfaces=surfaces(classes=REQUIRED_MUTATION_CLASSES, allow=True),
    allow_mutation=True,
    evidence_payload={"signals": [{"kind": "turn_id", "turn_id": "turn-123"}, {"kind": "scrollback", "description": "debug"}]},
)
require("mixed evidence blocked", mixed_evidence["status"], "mutation-blocked")
require_in("mixed evidence blocker", "scrollback evidence may be kept only as debug context, not as a completion source", mixed_evidence["blockers"])
cases.append("mixed-scrollback-evidence-rejected")

no_durable_policy = build_consent_policy_decision(coordinator_plan, surfaces=surfaces(classes=REQUIRED_MUTATION_CLASSES, allow=True, durable=False), allow_mutation=True)
require("no durable blocked", no_durable_policy["status"], "mutation-blocked")
require_in("no durable blocker", "durable completion evidence is required", no_durable_policy["blockers"])
cases.append("durable-evidence-policy-required")

cli_decision = run_json([
    "--cwd",
    str(ROOT),
    "--allow-mutation",
    "--mutation-classes",
    "sessions,questions,reports",
    "Use coordinator MCP machine control and poll the turn_id artifact state for this repo task",
])
require("CLI no execution", cli_decision["authorityBoundary"]["executionAllowedHere"], False)
require("CLI path", cli_decision["bridgePath"], "coordinator-mcp")
require("CLI consent source", cli_decision["mutationConsentGate"]["consentSource"], "explicit-policy-input")
cases.append("policy-cli-json")

for idx, decision in enumerate([
    visible,
    unsupported,
    coordinator_blocked,
    classes_only,
    coordinator_ready,
    delegate_ready,
    delegate_missing,
    coordinator_down,
    scrollback_only,
    mixed_evidence,
    no_durable_policy,
    cli_decision,
], start=1):
    require(f"decision {idx} execution false", decision["authorityBoundary"]["executionAllowedHere"], False)
    require(f"decision {idx} coordinator false", decision["authorityBoundary"]["justChillCallsCoordinator"], False)
    require(f"decision {idx} delegate false", decision["authorityBoundary"]["justChillCallsDelegateTools"], False)
    require(f"decision {idx} Hermes false", decision["authorityBoundary"]["justChillWritesHermes"], False)
cases.append("authority-boundary-invariant")

print(f"PASS: {len(cases)} just-chill GJC consent policy cases passed")
