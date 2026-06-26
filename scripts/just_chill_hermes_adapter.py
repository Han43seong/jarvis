#!/usr/bin/env python3
"""Hermes live-boundary adapter stub for just-chill memory contracts.

The adapter consumes deterministic records from ``just_chill_memory_contracts``
and emits both adapter stubs and live-boundary reports for Hermes. Canonical
Hermes writes remain disabled unless a real Hermes API is mapped; raw artifact
contracts may include a local staging plan so source evidence can be preserved
without claiming Hermes storage authority.
"""
from __future__ import annotations

import argparse
import json
from typing import Any

from just_chill_live_bindings import discover_live_surfaces
from just_chill_memory_contracts import (
    build_raw_artifact_record,
    build_summary_memory_record,
    validate_contract_record,
)
from just_chill_raw_artifact_store import build_local_store_plan, validate_local_store_plan
from just_chill_hermes_raw_artifact_boundary import (
    build_raw_artifact_api_report_from_surfaces,
    validate_raw_artifact_api_report,
)
from just_chill_summary_memory_receipts import (
    build_summary_provider_receipt_plan,
    validate_summary_provider_receipt_plan,
)
from just_chill_router import classify_request

SCHEMA_VERSION = 1
ADAPTER_NAME = "just-chill-hermes-boundary-adapter-v1"
HERMES_BOUNDARY_NAME = "just-chill-hermes-live-boundary-v1"


def _record_id(record: dict[str, Any]) -> str | None:
    if record.get("recordKind") == "raw-artifact-contract":
        return record.get("artifact", {}).get("id")
    if record.get("recordKind") == "summary-memory-contract":
        return record.get("summaryMemory", {}).get("id")
    return None


def _record_sensitivity(record: dict[str, Any]) -> str | None:
    if record.get("recordKind") == "raw-artifact-contract":
        return record.get("artifact", {}).get("sensitivity")
    if record.get("recordKind") == "summary-memory-contract":
        return record.get("summaryMemory", {}).get("sensitivity")
    return None


WRITE_ACTION_TERMS = ("add", "create", "write", "store", "persist", "upsert")


def _is_mapped_hermes_api(value: Any, *, required_terms: tuple[str, ...]) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    if not normalized or normalized == "unmapped":
        return False
    if not (
        normalized.startswith("hermes.")
        or normalized.startswith("hermes:")
        or normalized.startswith("mcp:hermes.")
    ):
        return False
    return (
        all(term in normalized for term in required_terms)
        and any(term in normalized for term in WRITE_ACTION_TERMS)
    )

def _summary_memory_provider_tool_ready(hermes: dict[str, Any]) -> bool:
    surface = hermes.get("memoryProviderSurface", {})
    return bool(surface.get("summaryMemoryWriteAvailable"))


def _provider_tool_write_plan(record: dict[str, Any], hermes: dict[str, Any]) -> dict[str, Any] | None:
    surface = hermes.get("memoryProviderSurface", {})
    tool = surface.get("tool", {})
    if record.get("recordKind") != "summary-memory-contract":
        return None
    if not surface.get("summaryMemoryWriteAvailable"):
        return None
    summary = record.get("summaryMemory", {})
    return {
        "type": "hermes-memory-provider-tool",
        "api": surface.get("summaryMemoryApi"),
        "provider": surface.get("provider"),
        "storageMode": surface.get("storageMode"),
        "tool": tool.get("name"),
        "arguments": {
            "action": tool.get("writeAction", "add"),
            "content": summary.get("summary"),
            "category": "project",
            "tags": ",".join([
                "just-chill",
                "summary-memory",
                str(summary.get("id")),
            ]),
        },
        "provenance": {
            "sourceArtifactRefs": summary.get("sourceArtifactRefs", []),
            "summaryHash": summary.get("summaryHash"),
            "rawContentHash": summary.get("provenance", {}).get("rawContentHash"),
        },
        "executionBoundary": surface.get("boundary"),
        "allowedHere": False,
    }



def build_hermes_live_boundary_report(
    record: dict[str, Any],
    *,
    surfaces: dict[str, Any] | None = None,
    approval_token: str | None = None,
) -> dict[str, Any]:
    """Map actual Hermes host surfaces without claiming unmapped write authority."""

    validation_issues = validate_contract_record(record)
    if surfaces is None:
        surfaces = discover_live_surfaces(probe=False)
    hermes = surfaces.get("hermes", {})
    sensitivity = _record_sensitivity(record)
    raw_api = hermes.get("rawArtifactApi", "unmapped")
    summary_api = hermes.get("summaryMemoryApi", "unmapped")
    live_write_available = bool(hermes.get("liveStorageWriteAvailable"))
    provider_tool_summary_ready = _summary_memory_provider_tool_ready(hermes)
    raw_mapped = _is_mapped_hermes_api(raw_api, required_terms=("raw", "artifact"))
    summary_mapped = _is_mapped_hermes_api(summary_api, required_terms=("summary", "memory"))
    raw_write_ready = live_write_available and raw_mapped
    summary_write_ready = (live_write_available and summary_mapped) or provider_tool_summary_ready
    sensitive_approved = sensitivity != "sensitive" or bool(approval_token)

    blocked_reasons = [*validation_issues]
    if record.get("recordKind") == "raw-artifact-contract" and not raw_write_ready:
        blocked_reasons.append("Hermes raw artifact write API is not mapped")
    if record.get("recordKind") == "summary-memory-contract" and not summary_write_ready:
        blocked_reasons.append("Hermes summary memory write API is not mapped")
    if sensitivity == "sensitive" and not approval_token:
        blocked_reasons.append("sensitive memory requires explicit approval before any Hermes write")
    if record.get("liveBinding", {}).get("status") != "contract-only":
        blocked_reasons.append("record must remain contract-only until Hermes write API is mapped")

    return {
        "schemaVersion": SCHEMA_VERSION,
        "mapper": HERMES_BOUNDARY_NAME,
        "recordKind": record.get("recordKind"),
        "recordId": _record_id(record),
        "storageAuthority": "Hermes",
        "contractAuthority": "just-chill",
        "status": "ready-for-hermes-write" if not blocked_reasons else "contract-only-write-blocked",
        "approval": {
            "sensitivity": sensitivity,
            "approvalTokenPresent": bool(approval_token),
            "sensitiveApproved": sensitive_approved,
        },
        "readSurfaces": {
            "memoryStatus": {
                "available": bool(hermes.get("memoryProbe", {}).get("ok")),
                "provider": hermes.get("memoryProvider"),
                "purpose": "status-only; not artifact or memory recall",
            },
            "mcpList": {
                "available": bool(hermes.get("mcpProbe", {}).get("ok")),
                "configured": bool(str(hermes.get("mcpProbe", {}).get("stdout", "")).strip() and "No MCP servers configured" not in str(hermes.get("mcpProbe", {}).get("stdout", ""))),
                "purpose": "MCP configuration visibility",
            },
            "setupSmoke": {
                "available": bool(hermes.get("setupSmoke", {}).get("ok")),
                "purpose": "render/smoke only; writes no Hermes memory",
            },
        },
        "writeSurfaces": {
            "rawArtifact": {
                "api": raw_api,
                "mapped": raw_mapped,
                "writeAvailable": raw_write_ready,
            },
            "summaryMemory": {
                "api": summary_api,
                "mapped": summary_mapped or provider_tool_summary_ready,
                "writeAvailable": summary_write_ready,
            },
            "memoryProviderTool": hermes.get("memoryProviderSurface", {}),
            "liveStorageWriteAvailable": live_write_available,
        },
        "writeGate": {
            "enabled": not blocked_reasons,
            "allowedHere": False,
            "blockedReasons": blocked_reasons,
        },
        "requiredFutureBinding": [
            "Hermes raw artifact create/read API or MCP tool",
            "Hermes summary memory create/read/search API or MCP tool",
            "explicit approval token for sensitive retention",
            "RDF/OWL TBox/ABox classification and SHACL validation before canonical promotion",
        ],
    }


def validate_hermes_live_boundary_report(report: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if report.get("schemaVersion") != SCHEMA_VERSION:
        issues.append("schemaVersion mismatch")
    if report.get("mapper") != HERMES_BOUNDARY_NAME:
        issues.append("mapper name mismatch")
    if report.get("storageAuthority") != "Hermes":
        issues.append("storage authority must remain Hermes")
    if report.get("contractAuthority") != "just-chill":
        issues.append("contract authority must remain just-chill")
    write_gate = report.get("writeGate", {})
    if write_gate.get("allowedHere") is not False:
        issues.append("Hermes writes must not be performed by just-chill locally")
    writes = report.get("writeSurfaces", {})
    provider_tool_ready = bool(writes.get("memoryProviderTool", {}).get("summaryMemoryWriteAvailable"))
    if write_gate.get("enabled") and not (writes.get("liveStorageWriteAvailable") or provider_tool_ready):
        issues.append("write gate cannot enable without live Hermes storage availability or provider tool")
    if write_gate.get("enabled"):
        record_kind = report.get("recordKind")
        if record_kind == "raw-artifact-contract" and not writes.get("rawArtifact", {}).get("writeAvailable"):
            issues.append("raw artifact write gate cannot enable without mapped raw artifact API")
        if record_kind == "summary-memory-contract" and not writes.get("summaryMemory", {}).get("writeAvailable"):
            issues.append("summary memory write gate cannot enable without mapped summary memory API or provider tool")
    if report.get("status") == "ready-for-hermes-write" and write_gate.get("blockedReasons"):
        issues.append("ready status cannot have blocked reasons")
    return issues



def build_hermes_adapter_stub(
    record: dict[str, Any],
    *,
    surfaces: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a fail-closed Hermes adapter envelope for a contract record."""
    if surfaces is None:
        surfaces = discover_live_surfaces(probe=False)
    hermes = surfaces.get("hermes", {})
    live_report = build_hermes_live_boundary_report(record, surfaces=surfaces)
    live_write_available = bool(hermes.get("liveStorageWriteAvailable"))
    record_kind = record.get("recordKind")
    blocked_reasons = list(live_report.get("writeGate", {}).get("blockedReasons", []))
    provider_tool_plan = _provider_tool_write_plan(record, hermes)
    local_artifact_plan = (
        build_local_store_plan(record)
        if record_kind == "raw-artifact-contract"
        else None
    )
    raw_api_discovery = (
        build_raw_artifact_api_report_from_surfaces(surfaces)
        if record_kind == "raw-artifact-contract"
        else None
    )
    summary_receipt_plan = (
        build_summary_provider_receipt_plan(record, surfaces, operation="add")
        if record_kind == "summary-memory-contract"
        else None
    )

    return {
        "schemaVersion": SCHEMA_VERSION,
        "adapter": ADAPTER_NAME,
        "recordKind": record_kind,
        "recordId": _record_id(record),
        "storageAuthority": "Hermes",
        "justChillAuthority": [
            "policy decision",
            "candidate record construction",
            "approval and promotion gate",
        ],
        "liveBoundary": {
            "status": "write-blocked" if blocked_reasons else "ready-for-hermes-write",
            "hermesCommandAvailable": bool(hermes.get("command", {}).get("available")),
            "memoryProvider": hermes.get("memoryProvider"),
            "memoryProviderSurface": hermes.get("memoryProviderSurface", {}),
            "rawArtifactApi": hermes.get("rawArtifactApi", "unmapped"),
            "summaryMemoryApi": hermes.get("summaryMemoryApi", "unmapped"),
            "memoryToolWriteAvailable": bool(hermes.get("memoryToolWriteAvailable")),
            "liveStorageWriteAvailable": live_write_available,
        },
        "liveBoundaryReport": live_report,
        "localArtifactStaging": local_artifact_plan,
        "rawArtifactApiDiscovery": raw_api_discovery,
        "summaryProviderReceiptPlan": summary_receipt_plan,
        "writePlan": {
            "enabled": not blocked_reasons,
            "allowedHere": False,
            "wouldCall": provider_tool_plan if not blocked_reasons else None,
            "blockedReasons": blocked_reasons,
        },
        "requiredFutureBinding": [
            "Hermes raw artifact create/read API or MCP tool",
            "Hermes summary memory create/read API or MCP tool",
            "explicit approval token for sensitive retention",
            "SHACL validation before canonical promotion",
        ],
    }


def validate_adapter_stub(stub: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if stub.get("schemaVersion") != SCHEMA_VERSION:
        issues.append("schemaVersion mismatch")
    if stub.get("adapter") != ADAPTER_NAME:
        issues.append("adapter name mismatch")
    write_plan = stub.get("writePlan", {})
    if write_plan.get("allowedHere") is not False:
        issues.append("adapter must not allow just-chill-local writes")
    provider_tool_ready = bool(stub.get("liveBoundary", {}).get("memoryToolWriteAvailable"))
    if write_plan.get("enabled") and not (stub.get("liveBoundary", {}).get("liveStorageWriteAvailable") or provider_tool_ready):
        issues.append("writePlan cannot enable writes without live Hermes storage availability or provider tool")
    if stub.get("storageAuthority") != "Hermes":
        issues.append("storage authority must remain Hermes")
    local_stage = stub.get("localArtifactStaging")
    if local_stage is not None:
        issues.extend(validate_local_store_plan(local_stage))
        if local_stage.get("canonicalStorageAuthority") != "Hermes":
            issues.append("local artifact staging must keep Hermes as canonical authority")
    raw_api_discovery = stub.get("rawArtifactApiDiscovery")
    if raw_api_discovery is not None:
        issues.extend(validate_raw_artifact_api_report(raw_api_discovery))
    summary_receipt_plan = stub.get("summaryProviderReceiptPlan")
    if summary_receipt_plan is not None:
        issues.extend(validate_summary_provider_receipt_plan(summary_receipt_plan))
        if summary_receipt_plan.get("canonicalMemoryAuthority") != "Hermes":
            issues.append("summary receipt bridge must keep Hermes as canonical authority")
    issues.extend(validate_hermes_live_boundary_report(stub.get("liveBoundaryReport", {})))
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a fail-closed Hermes adapter stub for just-chill memory contracts.")
    parser.add_argument("request", nargs="*", help="User request text.")
    parser.add_argument("--summary", help="Also build a summary memory contract and adapter stub.")
    parser.add_argument("--cwd", default=None, help="Repo/workdir for optional surface discovery.")
    parser.add_argument("--probe", action="store_true", help="Run allowlisted read-only surface probes.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    packet = classify_request(" ".join(args.request))
    surfaces = discover_live_surfaces(cwd=args.cwd, probe=args.probe)
    raw = build_raw_artifact_record(packet)
    raw_stub = build_hermes_adapter_stub(raw, surfaces=surfaces)
    output: dict[str, Any] = {
        "rawArtifact": raw,
        "rawAdapter": raw_stub,
        "rawLiveBoundary": raw_stub["liveBoundaryReport"],
        "validationIssues": [*validate_contract_record(raw), *validate_adapter_stub(raw_stub)],
    }
    if args.summary is not None:
        summary = build_summary_memory_record(raw, args.summary)
        summary_stub = build_hermes_adapter_stub(summary, surfaces=surfaces)
        output["summaryMemory"] = summary
        output["summaryAdapter"] = summary_stub
        output["summaryLiveBoundary"] = summary_stub["liveBoundaryReport"]
        output["validationIssues"].extend(validate_contract_record(summary))
        output["validationIssues"].extend(validate_adapter_stub(summary_stub))
    print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if not output["validationIssues"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
