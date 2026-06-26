#!/usr/bin/env python3
"""Contract-level Hermes artifact and memory records for just-chill.

The records produced here are deterministic local contracts. They do not write
to Hermes and do not claim a live Hermes binding exists. The purpose is to make
raw artifact, summary memory, sensitivity, retention, access, deletion/redaction,
and provenance requirements testable before a host-owned Hermes adapter is wired.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from typing import Any

from just_chill_router import SENSITIVE_KEYWORDS, classify_request

SCHEMA_VERSION = 1
CONTRACT_NAME = "just-chill-hermes-memory-contract-v1"
PLACEHOLDER_TIME = "host-timestamp-required"


def _canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_id(prefix: str, data: Any) -> str:
    digest = hashlib.sha256(_canonical_json(data).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}_{digest}"


def content_hash(content: str) -> str:
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def _contains_sensitive_text(text: str) -> bool:
    lower = text.lower()
    return any(keyword.lower() in lower for keyword in SENSITIVE_KEYWORDS)


def infer_sensitivity(packet: dict[str, Any], content: str | None = None) -> str:
    request = packet.get("request", "")
    risk_signals = " ".join(packet.get("signals", {}).get("risk", []))
    combined = " ".join(part for part in [request, risk_signals, content or ""] if part)
    if _contains_sensitive_text(combined):
        return "sensitive"
    if packet.get("classification", {}).get("approvalRequired"):
        return "restricted"
    return "internal"


def retention_for_sensitivity(sensitivity: str) -> dict[str, Any]:
    if sensitivity == "sensitive":
        return {
            "class": "approval-required",
            "autoPersistAllowed": False,
            "reviewRequiredBeforeRetention": True,
        }
    return {
        "class": "standard",
        "autoPersistAllowed": True,
        "reviewRequiredBeforeRetention": False,
    }


def access_policy_for_sensitivity(sensitivity: str) -> dict[str, Any]:
    return {
        "scope": "private-user",
        "hostEnforced": "Hermes",
        "requiresAccessCheckBeforeUse": True,
        "sensitivity": sensitivity,
    }


def memory_policy(packet: dict[str, Any], sensitivity: str) -> dict[str, Any]:
    approval_required = bool(packet.get("classification", {}).get("approvalRequired"))
    return {
        "candidateCreationAllowed": sensitivity != "sensitive",
        "canonicalPromotionAllowed": False,
        "decisionAssertionRequiresExplicitConfirmation": True,
        "policyAssertionRequiresExplicitConfirmation": True,
        "preferenceAutoPromotionAllowedOnlyWhen": [
            "repeated across independent source artifacts",
            "non-sensitive",
            "non-destructive",
            "access-allowed",
            "retention-valid",
            "conflict-free",
            "high confidence",
        ],
        "blockedReasons": [
            reason
            for reason, blocked in [
                ("sensitive memory requires explicit approval", sensitivity == "sensitive"),
                ("route approval gate is active", approval_required),
                ("raw Hermes artifact reference not yet live-bound", True),
                ("SHACL validation not yet run", True),
            ]
            if blocked
        ],
    }


def build_raw_artifact_record(
    packet: dict[str, Any],
    *,
    content: str | None = None,
    artifact_type: str = "user_request",
    source_channel: str = "local-cli",
) -> dict[str, Any]:
    request = packet.get("request", "")
    content_to_hash = content if content is not None else request
    sensitivity = infer_sensitivity(packet, content_to_hash)
    content_preview = "[redacted-sensitive]" if sensitivity == "sensitive" else content_to_hash[:160]
    base = {
        "artifactType": artifact_type,
        "request": request,
        "routeHint": packet.get("routing", {}).get("routeHint"),
        "bridgePath": packet.get("routing", {}).get("bridgePath"),
        "contentHash": content_hash(content_to_hash),
    }
    artifact_id = stable_id("raw", base)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "contract": CONTRACT_NAME,
        "recordKind": "raw-artifact-contract",
        "liveBinding": {
            "status": "contract-only",
            "owner": "Hermes",
            "unresolved": "live Hermes artifact write/read API is not bound in this repo slice",
        },
        "artifact": {
            "id": artifact_id,
            "type": artifact_type,
            "sourceChannel": source_channel,
            "createdAt": PLACEHOLDER_TIME,
            "contentHash": base["contentHash"],
            "contentPreview": content_preview,
            "sensitivity": sensitivity,
            "retention": retention_for_sensitivity(sensitivity),
            "accessPolicy": access_policy_for_sensitivity(sensitivity),
            "deletionState": "active",
            "redactionState": "not_redacted",
            "provenance": {
                "source": "just_chill_router_packet",
                "router": packet.get("router"),
                "routerSchemaVersion": packet.get("schemaVersion"),
                "routeHint": packet.get("routing", {}).get("routeHint"),
                "bridgePath": packet.get("routing", {}).get("bridgePath"),
                "approvalRequired": packet.get("classification", {}).get("approvalRequired"),
            },
            "memoryPolicy": memory_policy(packet, sensitivity),
        },
    }


def summary_policy_from_artifact(artifact: dict[str, Any], sensitivity: str) -> dict[str, Any]:
    policy = dict(artifact["memoryPolicy"])
    if sensitivity == "sensitive":
        blocked = list(policy.get("blockedReasons", []))
        if "summary text contains sensitive content" not in blocked:
            blocked.append("summary text contains sensitive content")
        policy["candidateCreationAllowed"] = False
        policy["canonicalPromotionAllowed"] = False
        policy["blockedReasons"] = blocked
    return policy


def build_summary_memory_record(
    raw_record: dict[str, Any],
    summary: str,
    *,
    confidence: float = 0.75,
) -> dict[str, Any]:
    artifact = raw_record["artifact"]
    source_ref = artifact["id"]
    summary_sensitive = _contains_sensitive_text(summary)
    sensitivity = "sensitive" if artifact["sensitivity"] == "sensitive" or summary_sensitive else artifact["sensitivity"]
    summary_text = "[redacted-sensitive]" if sensitivity == "sensitive" else summary
    base = {
        "source": source_ref,
        "summaryHash": content_hash(summary),
        "confidence": confidence,
    }
    return {
        "schemaVersion": SCHEMA_VERSION,
        "contract": CONTRACT_NAME,
        "recordKind": "summary-memory-contract",
        "liveBinding": {
            "status": "contract-only",
            "owner": "Hermes",
            "unresolved": "live Hermes summary memory write/read API is not bound in this repo slice",
        },
        "summaryMemory": {
            "id": stable_id("summary", base),
            "sourceArtifactRefs": [source_ref],
            "summary": summary_text,
            "summaryHash": base["summaryHash"],
            "createdAt": PLACEHOLDER_TIME,
            "extraction": {
                "method": "just-chill-contract-skeleton",
                "model": None,
                "confidence": confidence,
            },
            "sensitivity": sensitivity,
            "retention": retention_for_sensitivity(sensitivity),
            "accessPolicy": access_policy_for_sensitivity(sensitivity),
            "deletionState": artifact["deletionState"],
            "redactionState": "redacted" if sensitivity == "sensitive" else artifact["redactionState"],
            "promotionPolicy": summary_policy_from_artifact(artifact, sensitivity),
            "provenance": {
                "derivedFromRawArtifact": source_ref,
                "rawContentHash": artifact["contentHash"],
            },
        },
    }


def validate_contract_record(record: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if record.get("schemaVersion") != SCHEMA_VERSION:
        issues.append("schemaVersion mismatch")
    if record.get("contract") != CONTRACT_NAME:
        issues.append("contract name mismatch")
    if record.get("liveBinding", {}).get("status") != "contract-only":
        issues.append("live binding must remain contract-only in this slice")

    if record.get("recordKind") == "raw-artifact-contract":
        artifact = record.get("artifact", {})
        required = [
            "id", "type", "sourceChannel", "createdAt", "contentHash", "sensitivity",
            "retention", "accessPolicy", "deletionState", "redactionState", "provenance", "memoryPolicy",
        ]
        for key in required:
            if key not in artifact:
                issues.append(f"raw artifact missing {key}")
        if artifact.get("sensitivity") == "sensitive" and artifact.get("retention", {}).get("autoPersistAllowed"):
            issues.append("sensitive artifacts must not auto-persist")
    elif record.get("recordKind") == "summary-memory-contract":
        summary = record.get("summaryMemory", {})
        required = [
            "id", "sourceArtifactRefs", "summary", "summaryHash", "createdAt", "extraction",
            "sensitivity", "retention", "accessPolicy", "deletionState", "redactionState", "promotionPolicy", "provenance",
        ]
        for key in required:
            if key not in summary:
                issues.append(f"summary memory missing {key}")
        if not summary.get("sourceArtifactRefs"):
            issues.append("summary memory requires source artifact refs")
        if summary.get("sensitivity") == "sensitive" and summary.get("summary") != "[redacted-sensitive]":
            issues.append("sensitive summary must be redacted")
    else:
        issues.append("unknown recordKind")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build deterministic just-chill Hermes memory contract records.")
    parser.add_argument("request", nargs="*", help="User request text.")
    parser.add_argument("--summary", help="Also emit a summary memory contract derived from the raw artifact.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    request = " ".join(args.request)
    packet = classify_request(request)
    raw = build_raw_artifact_record(packet)
    output: dict[str, Any] = {"rawArtifact": raw}
    if args.summary is not None:
        output["summaryMemory"] = build_summary_memory_record(raw, args.summary)
    output["validationIssues"] = [*validate_contract_record(raw)]
    if "summaryMemory" in output:
        output["validationIssues"].extend(validate_contract_record(output["summaryMemory"]))
    print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if not output["validationIssues"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
