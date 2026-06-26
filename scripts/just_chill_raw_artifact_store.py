#!/usr/bin/env python3
"""Local raw artifact staging store for just-chill.

This module provides a deterministic, host-owned local staging layer for raw
artifact contracts while the canonical Hermes raw artifact API remains unmapped.
It intentionally does not claim Hermes storage authority: Hermes remains the
canonical memory/artifact authority, and this store is only a repo-local bridge
that preserves content, hashes, approval-gated sensitive reads, deletion
receipts, and provenance until a real Hermes artifact write/read/delete surface
is bound.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from just_chill_memory_contracts import (
    build_raw_artifact_record,
    content_hash,
    validate_contract_record,
)
from just_chill_router import classify_request

SCHEMA_VERSION = 1
STORE_NAME = "just-chill-local-raw-artifact-store-v1"
LOCAL_STAGING_AUTHORITY = "just-chill-host-local-artifact-staging"
CANONICAL_STORAGE_AUTHORITY = "Hermes"
ARTIFACT_ID_PATTERN = re.compile(r"^raw_[0-9a-f]{20}$")


class ArtifactStoreError(RuntimeError):
    """Raised when a local artifact staging operation is not policy-safe."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def default_store_root(cwd: str | None = None) -> Path:
    """Return the ignored repo-local staging root without creating it."""

    root = Path(cwd or os.getcwd()).resolve()
    return root / "tmp" / "just-chill-artifacts"


def _canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _safe_record_id(record_id: str) -> str:
    if not ARTIFACT_ID_PATTERN.fullmatch(record_id):
        raise ArtifactStoreError("raw artifact id is invalid")
    return record_id


def artifact_paths(record_id: str, *, store_root: str | Path | None = None, cwd: str | None = None) -> dict[str, str]:
    safe_id = _safe_record_id(record_id)
    root = Path(store_root).resolve() if store_root is not None else default_store_root(cwd)
    artifact_dir = root / safe_id
    return {
        "storeRoot": str(root),
        "artifactDir": str(artifact_dir),
        "contentPath": str(artifact_dir / "content.txt"),
        "contractPath": str(artifact_dir / "contract.json"),
        "writeReceiptPath": str(artifact_dir / "write-receipt.json"),
        "deleteReceiptPath": str(artifact_dir / "delete-receipt.json"),
    }


def _artifact(record: dict[str, Any]) -> dict[str, Any]:
    if record.get("recordKind") != "raw-artifact-contract":
        raise ArtifactStoreError("record must be a raw-artifact-contract")
    artifact = record.get("artifact")
    if not isinstance(artifact, dict):
        raise ArtifactStoreError("record missing artifact object")
    return artifact


def _blocked_reasons(record: dict[str, Any], *, content: str | None, approval_token: str | None, store_root: str | Path | None = None, cwd: str | None = None) -> list[str]:
    reasons = validate_contract_record(record)
    try:
        artifact = _artifact(record)
        record_id = _safe_record_id(str(artifact.get("id", "")))
    except ArtifactStoreError as exc:
        return [*reasons, str(exc)]

    if artifact.get("deletionState") != "active":
        reasons.append("only active raw artifacts can be staged")
    if artifact.get("sensitivity") == "sensitive" and not approval_token:
        reasons.append("sensitive raw artifact staging requires explicit approval")
    if content is not None and content_hash(content) != artifact.get("contentHash"):
        reasons.append("content hash does not match raw artifact contract")

    paths = artifact_paths(record_id, store_root=store_root, cwd=cwd)
    delete_receipt = Path(paths["deleteReceiptPath"])
    content_path = Path(paths["contentPath"])
    if delete_receipt.exists():
        reasons.append("raw artifact has a deletion receipt and cannot be restaged")
    if content is not None and content_path.exists():
        existing_hash = content_hash(content_path.read_text(encoding="utf-8"))
        if existing_hash != artifact.get("contentHash"):
            reasons.append("existing staged artifact content hash differs from contract")
    return reasons


def build_local_store_plan(
    record: dict[str, Any],
    *,
    content: str | None = None,
    store_root: str | Path | None = None,
    cwd: str | None = None,
    approval_token: str | None = None,
) -> dict[str, Any]:
    """Return a deterministic local staging plan for a raw artifact contract."""

    try:
        artifact = _artifact(record)
        record_id = _safe_record_id(str(artifact.get("id", "")))
        paths = artifact_paths(record_id, store_root=store_root, cwd=cwd)
        sensitivity = artifact.get("sensitivity")
    except ArtifactStoreError as exc:
        paths = {}
        sensitivity = None
        record_id = record.get("artifact", {}).get("id")
        blocked_reasons = [str(exc)]
    else:
        blocked_reasons = _blocked_reasons(
            record,
            content=content,
            approval_token=approval_token,
            store_root=store_root,
            cwd=cwd,
        )

    return {
        "schemaVersion": SCHEMA_VERSION,
        "store": STORE_NAME,
        "recordKind": record.get("recordKind"),
        "recordId": record_id,
        "status": "ready-for-local-stage" if not blocked_reasons else "local-stage-blocked",
        "canonicalStorageAuthority": CANONICAL_STORAGE_AUTHORITY,
        "localStagingAuthority": LOCAL_STAGING_AUTHORITY,
        "hermesRawArtifactApiMapped": False,
        "localOnlyUntilHermesRawApiMapped": True,
        "sensitivity": sensitivity,
        "paths": paths,
        "writeGate": {
            "enabled": not blocked_reasons,
            "localStagingAllowedHere": not blocked_reasons,
            "hermesWriteAllowedHere": False,
            "approvalTokenPresent": bool(approval_token),
            "blockedReasons": blocked_reasons,
        },
        "evidenceRequirements": [
            "content hash must match the raw artifact contract",
            "write receipt must include local path, hash, sensitivity, and approval state",
            "deletion must leave a durable deletion receipt",
            "Hermes canonical promotion remains blocked until a real raw artifact API is mapped",
        ],
    }


def validate_local_store_plan(plan: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if plan.get("schemaVersion") != SCHEMA_VERSION:
        issues.append("schemaVersion mismatch")
    if plan.get("store") != STORE_NAME:
        issues.append("store name mismatch")
    if plan.get("canonicalStorageAuthority") != CANONICAL_STORAGE_AUTHORITY:
        issues.append("canonical storage authority must remain Hermes")
    if plan.get("localStagingAuthority") != LOCAL_STAGING_AUTHORITY:
        issues.append("local staging authority mismatch")
    gate = plan.get("writeGate", {})
    if gate.get("hermesWriteAllowedHere") is not False:
        issues.append("local store must not claim Hermes write authority")
    if plan.get("hermesRawArtifactApiMapped") is not False:
        issues.append("local store must not claim a mapped Hermes raw artifact API")
    if plan.get("status") == "ready-for-local-stage" and gate.get("blockedReasons"):
        issues.append("ready local staging plan cannot have blocked reasons")
    return issues


def stage_raw_artifact(
    record: dict[str, Any],
    content: str,
    *,
    store_root: str | Path | None = None,
    cwd: str | None = None,
    approval_token: str | None = None,
) -> dict[str, Any]:
    """Write a raw artifact to the local staging store and return a receipt."""

    plan = build_local_store_plan(
        record,
        content=content,
        store_root=store_root,
        cwd=cwd,
        approval_token=approval_token,
    )
    issues = validate_local_store_plan(plan)
    if issues:
        raise ArtifactStoreError("; ".join(issues))
    blocked = plan.get("writeGate", {}).get("blockedReasons", [])
    if blocked:
        raise ArtifactStoreError("; ".join(blocked))

    artifact = _artifact(record)
    paths = plan["paths"]
    artifact_dir = Path(paths["artifactDir"])
    artifact_dir.mkdir(parents=True, exist_ok=True)

    content_path = Path(paths["contentPath"])
    contract_path = Path(paths["contractPath"])
    write_receipt_path = Path(paths["writeReceiptPath"])

    content_path.write_text(content, encoding="utf-8")
    contract_path.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = {
        "schemaVersion": SCHEMA_VERSION,
        "store": STORE_NAME,
        "operation": "stage-raw-artifact",
        "status": "staged",
        "recordId": artifact["id"],
        "canonicalStorageAuthority": CANONICAL_STORAGE_AUTHORITY,
        "localStagingAuthority": LOCAL_STAGING_AUTHORITY,
        "hermesRawArtifactApiMapped": False,
        "localOnlyUntilHermesRawApiMapped": True,
        "contentHash": artifact["contentHash"],
        "contentBytes": len(content.encode("utf-8")),
        "sensitivity": artifact.get("sensitivity"),
        "approvalTokenPresent": bool(approval_token),
        "createdAt": now_iso(),
        "paths": paths,
        "provenance": artifact.get("provenance", {}),
    }
    write_receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def read_staged_raw_artifact(
    record_id: str,
    *,
    store_root: str | Path | None = None,
    cwd: str | None = None,
    approval_token: str | None = None,
) -> dict[str, Any]:
    safe_id = _safe_record_id(record_id)
    paths = artifact_paths(safe_id, store_root=store_root, cwd=cwd)
    delete_receipt_path = Path(paths["deleteReceiptPath"])
    if delete_receipt_path.exists():
        return {
            "schemaVersion": SCHEMA_VERSION,
            "store": STORE_NAME,
            "operation": "read-raw-artifact",
            "status": "deleted",
            "recordId": safe_id,
            "paths": paths,
            "deleteReceipt": json.loads(delete_receipt_path.read_text(encoding="utf-8")),
        }

    content_path = Path(paths["contentPath"])
    receipt_path = Path(paths["writeReceiptPath"])
    if not content_path.exists() or not receipt_path.exists():
        raise ArtifactStoreError("staged raw artifact is missing content or receipt")

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("sensitivity") == "sensitive" and not approval_token:
        raise ArtifactStoreError("sensitive raw artifact read requires explicit approval")
    content = content_path.read_text(encoding="utf-8")
    actual_hash = content_hash(content)
    expected_hash = receipt.get("contentHash")
    return {
        "schemaVersion": SCHEMA_VERSION,
        "store": STORE_NAME,
        "operation": "read-raw-artifact",
        "status": "active",
        "recordId": safe_id,
        "content": content,
        "contentHash": actual_hash,
        "hashValid": actual_hash == expected_hash,
        "paths": paths,
        "writeReceipt": receipt,
    }


def delete_staged_raw_artifact(
    record_id: str,
    *,
    reason: str,
    approval_token: str | None,
    store_root: str | Path | None = None,
    cwd: str | None = None,
) -> dict[str, Any]:
    if not approval_token:
        raise ArtifactStoreError("deletion requires explicit approval")
    if not reason.strip():
        raise ArtifactStoreError("deletion requires a reason")

    safe_id = _safe_record_id(record_id)
    paths = artifact_paths(safe_id, store_root=store_root, cwd=cwd)
    content_path = Path(paths["contentPath"])
    receipt_path = Path(paths["writeReceiptPath"])
    if not receipt_path.exists():
        raise ArtifactStoreError("cannot delete an artifact without a write receipt")

    prior_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    prior_hash = prior_receipt.get("contentHash")
    if content_path.exists():
        content_path.unlink()

    delete_receipt = {
        "schemaVersion": SCHEMA_VERSION,
        "store": STORE_NAME,
        "operation": "delete-raw-artifact",
        "status": "deleted",
        "recordId": safe_id,
        "canonicalStorageAuthority": CANONICAL_STORAGE_AUTHORITY,
        "localStagingAuthority": LOCAL_STAGING_AUTHORITY,
        "hermesRawArtifactApiMapped": False,
        "contentHash": prior_hash,
        "reason": reason.strip(),
        "approvalTokenPresent": True,
        "deletedAt": now_iso(),
        "paths": paths,
    }
    delete_receipt_path = Path(paths["deleteReceiptPath"])
    delete_receipt_path.write_text(json.dumps(delete_receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return delete_receipt


def _content_from_args(args: argparse.Namespace, request: str) -> str:
    if args.content_file:
        return Path(args.content_file).read_text(encoding="utf-8")
    if args.content is not None:
        return args.content
    return request


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage just-chill raw artifact contracts in a local Hermes-compatible store.")
    parser.add_argument("request", nargs="*", help="Request text used to build a raw artifact contract for --plan/--write.")
    parser.add_argument("--cwd", default=None, help="Repo root for the default ignored local store root.")
    parser.add_argument("--store-root", default=None, help="Override local staging store root.")
    parser.add_argument("--content", help="Content to stage. Defaults to request text.")
    parser.add_argument("--content-file", help="Read content to stage from a UTF-8 file.")
    parser.add_argument("--approval-token", help="Required for sensitive staging, sensitive reading, and deletion.")
    parser.add_argument("--plan", action="store_true", help="Emit the local staging plan without writing.")
    parser.add_argument("--write", action="store_true", help="Stage the raw artifact and emit a write receipt.")
    parser.add_argument("--read-record-id", help="Read a staged raw artifact by id.")
    parser.add_argument("--delete-record-id", help="Delete a staged raw artifact by id and leave a deletion receipt.")
    parser.add_argument("--reason", default="operator-requested deletion", help="Deletion reason for --delete-record-id.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    try:
        if args.read_record_id:
            output = read_staged_raw_artifact(
                args.read_record_id,
                store_root=args.store_root,
                cwd=args.cwd,
                approval_token=args.approval_token,
            )
        elif args.delete_record_id:
            output = delete_staged_raw_artifact(
                args.delete_record_id,
                reason=args.reason,
                approval_token=args.approval_token,
                store_root=args.store_root,
                cwd=args.cwd,
            )
        else:
            request = " ".join(args.request).strip()
            if not request:
                raise ArtifactStoreError("request text is required for --plan or --write")
            content = _content_from_args(args, request)
            packet = classify_request(request)
            record = build_raw_artifact_record(packet, content=content)
            if args.write:
                output = stage_raw_artifact(
                    record,
                    content,
                    store_root=args.store_root,
                    cwd=args.cwd,
                    approval_token=args.approval_token,
                )
            else:
                output = build_local_store_plan(
                    record,
                    content=content,
                    store_root=args.store_root,
                    cwd=args.cwd,
                    approval_token=args.approval_token,
                )
                validation_issues = validate_local_store_plan(output)
                if validation_issues:
                    output["validationIssues"] = validation_issues
        print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
        return 0
    except ArtifactStoreError as exc:
        print(json.dumps({"schemaVersion": SCHEMA_VERSION, "store": STORE_NAME, "status": "error", "error": str(exc)}, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
