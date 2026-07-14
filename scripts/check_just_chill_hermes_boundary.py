#!/usr/bin/env python3
"""Acceptance checks for just-chill Hermes live-boundary mapping."""
from __future__ import annotations

from just_chill_hermes_adapter import (
    build_hermes_adapter_stub,
    build_hermes_live_boundary_report,
    validate_adapter_stub,
    validate_hermes_live_boundary_report,
)
from just_chill_memory_contracts import build_raw_artifact_record, build_summary_memory_record
from just_chill_router import classify_request


def require(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle, haystack) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


def fake_surfaces(*, write_ready: bool = False) -> dict:
    return {
        "schemaVersion": 1,
        "hermes": {
            "status": "provider-status-readable",
            "command": {"available": True, "path": "/fake/bin/hermes", "source": "path"},
            "memoryProvider": "(none — built-in only)",
            "memoryProbe": {
                "ok": True,
                "stdout": "Memory status\n  Built-in: always active\n  Provider: (none — built-in only)",
            },
            "mcpProbe": {"ok": True, "stdout": "No MCP servers configured."},
            "setupSmoke": {"ok": True, "json": {"ok": True, "files_written": []}},
            "rawArtifactApi": "hermes.raw_artifact.create" if write_ready else "unmapped",
            "summaryMemoryApi": "hermes.summary_memory.create" if write_ready else "unmapped",
            "liveStorageWriteAvailable": write_ready,
            "storageAuthority": "Hermes",
        },
    }


def malformed_api_surfaces() -> dict:
    surfaces = fake_surfaces(write_ready=True)
    surfaces["hermes"]["rawArtifactApi"] = ""
    surfaces["hermes"]["summaryMemoryApi"] = None
    return surfaces


def read_only_api_surfaces() -> dict:
    surfaces = fake_surfaces(write_ready=True)
    surfaces["hermes"]["rawArtifactApi"] = "hermes.raw_artifact.status"
    surfaces["hermes"]["summaryMemoryApi"] = "mcp:hermes.summary_memory.list"
    return surfaces
def provider_summary_surfaces() -> dict:
    surfaces = fake_surfaces(write_ready=False)
    surfaces["hermes"]["memoryProvider"] = "holographic"
    surfaces["hermes"]["summaryMemoryApi"] = "hermes.summary_memory.provider_tool.fact_store.add"
    surfaces["hermes"]["memoryToolWriteAvailable"] = True
    surfaces["hermes"]["memoryProviderSurface"] = {
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
    }
    return surfaces








cases: list[str] = []

packet = classify_request("remember that visible GJC sessions are preferred for development routing")
raw = build_raw_artifact_record(packet)
report = build_hermes_live_boundary_report(raw, surfaces=fake_surfaces())
require("raw boundary mapper", report["mapper"], "just-chill-hermes-live-boundary-v1")
require("raw boundary status", report["status"], "contract-only-write-blocked")
require("raw storage authority", report["storageAuthority"], "Hermes")
require("raw contract authority", report["contractAuthority"], "just-chill")
require("raw local write disabled", report["writeGate"]["allowedHere"], False)
require("raw write gate disabled", report["writeGate"]["enabled"], False)
require_in("raw write blocked", "Hermes raw artifact write API is not mapped", report["writeGate"]["blockedReasons"])
require("raw memory status readable", report["readSurfaces"]["memoryStatus"]["available"], True)
require("raw mcp list unconfigured", report["readSurfaces"]["mcpList"]["configured"], False)
require("raw live report validation", validate_hermes_live_boundary_report(report), [])
cases.append("raw-boundary-blocked")

raw_stub = build_hermes_adapter_stub(raw, surfaces=fake_surfaces())
require("stub embeds boundary", raw_stub["liveBoundaryReport"]["mapper"], "just-chill-hermes-live-boundary-v1")
require("stub write disabled", raw_stub["writePlan"]["enabled"], False)
require("stub validation", validate_adapter_stub(raw_stub), [])
require("stub local stage store", raw_stub["localArtifactStaging"]["store"], "just-chill-local-raw-artifact-store-v1")
require("stub local stage canonical", raw_stub["localArtifactStaging"]["canonicalStorageAuthority"], "Hermes")
require("stub local stage not hermes write", raw_stub["localArtifactStaging"]["writeGate"]["hermesWriteAllowedHere"], False)
require("stub raw api discovery", raw_stub["rawArtifactApiDiscovery"]["mapper"], "just-chill-hermes-raw-artifact-boundary-v1")
require("stub raw api discovery blocked", raw_stub["rawArtifactApiDiscovery"]["status"], "raw-artifact-api-unmapped")
cases.append("adapter-embeds-boundary")

sensitive_packet = classify_request("remember my API key <example-api-key> for later")
sensitive_raw = build_raw_artifact_record(sensitive_packet)
sensitive_report = build_hermes_live_boundary_report(sensitive_raw, surfaces=fake_surfaces(write_ready=True))
require("sensitive approval absent", sensitive_report["approval"]["approvalTokenPresent"], False)
require("sensitive not approved", sensitive_report["approval"]["sensitiveApproved"], False)
require("sensitive write disabled", sensitive_report["writeGate"]["enabled"], False)
require_in("sensitive approval blocker", "sensitive memory requires explicit approval before any Hermes write", sensitive_report["writeGate"]["blockedReasons"])
require("sensitive report validation", validate_hermes_live_boundary_report(sensitive_report), [])
cases.append("sensitive-approval-blocked")

approved_sensitive_report = build_hermes_live_boundary_report(
    sensitive_raw,
    surfaces=fake_surfaces(write_ready=True),
    approval_token="operator-approved-retention",
)
require("approved sensitive ready", approved_sensitive_report["status"], "ready-for-hermes-write")
require("approved sensitive gate enabled", approved_sensitive_report["writeGate"]["enabled"], True)
require("approved sensitive still local-disabled", approved_sensitive_report["writeGate"]["allowedHere"], False)
require("approved sensitive validation", validate_hermes_live_boundary_report(approved_sensitive_report), [])
cases.append("sensitive-token-ready-but-not-local")

summary = build_summary_memory_record(raw, "Visible GJC sessions are preferred for development routing.")
summary_report = build_hermes_live_boundary_report(summary, surfaces=fake_surfaces())
require("summary boundary kind", summary_report["recordKind"], "summary-memory-contract")
require_in("summary write blocked", "Hermes summary memory write API is not mapped", summary_report["writeGate"]["blockedReasons"])
require("summary validation", validate_hermes_live_boundary_report(summary_report), [])
cases.append("summary-boundary-blocked")
provider_raw_report = build_hermes_live_boundary_report(raw, surfaces=provider_summary_surfaces())
require("provider raw still blocked", provider_raw_report["status"], "contract-only-write-blocked")
require_in("provider raw artifact still unmapped", "Hermes raw artifact write API is not mapped", provider_raw_report["writeGate"]["blockedReasons"])
cases.append("provider-raw-artifact-still-blocked")

provider_summary_report = build_hermes_live_boundary_report(summary, surfaces=provider_summary_surfaces())
require("provider summary ready", provider_summary_report["status"], "ready-for-hermes-write")
require("provider summary gate enabled", provider_summary_report["writeGate"]["enabled"], True)
require("provider summary local disabled", provider_summary_report["writeGate"]["allowedHere"], False)
require("provider summary mapped", provider_summary_report["writeSurfaces"]["summaryMemory"]["mapped"], True)
require("provider summary tool", provider_summary_report["writeSurfaces"]["memoryProviderTool"]["tool"]["name"], "fact_store")
require("provider summary validation", validate_hermes_live_boundary_report(provider_summary_report), [])
provider_summary_stub = build_hermes_adapter_stub(summary, surfaces=provider_summary_surfaces())
require("provider summary stub enabled", provider_summary_stub["writePlan"]["enabled"], True)
require("provider summary would call", provider_summary_stub["writePlan"]["wouldCall"]["tool"], "fact_store")
require("provider summary would not execute here", provider_summary_stub["writePlan"]["wouldCall"]["allowedHere"], False)
require("provider summary stub validation", validate_adapter_stub(provider_summary_stub), [])
require("provider summary receipt plan", provider_summary_stub["summaryProviderReceiptPlan"]["bridge"], "just-chill-summary-memory-receipt-bridge-v1")
require("provider summary receipt ready", provider_summary_stub["summaryProviderReceiptPlan"]["status"], "ready-for-provider-add")
require("provider summary receipt no execution", provider_summary_stub["summaryProviderReceiptPlan"]["executionBoundary"]["allowedHere"], False)
cases.append("provider-summary-tool-ready")
empty_surface_report = build_hermes_live_boundary_report(raw, surfaces={})
require("empty surfaces deterministic blocked", empty_surface_report["status"], "contract-only-write-blocked")
require("empty surfaces memory status not host-dependent", empty_surface_report["readSurfaces"]["memoryStatus"]["available"], False)
require_in("empty surfaces raw blocked", "Hermes raw artifact write API is not mapped", empty_surface_report["writeGate"]["blockedReasons"])
cases.append("empty-surfaces-fail-closed")

malformed_api_report = build_hermes_live_boundary_report(raw, surfaces=malformed_api_surfaces())
require("malformed api blocked", malformed_api_report["status"], "contract-only-write-blocked")
require("malformed raw api not mapped", malformed_api_report["writeSurfaces"]["rawArtifact"]["mapped"], False)
require("malformed summary api not mapped", malformed_api_report["writeSurfaces"]["summaryMemory"]["mapped"], False)
require_in("malformed api blocked reason", "Hermes raw artifact write API is not mapped", malformed_api_report["writeGate"]["blockedReasons"])
cases.append("malformed-api-fail-closed")
read_only_api_report = build_hermes_live_boundary_report(raw, surfaces=read_only_api_surfaces())
require("read-only api blocked", read_only_api_report["status"], "contract-only-write-blocked")
require("read-only raw api not mapped", read_only_api_report["writeSurfaces"]["rawArtifact"]["mapped"], False)
require("read-only summary api not mapped", read_only_api_report["writeSurfaces"]["summaryMemory"]["mapped"], False)
require_in("read-only api blocked reason", "Hermes raw artifact write API is not mapped", read_only_api_report["writeGate"]["blockedReasons"])
cases.append("read-only-api-fail-closed")


malformed_report = dict(report)
malformed_report["storageAuthority"] = "just-chill"
require_in("storage authority guard", "storage authority must remain Hermes", validate_hermes_live_boundary_report(malformed_report))
cases.append("authority-guard")
malformed_contract_report = dict(report)
malformed_contract_report["contractAuthority"] = "Hermes"
require_in("contract authority guard", "contract authority must remain just-chill", validate_hermes_live_boundary_report(malformed_contract_report))
cases.append("contract-authority-guard")

print(f"PASS: {len(cases)} just-chill Hermes live-boundary cases passed")
