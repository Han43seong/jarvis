#!/usr/bin/env python3
"""Deterministic end-to-end dogfood harness for just-chill contracts.

The harness exercises request routing, memory/raw/RDF/vector contract generation,
recall admission, and GJC handoff planning without executing GJC, writing Hermes,
running SHACL, or searching a vector store locally.
"""
from __future__ import annotations

import argparse
import json
from typing import Any

from just_chill_cli import handoff_gjc_command, recall_command, remember_command, route_command
from just_chill_gjc_consent_policy import build_consent_policy_decision, validate_consent_policy_decision
from just_chill_memory_contracts import build_raw_artifact_record, content_hash, validate_contract_record
from just_chill_ontology_contracts import (
    build_ontology_contract,
    build_rdf_owl_export,
    build_shacl_shape_export,
    validate_ontology_contract,
    validate_rdf_owl_export,
    validate_shacl_shape_export,
)
from just_chill_router import classify_request
from just_chill_vector_recall import (
    build_retrieval_evidence,
    build_vector_sidecar_candidate,
    validate_recall_gate_decision,
    validate_vector_sidecar_candidate,
)

SCHEMA_VERSION = 1
HARNESS_NAME = "just-chill-e2e-dogfood-contract-v1"
DEFAULT_DEV_REQUEST = "fix src/hooks/bridge.ts and run focused checks"
DEFAULT_MEMORY_REQUEST = "remember that development requests route to visible GJC sessions first"
DEFAULT_SUMMARY = "Development requests route to visible GJC sessions first."


def ready_hermes_boundary() -> dict[str, Any]:
    return {
        "status": "ready-for-hermes-write",
        "writeGate": {"allowedHere": False, "enabled": True},
        "approval": {"sensitiveApproved": False},
        "storageAuthority": "Hermes",
        "justChillCallsHermes": False,
    }


def canonical_ref(summary_record: dict[str, Any]) -> dict[str, Any]:
    memory = summary_record["summaryMemory"]
    return {
        "sourceKind": "summary-memory",
        "canonicalSourceId": memory["id"],
        "canonicalContentHash": memory["summaryHash"],
        "observedContentHash": memory["summaryHash"],
        "receiptRef": "host-hermes-receipt://dogfood-summary-read-001",
        "receiptKind": "host-owned-summary-memory-receipt",
        "readBackHashMatches": True,
        "canonicalInHermes": True,
        "deletionState": memory["deletionState"],
        "redactionState": memory["redactionState"],
    }


def _independent_raw(memory_request: str) -> dict[str, Any]:
    packet = classify_request(memory_request + " (independent design note)")
    return build_raw_artifact_record(
        packet,
        content="Independent design note: development requests route to visible GJC sessions first.",
        artifact_type="dogfood_independent_source",
        source_channel="just-chill-dogfood-fixture",
    )


def _authority_boundary() -> dict[str, Any]:
    return {
        "executionAllowedHere": False,
        "justChillExecutesGjc": False,
        "justChillWritesHermes": False,
        "justChillOwnsCanonicalMemory": False,
        "justChillRunsShaclEngine": False,
        "justChillSearchesVectorStore": False,
    }


def build_dogfood_harness(
    *,
    dev_request: str = DEFAULT_DEV_REQUEST,
    memory_request: str = DEFAULT_MEMORY_REQUEST,
    summary: str = DEFAULT_SUMMARY,
    cwd: str | None = None,
    recall_source_hash_override: str | None = None,
    current_deletion_state: str | None = None,
    current_redaction_state: str | None = None,
) -> dict[str, Any]:
    route = route_command(dev_request, cwd=cwd, include_bridge=True)
    handoff = handoff_gjc_command(dev_request, cwd=cwd)
    remember = remember_command(memory_request, summary=summary, source_channel="just-chill-dogfood-fixture")
    raw = remember["rawArtifactContract"]
    summary_record = remember["summaryMemoryContract"]
    independent_raw = _independent_raw(memory_request)

    ontology = build_ontology_contract(
        raw,
        summary_record,
        assertion_kind="PreferenceAssertion",
        repeated_sources=2,
        confidence=0.91,
        non_destructive=True,
        access_allowed=True,
        conflict_free=True,
        hermes_boundary_report=ready_hermes_boundary(),
        independent_source_records=[independent_raw],
    )
    rdf_export = build_rdf_owl_export(ontology)
    shacl_export = build_shacl_shape_export(ontology)

    reference = canonical_ref(summary_record)
    vector = build_vector_sidecar_candidate(
        summary_record,
        canonical_reference=reference,
        embedding_model="dogfood-deterministic-exact-hash",
        embedding_dimensions=384,
    )
    retrieval = build_retrieval_evidence(vector, query="How should development be routed?", score=0.93)
    recall = recall_command(
        "How should development be routed?",
        candidate_json=json.dumps(vector, ensure_ascii=False, sort_keys=True),
        retrieval_evidence_json=json.dumps(retrieval, ensure_ascii=False, sort_keys=True),
        current_source_hash=recall_source_hash_override or reference["observedContentHash"],
        current_deletion_state=current_deletion_state or reference["deletionState"],
        current_redaction_state=current_redaction_state or reference["redactionState"],
    )
    consent = build_consent_policy_decision(
        handoff["bridgePlan"],
        surfaces={
            "visibleRoutedSession": {
                "status": "orchestration-plan-ready",
                "scrollbackIsCompletion": False,
                "evidencePolicy": {"durableEvidenceRequired": True, "scrollbackIsCompletion": False},
            },
            "operatorConsent": {"allowMutation": False, "source": "not-needed-visible", "requiredPerMutatingCall": True},
            "coordinatorMcp": {"status": "not-used", "missingTools": [], "mutationClassesEnabled": [], "mutationClassesRequiredForExecution": ["sessions", "questions", "reports"]},
            "gjcDelegation": {"delegateTools": {}},
        },
        evidence_payload={"kind": "test", "command": ["python3", "scripts/check_just_chill_dogfood_harness.py"]},
    )

    validation_issues: list[str] = []
    validation_issues.extend(validate_contract_record(raw))
    validation_issues.extend(validate_contract_record(summary_record))
    validation_issues.extend(validate_contract_record(independent_raw))
    validation_issues.extend(validate_ontology_contract(ontology))
    validation_issues.extend(validate_rdf_owl_export(rdf_export, ontology))
    validation_issues.extend(validate_shacl_shape_export(shacl_export, ontology))
    validation_issues.extend(validate_vector_sidecar_candidate(vector))
    if recall["recallGateDecision"]:
        validation_issues.extend(validate_recall_gate_decision(recall["recallGateDecision"]))
    validation_issues.extend(validate_consent_policy_decision(consent))

    assertions = {
        "devRoutesToGjc": route["routerPacket"]["classification"]["isDevelopment"] is True and route["routerPacket"]["routing"]["target"] == "GJC",
        "handoffDoesNotExecute": handoff["executionAllowedHere"] is False and handoff["bridgePlan"]["authorityBoundary"]["noExecutionInThisPlan"] is True,
        "memoryContractsReady": remember["status"] == "memory-candidate-ready" and raw["artifact"]["sensitivity"] == "internal",
        "rdfContractsValid": not validate_rdf_owl_export(rdf_export, ontology) and not validate_shacl_shape_export(shacl_export, ontology),
        "ontologyCandidateEligible": ontology["aboxCandidate"]["promotionPolicy"]["canonicalPromotionEligible"] is True,
        "vectorCandidateReady": vector["status"] == "ready-for-host-vector-index",
        "recallAllowed": recall["status"] == "recall-allowed" and recall["recallGateDecision"]["allowRecall"] is True,
        "consentKeepsVisibleFirst": consent["status"] == "visible-session-preferred" and consent["mutationConsentGate"]["approvedForHostMutation"] is False,
        "noHiddenExecution": all(
            item.get("executionAllowedHere") is False
            for item in [route, handoff, remember, recall]
        ) and consent["authorityBoundary"]["executionAllowedHere"] is False,
    }
    failed_assertions = [name for name, passed in assertions.items() if not passed]
    if failed_assertions:
        validation_issues.extend(f"assertion failed: {name}" for name in failed_assertions)

    return {
        "schemaVersion": SCHEMA_VERSION,
        "harness": HARNESS_NAME,
        "status": "passed" if not validation_issues else "blocked",
        "authorityBoundary": _authority_boundary(),
        "inputs": {"devRequest": dev_request, "memoryRequest": memory_request, "summary": summary},
        "routeFlow": route,
        "handoffFlow": handoff,
        "memoryFlow": remember,
        "ontologyFlow": {
            "contract": ontology,
            "rdfExport": rdf_export,
            "shaclExport": shacl_export,
            "independentRawArtifactContract": independent_raw,
        },
        "vectorFlow": {"candidate": vector, "retrievalEvidence": retrieval},
        "recallFlow": recall,
        "consentFlow": consent,
        "assertions": assertions,
        "validationIssues": validation_issues,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run deterministic just-chill e2e dogfood contract harness without executing GJC/Hermes.")
    parser.add_argument("--dev-request", default=DEFAULT_DEV_REQUEST)
    parser.add_argument("--memory-request", default=DEFAULT_MEMORY_REQUEST)
    parser.add_argument("--summary", default=DEFAULT_SUMMARY)
    parser.add_argument("--cwd", default=None)
    parser.add_argument("--recall-source-hash-override", default=None)
    parser.add_argument("--current-deletion-state", default=None)
    parser.add_argument("--current-redaction-state", default=None)
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_dogfood_harness(
        dev_request=args.dev_request,
        memory_request=args.memory_request,
        summary=args.summary,
        cwd=args.cwd,
        recall_source_hash_override=args.recall_source_hash_override,
        current_deletion_state=args.current_deletion_state,
        current_redaction_state=args.current_redaction_state,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
