#!/usr/bin/env python3
"""Acceptance checks for host-owned Hermes MCP lifecycle receipts."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from just_chill_hermes_mcp_receipts import (
    RECEIPT_KIND,
    REQUIRED_TOOLS,
    build_lifecycle_receipt,
    validate_lifecycle_receipt,
)


def require(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle, haystack) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


cases: list[str] = []

with TemporaryDirectory() as temp_root:
    receipt = build_lifecycle_receipt(store_root=Path(temp_root))
    require("receipt kind", receipt["receiptKind"], RECEIPT_KIND)
    require("host owned", receipt["executionOwner"], "host-hermes-mcp-runner")
    require("just-chill no Hermes call", receipt["justChillCallsHermes"], False)
    require("just-chill no execution here", receipt["justChillExecutionAllowedHere"], False)
    require("tools complete", set(receipt["toolManifest"]["tools"]).issuperset(REQUIRED_TOOLS), True)
    require("validation clean", receipt["validationIssues"], [])
    require("raw hash readback", receipt["rawArtifactLifecycle"]["readBackHashMatches"], True)
    require("raw delete", receipt["rawArtifactLifecycle"]["delete"]["status"], "deleted")
    require("raw read after delete blocked", receipt["rawArtifactLifecycle"]["readAfterDeleteBlocked"], True)
    require("rdf hash readback", receipt["rdfGraphLifecycle"]["readBackHashMatches"], True)
    require("rdf delete", receipt["rdfGraphLifecycle"]["delete"]["status"], "deleted")
    require("rdf read after delete blocked", receipt["rdfGraphLifecycle"]["readAfterDeleteBlocked"], True)
    require("vector hash readback", receipt["vectorSidecarLifecycle"]["readBackHashMatches"], True)
    require("vector search returned candidate", receipt["vectorSidecarLifecycle"]["searchReturnedCandidate"], True)
    require("vector search receipt recorded", receipt["vectorSidecarLifecycle"]["searchReceiptRecorded"], True)
    require("vector delete", receipt["vectorSidecarLifecycle"]["delete"]["status"], "deleted")
    require("vector read after delete blocked", receipt["vectorSidecarLifecycle"]["readAfterDeleteBlocked"], True)
    require("sensitive raw blocked", receipt["negativeChecks"]["sensitiveRawCreateWithoutApprovalBlocked"], True)
    require("hash mismatch blocked", receipt["negativeChecks"]["hashMismatchBlocked"], True)
    require("sensitive rdf blocked", receipt["negativeChecks"]["sensitiveRdfCreateWithoutApprovalBlocked"], True)
    require("sensitive vector blocked", receipt["negativeChecks"]["sensitiveVectorCreateWithoutApprovalBlocked"], True)
    require("deleted vector source blocked", receipt["negativeChecks"]["deletedVectorSourceBlocked"], True)
    require("redacted vector source blocked", receipt["negativeChecks"]["redactedVectorSourceBlocked"], True)
    require("active raw zero", receipt["statusAfterLifecycle"]["counts"]["raw"], 0)
    require("active rdf zero", receipt["statusAfterLifecycle"]["counts"]["rdf"], 0)
    require("active vector zero", receipt["statusAfterLifecycle"]["counts"]["vector"], 0)
    require("delete receipts present", receipt["statusAfterLifecycle"]["counts"]["deletions"] >= 3, True)
    cases.append("lifecycle-receipt")

    broken = {**receipt, "rawArtifactLifecycle": {**receipt["rawArtifactLifecycle"], "readBackHashMatches": False}}
    issues = validate_lifecycle_receipt(broken)
    require_in("raw mismatch validation", "raw artifact read-back hash/content mismatch", issues)
    cases.append("validation-fail-closed")
    broken_execution = {**receipt, "justChillExecutionAllowedHere": True}
    issues = validate_lifecycle_receipt(broken_execution)
    require_in("execution flag validation", "just-chill execution must not be allowed in this receipt", issues)
    cases.append("execution-flag-fail-closed")

    missing = {**receipt, "toolManifest": {**receipt["toolManifest"], "missingTools": ["hermes.raw_artifact.create"]}}
    issues = validate_lifecycle_receipt(missing)
    require("missing tool validation", any("missing required MCP tools" in issue for issue in issues), True)
    cases.append("missing-tool-fail-closed")

print(f"PASS: {len(cases)} just-chill Hermes MCP receipt cases passed")
