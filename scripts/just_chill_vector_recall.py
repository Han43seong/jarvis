#!/usr/bin/env python3
"""Vector sidecar and recall-gate contracts for just-chill.

This module does not embed, index, search, or persist memory by itself. It
creates deterministic contracts for a host-owned vector sidecar that references
Hermes-canonical raw/RDF/summary records and then validates whether a retrieved
candidate is admissible for just-chill context use.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from typing import Any, Callable

from just_chill_live_bindings import Runner, discover_live_surfaces
from just_chill_memory_contracts import (
    PLACEHOLDER_TIME,
    build_raw_artifact_record,
    build_summary_memory_record,
    content_hash,
    stable_id,
    validate_contract_record,
)
from just_chill_router import classify_request

SCHEMA_VERSION = 1
CONTRACT_NAME = "just-chill-vector-recall-contract-v1"
CANONICAL_MEMORY_AUTHORITY = "Hermes"
SIDECAR_AUTHORITY = "host-vector-sidecar"
MIN_RECALL_SCORE = 0.72
DEFAULT_EMBEDDING_MODEL = "contract-only.embedding-model-unbound"
REQUIRED_VECTOR_TOOLS = ["hermes.vector_sidecar.search", "hermes.vector_sidecar.read"]
Which = Callable[[str], str | None]
ModuleProbe = Callable[[str], bool]



def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def build_vector_boundary_report(
    *,
    cwd: str | None = None,
    probe: bool = False,
    surfaces: dict[str, Any] | None = None,
    which: Which | None = None,
    module_available: ModuleProbe | None = None,
    runner: Runner | None = None,
) -> dict[str, Any]:
    """Map vector/recall surfaces without calling live search or write APIs."""

    module_available = module_available or _module_available
    which = which or shutil.which
    surfaces = surfaces or discover_live_surfaces(cwd=cwd, probe=probe, runner=runner, which=which)
    hermes = surfaces.get("hermes", {}) if isinstance(surfaces, dict) else {}
    provider_surface = hermes.get("memoryProviderSurface", {}) if isinstance(hermes, dict) else {}
    provider_tool = provider_surface.get("tool", {}) if isinstance(provider_surface, dict) else {}
    read_actions = provider_tool.get("readActions", []) if isinstance(provider_tool, dict) else []
    provider_search_available = bool(
        provider_surface.get("status") == "provider-tool-available"
        and provider_tool.get("name")
        and any(action in read_actions for action in ["search", "probe", "list"])
    )

    embedding_modules = {
        "sentence_transformers": module_available("sentence_transformers"),
        "faiss": module_available("faiss"),
        "sklearn": module_available("sklearn"),
    }
    embedding_commands = {
        "sqlite3": bool(which("sqlite3")),
        "python3": bool(which("python3")),
    }
    required_vector_tools = REQUIRED_VECTOR_TOOLS
    known_vector_tools = {
        "hermes.vector_sidecar.create",
        "hermes.vector_sidecar.search",
        "hermes.vector_sidecar.read",
        "hermes.vector_sidecar.delete",
    }
    vector_api_candidates = []
    memory_api_tools = hermes.get("justChillMemoryApiSurface", {}).get("tools", []) if isinstance(hermes, dict) else []
    mapped_vector_tools: list[str] = []
    vector_like_tool_names: list[str] = []
    if isinstance(memory_api_tools, list):
        mapped_vector_tools = [str(tool) for tool in memory_api_tools if str(tool) in required_vector_tools]
        vector_like_tool_names = [
            str(tool)
            for tool in memory_api_tools
            if "vector" in str(tool).lower() and str(tool) not in known_vector_tools
        ]
        vector_api_candidates.extend([str(tool) for tool in memory_api_tools if str(tool) in known_vector_tools])
        vector_api_candidates.extend(vector_like_tool_names)
    if provider_search_available:
        vector_api_candidates.append("hermes.summary_memory.provider_tool.fact_store.search")

    live_vector_store_mapped = all(tool in mapped_vector_tools for tool in required_vector_tools)
    live_vector_ready = live_vector_store_mapped and any(embedding_modules.values())
    status = "live-vector-api-mapped" if live_vector_store_mapped else (
        "provider-search-only" if provider_search_available else "vector-api-unmapped"
    )
    blockers = []
    if not live_vector_store_mapped:
        blockers.append("Hermes-native vector sidecar store/search API is not mapped")
        if provider_search_available:
            blockers.append("Holographic fact_store search is provider summary search, not vector sidecar authority")
    if not any(embedding_modules.values()):
        blockers.append("no local embedding library is mapped for host-owned vector generation")
    if vector_like_tool_names:
        blockers.append("vector-like tool names are not sufficient without explicit search/read sidecar APIs")

    return {
        "schemaVersion": SCHEMA_VERSION,
        "reportKind": "vector-recall-live-boundary-v1",
        "status": status,
        "canonicalMemoryAuthority": CANONICAL_MEMORY_AUTHORITY,
        "sidecarAuthority": SIDECAR_AUTHORITY,
        "cwd": cwd,
        "probeMode": "read-only-smoke" if probe else "availability-only",
        "surfaces": {
            "hermesMemoryProvider": hermes.get("memoryProvider"),
            "providerSearchAvailable": provider_search_available,
            "providerSearchApi": "hermes.summary_memory.provider_tool.fact_store.search" if provider_search_available else "unmapped",
            "vectorSidecarApi": "mapped" if live_vector_store_mapped else "unmapped",
            "vectorApiCandidates": vector_api_candidates,
            "requiredVectorTools": required_vector_tools,
            "mappedVectorTools": mapped_vector_tools,
            "vectorLikeToolNames": vector_like_tool_names,
            "embeddingModules": embedding_modules,
            "embeddingCommands": embedding_commands,
        },
        "authorityBoundary": {
            "justChillEmbedsText": False,
            "justChillWritesVectorStore": False,
            "justChillSearchesVectorStore": False,
            "hostOwnsEmbeddingAndSearch": True,
            "hermesOwnsCanonicalMemory": True,
        },
        "liveSearchGate": {
            "ready": live_vector_ready,
            "blockedReasons": blockers,
        },
        "notes": [
            "Provider summary search may inform recall UX, but it does not make the vector sidecar canonical.",
            "Recall admission requires canonical Hermes source refs, fresh hashes, access policy, and host retrieval evidence.",
        ],
    }


def validate_vector_boundary_report(report: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if report.get("schemaVersion") != SCHEMA_VERSION:
        issues.append("schemaVersion mismatch")
    if report.get("reportKind") != "vector-recall-live-boundary-v1":
        issues.append("report kind mismatch")
    if report.get("canonicalMemoryAuthority") != CANONICAL_MEMORY_AUTHORITY:
        issues.append("canonical memory authority must remain Hermes")
    boundary = report.get("authorityBoundary", {})
    for key in ["justChillEmbedsText", "justChillWritesVectorStore", "justChillSearchesVectorStore"]:
        if boundary.get(key) is not False:
            issues.append(f"{key} must be false")
    if boundary.get("hermesOwnsCanonicalMemory") is not True:
        issues.append("Hermes must own canonical memory")
    gate = report.get("liveSearchGate", {})
    if gate.get("ready") and gate.get("blockedReasons"):
        issues.append("ready vector live-search gate cannot have blockers")
    return issues


def _summary(record: dict[str, Any]) -> dict[str, Any]:
    summary = record.get("summaryMemory")
    if record.get("recordKind") != "summary-memory-contract" or not isinstance(summary, dict):
        raise ValueError("record must be a summary-memory-contract")
    return summary


def default_canonical_reference(summary_record: dict[str, Any], *, receipt_ref: str = "host-receipt-required") -> dict[str, Any]:
    """Build a fail-closed canonical reference placeholder for a summary record."""

    summary = _summary(summary_record)
    return {
        "sourceKind": "summary-memory",
        "canonicalSourceId": summary.get("id"),
        "canonicalContentHash": summary.get("summaryHash"),
        "observedContentHash": summary.get("summaryHash"),
        "receiptRef": receipt_ref,
        "receiptKind": "host-owned-summary-memory-receipt",
        "readBackHashMatches": False,
        "canonicalInHermes": False,
        "deletionState": summary.get("deletionState"),
        "redactionState": summary.get("redactionState"),
    }


def build_vector_sidecar_candidate(
    summary_record: dict[str, Any],
    *,
    canonical_reference: dict[str, Any] | None = None,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    embedding_dimensions: int | None = None,
    approval_token: str | None = None,
) -> dict[str, Any]:
    """Create a deterministic vector sidecar candidate without embedding text."""

    contract_issues = validate_contract_record(summary_record)
    try:
        summary = _summary(summary_record)
    except ValueError as exc:
        summary = {}
        contract_issues.append(str(exc))
    canonical_reference = canonical_reference or (default_canonical_reference(summary_record) if summary else {})
    text = str(summary.get("summary", ""))
    source_refs = list(summary.get("sourceArtifactRefs", [])) if isinstance(summary.get("sourceArtifactRefs"), list) else []
    sensitivity = summary.get("sensitivity")
    deletion_state = canonical_reference.get("deletionState", summary.get("deletionState"))
    redaction_state = canonical_reference.get("redactionState", summary.get("redactionState"))
    canonical_hash = canonical_reference.get("canonicalContentHash")
    observed_hash = canonical_reference.get("observedContentHash")
    hash_matches = bool(canonical_hash and observed_hash and canonical_hash == observed_hash and canonical_reference.get("readBackHashMatches") is True)

    base = {
        "summaryId": summary.get("id"),
        "canonicalSourceId": canonical_reference.get("canonicalSourceId"),
        "canonicalContentHash": canonical_hash,
        "embeddingModel": embedding_model,
        "textHash": content_hash(text),
    }
    sidecar_id = stable_id("vector", base)
    blockers = [*contract_issues]
    if canonical_reference.get("canonicalInHermes") is not True:
        blockers.append("canonical source has not been proven in Hermes")
    if canonical_reference.get("readBackHashMatches") is not True or not hash_matches:
        blockers.append("canonical source read-back hash is missing or stale")
    if not canonical_reference.get("receiptRef"):
        blockers.append("canonical source receiptRef is required")
    if sensitivity == "sensitive" and not approval_token:
        blockers.append("sensitive memory requires explicit recall/index approval")
    if deletion_state != "active":
        blockers.append("deleted canonical source cannot be indexed or recalled")
    if redaction_state != "not_redacted":
        blockers.append("redacted canonical source cannot be indexed or recalled")
    if not source_refs:
        blockers.append("summary memory requires raw artifact provenance")
    if not embedding_model or embedding_model == DEFAULT_EMBEDDING_MODEL:
        blockers.append("host embedding model is not bound")
    if not embedding_dimensions or embedding_dimensions <= 0:
        blockers.append("host embedding dimensions are required")

    return {
        "schemaVersion": SCHEMA_VERSION,
        "contract": CONTRACT_NAME,
        "recordKind": "vector-sidecar-candidate",
        "status": "ready-for-host-vector-index" if not blockers else "vector-index-blocked",
        "canonicalMemoryAuthority": CANONICAL_MEMORY_AUTHORITY,
        "sidecarAuthority": SIDECAR_AUTHORITY,
        "sidecar": {
            "id": sidecar_id,
            "sourceSummaryId": summary.get("id"),
            "sourceArtifactRefs": source_refs,
            "canonicalReference": canonical_reference,
            "textHash": content_hash(text),
            "textPreview": "[redacted-sensitive]" if sensitivity == "sensitive" else text[:160],
            "sensitivity": sensitivity,
            "accessPolicy": summary.get("accessPolicy", {}),
            "retention": summary.get("retention", {}),
            "deletionState": deletion_state,
            "redactionState": redaction_state,
            "embedding": {
                "model": embedding_model,
                "dimensions": embedding_dimensions,
                "vectorPayloadStoredHere": False,
                "vectorHash": "host-vector-hash-required",
            },
            "freshness": {
                "canonicalContentHash": canonical_hash,
                "observedContentHash": observed_hash,
                "hashMatches": hash_matches,
            },
            "provenance": {
                "derivedFromSummaryHash": summary.get("summaryHash"),
                "rawContentHash": summary.get("provenance", {}).get("rawContentHash"),
                "canonicalReceiptRef": canonical_reference.get("receiptRef"),
                "generatedAt": PLACEHOLDER_TIME,
            },
        },
        "indexGate": {
            "ready": not blockers,
            "blockedReasons": blockers,
            "approvalTokenPresent": bool(approval_token),
        },
        "authorityBoundary": {
            "justChillEmbedsText": False,
            "justChillWritesVectorStore": False,
            "justChillOwnsCanonicalMemory": False,
            "hostOwnsEmbeddingAndIndexing": True,
            "hermesOwnsCanonicalMemory": True,
        },
        "evidenceRequirements": [
            "canonical Hermes source receipt with read-back hash",
            "host-owned embedding model and dimensions",
            "durable host vector-index receipt before live recall",
            "deletion/redaction receipts must invalidate sidecar recall",
        ],
    }


def validate_vector_sidecar_candidate(candidate: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if candidate.get("schemaVersion") != SCHEMA_VERSION:
        issues.append("schemaVersion mismatch")
    if candidate.get("contract") != CONTRACT_NAME:
        issues.append("contract name mismatch")
    if candidate.get("recordKind") != "vector-sidecar-candidate":
        issues.append("record kind mismatch")
    if candidate.get("canonicalMemoryAuthority") != CANONICAL_MEMORY_AUTHORITY:
        issues.append("canonical memory authority must remain Hermes")
    if candidate.get("sidecarAuthority") != SIDECAR_AUTHORITY:
        issues.append("sidecar authority mismatch")
    boundary = candidate.get("authorityBoundary", {})
    for key in ["justChillEmbedsText", "justChillWritesVectorStore", "justChillOwnsCanonicalMemory"]:
        if boundary.get(key) is not False:
            issues.append(f"{key} must be false")
    if boundary.get("hermesOwnsCanonicalMemory") is not True:
        issues.append("Hermes must own canonical memory")
    sidecar = candidate.get("sidecar", {})
    if not sidecar.get("id"):
        issues.append("sidecar id is required")
    if sidecar.get("freshness", {}).get("hashMatches") is not True and candidate.get("status") == "ready-for-host-vector-index":
        issues.append("ready candidate requires fresh canonical hash match")
    if candidate.get("status") == "ready-for-host-vector-index" and candidate.get("indexGate", {}).get("blockedReasons"):
        issues.append("ready candidate cannot have blocked reasons")
    if candidate.get("status") == "vector-index-blocked" and candidate.get("indexGate", {}).get("ready") is True:
        issues.append("blocked candidate cannot have ready index gate")
    return issues


def build_retrieval_evidence(candidate: dict[str, Any], *, query: str, score: float = 0.91, receipt_ref: str = "host-vector-search-receipt") -> dict[str, Any]:
    sidecar = candidate.get("sidecar", {})
    canonical_ref = sidecar.get("canonicalReference", {})
    return {
        "provider": SIDECAR_AUTHORITY,
        "retrievalKind": "host-vector-sidecar-search-result",
        "queryHash": content_hash(query),
        "resultId": sidecar.get("id"),
        "canonicalSourceId": canonical_ref.get("canonicalSourceId"),
        "observedContentHash": canonical_ref.get("observedContentHash"),
        "score": score,
        "receiptRef": receipt_ref,
    }


def build_recall_gate_decision(
    candidate: dict[str, Any],
    retrieval_evidence: dict[str, Any],
    *,
    actor_scope: str = "private-user",
    requested_scope: str = "private-user",
    approval_token: str | None = None,
    current_source_hash: str | None = None,
    current_deletion_state: str | None = None,
    current_redaction_state: str | None = None,
    min_score: float = MIN_RECALL_SCORE,
) -> dict[str, Any]:
    """Decide whether a host-retrieved vector candidate may enter context."""

    sidecar = candidate.get("sidecar", {}) if isinstance(candidate, dict) else {}
    canonical_ref = sidecar.get("canonicalReference", {}) if isinstance(sidecar, dict) else {}
    access = sidecar.get("accessPolicy", {}) if isinstance(sidecar, dict) else {}
    deletion_state = current_deletion_state if current_deletion_state is not None else sidecar.get("deletionState")
    redaction_state = current_redaction_state if current_redaction_state is not None else sidecar.get("redactionState")
    blockers = validate_vector_sidecar_candidate(candidate)
    if not current_source_hash:
        blockers.append("current canonical source hash is required for recall")
    if current_deletion_state is None:
        blockers.append("current canonical source deletion state is required for recall")
    if current_redaction_state is None:
        blockers.append("current canonical source redaction state is required for recall")
    if candidate.get("status") != "ready-for-host-vector-index":
        blockers.append("candidate is not ready for host vector index")
    if candidate.get("indexGate", {}).get("blockedReasons"):
        blockers.extend(candidate["indexGate"]["blockedReasons"])
    if retrieval_evidence.get("provider") != SIDECAR_AUTHORITY:
        blockers.append("retrieval evidence provider is not the host vector sidecar")
    if retrieval_evidence.get("retrievalKind") != "host-vector-sidecar-search-result":
        blockers.append("retrieval evidence kind is invalid")
    if retrieval_evidence.get("resultId") != sidecar.get("id"):
        blockers.append("retrieval result does not match sidecar candidate")
    if retrieval_evidence.get("canonicalSourceId") != canonical_ref.get("canonicalSourceId"):
        blockers.append("retrieval canonical source does not match candidate")
    if retrieval_evidence.get("observedContentHash") != canonical_ref.get("observedContentHash"):
        blockers.append("retrieval observed hash does not match candidate")
    if not retrieval_evidence.get("receiptRef"):
        blockers.append("retrieval requires durable host search receipt")
    try:
        retrieval_score = float(retrieval_evidence.get("score", 0.0) or 0.0)
    except (TypeError, ValueError):
        retrieval_score = 0.0
        blockers.append("retrieval score is invalid")
    if retrieval_score < min_score:
        blockers.append("retrieval score is below recall threshold")
    if sidecar.get("sensitivity") == "sensitive" and not approval_token:
        blockers.append("sensitive recall requires explicit approval")
    if current_deletion_state is not None and current_deletion_state != sidecar.get("deletionState"):
        blockers.append("current canonical source deletion state differs from sidecar")
    if current_redaction_state is not None and current_redaction_state != sidecar.get("redactionState"):
        blockers.append("current canonical source redaction state differs from sidecar")
    if deletion_state != "active":
        blockers.append("deleted source cannot be recalled")
    if redaction_state != "not_redacted":
        blockers.append("redacted source cannot be recalled")
    if not access.get("scope"):
        blockers.append("memory access policy scope is required")
    if access.get("scope") and access.get("scope") != requested_scope:
        blockers.append("requested scope is not allowed by memory access policy")
    if actor_scope != requested_scope:
        blockers.append("actor scope does not match requested recall scope")
    if current_source_hash and current_source_hash != canonical_ref.get("observedContentHash"):
        blockers.append("current canonical source hash is stale relative to sidecar")
    if canonical_ref.get("canonicalInHermes") is not True:
        blockers.append("candidate source is not canonical in Hermes")

    # Preserve order while removing duplicates.
    unique_blockers = list(dict.fromkeys(blockers))
    return {
        "schemaVersion": SCHEMA_VERSION,
        "contract": CONTRACT_NAME,
        "decisionKind": "recall-gate-decision-v1",
        "candidateId": sidecar.get("id"),
        "allowRecall": not unique_blockers,
        "status": "recall-allowed" if not unique_blockers else "recall-blocked",
        "canonicalMemoryAuthority": CANONICAL_MEMORY_AUTHORITY,
        "sidecarAuthority": SIDECAR_AUTHORITY,
        "thresholds": {"minScore": min_score},
        "retrievalEvidence": retrieval_evidence,
        "accessCheck": {
            "actorScope": actor_scope,
            "requestedScope": requested_scope,
            "policyScope": access.get("scope"),
            "approvalTokenPresent": bool(approval_token),
        },
        "freshnessCheck": {
            "currentSourceHash": current_source_hash,
            "currentDeletionState": current_deletion_state,
            "currentRedactionState": current_redaction_state,
        },
        "blockedReasons": unique_blockers,
        "authorityBoundary": {
            "justChillSearchesVectorStore": False,
            "justChillReadsCanonicalMemoryDirectly": False,
            "hostOwnsRetrieval": True,
            "hermesOwnsCanonicalMemory": True,
        },
        "contextUse": {
            "allowed": not unique_blockers,
            "mode": "retrieved-memory-context" if not unique_blockers else "not-available",
            "requiresSourceCitation": True,
            "requiresDeletionCheckEachUse": True,
        },
    }


def validate_recall_gate_decision(decision: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if decision.get("schemaVersion") != SCHEMA_VERSION:
        issues.append("schemaVersion mismatch")
    if decision.get("contract") != CONTRACT_NAME:
        issues.append("contract name mismatch")
    if decision.get("decisionKind") != "recall-gate-decision-v1":
        issues.append("decision kind mismatch")
    if decision.get("canonicalMemoryAuthority") != CANONICAL_MEMORY_AUTHORITY:
        issues.append("canonical memory authority must remain Hermes")
    boundary = decision.get("authorityBoundary", {})
    for key in ["justChillSearchesVectorStore", "justChillReadsCanonicalMemoryDirectly"]:
        if boundary.get(key) is not False:
            issues.append(f"{key} must be false")
    if boundary.get("hermesOwnsCanonicalMemory") is not True:
        issues.append("Hermes must own canonical memory")
    if decision.get("allowRecall") and decision.get("blockedReasons"):
        issues.append("allowed recall cannot have blocked reasons")
    if decision.get("allowRecall") is not bool(decision.get("contextUse", {}).get("allowed")):
        issues.append("contextUse allowed flag must match allowRecall")
    return issues


def _build_demo_summary(request: str, summary_text: str) -> dict[str, Any]:
    packet = classify_request(request)
    raw = build_raw_artifact_record(packet, content=request)
    return build_summary_memory_record(raw, summary_text)


def _ready_canonical_reference(summary: dict[str, Any], *, receipt_ref: str = "host-hermes-receipt://demo") -> dict[str, Any]:
    memory = _summary(summary)
    return {
        "sourceKind": "summary-memory",
        "canonicalSourceId": memory["id"],
        "canonicalContentHash": memory["summaryHash"],
        "observedContentHash": memory["summaryHash"],
        "receiptRef": receipt_ref,
        "receiptKind": "host-owned-summary-memory-receipt",
        "readBackHashMatches": True,
        "canonicalInHermes": True,
        "deletionState": memory["deletionState"],
        "redactionState": memory["redactionState"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build just-chill vector sidecar and recall-gate contracts.")
    parser.add_argument("request", nargs="*", help="Request text for demo contract generation.")
    parser.add_argument("--summary", default="User prefers visible GJC sessions for development work.", help="Summary text for demo candidate generation.")
    parser.add_argument("--cwd", default=None, help="Repo root for read-only boundary discovery.")
    parser.add_argument("--probe", action="store_true", help="Run read-only surface probes for boundary reports.")
    parser.add_argument("--boundary", action="store_true", help="Emit the vector/recall live-boundary report.")
    parser.add_argument("--candidate", action="store_true", help="Emit a demo vector sidecar candidate.")
    parser.add_argument("--recall", action="store_true", help="Emit a demo recall gate decision.")
    parser.add_argument("--blocked-demo", action="store_true", help="Build the demo candidate with fail-closed placeholder canonical evidence.")
    parser.add_argument("--embedding-model", default="local-test-embedding-model", help="Host-owned embedding model metadata.")
    parser.add_argument("--embedding-dimensions", type=int, default=384, help="Host-owned embedding vector dimensions.")
    parser.add_argument("--query", default="How should development requests be routed?", help="Query text for demo recall evidence.")
    parser.add_argument("--retrieval-evidence-json", help="Override retrieval evidence JSON for --recall.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    request = " ".join(args.request).strip() or "remember that development requests route to GJC visible sessions first"
    selected = [args.boundary, args.candidate, args.recall]
    if sum(1 for item in selected if item) != 1:
        parser.error("select exactly one of --boundary, --candidate, or --recall")

    if args.boundary:
        output = build_vector_boundary_report(cwd=args.cwd, probe=args.probe)
        issues = validate_vector_boundary_report(output)
    else:
        summary_record = _build_demo_summary(request, args.summary)
        canonical = default_canonical_reference(summary_record) if args.blocked_demo else _ready_canonical_reference(summary_record)
        candidate = build_vector_sidecar_candidate(
            summary_record,
            canonical_reference=canonical,
            embedding_model=args.embedding_model,
            embedding_dimensions=args.embedding_dimensions,
        )
        if args.candidate:
            output = candidate
            issues = validate_vector_sidecar_candidate(candidate)
        else:
            evidence = json.loads(args.retrieval_evidence_json) if args.retrieval_evidence_json else build_retrieval_evidence(candidate, query=args.query)
            output = build_recall_gate_decision(
                candidate,
                evidence,
                current_source_hash=canonical.get("observedContentHash"),
                current_deletion_state=canonical.get("deletionState"),
                current_redaction_state=canonical.get("redactionState"),
            )
            issues = validate_recall_gate_decision(output)
    if issues:
        output["validationIssues"] = issues
    print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
