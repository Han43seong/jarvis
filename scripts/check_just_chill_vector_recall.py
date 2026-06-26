#!/usr/bin/env python3
"""Acceptance checks for just-chill vector sidecar and recall gates."""
from __future__ import annotations

import copy

from just_chill_memory_contracts import build_raw_artifact_record, build_summary_memory_record
from just_chill_router import classify_request
from just_chill_vector_recall import (
    build_recall_gate_decision,
    build_retrieval_evidence,
    build_vector_boundary_report,
    build_vector_sidecar_candidate,
    validate_recall_gate_decision,
    validate_vector_boundary_report,
    validate_vector_sidecar_candidate,
)


def require(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, expected, actual) -> None:
    if expected not in actual:
        raise AssertionError(f"{name}: expected {expected!r} in {actual!r}")


def summary_record(text: str = "Development requests should route to GJC visible sessions first.") -> dict:
    packet = classify_request("remember that development requests route to GJC visible sessions first")
    raw = build_raw_artifact_record(packet, content=text)
    return build_summary_memory_record(raw, text, confidence=0.91)


def canonical_ref(summary: dict, *, deleted: bool = False, redacted: bool = False, canonical: bool = True) -> dict:
    memory = summary["summaryMemory"]
    return {
        "sourceKind": "summary-memory",
        "canonicalSourceId": memory["id"],
        "canonicalContentHash": memory["summaryHash"],
        "observedContentHash": memory["summaryHash"],
        "receiptRef": "host-hermes-receipt://summary-add-001",
        "receiptKind": "host-owned-summary-memory-receipt",
        "readBackHashMatches": canonical,
        "canonicalInHermes": canonical,
        "deletionState": "deleted" if deleted else memory["deletionState"],
        "redactionState": "redacted" if redacted else memory["redactionState"],
    }


cases: list[str] = []

surfaces = {
    "hermes": {
        "memoryProvider": "holographic",
        "memoryProviderSurface": {
            "status": "provider-tool-available",
            "provider": "holographic",
            "storageMode": "local-sqlite-fact-store",
            "summaryMemoryWriteAvailable": True,
            "tool": {"name": "fact_store", "writeAction": "add", "readActions": ["search", "probe", "list"], "deleteAction": "remove"},
        },
        "justChillMemoryApiSurface": {"tools": ["hermes.raw_artifact.create", "hermes.rdf_graph.create"]},
    }
}
boundary = build_vector_boundary_report(surfaces=surfaces, module_available=lambda name: False, which=lambda name: "/usr/bin/python3" if name == "python3" else None)
require("boundary status", boundary["status"], "provider-search-only")
require("provider search available", boundary["surfaces"]["providerSearchAvailable"], True)
require("vector search not ready", boundary["liveSearchGate"]["ready"], False)
require_in("vector API blocker", "Hermes-native vector sidecar store/search API is not mapped", boundary["liveSearchGate"]["blockedReasons"])
require("boundary validation", validate_vector_boundary_report(boundary), [])
cases.append("provider-search-not-vector-authority")
vector_name_only_surfaces = copy.deepcopy(surfaces)
vector_name_only_surfaces["hermes"]["justChillMemoryApiSurface"] = {"tools": ["hermes.vector_status"]}
vector_name_only = build_vector_boundary_report(surfaces=vector_name_only_surfaces, module_available=lambda name: True, which=lambda name: "/usr/bin/python3")
require("vector name-only status", vector_name_only["status"], "provider-search-only")
require("vector name-only ready", vector_name_only["liveSearchGate"]["ready"], False)
require_in("vector name-only blocker", "vector-like tool names are not sufficient without explicit search/read sidecar APIs", vector_name_only["liveSearchGate"]["blockedReasons"])
cases.append("vector-name-only-fail-closed")
vector_ready_surfaces = copy.deepcopy(surfaces)
vector_ready_surfaces["hermes"]["justChillMemoryApiSurface"] = {
    "tools": [
        "hermes.raw_artifact.create",
        "hermes.raw_artifact.read",
        "hermes.raw_artifact.delete",
        "hermes.rdf_graph.create",
        "hermes.rdf_graph.read",
        "hermes.rdf_graph.delete",
        "hermes.vector_sidecar.create",
        "hermes.vector_sidecar.search",
        "hermes.vector_sidecar.read",
        "hermes.vector_sidecar.delete",
    ]
}
vector_ready = build_vector_boundary_report(surfaces=vector_ready_surfaces, module_available=lambda name: True, which=lambda name: "/usr/bin/python3")
require("vector ready status", vector_ready["status"], "live-vector-api-mapped")
require("vector ready gate", vector_ready["liveSearchGate"]["ready"], True)
require("vector ready blockers", vector_ready["liveSearchGate"]["blockedReasons"], [])
require("known vector tools not vector-like", vector_ready["surfaces"]["vectorLikeToolNames"], [])
require("vector ready validation", validate_vector_boundary_report(vector_ready), [])
cases.append("live-vector-api-mapped")


summary = summary_record()
ready = build_vector_sidecar_candidate(summary, canonical_reference=canonical_ref(summary), embedding_model="local-test-embedding", embedding_dimensions=384)
require("candidate ready", ready["status"], "ready-for-host-vector-index")
require("candidate authority", ready["canonicalMemoryAuthority"], "Hermes")
require("candidate no local write", ready["authorityBoundary"]["justChillWritesVectorStore"], False)
require("candidate fresh hash", ready["sidecar"]["freshness"]["hashMatches"], True)
require("candidate validation", validate_vector_sidecar_candidate(ready), [])
cases.append("ready-vector-candidate")

def recall_decision(candidate: dict, retrieval_evidence: dict, **overrides) -> dict:
    sidecar = candidate["sidecar"]
    canonical = sidecar["canonicalReference"]
    defaults = {
        "current_source_hash": canonical.get("observedContentHash"),
        "current_deletion_state": sidecar.get("deletionState"),
        "current_redaction_state": sidecar.get("redactionState"),
    }
    defaults.update(overrides)
    return build_recall_gate_decision(candidate, retrieval_evidence, **defaults)

blocked = build_vector_sidecar_candidate(summary, canonical_reference=canonical_ref(summary, canonical=False), embedding_model="local-test-embedding", embedding_dimensions=384)
require("blocked status", blocked["status"], "vector-index-blocked")
require_in("canonical blocker", "canonical source has not been proven in Hermes", blocked["indexGate"]["blockedReasons"])
require_in("hash blocker", "canonical source read-back hash is missing or stale", blocked["indexGate"]["blockedReasons"])
require("blocked validation", validate_vector_sidecar_candidate(blocked), [])
cases.append("noncanonical-source-blocked")

missing_embedding = build_vector_sidecar_candidate(summary, canonical_reference=canonical_ref(summary), embedding_model="contract-only.embedding-model-unbound", embedding_dimensions=None)
require("missing embedding blocked", missing_embedding["status"], "vector-index-blocked")
require_in("model blocker", "host embedding model is not bound", missing_embedding["indexGate"]["blockedReasons"])
require_in("dimension blocker", "host embedding dimensions are required", missing_embedding["indexGate"]["blockedReasons"])
cases.append("embedding-metadata-required")

retrieval = build_retrieval_evidence(ready, query="How should development be routed?", score=0.93)
decision = recall_decision(ready, retrieval)
require("recall allowed", decision["allowRecall"], True)
require("recall status", decision["status"], "recall-allowed")
require("recall boundary", decision["authorityBoundary"]["justChillSearchesVectorStore"], False)
require("recall validation", validate_recall_gate_decision(decision), [])
missing_freshness = build_recall_gate_decision(ready, retrieval)
require("missing freshness blocked", missing_freshness["allowRecall"], False)
require_in("missing source hash blocker", "current canonical source hash is required for recall", missing_freshness["blockedReasons"])
require_in("missing deletion state blocker", "current canonical source deletion state is required for recall", missing_freshness["blockedReasons"])
require_in("missing redaction state blocker", "current canonical source redaction state is required for recall", missing_freshness["blockedReasons"])
cases.append("fresh-canonical-state-required")
cases.append("recall-allowed-with-host-evidence")

low_score = build_retrieval_evidence(ready, query="How should development be routed?", score=0.1)
low_decision = recall_decision(ready, low_score)
require("low score blocked", low_decision["allowRecall"], False)
require_in("score blocker", "retrieval score is below recall threshold", low_decision["blockedReasons"])
bad_score = copy.deepcopy(retrieval)
bad_score["score"] = "high"
bad_score_decision = recall_decision(ready, bad_score)
require("invalid score blocked", bad_score_decision["allowRecall"], False)
require_in("invalid score blocker", "retrieval score is invalid", bad_score_decision["blockedReasons"])
cases.append("low-score-blocked")
threshold_allow = recall_decision(ready, build_retrieval_evidence(ready, query="threshold", score=0.72))
require("threshold exact allowed", threshold_allow["allowRecall"], True)
threshold_block = recall_decision(ready, build_retrieval_evidence(ready, query="threshold", score=0.7199))
require("threshold below blocked", threshold_block["allowRecall"], False)
require_in("threshold blocker", "retrieval score is below recall threshold", threshold_block["blockedReasons"])
cases.append("score-threshold-boundary")
cases.append("invalid-score-blocked")


stale_decision = recall_decision(ready, retrieval, current_source_hash="sha256:stale")
require("stale blocked", stale_decision["allowRecall"], False)
require_in("stale blocker", "current canonical source hash is stale relative to sidecar", stale_decision["blockedReasons"])
cases.append("stale-hash-blocked")

deleted_candidate = build_vector_sidecar_candidate(summary, canonical_reference=canonical_ref(summary, deleted=True), embedding_model="local-test-embedding", embedding_dimensions=384)
deleted_decision = recall_decision(deleted_candidate, build_retrieval_evidence(deleted_candidate, query="route?"))
require("deleted candidate blocked", deleted_candidate["status"], "vector-index-blocked")
require_in("deleted index blocker", "deleted canonical source cannot be indexed or recalled", deleted_candidate["indexGate"]["blockedReasons"])
require_in("deleted recall blocker", "deleted source cannot be recalled", deleted_decision["blockedReasons"])
cases.append("deletion-propagates-to-recall-block")
redacted_candidate = build_vector_sidecar_candidate(summary, canonical_reference=canonical_ref(summary, redacted=True), embedding_model="local-test-embedding", embedding_dimensions=384)
redacted_decision = recall_decision(redacted_candidate, build_retrieval_evidence(redacted_candidate, query="route?"))
require("redacted candidate blocked", redacted_candidate["status"], "vector-index-blocked")
require_in("redacted index blocker", "redacted canonical source cannot be indexed or recalled", redacted_candidate["indexGate"]["blockedReasons"])
require_in("redacted recall blocker", "redacted source cannot be recalled", redacted_decision["blockedReasons"])
cases.append("redaction-propagates-to-recall-block")

post_index_deleted = recall_decision(
    ready,
    retrieval,
    current_deletion_state="deleted",
)
require("post-index deleted blocked", post_index_deleted["allowRecall"], False)
require_in("post-index deleted drift", "current canonical source deletion state differs from sidecar", post_index_deleted["blockedReasons"])
require_in("post-index deleted blocker", "deleted source cannot be recalled", post_index_deleted["blockedReasons"])
post_index_redacted = recall_decision(
    ready,
    retrieval,
    current_redaction_state="redacted",
)
require("post-index redacted blocked", post_index_redacted["allowRecall"], False)
require_in("post-index redacted drift", "current canonical source redaction state differs from sidecar", post_index_redacted["blockedReasons"])
require_in("post-index redacted blocker", "redacted source cannot be recalled", post_index_redacted["blockedReasons"])
cases.append("post-index-delete-redact-blocked")


wrong_scope = recall_decision(ready, retrieval, actor_scope="workspace", requested_scope="private-user")
require("wrong scope blocked", wrong_scope["allowRecall"], False)
require_in("scope blocker", "actor scope does not match requested recall scope", wrong_scope["blockedReasons"])
cases.append("scope-mismatch-blocked")
policy_scope = recall_decision(ready, retrieval, actor_scope="workspace", requested_scope="workspace")
require("policy scope blocked", policy_scope["allowRecall"], False)
require_in("policy scope blocker", "requested scope is not allowed by memory access policy", policy_scope["blockedReasons"])
cases.append("policy-scope-mismatch-blocked")


bad_retrieval = copy.deepcopy(retrieval)
bad_retrieval["provider"] = "untrusted-vector-store"
bad_decision = recall_decision(ready, bad_retrieval)
require("bad provider blocked", bad_decision["allowRecall"], False)
require_in("provider blocker", "retrieval evidence provider is not the host vector sidecar", bad_decision["blockedReasons"])
cases.append("untrusted-retrieval-blocked")
for field, value, blocker in [
    ("retrievalKind", "wrong-kind", "retrieval evidence kind is invalid"),
    ("resultId", "vector_other", "retrieval result does not match sidecar candidate"),
    ("canonicalSourceId", "summary_other", "retrieval canonical source does not match candidate"),
    ("observedContentHash", "sha256:forged", "retrieval observed hash does not match candidate"),
]:
    tampered = copy.deepcopy(retrieval)
    tampered[field] = value
    tampered_decision = recall_decision(ready, tampered)
    require(f"{field} tamper blocked", tampered_decision["allowRecall"], False)
    require_in(f"{field} tamper blocker", blocker, tampered_decision["blockedReasons"])
missing_receipt = copy.deepcopy(retrieval)
missing_receipt.pop("receiptRef")
missing_receipt_decision = recall_decision(ready, missing_receipt)
require("missing retrieval receipt blocked", missing_receipt_decision["allowRecall"], False)
require_in("missing receipt blocker", "retrieval requires durable host search receipt", missing_receipt_decision["blockedReasons"])
cases.append("retrieval-evidence-integrity-blocked")


sensitive_packet = classify_request("remember my API key sk-test-1234567890 for later")
sensitive_raw = build_raw_artifact_record(sensitive_packet, content="API key sk-test-1234567890")
sensitive_summary = build_summary_memory_record(sensitive_raw, "API key sk-test-1234567890", confidence=0.9)
sensitive_candidate = build_vector_sidecar_candidate(sensitive_summary, canonical_reference=canonical_ref(sensitive_summary), embedding_model="local-test-embedding", embedding_dimensions=384)
require("sensitive candidate blocked", sensitive_candidate["status"], "vector-index-blocked")
require_in("sensitive blocker", "sensitive memory requires explicit recall/index approval", sensitive_candidate["indexGate"]["blockedReasons"])
cases.append("sensitive-memory-blocked-without-approval")
sensitive_approved = build_vector_sidecar_candidate(
    sensitive_summary,
    canonical_reference=canonical_ref(sensitive_summary),
    embedding_model="local-test-embedding",
    embedding_dimensions=384,
    approval_token="approved-index",
)
require_in("sensitive remains redacted", "redacted canonical source cannot be indexed or recalled", sensitive_approved["indexGate"]["blockedReasons"])
require("sensitive preview redacted", sensitive_approved["sidecar"]["textPreview"], "[redacted-sensitive]")
recall_sensitive = copy.deepcopy(ready)
recall_sensitive["sidecar"]["sensitivity"] = "sensitive"
sensitive_recall_block = recall_decision(recall_sensitive, build_retrieval_evidence(recall_sensitive, query="sensitive"))
require("sensitive recall blocked", sensitive_recall_block["allowRecall"], False)
require_in("sensitive recall blocker", "sensitive recall requires explicit approval", sensitive_recall_block["blockedReasons"])
sensitive_recall_allowed = recall_decision(recall_sensitive, build_retrieval_evidence(recall_sensitive, query="sensitive"), approval_token="approved-recall")
require("sensitive recall approved", sensitive_recall_allowed["allowRecall"], True)
cases.append("sensitive-approval-boundaries")

print(f"PASS: {len(cases)} just-chill vector recall cases passed")
