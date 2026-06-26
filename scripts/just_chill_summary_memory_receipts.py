#!/usr/bin/env python3
"""Provider-backed summary memory receipt bridge for just-chill.

This module turns a ``summary-memory-contract`` into a host-owned provider-tool
plan and durable local receipts. It never calls Hermes or a provider directly:
Hermes remains the canonical memory authority, the host/operator owns provider
execution, and just-chill only records evidence that an allowed provider add or
remove operation happened.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from just_chill_live_bindings import discover_live_surfaces
from just_chill_memory_contracts import (
    build_raw_artifact_record,
    build_summary_memory_record,
    validate_contract_record,
)
from just_chill_router import classify_request

SCHEMA_VERSION = 1
BRIDGE_NAME = "just-chill-summary-memory-receipt-bridge-v1"
CANONICAL_MEMORY_AUTHORITY = "Hermes"
RECEIPT_AUTHORITY = "just-chill-host-summary-memory-receipts"
SUMMARY_ID_PATTERN = re.compile(r"^summary_[0-9a-f]{20}$")
SUPPORTED_OPERATIONS = {"add", "remove"}


class SummaryReceiptError(RuntimeError):
    """Raised when a summary memory provider receipt operation is unsafe."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def default_receipt_root(cwd: str | None = None) -> Path:
    """Return the ignored repo-local summary receipt root without creating it."""

    root = Path(cwd or os.getcwd()).resolve()
    return root / "tmp" / "just-chill-summary-memory-receipts"


def _safe_summary_id(summary_id: str) -> str:
    if not SUMMARY_ID_PATTERN.fullmatch(summary_id):
        raise SummaryReceiptError("summary memory id is invalid")
    return summary_id


def _summary(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("recordKind") != "summary-memory-contract":
        raise SummaryReceiptError("record must be a summary-memory-contract")
    summary = record.get("summaryMemory")
    if not isinstance(summary, dict):
        raise SummaryReceiptError("record missing summaryMemory object")
    return summary


def receipt_paths(summary_id: str, *, receipt_root: str | Path | None = None, cwd: str | None = None) -> dict[str, str]:
    safe_id = _safe_summary_id(summary_id)
    root = Path(receipt_root).resolve() if receipt_root is not None else default_receipt_root(cwd)
    summary_dir = root / safe_id
    return {
        "receiptRoot": str(root),
        "summaryDir": str(summary_dir),
        "contractPath": str(summary_dir / "contract.json"),
        "addReceiptPath": str(summary_dir / "add-receipt.json"),
        "removeReceiptPath": str(summary_dir / "remove-receipt.json"),
    }


def _provider_surface(surfaces: dict[str, Any]) -> dict[str, Any]:
    hermes = surfaces.get("hermes", {}) if isinstance(surfaces, dict) else {}
    surface = hermes.get("memoryProviderSurface", {})
    return surface if isinstance(surface, dict) else {}


def _provider_tool(surface: dict[str, Any]) -> dict[str, Any]:
    tool = surface.get("tool", {})
    return tool if isinstance(tool, dict) else {}


def _summary_tags(summary_id: str) -> str:
    return ",".join(["just-chill", "summary-memory", summary_id])

def _provider_api(surface: dict[str, Any], *, operation: str) -> str | None:
    api = surface.get("summaryMemoryApi")
    if not isinstance(api, str):
        return None
    if operation == "remove" and api.endswith(".add"):
        return api[:-4] + ".remove"
    return api


def _provider_arguments(summary: dict[str, Any], surface: dict[str, Any], *, operation: str) -> dict[str, Any]:
    tool = _provider_tool(surface)
    if operation == "add":
        return {
            "action": tool.get("writeAction", "add"),
            "content": summary.get("summary"),
            "category": "project",
            "tags": _summary_tags(str(summary.get("id"))),
        }
    return {
        "action": tool.get("deleteAction", "remove"),
        "selector": {
            "category": "project",
            "tags": _summary_tags(str(summary.get("id"))),
            "summaryId": summary.get("id"),
            "summaryHash": summary.get("summaryHash"),
            "sourceArtifactRefs": summary.get("sourceArtifactRefs", []),
        },
    }


def _provider_ready(surface: dict[str, Any], *, operation: str) -> bool:
    tool = _provider_tool(surface)
    if not surface.get("summaryMemoryWriteAvailable"):
        return False
    if not tool.get("name"):
        return False
    if operation == "add":
        return bool(tool.get("writeAction"))
    return bool(tool.get("deleteAction"))


def _blocked_reasons(
    record: dict[str, Any],
    surfaces: dict[str, Any],
    *,
    operation: str,
    reason: str | None,
    approval_token: str | None,
    receipt_root: str | Path | None = None,
    cwd: str | None = None,
) -> list[str]:
    reasons = validate_contract_record(record)
    if operation not in SUPPORTED_OPERATIONS:
        reasons.append("operation must be add or remove")
        return reasons

    try:
        summary = _summary(record)
        summary_id = _safe_summary_id(str(summary.get("id", "")))
    except SummaryReceiptError as exc:
        return [*reasons, str(exc)]

    surface = _provider_surface(surfaces)
    if surface.get("rawArtifactApi") and surface.get("rawArtifactApi") != "unmapped":
        reasons.append("summary receipt bridge must not claim raw artifact authority")
    if not _provider_ready(surface, operation=operation):
        reasons.append(f"Hermes summary memory provider {operation} tool is not mapped")
    if summary.get("sensitivity") == "sensitive" and not approval_token:
        reasons.append("sensitive summary memory requires explicit approval")

    paths = receipt_paths(summary_id, receipt_root=receipt_root, cwd=cwd)
    add_receipt = Path(paths["addReceiptPath"])
    remove_receipt = Path(paths["removeReceiptPath"])
    if operation == "add":
        if add_receipt.exists():
            reasons.append("summary memory already has an add receipt")
        if remove_receipt.exists():
            reasons.append("summary memory has a removal receipt and cannot be re-added under the same id")
    else:
        if not approval_token:
            reasons.append("summary memory removal requires explicit approval")
        if not reason or not reason.strip():
            reasons.append("summary memory removal requires a reason")
        if not add_receipt.exists():
            reasons.append("summary memory removal requires a prior add receipt")
        if remove_receipt.exists():
            reasons.append("summary memory already has a removal receipt")
    return reasons


def build_summary_provider_receipt_plan(
    record: dict[str, Any],
    surfaces: dict[str, Any],
    *,
    operation: str = "add",
    reason: str | None = None,
    approval_token: str | None = None,
    receipt_root: str | Path | None = None,
    cwd: str | None = None,
) -> dict[str, Any]:
    """Build a provider-tool receipt plan without executing Hermes/provider calls."""

    try:
        summary = _summary(record)
        summary_id = _safe_summary_id(str(summary.get("id", "")))
        paths = receipt_paths(summary_id, receipt_root=receipt_root, cwd=cwd)
        sensitivity = summary.get("sensitivity")
    except SummaryReceiptError as exc:
        summary = {}
        summary_id = record.get("summaryMemory", {}).get("id")
        paths = {}
        sensitivity = None
        blocked_reasons = [str(exc)]
    else:
        blocked_reasons = _blocked_reasons(
            record,
            surfaces,
            operation=operation,
            reason=reason,
            approval_token=approval_token,
            receipt_root=receipt_root,
            cwd=cwd,
        )

    surface = _provider_surface(surfaces)
    tool = _provider_tool(surface)
    action = tool.get("writeAction", "add") if operation == "add" else tool.get("deleteAction", "remove")
    return {
        "schemaVersion": SCHEMA_VERSION,
        "bridge": BRIDGE_NAME,
        "recordKind": record.get("recordKind"),
        "summaryId": summary_id,
        "operation": operation,
        "status": f"ready-for-provider-{operation}" if not blocked_reasons else f"provider-{operation}-blocked",
        "canonicalMemoryAuthority": CANONICAL_MEMORY_AUTHORITY,
        "receiptAuthority": RECEIPT_AUTHORITY,
        "provider": surface.get("provider"),
        "storageMode": surface.get("storageMode"),
        "providerTool": {
            "api": _provider_api(surface, operation=operation),
            "tool": tool.get("name"),
            "action": action,
            "arguments": _provider_arguments(summary, surface, operation=operation) if summary else None,
        },
        "sensitivity": sensitivity,
        "approval": {
            "approvalTokenPresent": bool(approval_token),
            "sensitiveApproved": sensitivity != "sensitive" or bool(approval_token),
            "sensitiveContentMode": "redacted-summary-only" if sensitivity == "sensitive" else "plain-summary",
        },
        "paths": paths,
        "provenance": {
            "sourceArtifactRefs": summary.get("sourceArtifactRefs", []),
            "summaryHash": summary.get("summaryHash"),
            "rawContentHash": summary.get("provenance", {}).get("rawContentHash"),
        },
        "executionBoundary": {
            "allowedHere": False,
            "hostMustExecuteProviderTool": True,
            "justChillCallsProvider": False,
            "hermesOwnsCanonicalMemory": True,
        },
        "receiptGate": {
            "enabled": not blocked_reasons,
            "blockedReasons": blocked_reasons,
            "reason": reason.strip() if isinstance(reason, str) else None,
        },
        "evidenceRequirements": [
            "host/operator provider result must be supplied before a receipt is recorded",
            "provider result must match the planned provider, tool, and action",
            "removal requires a prior add receipt, explicit approval, and a reason",
            "receipts are local evidence only and do not replace Hermes canonical memory state",
        ],
    }


def validate_summary_provider_receipt_plan(plan: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if plan.get("schemaVersion") != SCHEMA_VERSION:
        issues.append("schemaVersion mismatch")
    if plan.get("bridge") != BRIDGE_NAME:
        issues.append("bridge name mismatch")
    if plan.get("canonicalMemoryAuthority") != CANONICAL_MEMORY_AUTHORITY:
        issues.append("canonical memory authority must remain Hermes")
    if plan.get("receiptAuthority") != RECEIPT_AUTHORITY:
        issues.append("receipt authority mismatch")
    if plan.get("operation") not in SUPPORTED_OPERATIONS:
        issues.append("unsupported operation")
    boundary = plan.get("executionBoundary", {})
    if boundary.get("allowedHere") is not False:
        issues.append("summary receipt bridge must not execute provider calls locally")
    if boundary.get("justChillCallsProvider") is not False:
        issues.append("just-chill must not call provider tools directly")
    if boundary.get("hermesOwnsCanonicalMemory") is not True:
        issues.append("Hermes must remain canonical memory owner")
    if plan.get("status", "").startswith("ready") and plan.get("receiptGate", {}).get("blockedReasons"):
        issues.append("ready receipt plan cannot have blocked reasons")
    provider_tool = plan.get("providerTool", {})
    if plan.get("status", "").startswith("ready") and not provider_tool.get("tool"):
        issues.append("ready receipt plan requires a provider tool")
    return issues


def _load_json_object(raw: str, *, label: str) -> dict[str, Any]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise SummaryReceiptError(f"{label} must decode to an object")
    return data


def _provider_result_issues(plan: dict[str, Any], provider_result: dict[str, Any]) -> list[str]:
    provider_tool = plan.get("providerTool", {})
    expected_provider = plan.get("provider")
    expected_tool = provider_tool.get("tool")
    expected_action = provider_tool.get("action")
    expected_summary_id = plan.get("summaryId")
    expected_summary_hash = plan.get("provenance", {}).get("summaryHash")
    operation = plan.get("operation")
    ok_statuses = {"succeeded", "ok", "added"} if operation == "add" else {"succeeded", "ok", "removed"}
    summary_bound = (
        bool(expected_summary_id and provider_result.get("summaryId") == expected_summary_id)
        or bool(expected_summary_hash and provider_result.get("summaryHash") == expected_summary_hash)
    )
    issues: list[str] = []
    if provider_result.get("provider") != expected_provider:
        issues.append("provider result does not match planned provider")
    if provider_result.get("tool") != expected_tool:
        issues.append("provider result does not match planned tool")
    if provider_result.get("action") != expected_action:
        issues.append("provider result does not match planned action")
    if provider_result.get("status") not in ok_statuses:
        issues.append("provider result must report a successful terminal status for the planned operation")
    if not summary_bound:
        issues.append("provider result must include matching summaryId or summaryHash")
    if not any(provider_result.get(key) for key in ["providerCallId", "turnId", "artifactRef", "receiptRef", "resultHash"]):
        issues.append("provider result requires durable evidence reference")
    return issues


def record_summary_provider_receipt(
    record: dict[str, Any],
    surfaces: dict[str, Any],
    *,
    operation: str,
    provider_result: dict[str, Any],
    reason: str | None = None,
    approval_token: str | None = None,
    receipt_root: str | Path | None = None,
    cwd: str | None = None,
) -> dict[str, Any]:
    """Record local evidence for a host-executed summary provider operation."""

    plan = build_summary_provider_receipt_plan(
        record,
        surfaces,
        operation=operation,
        reason=reason,
        approval_token=approval_token,
        receipt_root=receipt_root,
        cwd=cwd,
    )
    plan_issues = validate_summary_provider_receipt_plan(plan)
    if plan_issues:
        raise SummaryReceiptError("; ".join(plan_issues))
    blocked = plan.get("receiptGate", {}).get("blockedReasons", [])
    if blocked:
        raise SummaryReceiptError("; ".join(blocked))

    result_issues = _provider_result_issues(plan, provider_result)
    if result_issues:
        raise SummaryReceiptError("; ".join(result_issues))

    summary = _summary(record)
    paths = plan["paths"]
    summary_dir = Path(paths["summaryDir"])
    summary_dir.mkdir(parents=True, exist_ok=True)
    contract_path = Path(paths["contractPath"])
    contract_path.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = {
        "schemaVersion": SCHEMA_VERSION,
        "bridge": BRIDGE_NAME,
        "operation": f"provider-{operation}-summary-memory",
        "status": "recorded",
        "summaryId": summary["id"],
        "canonicalMemoryAuthority": CANONICAL_MEMORY_AUTHORITY,
        "receiptAuthority": RECEIPT_AUTHORITY,
        "provider": plan.get("provider"),
        "providerTool": plan.get("providerTool"),
        "providerResult": provider_result,
        "sensitivity": summary.get("sensitivity"),
        "approvalTokenPresent": bool(approval_token),
        "reason": reason.strip() if isinstance(reason, str) else None,
        "recordedAt": now_iso(),
        "paths": paths,
        "provenance": plan.get("provenance", {}),
        "executionBoundary": plan.get("executionBoundary", {}),
    }
    receipt_path = Path(paths["addReceiptPath"] if operation == "add" else paths["removeReceiptPath"])
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def read_summary_provider_receipts(
    summary_id: str,
    *,
    receipt_root: str | Path | None = None,
    cwd: str | None = None,
) -> dict[str, Any]:
    safe_id = _safe_summary_id(summary_id)
    paths = receipt_paths(safe_id, receipt_root=receipt_root, cwd=cwd)
    add_path = Path(paths["addReceiptPath"])
    remove_path = Path(paths["removeReceiptPath"])
    if not add_path.exists():
        raise SummaryReceiptError("summary memory add receipt is missing")
    add_receipt = json.loads(add_path.read_text(encoding="utf-8"))
    remove_receipt = json.loads(remove_path.read_text(encoding="utf-8")) if remove_path.exists() else None
    return {
        "schemaVersion": SCHEMA_VERSION,
        "bridge": BRIDGE_NAME,
        "operation": "read-summary-memory-receipts",
        "status": "removed" if remove_receipt else "active",
        "summaryId": safe_id,
        "canonicalMemoryAuthority": CANONICAL_MEMORY_AUTHORITY,
        "receiptAuthority": RECEIPT_AUTHORITY,
        "paths": paths,
        "addReceipt": add_receipt,
        "removeReceipt": remove_receipt,
    }


def _contract_from_args(args: argparse.Namespace) -> dict[str, Any]:
    request = " ".join(args.request).strip()
    if not request:
        raise SummaryReceiptError("request text is required")
    if args.summary is None:
        raise SummaryReceiptError("--summary is required for summary memory receipt operations")
    packet = classify_request(request)
    raw = build_raw_artifact_record(packet)
    return build_summary_memory_record(raw, args.summary)


def _provider_result_from_args(args: argparse.Namespace) -> dict[str, Any]:
    if not args.provider_result_json:
        raise SummaryReceiptError("--provider-result-json is required when recording a receipt")
    return _load_json_object(args.provider_result_json, label="provider result JSON")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan and record host-owned summary memory provider receipts.")
    parser.add_argument("request", nargs="*", help="Request text used to build a summary memory contract.")
    parser.add_argument("--summary", help="Summary text used to build a summary memory contract.")
    parser.add_argument("--cwd", default=None, help="Repo root for surface discovery and default receipt root.")
    parser.add_argument("--receipt-root", default=None, help="Override local summary receipt root.")
    parser.add_argument("--probe", action="store_true", help="Run allowlisted read-only surface probes.")
    parser.add_argument("--approval-token", help="Required for sensitive summary writes and all removals.")
    parser.add_argument("--reason", default="operator-requested summary memory removal", help="Removal reason.")
    parser.add_argument("--provider-result-json", help="Host/operator provider result evidence for receipt recording.")
    parser.add_argument("--plan-add", action="store_true", help="Emit an add receipt plan without writing.")
    parser.add_argument("--record-add-receipt", action="store_true", help="Record an add receipt from supplied provider result evidence.")
    parser.add_argument("--plan-remove", action="store_true", help="Emit a remove receipt plan without writing.")
    parser.add_argument("--record-remove-receipt", action="store_true", help="Record a remove receipt from supplied provider result evidence.")
    parser.add_argument("--read-summary-id", help="Read local add/remove receipts for a summary id.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    try:
        if args.read_summary_id:
            output = read_summary_provider_receipts(
                args.read_summary_id,
                receipt_root=args.receipt_root,
                cwd=args.cwd,
            )
        else:
            selected = [args.plan_add, args.record_add_receipt, args.plan_remove, args.record_remove_receipt]
            if sum(1 for item in selected if item) != 1:
                raise SummaryReceiptError("select exactly one of --plan-add, --record-add-receipt, --plan-remove, or --record-remove-receipt")
            record = _contract_from_args(args)
            surfaces = discover_live_surfaces(cwd=args.cwd, probe=args.probe)
            if args.plan_add:
                output = build_summary_provider_receipt_plan(
                    record,
                    surfaces,
                    operation="add",
                    approval_token=args.approval_token,
                    receipt_root=args.receipt_root,
                    cwd=args.cwd,
                )
                issues = validate_summary_provider_receipt_plan(output)
                if issues:
                    output["validationIssues"] = issues
            elif args.record_add_receipt:
                output = record_summary_provider_receipt(
                    record,
                    surfaces,
                    operation="add",
                    provider_result=_provider_result_from_args(args),
                    approval_token=args.approval_token,
                    receipt_root=args.receipt_root,
                    cwd=args.cwd,
                )
            elif args.plan_remove:
                output = build_summary_provider_receipt_plan(
                    record,
                    surfaces,
                    operation="remove",
                    reason=args.reason,
                    approval_token=args.approval_token,
                    receipt_root=args.receipt_root,
                    cwd=args.cwd,
                )
                issues = validate_summary_provider_receipt_plan(output)
                if issues:
                    output["validationIssues"] = issues
            else:
                output = record_summary_provider_receipt(
                    record,
                    surfaces,
                    operation="remove",
                    provider_result=_provider_result_from_args(args),
                    reason=args.reason,
                    approval_token=args.approval_token,
                    receipt_root=args.receipt_root,
                    cwd=args.cwd,
                )
        print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
        return 0
    except SummaryReceiptError as exc:
        print(json.dumps({"schemaVersion": SCHEMA_VERSION, "bridge": BRIDGE_NAME, "status": "error", "error": str(exc)}, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
