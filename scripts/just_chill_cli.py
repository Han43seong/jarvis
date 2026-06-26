#!/usr/bin/env python3
"""Safe user-facing CLI contracts for just-chill.

The CLI composes the existing router, GJC bridge, memory contract, and recall
contract modules. It never executes GJC, never writes Hermes memory, and never
claims canonical memory promotion. Host-owned tools may consume its JSON output
later under explicit approval and evidence gates.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from just_chill_approval_registry import ENV_REGISTRY_PATH, token_shape_valid, verify_approval
from just_chill_bridge import build_bridge_plan
from just_chill_memory_contracts import build_raw_artifact_record, build_summary_memory_record, validate_contract_record
from just_chill_router import classify_request
from just_chill_vector_recall import build_recall_gate_decision, build_vector_boundary_report, validate_recall_gate_decision

SCHEMA_VERSION = 1
CLI_NAME = "just-chill-cli-contract-v1"
APPROVAL_TOKEN_PREFIXES = ("approval://", "host-approval://", "hermes-approval://")


def json_text(data: Any, *, pretty: bool = False) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2 if pretty else None, sort_keys=True)


def read_text_arg(parts: list[str], *, stdin_if_empty: bool = True) -> str:
    if parts:
        return " ".join(parts).strip()
    if stdin_if_empty:
        return sys.stdin.read().strip()
    return ""



def approval_token_check(
    token: str | None,
    *,
    registry_path: str | None = None,
    scope: str,
    subject: str | None = None,
) -> dict[str, Any]:
    """Validate approval tokens.

    Without a configured registry this preserves legacy shape-only acceptance for
    local fixtures. With a registry path or JUST_CHILL_APPROVAL_REGISTRY it
    requires an active, scope/subject-matching registry record.
    """
    configured_registry = registry_path or os.environ.get(ENV_REGISTRY_PATH)
    shape_valid = token_shape_valid(token)
    if not configured_registry:
        return {
            "status": "shape-only-accepted" if shape_valid else "approval-denied",
            "approved": shape_valid,
            "mode": "shape-only",
            "tokenPresent": bool(token),
            "tokenShapeValid": shape_valid,
            "registryPath": None,
            "blockedReasons": [] if shape_valid or not token else ["approval token must be a host approval reference"],
        }
    return {
        **verify_approval(token=token, scope=scope, subject=subject, registry=configured_registry),
        "mode": "registry",
    }


def approval_token_is_valid(token: str | None) -> bool:
    return approval_token_check(token, scope="shape-only")["approved"]

def base_envelope(command: str) -> dict[str, Any]:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "cli": CLI_NAME,
        "command": command,
        "authorityBoundary": {
            "justChillExecutesGjc": False,
            "justChillWritesHermes": False,
            "justChillOwnsCanonicalMemory": False,
            "hostOwnedToolsMayExecuteLater": True,
        },
        "executionAllowedHere": False,
    }


def route_command(request: str, *, cwd: str | None = None, include_bridge: bool = False) -> dict[str, Any]:
    packet = classify_request(request)
    output = base_envelope("route")
    output.update({
        "request": request,
        "routerPacket": packet,
        "status": "route-ready",
        "nextStep": "handoff-gjc" if packet["classification"]["isDevelopment"] else "remember/recall/non-development-tool",
    })
    if include_bridge:
        output["bridgePlan"] = build_bridge_plan(packet, cwd=cwd)
    return output


def handoff_gjc_command(request: str, *, cwd: str | None = None, allow_mutation: bool = False) -> dict[str, Any]:
    packet = classify_request(request)
    output = base_envelope("handoff-gjc")
    output["request"] = request
    output["routerPacket"] = packet
    output["mutationConsent"] = {
        "allowMutationRequested": allow_mutation,
        "allowedHere": False,
        "reason": "just-chill prepares a GJC handoff contract only; GJC/operator-owned execution happens later",
    }
    if not packet["classification"]["isDevelopment"]:
        output["status"] = "handoff-blocked"
        output["blockedReasons"] = ["request is not classified as development work"]
        output["bridgePlan"] = None
        return output
    plan = build_bridge_plan(packet, cwd=cwd)
    output["status"] = "handoff-plan-ready"
    output["blockedReasons"] = []
    output["bridgePlan"] = plan
    output["operatorReminder"] = [
        "start with a visible GJC routed session when possible",
        "do not treat tmux scrollback as completion evidence",
        "mutating coordinator/delegation calls require separate host-owned consent",
    ]
    return output


def remember_command(
    request: str,
    *,
    summary: str | None = None,
    approval_token: str | None = None,
    source_channel: str = "just-chill-cli",
    approval_registry: str | None = None,
    approval_scope: str = "memory.write",
    approval_subject: str | None = None,
) -> dict[str, Any]:
    packet = classify_request(request)
    token_check = approval_token_check(
        approval_token,
        registry_path=approval_registry,
        scope=approval_scope,
        subject=approval_subject or request,
    )
    token_valid = bool(token_check["approved"])
    raw = build_raw_artifact_record(packet, content=request, artifact_type="user_memory_candidate", source_channel=source_channel)
    raw_issues = validate_contract_record(raw)
    output = base_envelope("remember")
    output.update({
        "request": request,
        "routerPacket": packet,
        "rawArtifactContract": raw,
        "summaryMemoryContract": None,
        "approvalTokenPresent": bool(approval_token),
        "approvalTokenAccepted": token_valid,
        "approvalVerification": token_check,
        "blockedReasons": list(raw_issues),
        "hostOwnedNextSteps": [
            "review candidate sensitivity and retention policy",
            "write through Hermes only via host-owned MCP tools or provider receipts",
            "preserve raw artifact provenance and read-back hashes before canonical promotion",
        ],
    })
    if summary is not None:
        summary_record = build_summary_memory_record(raw, summary)
        summary_issues = validate_contract_record(summary_record)
        output["summaryMemoryContract"] = summary_record
        output["blockedReasons"].extend(summary_issues)
    if approval_token and not token_valid:
        output["blockedReasons"].extend(token_check.get("blockedReasons", []))
    sensitivity = raw["artifact"].get("sensitivity")
    if sensitivity == "sensitive" and not token_valid:
        output["blockedReasons"].append("sensitive memory requires explicit approval before host-owned persistence")
    if packet["classification"].get("approvalRequired") and not token_valid:
        output["blockedReasons"].append("route approval gate requires explicit approval before host-owned persistence")
    output["status"] = "memory-candidate-blocked" if output["blockedReasons"] else "memory-candidate-ready"
    return output

def _json_object_or_issue(raw_json: str, label: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        decoded = json.loads(raw_json)
    except json.JSONDecodeError:
        return None, f"{label} JSON must decode to an object"
    if not isinstance(decoded, dict):
        return None, f"{label} JSON must decode to an object"
    return decoded, None



def recall_command(
    query: str,
    *,
    cwd: str | None = None,
    candidate_json: str | None = None,
    retrieval_evidence_json: str | None = None,
    current_source_hash: str | None = None,
    current_deletion_state: str | None = None,
    current_redaction_state: str | None = None,
    approval_token: str | None = None,
    approval_registry: str | None = None,
    approval_scope: str = "memory.recall",
    approval_subject: str | None = None,
    probe: bool = False,
) -> dict[str, Any]:
    output = base_envelope("recall")
    token_check = approval_token_check(
        approval_token,
        registry_path=approval_registry,
        scope=approval_scope,
        subject=approval_subject or query,
    )
    token_valid = bool(token_check["approved"])
    token_issues = list(token_check.get("blockedReasons", [])) if approval_token and not token_valid else []
    boundary = build_vector_boundary_report(cwd=cwd, probe=probe)
    output.update({
        "query": query,
        "vectorBoundary": boundary,
        "approvalTokenPresent": bool(approval_token),
        "approvalTokenAccepted": token_valid,
        "approvalVerification": token_check,
        "status": "host-retrieval-required",
        "blockedReasons": ["host-owned retrieval evidence is required before recall enters context", *token_issues],
        "recallGateDecision": None,
        "hostOwnedNextSteps": [
            "run host-owned vector search/read through Hermes sidecar tools",
            "provide candidate JSON, retrieval evidence, and fresh canonical source hash/deletion/redaction state",
            "do not inject provider search output directly into context",
        ],
    })
    if token_issues and not (candidate_json or retrieval_evidence_json):
        output["status"] = "recall-blocked"
    if candidate_json or retrieval_evidence_json:
        if not candidate_json or not retrieval_evidence_json:
            output["status"] = "recall-blocked"
            output["blockedReasons"].append("candidate JSON and retrieval evidence JSON must be supplied together")
            return output
        candidate, candidate_issue = _json_object_or_issue(candidate_json, "candidate")
        evidence, evidence_issue = _json_object_or_issue(retrieval_evidence_json, "retrieval evidence")
        json_issues = [issue for issue in [candidate_issue, evidence_issue] if issue]
        if json_issues:
            output["status"] = "recall-blocked"
            output["blockedReasons"] = json_issues + token_issues
            return output
        approval = approval_token if token_valid else None
        decision = build_recall_gate_decision(
            candidate,
            evidence,
            approval_token=approval,
            current_source_hash=current_source_hash,
            current_deletion_state=current_deletion_state,
            current_redaction_state=current_redaction_state,
        )
        issues = validate_recall_gate_decision(decision)
        output["recallGateDecision"] = decision
        output["blockedReasons"] = list(decision.get("blockedReasons", [])) + issues + token_issues
        output["status"] = "recall-allowed" if decision.get("allowRecall") and not issues and not token_issues else "recall-blocked"
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build safe just-chill route/memory/recall/GJC handoff contracts without executing them.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    sub = parser.add_subparsers(dest="command", required=True)

    route = sub.add_parser("route", help="Classify a request and optionally include a bridge plan.")
    route.add_argument("request", nargs="*", help="Request text; stdin is used when omitted.")
    route.add_argument("--cwd", default=None, help="Target workdir for optional bridge planning.")
    route.add_argument("--include-bridge", action="store_true", help="Include the non-executing bridge plan.")

    handoff = sub.add_parser("handoff-gjc", help="Build a GJC handoff plan for development requests.")
    handoff.add_argument("request", nargs="*", help="Request text; stdin is used when omitted.")
    handoff.add_argument("--cwd", default=None, help="Target workdir for handoff planning.")
    handoff.add_argument("--allow-mutation", action="store_true", help="Record requested mutation consent; execution still remains disallowed here.")

    remember = sub.add_parser("remember", help="Build raw/summary memory candidate contracts without writing Hermes.")
    remember.add_argument("request", nargs="*", help="Memory text; stdin is used when omitted.")
    remember.add_argument("--summary", help="Optional derived summary text.")
    remember.add_argument("--approval-token", help="Record explicit approval presence for sensitive candidates.")
    remember.add_argument("--source-channel", default="just-chill-cli", help="Source channel metadata for the raw artifact contract.")
    remember.add_argument("--approval-registry", help="Optional approval registry JSONL path; defaults to JUST_CHILL_APPROVAL_REGISTRY when set.")
    remember.add_argument("--approval-scope", default="memory.write", help="Required approval scope when using a registry.")
    remember.add_argument("--approval-subject", help="Optional approval subject; defaults to the memory request text.")

    recall = sub.add_parser("recall", help="Build recall plan or gate host-owned retrieval evidence.")
    recall.add_argument("query", nargs="*", help="Recall query; stdin is used when omitted.")
    recall.add_argument("--cwd", default=None, help="Repo root for live-boundary discovery.")
    recall.add_argument("--candidate-json", help="Vector sidecar candidate JSON for admission gating.")
    recall.add_argument("--retrieval-evidence-json", help="Host retrieval evidence JSON for admission gating.")
    recall.add_argument("--current-source-hash", help="Fresh canonical source hash read by host.")
    recall.add_argument("--current-deletion-state", help="Fresh canonical source deletion state read by host.")
    recall.add_argument("--current-redaction-state", help="Fresh canonical source redaction state read by host.")
    recall.add_argument("--approval-token", help="Record explicit recall approval presence for sensitive candidates.")
    recall.add_argument("--approval-registry", help="Optional approval registry JSONL path; defaults to JUST_CHILL_APPROVAL_REGISTRY when set.")
    recall.add_argument("--approval-scope", default="memory.recall", help="Required approval scope when using a registry.")
    recall.add_argument("--approval-subject", help="Optional approval subject; defaults to the recall query.")
    recall.add_argument("--probe", action="store_true", help="Run read-only live-boundary probes for recall planning; defaults to deterministic availability-only output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command
    if command == "route":
        output = route_command(read_text_arg(args.request), cwd=args.cwd, include_bridge=args.include_bridge)
    elif command == "handoff-gjc":
        output = handoff_gjc_command(read_text_arg(args.request), cwd=args.cwd, allow_mutation=args.allow_mutation)
    elif command == "remember":
        output = remember_command(
            read_text_arg(args.request),
            summary=args.summary,
            approval_token=args.approval_token,
            source_channel=args.source_channel,
            approval_registry=args.approval_registry,
            approval_scope=args.approval_scope,
            approval_subject=args.approval_subject,
        )
    elif command == "recall":
        output = recall_command(
            read_text_arg(args.query),
            cwd=args.cwd,
            candidate_json=args.candidate_json,
            retrieval_evidence_json=args.retrieval_evidence_json,
            current_source_hash=args.current_source_hash,
            current_deletion_state=args.current_deletion_state,
            current_redaction_state=args.current_redaction_state,
            approval_token=args.approval_token,
            approval_registry=args.approval_registry,
            approval_scope=args.approval_scope,
            approval_subject=args.approval_subject,
            probe=args.probe,
        )
    else:  # pragma: no cover - argparse enforces command choices.
        parser.error(f"unsupported command: {command}")
    print(json_text(output, pretty=args.pretty))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
