#!/usr/bin/env python3
"""Acceptance checks for just-chill local raw artifact staging."""
from __future__ import annotations

from tempfile import TemporaryDirectory

from just_chill_hermes_adapter import build_hermes_adapter_stub, validate_adapter_stub
from just_chill_memory_contracts import build_raw_artifact_record, content_hash
from just_chill_raw_artifact_store import (
    ArtifactStoreError,
    build_local_store_plan,
    delete_staged_raw_artifact,
    read_staged_raw_artifact,
    stage_raw_artifact,
    validate_local_store_plan,
)
from just_chill_router import classify_request


cases: list[str] = []


def require(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle, haystack) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


def require_raises(name: str, expected: str, fn) -> None:
    try:
        fn()
    except ArtifactStoreError as exc:
        require_in(name, expected, str(exc))
        return
    raise AssertionError(f"{name}: expected ArtifactStoreError")


packet = classify_request("remember that Hermes owns raw artifact evidence")
content = "Hermes owns raw artifact evidence."
raw = build_raw_artifact_record(packet, content=content)
plan = build_local_store_plan(raw, content=content)
require("plan store", plan["store"], "just-chill-local-raw-artifact-store-v1")
require("plan status", plan["status"], "ready-for-local-stage")
require("plan canonical", plan["canonicalStorageAuthority"], "Hermes")
require("plan hermes unmapped", plan["hermesRawArtifactApiMapped"], False)
require("plan local allowed", plan["writeGate"]["localStagingAllowedHere"], True)
require("plan hermes disallowed", plan["writeGate"]["hermesWriteAllowedHere"], False)
require("plan validation", validate_local_store_plan(plan), [])
cases.append("local-plan-ready")

with TemporaryDirectory() as store_root:
    receipt = stage_raw_artifact(raw, content, store_root=store_root)
    require("write status", receipt["status"], "staged")
    require("write hash", receipt["contentHash"], content_hash(content))
    require("write canonical", receipt["canonicalStorageAuthority"], "Hermes")
    require("write local only", receipt["localOnlyUntilHermesRawApiMapped"], True)

    read_back = read_staged_raw_artifact(raw["artifact"]["id"], store_root=store_root)
    require("read status", read_back["status"], "active")
    require("read content", read_back["content"], content)
    require("read hash valid", read_back["hashValid"], True)

    second_receipt = stage_raw_artifact(raw, content, store_root=store_root)
    require("idempotent write hash", second_receipt["contentHash"], receipt["contentHash"])
    cases.append("write-read-idempotent")

with TemporaryDirectory() as store_root:
    mismatched = build_raw_artifact_record(packet, content="original evidence")
    require_raises(
        "hash mismatch blocked",
        "content hash does not match raw artifact contract",
        lambda: stage_raw_artifact(mismatched, "changed evidence", store_root=store_root),
    )
    cases.append("hash-mismatch-blocked")

sensitive_packet = classify_request("remember my API key sk-test-1234567890 for later")
sensitive_content = "api key sk-test-1234567890"
sensitive_raw = build_raw_artifact_record(sensitive_packet, content=sensitive_content)
with TemporaryDirectory() as store_root:
    sensitive_plan = build_local_store_plan(sensitive_raw, content=sensitive_content, store_root=store_root)
    require("sensitive plan blocked", sensitive_plan["status"], "local-stage-blocked")
    require_in("sensitive blocked reason", "sensitive raw artifact staging requires explicit approval", sensitive_plan["writeGate"]["blockedReasons"])
    require_raises(
        "sensitive write blocked",
        "sensitive raw artifact staging requires explicit approval",
        lambda: stage_raw_artifact(sensitive_raw, sensitive_content, store_root=store_root),
    )

    approved = stage_raw_artifact(
        sensitive_raw,
        sensitive_content,
        store_root=store_root,
        approval_token="operator-approved-sensitive-staging",
    )
    require("approved sensitive staged", approved["status"], "staged")
    require("approved token recorded", approved["approvalTokenPresent"], True)
    require_raises(
        "sensitive read blocked",
        "sensitive raw artifact read requires explicit approval",
        lambda: read_staged_raw_artifact(approved["recordId"], store_root=store_root),
    )
    approved_read = read_staged_raw_artifact(
        approved["recordId"],
        store_root=store_root,
        approval_token="operator-approved-sensitive-read",
    )
    require("approved sensitive read", approved_read["status"], "active")
    require("approved sensitive content", approved_read["content"], sensitive_content)
    cases.append("sensitive-approval-required")

with TemporaryDirectory() as store_root:
    receipt = stage_raw_artifact(raw, content, store_root=store_root)
    require_raises(
        "delete requires approval",
        "deletion requires explicit approval",
        lambda: delete_staged_raw_artifact(receipt["recordId"], reason="cleanup", approval_token=None, store_root=store_root),
    )
    deletion = delete_staged_raw_artifact(
        receipt["recordId"],
        reason="operator-requested cleanup",
        approval_token="operator-approved-deletion",
        store_root=store_root,
    )
    require("delete status", deletion["status"], "deleted")
    read_deleted = read_staged_raw_artifact(receipt["recordId"], store_root=store_root)
    require("read deleted", read_deleted["status"], "deleted")
    require_raises(
        "restage after deletion blocked",
        "raw artifact has a deletion receipt and cannot be restaged",
        lambda: stage_raw_artifact(raw, content, store_root=store_root),
    )
    cases.append("deletion-receipt")

require_raises(
    "invalid id rejected",
    "raw artifact id is invalid",
    lambda: read_staged_raw_artifact("../escape", store_root="/tmp/unused"),
)
cases.append("invalid-id-rejected")

stub = build_hermes_adapter_stub(raw, surfaces={})
local_stage = stub["localArtifactStaging"]
require("stub has local staging", local_stage["store"], "just-chill-local-raw-artifact-store-v1")
require("stub canonical local stage", local_stage["canonicalStorageAuthority"], "Hermes")
require("stub hermes write disabled", local_stage["writeGate"]["hermesWriteAllowedHere"], False)
require("adapter validation", validate_adapter_stub(stub), [])
cases.append("adapter-exposes-local-stage")

print(f"PASS: {len(cases)} just-chill raw artifact store cases passed")
