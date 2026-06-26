#!/usr/bin/env python3
"""Acceptance checks for just-chill Hermes raw artifact boundary discovery."""
from __future__ import annotations

from tempfile import TemporaryDirectory

from just_chill_hermes_adapter import build_hermes_adapter_stub, validate_adapter_stub
from just_chill_hermes_raw_artifact_boundary import (
    build_raw_artifact_api_report,
    build_raw_artifact_api_report_from_candidates,
    build_raw_artifact_api_report_from_surfaces,
    build_raw_artifact_hermes_promotion_plan,
    validate_raw_artifact_api_report,
    validate_raw_artifact_hermes_promotion_plan,
)
from just_chill_memory_contracts import build_raw_artifact_record
from just_chill_raw_artifact_store import stage_raw_artifact
from just_chill_router import classify_request


def require(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle, haystack) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


cases: list[str] = []


def fake_runner_unmapped(argv, cwd, timeout):
    if list(argv) == ["hermes", "--help"]:
        return {"argv": list(argv), "exitCode": 0, "ok": True, "stdout": "usage: hermes {memory,mcp,tools}", "stderr": "", "json": None}
    if list(argv) == ["hermes", "memory", "--help"]:
        return {"argv": list(argv), "exitCode": 0, "ok": True, "stdout": "usage: hermes memory {setup,status,off,reset}", "stderr": "", "json": None}
    if list(argv) == ["hermes", "mcp", "list"]:
        return {"argv": list(argv), "exitCode": 0, "ok": True, "stdout": "No MCP servers configured.", "stderr": "", "json": None}
    if list(argv) == ["hermes", "tools", "list"]:
        return {"argv": list(argv), "exitCode": 0, "ok": True, "stdout": "Built-in toolsets: memory", "stderr": "", "json": None}
    if argv[:4] == ["gjc", "setup", "hermes", "--root"]:
        return {"argv": list(argv), "exitCode": 0, "ok": True, "stdout": "{}", "stderr": "", "json": {"ok": True}}
    if list(argv)[-1:] == ["--check"] and "just_chill_hermes_memory_mcp.py" in " ".join(map(str, argv)):
        return {"argv": list(argv), "exitCode": 0, "ok": True, "stdout": "{\"tools\": []}", "stderr": "", "json": {"tools": []}}
    raise AssertionError(f"unexpected argv: {argv!r}")


def fake_runner_mapped(argv, cwd, timeout):
    result = fake_runner_unmapped(argv, cwd, timeout)
    if list(argv) == ["hermes", "tools", "list"]:
        result["stdout"] = (
            "mcp:hermes.raw_artifact.create\n"
            "mcp:hermes.raw_artifact.read\n"
            "mcp:hermes.raw_artifact.delete\n"
        )
    if list(argv) == ["hermes", "mcp", "list"]:
        result["stdout"] = "gjc_hermes_raw_artifact configured"
    return result
def fake_runner_help_false_positive(argv, cwd, timeout):
    result = fake_runner_unmapped(argv, cwd, timeout)
    if list(argv) == ["hermes", "--help"]:
        result["stdout"] = (
            "examples only: mcp:hermes.raw_artifact.create "
            "mcp:hermes.raw_artifact.read mcp:hermes.raw_artifact.delete"
        )
    return result



unmapped_report = build_raw_artifact_api_report(cwd="/home/hskim/jarvis", probe=True, runner=fake_runner_unmapped)
require("unmapped status", unmapped_report["status"], "raw-artifact-api-unmapped")
require("unmapped gate", unmapped_report["writeGate"]["enabled"], False)
require_in("unmapped create blocker", "Hermes raw artifact create/write API is not mapped", unmapped_report["writeGate"]["blockedReasons"])
require("unmapped validation", validate_raw_artifact_api_report(unmapped_report), [])
cases.append("unmapped-fail-closed")

help_false_positive_report = build_raw_artifact_api_report(
    cwd="/home/hskim/jarvis",
    probe=True,
    runner=fake_runner_help_false_positive,
)
require("help false-positive status", help_false_positive_report["status"], "raw-artifact-api-unmapped")
require("help false-positive candidates ignored", help_false_positive_report["candidateApis"], [])
cases.append("help-text-candidates-ignored")

mapped_report = build_raw_artifact_api_report(cwd="/home/hskim/jarvis", probe=True, runner=fake_runner_mapped)
require("mapped status", mapped_report["status"], "raw-artifact-api-mapped")
require("mapped gate", mapped_report["writeGate"]["enabled"], True)
require("mapped create api", mapped_report["rawArtifactApis"]["create"]["api"], "mcp:hermes.raw_artifact.create")
require("mapped read api", mapped_report["rawArtifactApis"]["read"]["api"], "mcp:hermes.raw_artifact.read")
require("mapped delete api", mapped_report["rawArtifactApis"]["delete"]["api"], "mcp:hermes.raw_artifact.delete")
require("mapped validation", validate_raw_artifact_api_report(mapped_report), [])
cases.append("mapped-api-report")
underscore_report = build_raw_artifact_api_report_from_candidates([
    "hermes_raw_artifact_create",
    "hermes_raw_artifact_read",
    "hermes_raw_artifact_delete",
])
require("underscore mcp-style mapped", underscore_report["status"], "raw-artifact-api-mapped")
require("underscore validation", validate_raw_artifact_api_report(underscore_report), [])
cases.append("underscore-tool-name-map")
artifact_only_report = build_raw_artifact_api_report_from_candidates([
    "hermes.artifact.create",
    "hermes.artifact.read",
    "hermes.artifact.delete",
])
require("artifact-only api mapped", artifact_only_report["status"], "raw-artifact-api-mapped")
require("artifact-only validation", validate_raw_artifact_api_report(artifact_only_report), [])
cases.append("artifact-only-tool-name-map")


partial_report = build_raw_artifact_api_report_from_candidates(["hermes.raw_artifact.create"])
require("partial status", partial_report["status"], "raw-artifact-api-partial")
require("partial gate", partial_report["writeGate"]["enabled"], False)
require_in("partial read blocker", "Hermes raw artifact read API is not mapped", partial_report["writeGate"]["blockedReasons"])
require("partial validation", validate_raw_artifact_api_report(partial_report), [])
cases.append("partial-api-blocked")

surface_report = build_raw_artifact_api_report_from_surfaces({
    "hermes": {
        "command": {"available": True},
        "rawArtifactApi": "hermes.raw_artifact.create",
        "rawArtifactReadApi": "hermes.raw_artifact.read",
        "rawArtifactDeleteApi": "hermes.raw_artifact.delete",
        "mcpProbe": {"ok": True, "stdout": "raw artifact server configured"},
    }
})
require("surface mapped", surface_report["status"], "raw-artifact-api-mapped")
require("surface command available", surface_report["hermesCommandAvailable"], True)
require("surface mcp configured", surface_report["mcpConfigured"], True)
cases.append("surface-map-ready")
empty_surface_report = build_raw_artifact_api_report_from_surfaces({"hermes": {"rawArtifactApi": "unmapped"}})
require("surface sentinel filtered", empty_surface_report["candidateApis"], [])
require("surface sentinel status", empty_surface_report["status"], "raw-artifact-api-unmapped")
cases.append("surface-sentinel-filtered")


packet = classify_request("remember that Hermes owns raw artifact evidence")
content = "Hermes owns raw artifact evidence."
raw = build_raw_artifact_record(packet, content=content)
with TemporaryDirectory() as store_root:
    receipt = stage_raw_artifact(raw, content, store_root=store_root)
    blocked_promotion = build_raw_artifact_hermes_promotion_plan(raw, receipt, unmapped_report)
    require("blocked promotion", blocked_promotion["status"], "host-hermes-promotion-blocked")
    require_in("blocked promotion reason", "Hermes raw artifact create/write API is not mapped", blocked_promotion["promotionGate"]["blockedReasons"])
    require("blocked promotion validation", validate_raw_artifact_hermes_promotion_plan(blocked_promotion), [])

    ready_promotion = build_raw_artifact_hermes_promotion_plan(raw, receipt, mapped_report)
    require("ready promotion", ready_promotion["status"], "ready-for-host-hermes-promotion")
    require("ready no local execution", ready_promotion["executionBoundary"]["allowedHere"], False)
    require("ready hermes owner", ready_promotion["executionBoundary"]["hermesOwnsCanonicalStorage"], True)
    require("ready create call", ready_promotion["wouldCall"]["create"], "mcp:hermes.raw_artifact.create")
    require("ready validation", validate_raw_artifact_hermes_promotion_plan(ready_promotion), [])

    mismatched = dict(receipt)
    mismatched["contentHash"] = "sha256:mismatch"
    mismatch_promotion = build_raw_artifact_hermes_promotion_plan(raw, mismatched, mapped_report)
    require("mismatch promotion blocked", mismatch_promotion["status"], "host-hermes-promotion-blocked")
    require_in("mismatch reason", "local receipt content hash does not match raw artifact", mismatch_promotion["promotionGate"]["blockedReasons"])
    cases.append("promotion-gates")
non_raw_record = {"schemaVersion": 1, "recordKind": "summary-memory-contract"}
non_raw_promotion = build_raw_artifact_hermes_promotion_plan(non_raw_record, {}, mapped_report)
require("non-raw promotion blocked", non_raw_promotion["status"], "host-hermes-promotion-blocked")
require_in("non-raw promotion reason", "record must be a raw-artifact-contract", non_raw_promotion["promotionGate"]["blockedReasons"])
require("non-raw promotion validation", validate_raw_artifact_hermes_promotion_plan(non_raw_promotion), [])
cases.append("non-raw-promotion-fails-closed")

sensitive_packet = classify_request("remember my API key sk-test-1234567890 for later")
sensitive_content = "api key sk-test-1234567890"
sensitive_raw = build_raw_artifact_record(sensitive_packet, content=sensitive_content)
with TemporaryDirectory() as store_root:
    sensitive_receipt = stage_raw_artifact(
        sensitive_raw,
        sensitive_content,
        store_root=store_root,
        approval_token="operator-approved-local-stage",
    )
    sensitive_blocked = build_raw_artifact_hermes_promotion_plan(sensitive_raw, sensitive_receipt, mapped_report)
    require("sensitive promotion blocked", sensitive_blocked["status"], "host-hermes-promotion-blocked")
    require_in("sensitive approval blocker", "sensitive raw artifact Hermes promotion requires explicit approval", sensitive_blocked["promotionGate"]["blockedReasons"])
    sensitive_ready = build_raw_artifact_hermes_promotion_plan(
        sensitive_raw,
        sensitive_receipt,
        mapped_report,
        approval_token="operator-approved-hermes-promotion",
    )
    require("sensitive promotion ready", sensitive_ready["status"], "ready-for-host-hermes-promotion")
    require("sensitive approval recorded", sensitive_ready["approval"]["approvalTokenPresent"], True)
    cases.append("sensitive-promotion-approval")

stub = build_hermes_adapter_stub(raw, surfaces={})
require("adapter exposes raw discovery", stub["rawArtifactApiDiscovery"]["mapper"], "just-chill-hermes-raw-artifact-boundary-v1")
require("adapter raw discovery blocked", stub["rawArtifactApiDiscovery"]["status"], "raw-artifact-api-unmapped")
require("adapter validation", validate_adapter_stub(stub), [])
cases.append("adapter-exposes-raw-discovery")

print(f"PASS: {len(cases)} just-chill Hermes raw artifact boundary cases passed")
