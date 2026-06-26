#!/usr/bin/env python3
"""Host-owned approval registry for just-chill.

The registry records explicit host/operator approvals without granting just-chill
execution or storage authority. Tokens are shown once to the caller, stored only
as hashes, and verified against scope/subject/expiry before sensitive memory or
recall gates may treat them as real approvals.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import secrets
import uuid
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
REGISTRY_NAME = "just-chill-approval-registry-v1"
DEFAULT_REGISTRY_PATH = Path.home() / ".local" / "share" / "jarvis" / "just-chill-approval-registry" / "approvals.jsonl"
APPROVAL_TOKEN_PREFIXES = ("approval://", "host-approval://", "hermes-approval://")
DEFAULT_TOKEN_PREFIX = "approval://jcar-v1-"
ENV_REGISTRY_PATH = "JUST_CHILL_APPROVAL_REGISTRY"


class ApprovalRegistryError(ValueError):
    """Fail-closed approval registry error."""


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def iso_time(value: dt.datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def registry_path(path: str | os.PathLike[str] | None = None) -> Path:
    raw = path or os.environ.get(ENV_REGISTRY_PATH) or DEFAULT_REGISTRY_PATH
    return Path(raw).expanduser()


def token_shape_valid(token: str | None) -> bool:
    if token is None:
        return False
    stripped = token.strip()
    if not stripped or any(ch.isspace() for ch in stripped):
        return False
    return any(stripped.startswith(prefix) and len(stripped) > len(prefix) + 7 for prefix in APPROVAL_TOKEN_PREFIXES)


def token_hash(token: str) -> str:
    return "sha256:" + hashlib.sha256(("just-chill-approval-token\0" + token).encode("utf-8")).hexdigest()


def subject_hash(subject: str | None) -> str | None:
    if subject is None:
        return None
    normalized = " ".join(str(subject).split())
    return "sha256:" + hashlib.sha256(("just-chill-approval-subject\0" + normalized).encode("utf-8")).hexdigest()


def token_preview(token: str) -> str:
    stripped = token.strip()
    if "://" in stripped:
        prefix, rest = stripped.split("://", 1)
        return f"{prefix}://{rest[:10]}…{rest[-6:]}"
    return f"{stripped[:10]}…{stripped[-6:]}"


def json_text(data: Any, *, pretty: bool = False) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2 if pretty else None, sort_keys=True)


def read_events(path: str | os.PathLike[str] | None = None) -> list[dict[str, Any]]:
    target = registry_path(path)
    if not target.exists():
        return []
    events: list[dict[str, Any]] = []
    for line_no, line in enumerate(target.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ApprovalRegistryError(f"registry line {line_no} is not valid JSON") from exc
        if not isinstance(event, dict):
            raise ApprovalRegistryError(f"registry line {line_no} must be a JSON object")
        events.append(event)
    return events


def append_event(event: dict[str, Any], path: str | os.PathLike[str] | None = None) -> Path:
    target = registry_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return target


def latest_event_for_token(token: str, path: str | os.PathLike[str] | None = None) -> dict[str, Any] | None:
    digest = token_hash(token)
    latest: dict[str, Any] | None = None
    for event in read_events(path):
        if event.get("tokenHash") == digest:
            latest = event
    return latest


def issue_approval(
    *,
    scope: str,
    actor: str,
    reason: str,
    subject: str | None = None,
    expires_at: str | None = None,
    ttl_seconds: int | None = None,
    registry: str | os.PathLike[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not scope.strip():
        raise ApprovalRegistryError("scope is required")
    if not actor.strip():
        raise ApprovalRegistryError("actor is required")
    if not reason.strip():
        raise ApprovalRegistryError("reason is required")
    now = utc_now()
    parsed_expires = parse_time(expires_at)
    if ttl_seconds is not None:
        if ttl_seconds <= 0:
            raise ApprovalRegistryError("ttl seconds must be positive")
        ttl_expires = now + dt.timedelta(seconds=ttl_seconds)
        parsed_expires = min(parsed_expires, ttl_expires) if parsed_expires else ttl_expires
    token = DEFAULT_TOKEN_PREFIX + secrets.token_urlsafe(24)
    event = {
        "schemaVersion": SCHEMA_VERSION,
        "registry": REGISTRY_NAME,
        "eventId": str(uuid.uuid4()),
        "eventType": "issued",
        "createdAt": iso_time(now),
        "tokenHash": token_hash(token),
        "tokenPreview": token_preview(token),
        "scope": scope.strip(),
        "subjectHash": subject_hash(subject),
        "subjectRequired": subject is not None,
        "actor": actor.strip(),
        "reason": reason.strip(),
        "expiresAt": iso_time(parsed_expires),
        "revoked": False,
        "metadata": metadata or {},
        "authorityBoundary": {
            "justChillExecutesGjc": False,
            "justChillWritesHermes": False,
            "justChillOwnsCanonicalMemory": False,
            "hostOwnedApprovalOnly": True,
        },
    }
    target = append_event(event, registry)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "registry": REGISTRY_NAME,
        "status": "approval-issued",
        "approvalToken": token,
        "approvalTokenPreview": event["tokenPreview"],
        "scope": event["scope"],
        "subjectHash": event["subjectHash"],
        "expiresAt": event["expiresAt"],
        "registryPath": str(target),
        "eventId": event["eventId"],
        "warning": "Store the approvalToken securely; only its hash is persisted.",
    }


def revoke_approval(
    *,
    token: str,
    actor: str,
    reason: str,
    registry: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    if not token_shape_valid(token):
        raise ApprovalRegistryError("approval token must be a host approval reference")
    if not actor.strip():
        raise ApprovalRegistryError("actor is required")
    if not reason.strip():
        raise ApprovalRegistryError("reason is required")
    existing = latest_event_for_token(token, registry)
    if existing is None:
        raise ApprovalRegistryError("approval token is not registered")
    event = {
        "schemaVersion": SCHEMA_VERSION,
        "registry": REGISTRY_NAME,
        "eventId": str(uuid.uuid4()),
        "eventType": "revoked",
        "createdAt": iso_time(utc_now()),
        "tokenHash": token_hash(token),
        "tokenPreview": token_preview(token),
        "scope": existing.get("scope"),
        "subjectHash": existing.get("subjectHash"),
        "actor": actor.strip(),
        "reason": reason.strip(),
        "revoked": True,
    }
    target = append_event(event, registry)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "registry": REGISTRY_NAME,
        "status": "approval-revoked",
        "approvalTokenPreview": event["tokenPreview"],
        "registryPath": str(target),
        "eventId": event["eventId"],
    }


def verify_approval(
    *,
    token: str | None,
    scope: str,
    subject: str | None = None,
    registry: str | os.PathLike[str] | None = None,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    result = {
        "schemaVersion": SCHEMA_VERSION,
        "registry": REGISTRY_NAME,
        "status": "approval-denied",
        "approved": False,
        "tokenPresent": bool(token),
        "tokenShapeValid": token_shape_valid(token),
        "scope": scope,
        "subjectHash": subject_hash(subject),
        "registryPath": str(registry_path(registry)),
        "blockedReasons": [],
    }
    if not token:
        result["blockedReasons"].append("approval token is required")
        return result
    if not result["tokenShapeValid"]:
        result["blockedReasons"].append("approval token must be a host approval reference")
        return result
    event = latest_event_for_token(token, registry)
    if event is None:
        result["blockedReasons"].append("approval token is not registered")
        return result
    result["approvalTokenPreview"] = event.get("tokenPreview") or token_preview(token)
    result["eventId"] = event.get("eventId")
    result["issuedScope"] = event.get("scope")
    result["issuedSubjectHash"] = event.get("subjectHash")
    if event.get("eventType") == "revoked" or event.get("revoked") is True:
        result["blockedReasons"].append("approval token is revoked")
    if event.get("scope") != scope:
        result["blockedReasons"].append(f"approval token scope mismatch: expected {scope}")
    issued_subject = event.get("subjectHash")
    expected_subject = subject_hash(subject)
    if issued_subject and issued_subject != expected_subject:
        result["blockedReasons"].append("approval token subject mismatch")
    if issued_subject and expected_subject is None:
        result["blockedReasons"].append("approval token requires a subject for verification")
    expires = parse_time(event.get("expiresAt"))
    current = now or utc_now()
    if expires and current > expires:
        result["blockedReasons"].append("approval token is expired")
    if event.get("schemaVersion") != SCHEMA_VERSION or event.get("registry") != REGISTRY_NAME:
        result["blockedReasons"].append("approval registry record schema mismatch")
    if not result["blockedReasons"]:
        result["status"] = "approval-verified"
        result["approved"] = True
    return result


def registry_status(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    events = read_events(path)
    issued = [event for event in events if event.get("eventType") == "issued"]
    revoked = [event for event in events if event.get("eventType") == "revoked"]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "registry": REGISTRY_NAME,
        "status": "ready",
        "registryPath": str(registry_path(path)),
        "eventCount": len(events),
        "issuedCount": len(issued),
        "revokedCount": len(revoked),
        "authorityBoundary": {
            "justChillExecutesGjc": False,
            "justChillWritesHermes": False,
            "justChillOwnsCanonicalMemory": False,
            "hostOwnedApprovalOnly": True,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Host-owned approval registry for just-chill approval tokens.")
    parser.add_argument("--registry", help=f"Registry JSONL path. Defaults to ${ENV_REGISTRY_PATH} or {DEFAULT_REGISTRY_PATH}.")
    parser.add_argument("--pretty", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    issue = sub.add_parser("issue", help="Issue a new approval token and persist only its hash.")
    issue.add_argument("--scope", required=True, help="Approval scope, e.g. memory.write or memory.recall.")
    issue.add_argument("--subject", help="Optional subject text bound to this token; only a hash is stored.")
    issue.add_argument("--actor", required=True, help="Approving user/operator identity.")
    issue.add_argument("--reason", required=True, help="Reason for the approval.")
    issue.add_argument("--expires-at", help="Optional ISO timestamp expiration.")
    issue.add_argument("--ttl-seconds", type=int, help="Optional positive TTL in seconds.")

    verify = sub.add_parser("verify", help="Verify an approval token against scope/subject/expiry.")
    verify.add_argument("--token", required=True)
    verify.add_argument("--scope", required=True)
    verify.add_argument("--subject")

    revoke = sub.add_parser("revoke", help="Revoke an approval token.")
    revoke.add_argument("--token", required=True)
    revoke.add_argument("--actor", required=True)
    revoke.add_argument("--reason", required=True)

    sub.add_parser("status", help="Print registry status.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "issue":
            output = issue_approval(
                scope=args.scope,
                subject=args.subject,
                actor=args.actor,
                reason=args.reason,
                expires_at=args.expires_at,
                ttl_seconds=args.ttl_seconds,
                registry=args.registry,
            )
        elif args.command == "verify":
            output = verify_approval(token=args.token, scope=args.scope, subject=args.subject, registry=args.registry)
        elif args.command == "revoke":
            output = revoke_approval(token=args.token, actor=args.actor, reason=args.reason, registry=args.registry)
        elif args.command == "status":
            output = registry_status(args.registry)
        else:  # pragma: no cover - argparse prevents this.
            raise ApprovalRegistryError(f"unknown command {args.command}")
    except Exception as exc:
        output = {
            "schemaVersion": SCHEMA_VERSION,
            "registry": REGISTRY_NAME,
            "status": "error",
            "error": str(exc),
            "registryPath": str(registry_path(args.registry)),
        }
        print(json_text(output, pretty=args.pretty))
        return 1
    print(json_text(output, pretty=args.pretty))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
