#!/usr/bin/env python3
"""Acceptance checks for the just-chill approval registry."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from just_chill_approval_registry import issue_approval, registry_status, revoke_approval, verify_approval
from just_chill_cli import recall_command, remember_command

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_SCRIPT = ROOT / "scripts" / "just_chill_approval_registry.py"


def require(name: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle: Any, haystack: Any) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


def require_truthy(name: str, value: Any) -> None:
    if not value:
        raise AssertionError(f"{name}: expected truthy, got {value!r}")


def run_json(argv: list[str]) -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(REGISTRY_SCRIPT), *argv], cwd=ROOT, text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


cases: list[str] = []

with TemporaryDirectory() as tmp:
    registry = str(Path(tmp) / "approvals.jsonl")
    subject = "remember my API key <example-api-key> for later"
    issued = issue_approval(scope="memory.write", subject=subject, actor="example-user", reason="test sensitive memory write", registry=registry)
    token = issued["approvalToken"]
    require("issue status", issued["status"], "approval-issued")
    require_truthy("issued token", token.startswith("approval://jcar-v1-"))
    stored = Path(registry).read_text(encoding="utf-8")
    if token in stored:
        raise AssertionError("registry must not persist plaintext approval token")
    cases.append("issue-hashes-token")

    verified = verify_approval(token=token, scope="memory.write", subject=subject, registry=registry)
    require("verify approved", verified["approved"], True)
    require("verify status", verified["status"], "approval-verified")
    cases.append("verify-scope-subject")

    wrong_scope = verify_approval(token=token, scope="memory.recall", subject=subject, registry=registry)
    require("wrong scope denied", wrong_scope["approved"], False)
    require_in("wrong scope blocker", "approval token scope mismatch: expected memory.recall", wrong_scope["blockedReasons"])
    cases.append("verify-wrong-scope-blocked")

    wrong_subject = verify_approval(token=token, scope="memory.write", subject="other subject", registry=registry)
    require("wrong subject denied", wrong_subject["approved"], False)
    require_in("wrong subject blocker", "approval token subject mismatch", wrong_subject["blockedReasons"])
    cases.append("verify-wrong-subject-blocked")

    memory = remember_command(subject, approval_token=token, approval_registry=registry)
    require("remember approved by registry", memory["status"], "memory-candidate-ready")
    require("remember registry mode", memory["approvalVerification"]["mode"], "registry")
    require("remember token accepted", memory["approvalTokenAccepted"], True)
    cases.append("remember-registry-approved")

    unregistered = remember_command(subject, approval_token="approval://jcar-v1-unregistered-token", approval_registry=registry)
    require("unregistered memory blocked", unregistered["status"], "memory-candidate-blocked")
    require_in("unregistered blocker", "approval token is not registered", unregistered["blockedReasons"])
    cases.append("remember-unregistered-blocked")

    revoked = revoke_approval(token=token, actor="example-user", reason="test cleanup", registry=registry)
    require("revoke status", revoked["status"], "approval-revoked")
    revoked_verify = verify_approval(token=token, scope="memory.write", subject=subject, registry=registry)
    require("revoked denied", revoked_verify["approved"], False)
    require_in("revoked blocker", "approval token is revoked", revoked_verify["blockedReasons"])
    cases.append("revoke-blocks-token")

    expired = issue_approval(scope="memory.write", subject=subject, actor="example-user", reason="expired test", ttl_seconds=1, registry=registry)
    expired_check = verify_approval(token=expired["approvalToken"], scope="memory.write", subject=subject, registry=registry)
    require("fresh ttl approved", expired_check["approved"], True)
    cases.append("ttl-token-fresh")

    status = registry_status(registry)
    require("status ready", status["status"], "ready")
    require("status no Hermes write", status["authorityBoundary"]["justChillWritesHermes"], False)
    cases.append("status-boundary")

with TemporaryDirectory() as tmp:
    registry = str(Path(tmp) / "approvals.jsonl")
    query = "Recall sensitive design preference"
    issued = issue_approval(scope="memory.recall", subject=query, actor="example-user", reason="test recall", registry=registry)
    recall_default = recall_command(query, approval_token=issued["approvalToken"], approval_registry=registry)
    require("recall registry accepted", recall_default["approvalTokenAccepted"], True)
    require("recall still needs evidence", recall_default["status"], "host-retrieval-required")
    require("recall registry mode", recall_default["approvalVerification"]["mode"], "registry")
    cases.append("recall-registry-token-accepted")

with TemporaryDirectory() as tmp:
    registry = str(Path(tmp) / "approvals.jsonl")
    cli_issue = run_json([
        "--registry", registry,
        "issue",
        "--scope", "memory.write",
        "--subject", "cli subject",
        "--actor", "example-user",
        "--reason", "cli test",
    ])
    require("CLI issue", cli_issue["status"], "approval-issued")
    cli_verify = run_json([
        "--registry", registry,
        "verify",
        "--token", cli_issue["approvalToken"],
        "--scope", "memory.write",
        "--subject", "cli subject",
    ])
    require("CLI verify", cli_verify["approved"], True)
    cases.append("cli-issue-verify")

print(f"PASS: {len(cases)} just-chill approval registry cases passed")
