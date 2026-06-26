#!/usr/bin/env python3
"""Acceptance checks for just-chill summary memory provider receipts."""
from __future__ import annotations

import tempfile
from pathlib import Path

from just_chill_hermes_adapter import build_hermes_adapter_stub, validate_adapter_stub
from just_chill_memory_contracts import build_raw_artifact_record, build_summary_memory_record
from just_chill_router import classify_request
from just_chill_summary_memory_receipts import (
    build_summary_provider_receipt_plan,
    read_summary_provider_receipts,
    receipt_paths,
    record_summary_provider_receipt,
    validate_summary_provider_receipt_plan,
)


def require(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle, haystack) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


def require_raises(name: str, func, expected_substring: str) -> None:
    try:
        func()
    except Exception as exc:
        if expected_substring not in str(exc):
            raise AssertionError(f"{name}: expected {expected_substring!r} in {exc!r}") from exc
        return
    raise AssertionError(f"{name}: expected exception containing {expected_substring!r}")


def provider_summary_surfaces() -> dict:
    return {
        "schemaVersion": 1,
        "hermes": {
            "status": "provider-status-readable",
            "memoryProvider": "holographic",
            "rawArtifactApi": "unmapped",
            "summaryMemoryApi": "hermes.summary_memory.provider_tool.fact_store.add",
            "memoryToolWriteAvailable": True,
            "liveStorageWriteAvailable": False,
            "storageAuthority": "Hermes",
            "memoryProviderSurface": {
                "status": "provider-tool-available",
                "provider": "holographic",
                "storageMode": "local-sqlite-fact-store",
                "rawArtifactApi": "unmapped",
                "summaryMemoryApi": "hermes.summary_memory.provider_tool.fact_store.add",
                "summaryMemoryWriteAvailable": True,
                "tool": {
                    "name": "fact_store",
                    "writeAction": "add",
                    "readActions": ["search", "probe", "related", "reason", "list"],
                    "deleteAction": "remove",
                },
                "boundary": "host-owned Hermes memory provider tool; just-chill emits a plan and does not call the tool directly",
            },
        },
    }


def no_provider_surfaces() -> dict:
    surfaces = provider_summary_surfaces()
    surfaces["hermes"]["memoryProviderSurface"] = {
        "status": "no-external-provider",
        "provider": None,
        "rawArtifactApi": "unmapped",
        "summaryMemoryApi": "unmapped",
        "summaryMemoryWriteAvailable": False,
        "limitations": ["no active external Hermes memory provider"],
    }
    surfaces["hermes"]["summaryMemoryApi"] = "unmapped"
    surfaces["hermes"]["memoryToolWriteAvailable"] = False
    return surfaces


def raw_claim_surfaces() -> dict:
    surfaces = provider_summary_surfaces()
    surfaces["hermes"]["memoryProviderSurface"]["rawArtifactApi"] = "hermes.raw_artifact.create"
    return surfaces


cases: list[str] = []

packet = classify_request("remember that visible routed GJC sessions are preferred for development routing")
raw = build_raw_artifact_record(packet)
summary = build_summary_memory_record(raw, "Visible routed GJC sessions are preferred for development routing.")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    plan = build_summary_provider_receipt_plan(
        summary,
        provider_summary_surfaces(),
        receipt_root=root,
    )
    require("add plan ready", plan["status"], "ready-for-provider-add")
    require("add plan no local execute", plan["executionBoundary"]["allowedHere"], False)
    require("add provider", plan["provider"], "holographic")
    require("add action", plan["providerTool"]["action"], "add")
    require("add api", plan["providerTool"]["api"], "hermes.summary_memory.provider_tool.fact_store.add")
    require("add validation", validate_summary_provider_receipt_plan(plan), [])
    cases.append("provider-add-plan-ready")

    blocked_plan = build_summary_provider_receipt_plan(
        summary,
        no_provider_surfaces(),
        receipt_root=root,
    )
    require("missing provider blocked", blocked_plan["status"], "provider-add-blocked")
    require_in("missing provider reason", "Hermes summary memory provider add tool is not mapped", blocked_plan["receiptGate"]["blockedReasons"])
    require("missing provider validation", validate_summary_provider_receipt_plan(blocked_plan), [])
    cases.append("missing-provider-fail-closed")

    raw_claim_plan = build_summary_provider_receipt_plan(summary, raw_claim_surfaces(), receipt_root=root)
    require("raw claim blocks", raw_claim_plan["status"], "provider-add-blocked")
    require_in("raw authority guard", "summary receipt bridge must not claim raw artifact authority", raw_claim_plan["receiptGate"]["blockedReasons"])
    cases.append("raw-authority-guard")

    sensitive_packet = classify_request("remember my API key sk-test-1234567890 for later")
    sensitive_raw = build_raw_artifact_record(sensitive_packet)
    sensitive_summary = build_summary_memory_record(sensitive_raw, "Sensitive API key must not persist without approval.")
    sensitive_blocked = build_summary_provider_receipt_plan(sensitive_summary, provider_summary_surfaces(), receipt_root=root)
    require("sensitive add blocked", sensitive_blocked["status"], "provider-add-blocked")
    require_in("sensitive approval reason", "sensitive summary memory requires explicit approval", sensitive_blocked["receiptGate"]["blockedReasons"])
    sensitive_ready = build_summary_provider_receipt_plan(
        sensitive_summary,
        provider_summary_surfaces(),
        receipt_root=root,
        approval_token="operator-approved",
    )
    require("sensitive add approved", sensitive_ready["status"], "ready-for-provider-add")
    require("sensitive content redacted", sensitive_ready["providerTool"]["arguments"]["content"], "[redacted-sensitive]")
    require("sensitive approval redacted-only mode", sensitive_ready["approval"]["sensitiveContentMode"], "redacted-summary-only")
    cases.append("sensitive-add-approval")

    provider_add_result = {
        "provider": "holographic",
        "tool": "fact_store",
        "action": "add",
        "status": "succeeded",
        "providerCallId": "fact-store-add-001",
        "summaryId": summary["summaryMemory"]["id"],
        "summaryHash": summary["summaryMemory"]["summaryHash"],
    }
    require_raises(
        "mismatched add evidence rejected",
        lambda: record_summary_provider_receipt(
            summary,
            provider_summary_surfaces(),
            operation="add",
            provider_result={**provider_add_result, "summaryId": "summary_00000000000000000000", "summaryHash": "sha256:mismatch"},
            receipt_root=root,
        ),
        "provider result must include matching summaryId or summaryHash",
    )
    require_raises(
        "wrong add terminal status rejected",
        lambda: record_summary_provider_receipt(
            summary,
            provider_summary_surfaces(),
            operation="add",
            provider_result={**provider_add_result, "status": "removed"},
            receipt_root=root,
        ),
        "provider result must report a successful terminal status for the planned operation",
    )
    add_receipt = record_summary_provider_receipt(
        summary,
        provider_summary_surfaces(),
        operation="add",
        provider_result=provider_add_result,
        receipt_root=root,
    )
    require("add receipt operation", add_receipt["operation"], "provider-add-summary-memory")
    require("add receipt authority", add_receipt["canonicalMemoryAuthority"], "Hermes")
    require("add receipt local no execute", add_receipt["executionBoundary"]["allowedHere"], False)
    read_active = read_summary_provider_receipts(summary["summaryMemory"]["id"], receipt_root=root)
    require("read active", read_active["status"], "active")
    require("read add receipt", read_active["addReceipt"]["providerResult"]["providerCallId"], "fact-store-add-001")
    duplicate_add = build_summary_provider_receipt_plan(summary, provider_summary_surfaces(), receipt_root=root)
    require_in("duplicate add blocked", "summary memory already has an add receipt", duplicate_add["receiptGate"]["blockedReasons"])
    cases.append("record-add-receipt")

    no_approval_remove = build_summary_provider_receipt_plan(
        summary,
        provider_summary_surfaces(),
        operation="remove",
        receipt_root=root,
        reason="cleanup",
    )
    require("remove without approval blocked", no_approval_remove["status"], "provider-remove-blocked")
    require_in("remove approval reason", "summary memory removal requires explicit approval", no_approval_remove["receiptGate"]["blockedReasons"])
    remove_plan = build_summary_provider_receipt_plan(
        summary,
        provider_summary_surfaces(),
        operation="remove",
        receipt_root=root,
        approval_token="operator-approved",
        reason="cleanup stale candidate",
    )
    require("remove plan ready", remove_plan["status"], "ready-for-provider-remove")
    require("remove action", remove_plan["providerTool"]["action"], "remove")
    require("remove api", remove_plan["providerTool"]["api"], "hermes.summary_memory.provider_tool.fact_store.remove")
    require("remove validation", validate_summary_provider_receipt_plan(remove_plan), [])
    cases.append("provider-remove-plan-ready")

    provider_remove_result = {
        "provider": "holographic",
        "tool": "fact_store",
        "action": "remove",
        "status": "succeeded",
        "providerCallId": "fact-store-remove-001",
        "summaryId": summary["summaryMemory"]["id"],
        "summaryHash": summary["summaryMemory"]["summaryHash"],
    }
    remove_receipt = record_summary_provider_receipt(
        summary,
        provider_summary_surfaces(),
        operation="remove",
        provider_result=provider_remove_result,
        receipt_root=root,
        approval_token="operator-approved",
        reason="cleanup stale candidate",
    )
    require("remove receipt operation", remove_receipt["operation"], "provider-remove-summary-memory")
    read_removed = read_summary_provider_receipts(summary["summaryMemory"]["id"], receipt_root=root)
    require("read removed", read_removed["status"], "removed")
    require("remove receipt result", read_removed["removeReceipt"]["providerResult"]["providerCallId"], "fact-store-remove-001")
    readd_blocked = build_summary_provider_receipt_plan(summary, provider_summary_surfaces(), receipt_root=root)
    require_in("readd after removal blocked", "summary memory has a removal receipt and cannot be re-added under the same id", readd_blocked["receiptGate"]["blockedReasons"])
    cases.append("record-remove-receipt")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    missing_add_remove = build_summary_provider_receipt_plan(
        summary,
        provider_summary_surfaces(),
        operation="remove",
        receipt_root=root,
        approval_token="operator-approved",
        reason="cleanup",
    )
    require("remove without prior add blocked", missing_add_remove["status"], "provider-remove-blocked")
    require_in("prior add required", "summary memory removal requires a prior add receipt", missing_add_remove["receiptGate"]["blockedReasons"])
    require_raises(
        "record remove without prior add rejected",
        lambda: record_summary_provider_receipt(
            summary,
            provider_summary_surfaces(),
            operation="remove",
            provider_result={"provider": "holographic", "tool": "fact_store", "action": "remove", "status": "succeeded", "providerCallId": "remove-missing-add", "summaryId": summary["summaryMemory"]["id"], "summaryHash": summary["summaryMemory"]["summaryHash"]},
            receipt_root=root,
            approval_token="operator-approved",
            reason="cleanup",
        ),
        "summary memory removal requires a prior add receipt",
    )
    require_raises("invalid summary id rejected", lambda: receipt_paths("../bad", receipt_root=root), "summary memory id is invalid")
    cases.append("remove-requires-prior-add")

summary_stub = build_hermes_adapter_stub(summary, surfaces=provider_summary_surfaces())
require("adapter exposes summary receipt plan", summary_stub["summaryProviderReceiptPlan"]["bridge"], "just-chill-summary-memory-receipt-bridge-v1")
require("adapter summary receipt ready", summary_stub["summaryProviderReceiptPlan"]["status"], "ready-for-provider-add")
require("adapter summary no local stage", summary_stub["localArtifactStaging"], None)
require("adapter validation", validate_adapter_stub(summary_stub), [])
raw_stub = build_hermes_adapter_stub(raw, surfaces=provider_summary_surfaces())
require("raw has no summary receipt plan", raw_stub["summaryProviderReceiptPlan"], None)
cases.append("adapter-summary-receipt-plan")

print(f"PASS: {len(cases)} just-chill summary memory receipt cases passed")
