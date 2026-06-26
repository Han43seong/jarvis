#!/usr/bin/env python3
"""Hermes raw artifact live-boundary discovery for just-chill.

This module probes only read-only Hermes/GJC surfaces, classifies whether a real
Hermes raw artifact create/read/delete API or MCP tool is mapped, and builds a
host-owned promotion plan from local raw artifact staging receipts. It never
calls Hermes write/read/delete APIs itself: Hermes remains the canonical raw
artifact authority and just-chill only emits deterministic plans and guards.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Sequence

from just_chill_memory_contracts import build_raw_artifact_record, validate_contract_record
from just_chill_raw_artifact_store import CANONICAL_STORAGE_AUTHORITY, STORE_NAME, validate_local_store_plan
from just_chill_router import classify_request

SCHEMA_VERSION = 1
BOUNDARY_NAME = "just-chill-hermes-raw-artifact-boundary-v1"
PROMOTION_PLAN_NAME = "just-chill-hermes-raw-artifact-promotion-plan-v1"
RAW_API_PATTERN = re.compile(r"(?:mcp:)?hermes[._:][A-Za-z0-9_.:-]*(?:raw|artifact)[A-Za-z0-9_.:-]*", re.IGNORECASE)
WRITE_TERMS = ("create", "write", "store", "persist", "upsert", "add")
READ_TERMS = ("read", "get", "fetch", "retrieve")
DELETE_TERMS = ("delete", "remove", "redact", "erase")
RAW_TERMS = ("raw", "artifact")
READ_ONLY_PROBES = {
    "hermesHelp": ["hermes", "--help"],
    "hermesMemoryHelp": ["hermes", "memory", "--help"],
    "hermesMcpList": ["hermes", "mcp", "list"],
    "hermesToolsList": ["hermes", "tools", "list"],
    "hermesSetupSmoke": ["gjc", "setup", "hermes", "--smoke", "--json"],
    "justChillMemoryMcpCheck": [sys.executable, str(Path(__file__).with_name("just_chill_hermes_memory_mcp.py")), "--check"],
}
AUTHORITATIVE_API_PROBES = {"hermesMcpList", "hermesToolsList", "mcpList", "toolsList", "justChillMemoryMcpCheck"}

Runner = Callable[[Sequence[str], str | None, int], dict[str, Any]]


class RawBoundaryError(RuntimeError):
    """Raised when a raw artifact promotion plan would be unsafe."""


def default_runner(argv: Sequence[str], cwd: str | None, timeout: int) -> dict[str, Any]:
    completed = subprocess.run(  # noqa: S603 - argv is fixed by READ_ONLY_PROBES callers.
        list(argv),
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    parsed_json: Any | None = None
    if stdout:
        try:
            parsed_json = json.loads(stdout)
        except json.JSONDecodeError:
            parsed_json = None
    return {
        "argv": list(argv),
        "exitCode": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout": stdout,
        "stderr": stderr,
        "json": parsed_json,
    }


def _probe_if_allowed(name: str, *, cwd: str | None, probe: bool, runner: Runner, timeout: int) -> dict[str, Any]:
    argv = list(READ_ONLY_PROBES[name])
    if name == "hermesSetupSmoke":
        argv = ["gjc", "setup", "hermes", "--root", cwd or os.getcwd(), "--smoke", "--json"]
    if not probe:
        return {"argv": argv, "ok": None, "status": "not-probed"}
    try:
        result = runner(argv, cwd, timeout)
        result["status"] = "ok" if result.get("ok") else "failed"
        return result
    except Exception as exc:  # pragma: no cover - exercised through fake runners.
        return {"argv": argv, "ok": False, "status": "error", "error": str(exc)}


def _candidate_texts_from_probe(probe: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    stdout = probe.get("stdout")
    if isinstance(stdout, str) and stdout:
        texts.append(stdout)
    parsed = probe.get("json")
    if parsed is not None:
        texts.append(json.dumps(parsed, ensure_ascii=False, sort_keys=True))
    return texts


def _extract_candidate_apis_from_probes(probes: dict[str, dict[str, Any]]) -> list[str]:
    candidates: set[str] = set()
    for name, probe in probes.items():
        if name not in AUTHORITATIVE_API_PROBES:
            continue
        for text in _candidate_texts_from_probe(probe):
            candidates.update(match.group(0) for match in RAW_API_PATTERN.finditer(text))
    return sorted(candidates)


def _api_has_terms(api: Any, terms: tuple[str, ...]) -> bool:
    if not isinstance(api, str):
        return False
    normalized = api.lower()
    return (
        normalized.startswith(("hermes.", "hermes:", "hermes_", "mcp:hermes.", "mcp:hermes_"))
        and any(term in normalized for term in RAW_TERMS)
        and any(term in normalized for term in terms)
    )


def _first_api(candidates: Sequence[str], terms: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        if _api_has_terms(candidate, terms):
            return candidate
    return None


def _configured_mcp(mcp_probe: dict[str, Any]) -> bool:
    stdout = str(mcp_probe.get("stdout", ""))
    return bool(stdout.strip() and "No MCP servers configured" not in stdout)


def build_raw_artifact_api_report_from_surfaces(surfaces: dict[str, Any] | None) -> dict[str, Any]:
    """Build a raw artifact API report from an existing live-surface map."""

    hermes = (surfaces or {}).get("hermes", {}) if isinstance(surfaces, dict) else {}
    raw_create = hermes.get("rawArtifactApi")
    raw_read = hermes.get("rawArtifactReadApi")
    raw_delete = hermes.get("rawArtifactDeleteApi")
    candidates = [
        value for value in [raw_create, raw_read, raw_delete]
        if isinstance(value, str) and value and value != "unmapped"
    ]
    return build_raw_artifact_api_report_from_candidates(
        candidates,
        probes={
            "memoryStatus": hermes.get("memoryProbe", {}),
            "mcpList": hermes.get("mcpProbe", {}),
            "setupSmoke": hermes.get("setupSmoke", {}),
        },
        command_available=bool(hermes.get("command", {}).get("available")),
    )


def build_raw_artifact_api_report_from_candidates(
    candidates: Sequence[str],
    *,
    probes: dict[str, dict[str, Any]] | None = None,
    command_available: bool | None = None,
) -> dict[str, Any]:
    create_api = _first_api(candidates, WRITE_TERMS)
    read_api = _first_api(candidates, READ_TERMS)
    delete_api = _first_api(candidates, DELETE_TERMS)
    mapped = bool(create_api and read_api and delete_api)
    partial = bool(create_api or read_api or delete_api)
    blocked_reasons: list[str] = []
    if not create_api:
        blocked_reasons.append("Hermes raw artifact create/write API is not mapped")
    if not read_api:
        blocked_reasons.append("Hermes raw artifact read API is not mapped")
    if not delete_api:
        blocked_reasons.append("Hermes raw artifact delete/redact API is not mapped")

    probes = probes or {}
    mcp_probe = probes.get("hermesMcpList") or probes.get("mcpList") or {}
    return {
        "schemaVersion": SCHEMA_VERSION,
        "mapper": BOUNDARY_NAME,
        "storageAuthority": CANONICAL_STORAGE_AUTHORITY,
        "status": "raw-artifact-api-mapped" if mapped else ("raw-artifact-api-partial" if partial else "raw-artifact-api-unmapped"),
        "hermesCommandAvailable": command_available,
        "mcpConfigured": _configured_mcp(mcp_probe),
        "candidateApis": sorted(set(candidate for candidate in candidates if isinstance(candidate, str) and candidate)),
        "rawArtifactApis": {
            "create": {"api": create_api or "unmapped", "mapped": bool(create_api)},
            "read": {"api": read_api or "unmapped", "mapped": bool(read_api)},
            "delete": {"api": delete_api or "unmapped", "mapped": bool(delete_api)},
        },
        "writeGate": {
            "enabled": mapped,
            "allowedHere": False,
            "blockedReasons": blocked_reasons,
        },
        "probes": probes,
        "requiredFutureBinding": [
            "Hermes raw artifact create/write API or MCP tool",
            "Hermes raw artifact read API or MCP tool",
            "Hermes raw artifact delete/redact API or MCP tool",
            "host-owned migration runner that supplies provider/Hermes result evidence",
        ],
    }


def build_raw_artifact_api_report(
    *,
    cwd: str | None = None,
    probe: bool = False,
    runner: Runner | None = None,
    timeout: int = 20,
) -> dict[str, Any]:
    """Probe local read-only Hermes surfaces and report raw artifact API readiness."""

    runner = runner or default_runner
    probes = {
        name: _probe_if_allowed(name, cwd=cwd, probe=probe, runner=runner, timeout=timeout)
        for name in READ_ONLY_PROBES
    }
    candidates = _extract_candidate_apis_from_probes(probes)
    command_available = None
    if probe:
        command_available = probes.get("hermesHelp", {}).get("ok")
    return build_raw_artifact_api_report_from_candidates(candidates, probes=probes, command_available=command_available)


def validate_raw_artifact_api_report(report: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if report.get("schemaVersion") != SCHEMA_VERSION:
        issues.append("schemaVersion mismatch")
    if report.get("mapper") != BOUNDARY_NAME:
        issues.append("mapper name mismatch")
    if report.get("storageAuthority") != CANONICAL_STORAGE_AUTHORITY:
        issues.append("storage authority must remain Hermes")
    gate = report.get("writeGate", {})
    if gate.get("allowedHere") is not False:
        issues.append("raw artifact report must not allow local Hermes writes")
    apis = report.get("rawArtifactApis", {})
    mapped = all(apis.get(name, {}).get("mapped") for name in ["create", "read", "delete"])
    if gate.get("enabled") and not mapped:
        issues.append("write gate cannot enable without create/read/delete APIs")
    if report.get("status") == "raw-artifact-api-mapped" and gate.get("blockedReasons"):
        issues.append("mapped status cannot have blocked reasons")
    return issues


def _artifact(record: dict[str, Any]) -> dict[str, Any]:
    artifact = record.get("artifact")
    if record.get("recordKind") != "raw-artifact-contract" or not isinstance(artifact, dict):
        raise RawBoundaryError("record must be a raw-artifact-contract")
    return artifact


def _local_receipt_issues(record: dict[str, Any], local_receipt: dict[str, Any], *, artifact: dict[str, Any] | None = None) -> list[str]:
    issues: list[str] = []
    artifact = artifact if artifact is not None else _artifact(record)
    if local_receipt.get("store") != STORE_NAME:
        issues.append("local receipt must come from just-chill local raw artifact store")
    if local_receipt.get("status") != "staged":
        issues.append("local receipt must be a staged raw artifact receipt")
    if local_receipt.get("recordId") != artifact.get("id"):
        issues.append("local receipt record id does not match raw artifact")
    if local_receipt.get("contentHash") != artifact.get("contentHash"):
        issues.append("local receipt content hash does not match raw artifact")
    if local_receipt.get("canonicalStorageAuthority") != CANONICAL_STORAGE_AUTHORITY:
        issues.append("local receipt must preserve Hermes as canonical authority")
    paths = local_receipt.get("paths", {})
    local_plan = {
        "schemaVersion": SCHEMA_VERSION,
        "store": STORE_NAME,
        "canonicalStorageAuthority": CANONICAL_STORAGE_AUTHORITY,
        "localStagingAuthority": local_receipt.get("localStagingAuthority"),
        "hermesRawArtifactApiMapped": False,
        "status": "ready-for-local-stage",
        "writeGate": {"hermesWriteAllowedHere": False, "blockedReasons": []},
        "paths": paths,
    }
    issues.extend(validate_local_store_plan(local_plan))
    if not paths.get("contentPath") or not paths.get("writeReceiptPath"):
        issues.append("local receipt must include content and write receipt paths")
    return issues


def build_raw_artifact_hermes_promotion_plan(
    record: dict[str, Any],
    local_receipt: dict[str, Any] | None,
    api_report: dict[str, Any],
    *,
    approval_token: str | None = None,
) -> dict[str, Any]:
    """Plan host-owned promotion from local staging to Hermes raw artifact storage."""

    validation_issues = validate_contract_record(record)
    api_issues = validate_raw_artifact_api_report(api_report)
    blocked_reasons = [*validation_issues, *api_issues]
    try:
        artifact = _artifact(record)
    except RawBoundaryError as exc:
        artifact = {}
        blocked_reasons.append(str(exc))

    if local_receipt is None:
        blocked_reasons.append("local raw artifact staging receipt is required before Hermes promotion")
    else:
        if artifact:
            blocked_reasons.extend(_local_receipt_issues(record, local_receipt, artifact=artifact))

    if api_report.get("writeGate", {}).get("enabled") is not True:
        blocked_reasons.extend(api_report.get("writeGate", {}).get("blockedReasons", []))
    if artifact.get("sensitivity") == "sensitive" and not approval_token:
        blocked_reasons.append("sensitive raw artifact Hermes promotion requires explicit approval")

    apis = api_report.get("rawArtifactApis", {})
    return {
        "schemaVersion": SCHEMA_VERSION,
        "planner": PROMOTION_PLAN_NAME,
        "recordKind": record.get("recordKind"),
        "recordId": artifact.get("id"),
        "status": "ready-for-host-hermes-promotion" if not blocked_reasons else "host-hermes-promotion-blocked",
        "storageAuthority": CANONICAL_STORAGE_AUTHORITY,
        "localStagingAuthority": local_receipt.get("localStagingAuthority") if isinstance(local_receipt, dict) else None,
        "approval": {
            "sensitivity": artifact.get("sensitivity"),
            "approvalTokenPresent": bool(approval_token),
            "sensitiveApproved": artifact.get("sensitivity") != "sensitive" or bool(approval_token),
        },
        "wouldCall": {
            "create": apis.get("create", {}).get("api", "unmapped"),
            "read": apis.get("read", {}).get("api", "unmapped"),
            "delete": apis.get("delete", {}).get("api", "unmapped"),
            "arguments": {
                "recordId": artifact.get("id"),
                "contentHash": artifact.get("contentHash"),
                "sourceLocalContentPath": (local_receipt or {}).get("paths", {}).get("contentPath") if isinstance(local_receipt, dict) else None,
                "sourceLocalReceiptPath": (local_receipt or {}).get("paths", {}).get("writeReceiptPath") if isinstance(local_receipt, dict) else None,
                "provenance": artifact.get("provenance"),
            },
        },
        "executionBoundary": {
            "allowedHere": False,
            "justChillCallsHermes": False,
            "hostMustExecuteHermesApi": True,
            "hermesOwnsCanonicalStorage": True,
        },
        "promotionGate": {
            "enabled": not blocked_reasons,
            "blockedReasons": sorted(set(blocked_reasons)),
        },
        "evidenceRequirements": [
            "host/operator Hermes create result must be supplied before canonical promotion is recorded",
            "Hermes read-back evidence must match the raw artifact content hash",
            "local staging receipt remains migration evidence and is not canonical storage",
            "sensitive promotion requires explicit approval",
        ],
    }


def validate_raw_artifact_hermes_promotion_plan(plan: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if plan.get("schemaVersion") != SCHEMA_VERSION:
        issues.append("schemaVersion mismatch")
    if plan.get("planner") != PROMOTION_PLAN_NAME:
        issues.append("planner name mismatch")
    if plan.get("storageAuthority") != CANONICAL_STORAGE_AUTHORITY:
        issues.append("storage authority must remain Hermes")
    boundary = plan.get("executionBoundary", {})
    if boundary.get("allowedHere") is not False:
        issues.append("promotion plan must not allow local Hermes execution")
    if boundary.get("justChillCallsHermes") is not False:
        issues.append("just-chill must not call Hermes raw artifact APIs directly")
    if boundary.get("hermesOwnsCanonicalStorage") is not True:
        issues.append("Hermes must own canonical raw artifact storage")
    if plan.get("status") == "ready-for-host-hermes-promotion" and plan.get("promotionGate", {}).get("blockedReasons"):
        issues.append("ready promotion plan cannot have blocked reasons")
    return issues


def _load_json_object(raw: str, *, label: str) -> dict[str, Any]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise RawBoundaryError(f"{label} must decode to an object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discover Hermes raw artifact APIs and build fail-closed promotion plans.")
    parser.add_argument("request", nargs="*", help="Request text used for promotion planning when --plan-promotion is set.")
    parser.add_argument("--cwd", default=None, help="Repo/workdir for read-only probes.")
    parser.add_argument("--content", help="Raw artifact content for promotion planning. Defaults to request text.")
    parser.add_argument("--probe", action="store_true", help="Run allowlisted read-only Hermes/GJC probes.")
    parser.add_argument("--approval-token", help="Required for sensitive promotion planning.")
    parser.add_argument("--local-receipt-json", help="Local raw staging receipt JSON for --plan-promotion.")
    parser.add_argument("--plan-promotion", action="store_true", help="Emit a host-owned Hermes promotion plan without writing to Hermes.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    try:
        report = build_raw_artifact_api_report(cwd=args.cwd, probe=args.probe)
        output: dict[str, Any] = {"rawArtifactApiReport": report, "validationIssues": validate_raw_artifact_api_report(report)}
        if args.plan_promotion:
            request = " ".join(args.request).strip()
            if not request:
                raise RawBoundaryError("request text is required for --plan-promotion")
            content = args.content if args.content is not None else request
            record = build_raw_artifact_record(classify_request(request), content=content)
            local_receipt = _load_json_object(args.local_receipt_json, label="local receipt JSON") if args.local_receipt_json else None
            promotion = build_raw_artifact_hermes_promotion_plan(
                record,
                local_receipt,
                report,
                approval_token=args.approval_token,
            )
            output["rawArtifact"] = record
            output["promotionPlan"] = promotion
            output["validationIssues"].extend(validate_raw_artifact_hermes_promotion_plan(promotion))
        print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
        return 0 if not output["validationIssues"] else 1
    except RawBoundaryError as exc:
        print(json.dumps({"schemaVersion": SCHEMA_VERSION, "mapper": BOUNDARY_NAME, "status": "error", "error": str(exc)}, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
