#!/usr/bin/env python3
"""Acceptance checks for the safe just-chill CLI entrypoint contracts."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from just_chill_cli import handoff_gjc_command, recall_command, remember_command, route_command
from just_chill_memory_contracts import build_raw_artifact_record, build_summary_memory_record
from just_chill_router import classify_request
from just_chill_vector_recall import build_retrieval_evidence, build_vector_sidecar_candidate

ROOT = Path(__file__).resolve().parents[1]
CLI_SCRIPT = ROOT / "scripts" / "just_chill_cli.py"
CLI_WRAPPER = ROOT / "scripts" / "just-chill"


def require(name: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_truthy(name: str, value: Any) -> None:
    if not value:
        raise AssertionError(f"{name}: expected truthy value, got {value!r}")


def require_in(name: str, needle: Any, haystack: Any) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


def run_json(argv: list[str], *, wrapper: bool = False, stdin: str | None = None) -> dict[str, Any]:
    command = [str(CLI_WRAPPER)] if wrapper else [sys.executable, str(CLI_SCRIPT)]
    result = subprocess.run(
        command + argv,
        input=stdin,
        text=True,
        capture_output=True,
        check=True,
        cwd=ROOT,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - failure diagnostics only.
        raise AssertionError(f"CLI did not emit JSON. stdout={result.stdout!r} stderr={result.stderr!r}") from exc


def canonical_ref(summary: dict[str, Any]) -> dict[str, Any]:
    memory = summary["summaryMemory"]
    return {
        "sourceKind": "summary-memory",
        "canonicalSourceId": memory["id"],
        "canonicalContentHash": memory["summaryHash"],
        "observedContentHash": memory["summaryHash"],
        "receiptRef": "host-hermes-receipt://summary-add-cli-001",
        "receiptKind": "host-owned-summary-memory-receipt",
        "readBackHashMatches": True,
        "canonicalInHermes": True,
        "deletionState": memory["deletionState"],
        "redactionState": memory["redactionState"],
    }


cases: list[str] = []

route = route_command("fix TypeError in src/hooks/bridge.ts and run bun test", cwd=str(ROOT), include_bridge=True)
require("route command", route["command"], "route")
require("route status", route["status"], "route-ready")
require("route dev", route["routerPacket"]["classification"]["isDevelopment"], True)
require("route next step", route["nextStep"], "handoff-gjc")
require("route no execution", route["executionAllowedHere"], False)
require("route no direct GJC", route["authorityBoundary"]["justChillExecutesGjc"], False)
require("route bridge no execution", route["bridgePlan"]["authorityBoundary"]["noExecutionInThisPlan"], True)
require("route bridge path", route["bridgePlan"]["bridgePlan"]["executionAllowedHere"], False)
cases.append("route-with-bridge-contract")

handoff = handoff_gjc_command(
    "Refine this auth architecture plan before implementation",
    cwd=str(ROOT),
    allow_mutation=True,
)
require("handoff status", handoff["status"], "handoff-plan-ready")
require("handoff target", handoff["bridgePlan"]["target"], "GJC")
require("mutation requested", handoff["mutationConsent"]["allowMutationRequested"], True)
require("mutation disallowed here", handoff["mutationConsent"]["allowedHere"], False)
require("handoff execution disallowed", handoff["executionAllowedHere"], False)
require("handoff bridge disallowed", handoff["bridgePlan"]["bridgePlan"]["executionAllowedHere"], False)
require_in("operator reminder", "do not treat tmux scrollback as completion evidence", handoff["operatorReminder"])
cases.append("handoff-gjc-contract")

nondev_handoff = handoff_gjc_command("메일 초안을 작성해서 요약해줘", cwd=str(ROOT))
require("nondev handoff blocked", nondev_handoff["status"], "handoff-blocked")
require("nondev handoff plan", nondev_handoff["bridgePlan"], None)
require_in("nondev handoff reason", "request is not classified as development work", nondev_handoff["blockedReasons"])
cases.append("nondevelopment-handoff-blocked")

remember = remember_command(
    "remember that just-chill routes development requests to visible GJC sessions first",
    summary="Development requests should start with visible GJC routed sessions.",
)
require("remember command", remember["command"], "remember")
require("remember status", remember["status"], "memory-candidate-ready")
require("remember no Hermes write", remember["authorityBoundary"]["justChillWritesHermes"], False)
require("remember no canonical authority", remember["authorityBoundary"]["justChillOwnsCanonicalMemory"], False)
require("remember raw kind", remember["rawArtifactContract"]["recordKind"], "raw-artifact-contract")
require("remember raw sensitivity", remember["rawArtifactContract"]["artifact"]["sensitivity"], "internal")
require("remember summary kind", remember["summaryMemoryContract"]["recordKind"], "summary-memory-contract")
cases.append("remember-contract-ready")

sensitive = remember_command("remember my API key <example-api-key> for later")
require("sensitive blocked", sensitive["status"], "memory-candidate-blocked")
require("sensitive redacted", sensitive["rawArtifactContract"]["artifact"]["contentPreview"], "[redacted-sensitive]")
require_in("sensitive approval blocker", "sensitive memory requires explicit approval before host-owned persistence", sensitive["blockedReasons"])
require("sensitive no auto persist", sensitive["rawArtifactContract"]["artifact"]["retention"]["autoPersistAllowed"], False)
cases.append("sensitive-remember-blocked")
sensitive_fake_token = remember_command("remember my API key <example-api-key> for later", approval_token="x")
require("sensitive fake token blocked", sensitive_fake_token["status"], "memory-candidate-blocked")
require("sensitive fake token rejected", sensitive_fake_token["approvalTokenAccepted"], False)
require_in("fake token blocker", "approval token must be a host approval reference", sensitive_fake_token["blockedReasons"])
require_in("fake token still needs approval", "sensitive memory requires explicit approval before host-owned persistence", sensitive_fake_token["blockedReasons"])
cases.append("sensitive-fake-approval-token-blocked")

sensitive_valid_token = remember_command("remember my API key <example-api-key> for later", approval_token="approval://cli-sensitive-approval-001")
require("sensitive valid token accepted", sensitive_valid_token["approvalTokenAccepted"], True)
require("sensitive valid token status", sensitive_valid_token["status"], "memory-candidate-ready")
require("sensitive valid token no auto persist", sensitive_valid_token["rawArtifactContract"]["artifact"]["retention"]["autoPersistAllowed"], False)
cases.append("sensitive-host-approval-token-shape")


recall_default = recall_command("How should just-chill route development work?", cwd=str(ROOT))
require("recall default status", recall_default["status"], "host-retrieval-required")
require("recall default no decision", recall_default["recallGateDecision"], None)
require_in("recall host evidence blocker", "host-owned retrieval evidence is required before recall enters context", recall_default["blockedReasons"])
require("recall no local vector search", recall_default["authorityBoundary"]["justChillWritesHermes"], False)
require("recall default no live probe", recall_default["vectorBoundary"]["probeMode"], "availability-only")
cases.append("recall-requires-host-evidence")
recall_default_fake_token = recall_command("How should just-chill route development work?", cwd=str(ROOT), approval_token="x")
require("recall default fake token blocked", recall_default_fake_token["status"], "recall-blocked")
require("recall default fake token rejected", recall_default_fake_token["approvalTokenAccepted"], False)
require_in("recall default fake token blocker", "approval token must be a host approval reference", recall_default_fake_token["blockedReasons"])
cases.append("default-recall-fake-approval-token-blocked")


packet = classify_request("remember that development requests route to GJC visible sessions first")
raw = build_raw_artifact_record(packet, content="Development requests route to GJC visible sessions first.")
summary = build_summary_memory_record(raw, "Development requests route to GJC visible sessions first.", confidence=0.91)
reference = canonical_ref(summary)
candidate = build_vector_sidecar_candidate(
    summary,
    canonical_reference=reference,
    embedding_model="local-test-embedding",
    embedding_dimensions=384,
)
retrieval = build_retrieval_evidence(candidate, query="How should development be routed?", score=0.93)
recall_allowed = recall_command(
    "How should development be routed?",
    candidate_json=json.dumps(candidate, ensure_ascii=False, sort_keys=True),
    retrieval_evidence_json=json.dumps(retrieval, ensure_ascii=False, sort_keys=True),
    current_source_hash=reference["observedContentHash"],
    current_deletion_state=reference["deletionState"],
    current_redaction_state=reference["redactionState"],
)
require("recall allowed status", recall_allowed["status"], "recall-allowed")
require("recall allowed", recall_allowed["recallGateDecision"]["allowRecall"], True)
require("recall gate no blockers", recall_allowed["blockedReasons"], [])
require("recall no local execution", recall_allowed["executionAllowedHere"], False)
cases.append("recall-host-evidence-admitted")

partial_recall = recall_command(
    "How should development be routed?",
    candidate_json=json.dumps(candidate, ensure_ascii=False, sort_keys=True),
)
require("partial recall blocked", partial_recall["status"], "recall-blocked")
require_in("partial recall blocker", "candidate JSON and retrieval evidence JSON must be supplied together", partial_recall["blockedReasons"])
cases.append("partial-recall-input-blocked")
reverse_partial_recall = recall_command(
    "How should development be routed?",
    retrieval_evidence_json=json.dumps(retrieval, ensure_ascii=False, sort_keys=True),
)
require("reverse partial recall blocked", reverse_partial_recall["status"], "recall-blocked")
require_in("reverse partial recall blocker", "candidate JSON and retrieval evidence JSON must be supplied together", reverse_partial_recall["blockedReasons"])
cases.append("reverse-partial-recall-input-blocked")

stale_recall = recall_command(
    "How should development be routed?",
    candidate_json=json.dumps(candidate, ensure_ascii=False, sort_keys=True),
    retrieval_evidence_json=json.dumps(retrieval, ensure_ascii=False, sort_keys=True),
    current_source_hash="sha256:stale",
    current_deletion_state=reference["deletionState"],
    current_redaction_state=reference["redactionState"],
)
require("stale recall blocked", stale_recall["status"], "recall-blocked")
require_in("stale recall blocker", "current canonical source hash is stale relative to sidecar", stale_recall["blockedReasons"])
cases.append("stale-recall-evidence-blocked")

deleted_recall = recall_command(
    "How should development be routed?",
    candidate_json=json.dumps(candidate, ensure_ascii=False, sort_keys=True),
    retrieval_evidence_json=json.dumps(retrieval, ensure_ascii=False, sort_keys=True),
    current_source_hash=reference["observedContentHash"],
    current_deletion_state="deleted",
    current_redaction_state=reference["redactionState"],
)
require("deleted recall blocked", deleted_recall["status"], "recall-blocked")
require_in("deleted recall drift", "current canonical source deletion state differs from sidecar", deleted_recall["blockedReasons"])
require_in("deleted recall blocker", "deleted source cannot be recalled", deleted_recall["blockedReasons"])
cases.append("deleted-recall-evidence-blocked")
redacted_recall = recall_command(
    "How should development be routed?",
    candidate_json=json.dumps(candidate, ensure_ascii=False, sort_keys=True),
    retrieval_evidence_json=json.dumps(retrieval, ensure_ascii=False, sort_keys=True),
    current_source_hash=reference["observedContentHash"],
    current_deletion_state=reference["deletionState"],
    current_redaction_state="redacted",
)
require("redacted recall blocked", redacted_recall["status"], "recall-blocked")
require_in("redacted recall drift", "current canonical source redaction state differs from sidecar", redacted_recall["blockedReasons"])
require_in("redacted recall blocker", "redacted source cannot be recalled", redacted_recall["blockedReasons"])
cases.append("redacted-recall-evidence-blocked")


recall_fake_token = recall_command(
    "How should development be routed?",
    candidate_json=json.dumps(candidate, ensure_ascii=False, sort_keys=True),
    retrieval_evidence_json=json.dumps(retrieval, ensure_ascii=False, sort_keys=True),
    current_source_hash=reference["observedContentHash"],
    current_deletion_state=reference["deletionState"],
    current_redaction_state=reference["redactionState"],
    approval_token="x",
)
require("recall fake token blocked", recall_fake_token["status"], "recall-blocked")
require_in("recall fake token blocker", "approval token must be a host approval reference", recall_fake_token["blockedReasons"])
cases.append("recall-fake-approval-token-blocked")
malformed_recall = recall_command(
    "How should development be routed?",
    candidate_json="{not-json}",
    retrieval_evidence_json=json.dumps(retrieval, ensure_ascii=False, sort_keys=True),
    current_source_hash=reference["observedContentHash"],
    current_deletion_state=reference["deletionState"],
    current_redaction_state=reference["redactionState"],
)
require("malformed recall blocked", malformed_recall["status"], "recall-blocked")
require_in("malformed recall blocker", "candidate JSON must decode to an object", malformed_recall["blockedReasons"])
cases.append("malformed-recall-json-blocked")

route_cli = run_json(["route", "--include-bridge", "--cwd", str(ROOT), "fix", "src/hooks/bridge.ts"])
require("route CLI status", route_cli["status"], "route-ready")
require("route CLI bridge target", route_cli["bridgePlan"]["target"], "GJC")
require("route CLI execution disallowed", route_cli["executionAllowedHere"], False)
cases.append("route-cli-subprocess")

require_truthy("CLI wrapper executable", os.access(CLI_WRAPPER, os.X_OK))
wrapper = run_json(
    [
        "remember",
        "--summary",
        "Development requests should route through GJC.",
        "remember",
        "that",
        "development",
        "requests",
        "route",
        "through",
        "GJC",
    ],
    wrapper=True,
)
require("wrapper command", wrapper["command"], "remember")
require("wrapper status", wrapper["status"], "memory-candidate-ready")
require("wrapper no write", wrapper["authorityBoundary"]["justChillWritesHermes"], False)
cases.append("wrapper-cli-subprocess")

stdin_route = run_json(["route"], stdin="fix the null check in src/hooks/bridge.ts")
require("stdin route status", stdin_route["status"], "route-ready")
require("stdin route dev", stdin_route["routerPacket"]["classification"]["isDevelopment"], True)
cases.append("stdin-request-supported")

for idx, output in enumerate([
    route,
    handoff,
    nondev_handoff,
    remember,
    sensitive,
    sensitive_fake_token,
    sensitive_valid_token,
    recall_default,
    recall_default_fake_token,
    recall_allowed,
    partial_recall,
    reverse_partial_recall,
    stale_recall,
    deleted_recall,
    redacted_recall,
    recall_fake_token,
    malformed_recall,
    route_cli,
    wrapper,
    stdin_route,
], start=1):
    require(f"output {idx} no local execution", output["executionAllowedHere"], False)
    require(f"output {idx} no GJC execution", output["authorityBoundary"]["justChillExecutesGjc"], False)
    require(f"output {idx} no Hermes write", output["authorityBoundary"]["justChillWritesHermes"], False)
    require(f"output {idx} no memory ownership", output["authorityBoundary"]["justChillOwnsCanonicalMemory"], False)
cases.append("authority-boundary-invariant")

print(f"PASS: {len(cases)} just-chill CLI contract cases passed")
