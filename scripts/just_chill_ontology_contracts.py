#!/usr/bin/env python3
"""Deterministic ontology contracts for just-chill memory candidates.

This module builds contract-level TBox/ABox and SHACL-style validation output
from just-chill raw artifact / summary memory records. It does not write Hermes
memory, persist RDF, or promote canonical assertions.
"""
from __future__ import annotations

import argparse
import importlib.util
import hashlib
import json
import shutil
from typing import Any

from just_chill_hermes_adapter import build_hermes_live_boundary_report
from just_chill_memory_contracts import (
    build_raw_artifact_record,
    build_summary_memory_record,
    validate_contract_record,
)
from just_chill_router import classify_request

SCHEMA_VERSION = 1
ONTOLOGY_CONTRACT_NAME = "just-chill-ontology-contract-v1"
BASE_IRI = "https://just-chill.local/ontology#"
ASSERTION_KINDS = {"DecisionAssertion", "PolicyAssertion", "PreferenceAssertion", "OperationalEvent"}
EXPLICIT_CONFIRMATION_KINDS = {"DecisionAssertion", "PolicyAssertion"}
PREFERENCE_AUTO_PROMOTION_CRITERIA = [
    "repeated-independent-sources",
    "non-sensitive",
    "non-destructive",
    "access-allowed",
    "retention-valid",
    "conflict-free",
    "high-confidence",
    "hermes-boundary-ready",
]
SENSITIVITY_RANK = {"internal": 0, "restricted": 1, "sensitive": 2}
RDF_EXPORT_CONTRACT_NAME = "just-chill-rdf-owl-export-contract-v1"
SHACL_EXPORT_CONTRACT_NAME = "just-chill-shacl-shapes-contract-v1"
RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS_NS = "http://www.w3.org/2000/01/rdf-schema#"
OWL_NS = "http://www.w3.org/2002/07/owl#"
SHACL_NS = "http://www.w3.org/ns/shacl#"
XSD_NS = "http://www.w3.org/2001/XMLSchema#"
DENIED_PERSISTENCE_KEYS = {
    "canonicalABoxWrite",
    "graphStoreIri",
    "hermesWriteReceipt",
    "persistedAt",
    "persistenceReceipt",
    "rdfStoreIri",
    "shaclEngineReceipt",
    "storageWrite",
}
RDF_SHACL_LIVE_BOUNDARY_NAME = "just-chill-rdf-shacl-live-boundary-v1"
RDF_SHACL_PERSISTENCE_PLAN_NAME = "just-chill-rdf-shacl-persistence-plan-v1"
RDF_PARSER_COMMANDS = ("rdfpipe", "rapper", "riot")
SHACL_ENGINE_COMMANDS = ("pyshacl", "shacl")
RDF_MODULES = ("rdflib", "pyshacl")
RDF_GRAPH_TERMS = ("rdf", "graph", "ontology", "abox", "tbox")
RDF_WRITE_TERMS = ("create", "write", "store", "persist", "upsert", "add")
RDF_READ_TERMS = ("read", "get", "fetch", "retrieve")
RDF_DELETE_TERMS = ("delete", "remove", "redact", "erase")




def _canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_id(prefix: str, data: Any) -> str:
    digest = hashlib.sha256(_canonical_json(data).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}_{digest}"


def _class_iri(name: str) -> str:
    return f"{BASE_IRI}{name}"


def build_tbox() -> dict[str, Any]:
    return {
        "iri": f"{BASE_IRI}JustChillMemoryOntology",
        "classes": [
            {"id": _class_iri("RawArtifact"), "label": "RawArtifact"},
            {"id": _class_iri("SummaryMemory"), "label": "SummaryMemory"},
            {"id": _class_iri("DecisionAssertion"), "label": "DecisionAssertion", "explicitConfirmationRequired": True},
            {"id": _class_iri("PolicyAssertion"), "label": "PolicyAssertion", "explicitConfirmationRequired": True},
            {"id": _class_iri("PreferenceAssertion"), "label": "PreferenceAssertion", "autoPromotionCriteria": PREFERENCE_AUTO_PROMOTION_CRITERIA},
            {"id": _class_iri("OperationalEvent"), "label": "OperationalEvent", "canonicalPersonalMemory": False},
            {"id": _class_iri("SourceProvenance"), "label": "SourceProvenance"},
            {"id": _class_iri("PromotionCandidate"), "label": "PromotionCandidate"},
        ],
        "properties": [
            {"id": _class_iri("sourceArtifactRef"), "domain": "PromotionCandidate", "range": "RawArtifact"},
            {"id": _class_iri("summaryMemoryRef"), "domain": "PromotionCandidate", "range": "SummaryMemory"},
            {"id": _class_iri("assertionKind"), "domain": "PromotionCandidate", "range": "AssertionKind"},
            {"id": _class_iri("contentHash"), "domain": "RawArtifact", "range": "string"},
            {"id": _class_iri("sensitivity"), "domain": "RawArtifact", "range": "SensitivityClass"},
            {"id": _class_iri("requiresExplicitConfirmation"), "domain": "PromotionCandidate", "range": "boolean"},
            {"id": _class_iri("hasValidationBlocker"), "domain": "PromotionCandidate", "range": "string"},
        ],
    }


def infer_assertion_kind(text: str) -> str:
    lower = text.lower()
    if any(term in lower for term in ["decide", "decided", "decision", "choose", "chosen"]):
        return "DecisionAssertion"
    if any(term in lower for term in ["policy", "must", "always", "never", "require", "required"]):
        return "PolicyAssertion"
    if any(term in lower for term in ["prefer", "preference", "default", "like", "want"]):
        return "PreferenceAssertion"
    return "OperationalEvent"


def _raw_artifact(raw_record: dict[str, Any]) -> dict[str, Any]:
    return raw_record.get("artifact", {})


def _summary_memory(summary_record: dict[str, Any] | None) -> dict[str, Any]:
    return (summary_record or {}).get("summaryMemory", {})


def _source_statement(raw_record: dict[str, Any], summary_record: dict[str, Any] | None) -> str:
    summary = _summary_memory(summary_record)
    if summary.get("summary"):
        return summary["summary"]
    artifact = _raw_artifact(raw_record)
    return artifact.get("contentPreview") or artifact.get("contentHash") or ""


def _source_sensitivity(raw_record: dict[str, Any], summary_record: dict[str, Any] | None) -> str | None:
    values = [
        _raw_artifact(raw_record).get("sensitivity"),
        _summary_memory(summary_record).get("sensitivity"),
    ]
    ranked = [value for value in values if value in SENSITIVITY_RANK]
    if not ranked:
        return None
    return max(ranked, key=lambda value: SENSITIVITY_RANK[value])


def _retention_valid(raw_record: dict[str, Any], summary_record: dict[str, Any] | None) -> bool:
    artifact = _raw_artifact(raw_record)
    summary = _summary_memory(summary_record)
    retention = summary.get("retention") or artifact.get("retention") or {}
    return bool(retention.get("autoPersistAllowed"))


def _boundary_ready(boundary_report: dict[str, Any] | None) -> bool:
    if not boundary_report:
        return False
    return boundary_report.get("status") == "ready-for-hermes-write" and boundary_report.get("writeGate", {}).get("allowedHere") is False


def _sensitive_approved(boundary_report: dict[str, Any] | None, sensitivity: str | None) -> bool:
    if sensitivity != "sensitive":
        return True
    return bool((boundary_report or {}).get("approval", {}).get("sensitiveApproved"))


def _source_state_blockers(raw_record: dict[str, Any], summary_record: dict[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    artifact = _raw_artifact(raw_record)
    summary = _summary_memory(summary_record)
    if artifact.get("deletionState") != "active":
        blockers.append("source artifact is not active")
    if artifact.get("redactionState") == "redacted":
        blockers.append("source artifact is redacted")
    if summary and summary.get("deletionState") != "active":
        blockers.append("summary memory source is not active")
    if summary and summary.get("redactionState") == "redacted":
        blockers.append("summary memory source is redacted")
    return blockers


def _source_policy_blockers(
    raw_record: dict[str, Any],
    summary_record: dict[str, Any] | None,
    *,
    boundary_ready: bool,
    sensitive_approved: bool,
) -> list[str]:
    blockers: list[str] = []
    artifact = _raw_artifact(raw_record)
    summary = _summary_memory(summary_record)
    source_blockers = list(artifact.get("memoryPolicy", {}).get("blockedReasons", []))
    source_blockers.extend(summary.get("promotionPolicy", {}).get("blockedReasons", []))
    for blocker in source_blockers:
        if blocker == "raw Hermes artifact reference not yet live-bound" and boundary_ready:
            continue
        if blocker == "SHACL validation not yet run":
            continue
        if blocker in {"sensitive memory requires explicit approval", "summary text contains sensitive content"} and sensitive_approved:
            continue
        labeled = f"source policy blocker: {blocker}"
        if labeled not in blockers:
            blockers.append(labeled)
    return blockers



def build_ontology_contract(
    raw_record: dict[str, Any],
    summary_record: dict[str, Any] | None = None,
    *,
    assertion_kind: str | None = None,
    repeated_sources: int = 1,
    confidence: float | None = None,
    non_destructive: bool = True,
    access_allowed: bool = True,
    conflict_free: bool = True,
    explicit_confirmation: bool = False,
    hermes_boundary_report: dict[str, Any] | None = None,
    independent_source_refs: list[str] | None = None,
    independent_source_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a candidate-only ontology contract with promotion blockers."""

    statement = _source_statement(raw_record, summary_record)
    kind = assertion_kind or infer_assertion_kind(statement)
    if kind not in ASSERTION_KINDS:
        kind = "OperationalEvent"
    artifact = _raw_artifact(raw_record)
    summary = _summary_memory(summary_record)
    sensitivity = _source_sensitivity(raw_record, summary_record)
    confidence_value = confidence if confidence is not None else summary.get("extraction", {}).get("confidence", 0.75)
    primary_source_refs = [artifact.get("id")] if artifact.get("id") else []
    independent_source_refs = independent_source_refs or []
    independent_source_records = independent_source_records or []
    independent_artifacts = [_raw_artifact(record) for record in independent_source_records]
    validated_independent_refs = [item.get("id") for item in independent_artifacts if item.get("id")]
    source_artifact_refs = list(dict.fromkeys([*primary_source_refs, *validated_independent_refs]))
    summary_refs = [summary.get("id")] if summary.get("id") else []
    boundary = hermes_boundary_report or build_hermes_live_boundary_report(summary_record or raw_record)
    boundary_is_ready = _boundary_ready(boundary)
    source_is_approved = _sensitive_approved(boundary, sensitivity)
    for independent_record in independent_source_records:
        independent_sensitivity = _source_sensitivity(independent_record, None)
        if independent_sensitivity and (
            sensitivity not in SENSITIVITY_RANK
            or SENSITIVITY_RANK[independent_sensitivity] > SENSITIVITY_RANK[sensitivity]
        ):
            sensitivity = independent_sensitivity
    source_is_approved = _sensitive_approved(boundary, sensitivity)

    criteria = {
        "repeated-independent-sources": len(source_artifact_refs) >= 2,
        "non-sensitive": sensitivity != "sensitive",
        "non-destructive": bool(non_destructive),
        "access-allowed": bool(access_allowed),
        "retention-valid": _retention_valid(raw_record, summary_record),
        "conflict-free": bool(conflict_free),
        "high-confidence": float(confidence_value or 0) >= 0.8,
        "hermes-boundary-ready": boundary_is_ready,
    }

    blockers: list[str] = []
    blockers.extend(validate_contract_record(raw_record))
    if summary_record is not None:
        blockers.extend(validate_contract_record(summary_record))
    for independent_record in independent_source_records:
        blockers.extend(validate_contract_record(independent_record))
    if not source_artifact_refs:
        blockers.append("candidate requires sourceArtifactRefs")
    if kind in EXPLICIT_CONFIRMATION_KINDS and not explicit_confirmation:
        blockers.append(f"{kind} requires explicit confirmation")
    if sensitivity == "sensitive" and not source_is_approved:
        blockers.append("sensitive source requires explicit approval")
    if not boundary_is_ready:
        blockers.append("Hermes live write boundary is not ready")
    blockers.extend(_source_state_blockers(raw_record, summary_record))
    blockers.extend(
        _source_policy_blockers(
            raw_record,
            summary_record,
            boundary_ready=boundary_is_ready,
            sensitive_approved=source_is_approved,
        )
    )
    for independent_record in independent_source_records:
        if _source_sensitivity(independent_record, None) == "sensitive" and not source_is_approved:
            blockers.append("sensitive independent source requires explicit approval")
        blockers.extend(_source_state_blockers(independent_record, None))
        blockers.extend(
            _source_policy_blockers(
                independent_record,
                None,
                boundary_ready=boundary_is_ready,
                sensitive_approved=source_is_approved,
            )
        )
    if independent_source_refs:
        blockers.append("independent source refs require raw artifact record provenance")
    if kind == "PreferenceAssertion":
        for criterion, passed in criteria.items():
            if not passed:
                blockers.append(f"PreferenceAssertion auto-promotion requires {criterion}")

    canonical_eligible = not blockers and (
        explicit_confirmation if kind in EXPLICIT_CONFIRMATION_KINDS else kind == "PreferenceAssertion"
    )
    source_records = [
        {
            "id": item.get("id"),
            "contentHash": item.get("contentHash"),
            "recordKind": "raw-artifact-contract",
            "sensitivity": item.get("sensitivity"),
            "deletionState": item.get("deletionState"),
            "redactionState": item.get("redactionState"),
        }
        for item in [artifact, *independent_artifacts]
        if item.get("id")
    ]

    candidate_id = stable_id(
        "abox",
        {
            "kind": kind,
            "statement": statement,
            "sourceArtifactRefs": source_artifact_refs,
            "summaryMemoryRefs": summary_refs,
            "criteria": criteria,
        },
    )

    abox_candidate = {
        "@id": f"urn:just-chill:memory:{candidate_id}",
        "@type": ["PromotionCandidate", kind],
        "assertionKind": kind,
        "statement": statement,
        "sensitivity": sensitivity,
        "sourceArtifactRefs": source_artifact_refs,
        "unvalidatedIndependentSourceRefs": independent_source_refs,
        "summaryMemoryRefs": summary_refs,
        "provenance": {
            "rawContentHash": artifact.get("contentHash"),
            "summaryHash": summary.get("summaryHash"),
            "rawRecordKind": raw_record.get("recordKind"),
            "summaryRecordKind": summary_record.get("recordKind") if summary_record else None,
            "hermesBoundaryStatus": boundary.get("status"),
            "sourceRecords": source_records,
        },
        "promotionPolicy": {
            "candidateOnly": True,
            "canonicalPromotionEligible": canonical_eligible,
            "explicitConfirmationRequired": kind in EXPLICIT_CONFIRMATION_KINDS,
            "explicitConfirmationPresent": explicit_confirmation,
            "repeatedSourceClaim": repeated_sources,
            "preferenceCriteria": criteria,
            "blockedReasons": blockers,
        },
    }

    shacl_validation = {
        "validator": "just-chill-shacl-contract-v1",
        "status": "passed" if not blockers else "blocked",
        "shapes": [
            "SourceProvenanceShape",
            "AssertionKindShape",
            "SensitivityApprovalShape",
            "HermesBoundaryShape",
            "PreferencePromotionShape",
        ],
        "blockingReasons": blockers,
    }

    return {
        "schemaVersion": SCHEMA_VERSION,
        "contract": ONTOLOGY_CONTRACT_NAME,
        "storageAuthority": "Hermes",
        "contractAuthority": "just-chill",
        "liveBinding": {
            "status": "contract-only",
            "owner": "Hermes",
            "unresolved": "RDF/OWL persistence and SHACL engine are not live-bound in this repo slice",
        },
        "tbox": build_tbox(),
        "aboxCandidate": abox_candidate,
        "shaclValidation": shacl_validation,
    }


def validate_ontology_contract(contract: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if contract.get("schemaVersion") != SCHEMA_VERSION:
        issues.append("schemaVersion mismatch")
    if contract.get("contract") != ONTOLOGY_CONTRACT_NAME:
        issues.append("contract name mismatch")
    if contract.get("storageAuthority") != "Hermes":
        issues.append("storage authority must remain Hermes")
    if contract.get("contractAuthority") != "just-chill":
        issues.append("contract authority must remain just-chill")
    if contract.get("liveBinding", {}).get("status") != "contract-only":
        issues.append("ontology live binding must remain contract-only in this slice")
    if not contract.get("tbox", {}).get("classes"):
        issues.append("tbox requires classes")
    if not contract.get("tbox", {}).get("properties"):
        issues.append("tbox requires properties")

    candidate = contract.get("aboxCandidate", {})
    if not candidate.get("@id"):
        issues.append("candidate missing @id")
    if not candidate.get("sourceArtifactRefs"):
        issues.append("candidate requires sourceArtifactRefs")
    if candidate.get("assertionKind") not in ASSERTION_KINDS:
        issues.append("candidate assertionKind is not recognized")
    provenance = candidate.get("provenance", {})
    if not isinstance(provenance, dict) or not provenance:
        issues.append("candidate requires provenance")
    else:
        if not provenance.get("rawContentHash"):
            issues.append("candidate provenance requires rawContentHash")
        if provenance.get("rawRecordKind") != "raw-artifact-contract":
            issues.append("candidate provenance requires raw-artifact-contract")
        if candidate.get("summaryMemoryRefs") and not provenance.get("summaryHash"):
            issues.append("summary-backed candidate provenance requires summaryHash")
        source_records = provenance.get("sourceRecords", [])
        source_refs = candidate.get("sourceArtifactRefs", [])
        if len(source_records) != len(source_refs):
            issues.append("candidate provenance requires one sourceRecord per sourceArtifactRef")
        source_record_ids = [source_record.get("id") for source_record in source_records]
        if len(source_record_ids) != len(set(source_record_ids)):
            issues.append("candidate provenance sourceRecord ids must be unique")
        if set(source_record_ids) != set(source_refs):
            issues.append("candidate provenance sourceRecord ids must exactly match sourceArtifactRefs")
        for source_record in source_records:
            if source_record.get("id") not in source_refs:
                issues.append("candidate provenance sourceRecord id must match sourceArtifactRefs")
            if not source_record.get("contentHash"):
                issues.append("candidate provenance sourceRecord requires contentHash")
            if source_record.get("recordKind") != "raw-artifact-contract":
                issues.append("candidate provenance sourceRecord requires raw-artifact-contract")
            if source_record.get("deletionState") != "active":
                issues.append("candidate provenance sourceRecord must be active")
            if source_record.get("redactionState") != "not_redacted":
                issues.append("candidate provenance sourceRecord must be not_redacted")
    policy = candidate.get("promotionPolicy", {})
    blockers = policy.get("blockedReasons", [])
    if policy.get("candidateOnly") is not True:
        issues.append("candidate policy must remain candidateOnly")
    if candidate.get("unvalidatedIndependentSourceRefs") and policy.get("canonicalPromotionEligible"):
        issues.append("unvalidated independent source refs cannot support canonical promotion")
    if policy.get("canonicalPromotionEligible") and blockers:
        issues.append("eligible candidate cannot have blocked reasons")
    if policy.get("canonicalPromotionEligible") and contract.get("shaclValidation", {}).get("status") != "passed":
        issues.append("eligible candidate requires passed SHACL validation")
    kind = candidate.get("assertionKind")
    if kind in EXPLICIT_CONFIRMATION_KINDS:
        if policy.get("explicitConfirmationRequired") is not True:
            issues.append(f"{kind} must require explicit confirmation")
        if policy.get("explicitConfirmationPresent") is not True:
            expected = f"{kind} requires explicit confirmation"
            if policy.get("canonicalPromotionEligible"):
                issues.append(f"{kind} cannot be eligible without explicit confirmation")
            if expected not in blockers:
                issues.append(f"{kind} missing explicit confirmation blocker")
    if kind == "PreferenceAssertion":
        criteria = policy.get("preferenceCriteria", {})
        if criteria.get("repeated-independent-sources") and len(set(candidate.get("sourceArtifactRefs", []))) < 2:
            issues.append("PreferenceAssertion repeated-independent-sources requires at least two sourceArtifactRefs")
        for criterion in PREFERENCE_AUTO_PROMOTION_CRITERIA:
            passed = criteria.get(criterion)
            expected = f"PreferenceAssertion auto-promotion requires {criterion}"
            if passed is not True and policy.get("canonicalPromotionEligible"):
                issues.append(f"PreferenceAssertion cannot be eligible without {criterion}")
            if passed is not True and expected not in blockers:
                issues.append(f"PreferenceAssertion missing blocker for {criterion}")
    if contract.get("shaclValidation", {}).get("status") == "passed" and contract.get("shaclValidation", {}).get("blockingReasons"):
        issues.append("passed SHACL validation cannot include blocking reasons")
    return issues


def _escape_turtle_text(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r").replace('"', '\\"')


def _literal(value: Any) -> str:
    if isinstance(value, bool):
        return f'"{str(value).lower()}"^^<{XSD_NS}boolean>'
    if isinstance(value, int | float) and not isinstance(value, bool):
        return f'"{value}"^^<{XSD_NS}decimal>'
    return f'"{_escape_turtle_text(value)}"'


def _urn(kind: str, value: Any) -> str:
    safe = "".join(char if char.isalnum() or char in "-_:.#" else "_" for char in str(value))
    return f"urn:just-chill:{kind}:{safe}"


def _triple(subject: str, predicate: str, obj: Any, *, object_type: str = "literal") -> dict[str, Any]:
    return {
        "subject": subject,
        "predicate": predicate,
        "object": obj,
        "objectType": object_type,
    }


def _format_turtle(triples: list[dict[str, Any]]) -> str:
    lines = [
        f"@prefix jc: <{BASE_IRI}> .",
        f"@prefix owl: <{OWL_NS}> .",
        f"@prefix rdf: <{RDF_NS}> .",
        f"@prefix rdfs: <{RDFS_NS}> .",
        f"@prefix sh: <{SHACL_NS}> .",
        f"@prefix xsd: <{XSD_NS}> .",
        "",
    ]
    for triple in triples:
        subject = f"<{triple['subject']}>"
        predicate = f"<{triple['predicate']}>"
        if triple.get("objectType") == "iri":
            obj = f"<{triple['object']}>"
        else:
            obj = _literal(triple.get("object"))
        lines.append(f"{subject} {predicate} {obj} .")
    return "\n".join(lines) + "\n"


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _find_denied_persistence_keys(data: Any, path: str = "$") -> list[str]:
    issues: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            child_path = f"{path}.{key}"
            if key in DENIED_PERSISTENCE_KEYS:
                issues.append(f"export must not contain live persistence key {child_path}")
            issues.extend(_find_denied_persistence_keys(value, child_path))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            issues.extend(_find_denied_persistence_keys(value, f"{path}[{index}]"))
    return issues
def _command_available(name: str, which: Any | None = None) -> bool:
    resolver = which or shutil.which
    return bool(resolver(name))


def _module_available(name: str, module_available: Any | None = None) -> bool:
    if module_available is not None:
        return bool(module_available(name))
    return importlib.util.find_spec(name) is not None


def _rdf_api_has_terms(api: Any, terms: tuple[str, ...]) -> bool:
    if not isinstance(api, str):
        return False
    normalized = api.lower()
    return (
        normalized.startswith(("hermes.", "hermes:", "hermes_", "mcp:hermes.", "mcp:hermes_"))
        and any(term in normalized for term in RDF_GRAPH_TERMS)
        and any(term in normalized for term in terms)
    )


def _first_rdf_api(candidates: list[str], terms: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        if _rdf_api_has_terms(candidate, terms):
            return candidate
    return None


def _rdf_api_candidates_from_surfaces(surfaces: dict[str, Any] | None) -> list[str]:
    hermes = (surfaces or {}).get("hermes", {}) if isinstance(surfaces, dict) else {}
    values = [
        hermes.get("rdfGraphApi"),
        hermes.get("rdfGraphReadApi"),
        hermes.get("rdfGraphDeleteApi"),
        hermes.get("ontologyGraphApi"),
        hermes.get("ontologyGraphReadApi"),
        hermes.get("ontologyGraphDeleteApi"),
        hermes.get("aboxApi"),
        hermes.get("aboxReadApi"),
        hermes.get("aboxDeleteApi"),
    ]
    return sorted({value for value in values if isinstance(value, str) and value and value != "unmapped"})
def _local_memory_mcp_candidates() -> list[str]:
    try:
        from just_chill_hermes_memory_mcp import tool_names
    except Exception:
        return []
    return [name for name in tool_names() if isinstance(name, str)]



def build_rdf_shacl_live_boundary_report(
    *,
    surfaces: dict[str, Any] | None = None,
    which: Any | None = None,
    module_available: Any | None = None,
) -> dict[str, Any]:
    """Discover local RDF/OWL parser, SHACL engine, and Hermes graph-store readiness.

    The report is read-only. It never runs a parser/engine and never writes Hermes.
    """

    command_status = {
        name: {"available": _command_available(name, which)}
        for name in [*RDF_PARSER_COMMANDS, *SHACL_ENGINE_COMMANDS, "hermes"]
    }
    module_status = {
        name: {"available": _module_available(name, module_available)}
        for name in RDF_MODULES
    }
    candidates = sorted(set([*_rdf_api_candidates_from_surfaces(surfaces), *_local_memory_mcp_candidates()]))
    create_api = _first_rdf_api(candidates, RDF_WRITE_TERMS)
    read_api = _first_rdf_api(candidates, RDF_READ_TERMS)
    delete_api = _first_rdf_api(candidates, RDF_DELETE_TERMS)
    rdf_parser_available = module_status["rdflib"]["available"] or any(
        command_status[name]["available"] for name in RDF_PARSER_COMMANDS
    )
    shacl_engine_available = module_status["pyshacl"]["available"] or any(
        command_status[name]["available"] for name in SHACL_ENGINE_COMMANDS
    )
    graph_store_mapped = bool(create_api and read_api and delete_api)

    blocked_reasons: list[str] = []
    if not rdf_parser_available:
        blocked_reasons.append("RDF/OWL Turtle parser is not mapped")
    if not shacl_engine_available:
        blocked_reasons.append("live SHACL engine is not mapped")
    if not create_api:
        blocked_reasons.append("Hermes RDF graph create/write API is not mapped")
    if not read_api:
        blocked_reasons.append("Hermes RDF graph read API is not mapped")
    if not delete_api:
        blocked_reasons.append("Hermes RDF graph delete/redact API is not mapped")

    ready = rdf_parser_available and shacl_engine_available and graph_store_mapped
    partial = rdf_parser_available or shacl_engine_available or bool(candidates)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "mapper": RDF_SHACL_LIVE_BOUNDARY_NAME,
        "storageAuthority": "Hermes",
        "contractAuthority": "just-chill",
        "status": "rdf-shacl-live-ready" if ready else ("rdf-shacl-partial" if partial else "rdf-shacl-unmapped"),
        "commands": command_status,
        "modules": module_status,
        "candidateApis": candidates,
        "rdfParser": {
            "available": rdf_parser_available,
            "mode": "host-owned-validation-only",
        },
        "shaclEngine": {
            "available": shacl_engine_available,
            "executionAllowedHere": False,
            "mode": "host-owned-validation-only",
        },
        "rdfGraphApis": {
            "create": {"api": create_api or "unmapped", "mapped": bool(create_api)},
            "read": {"api": read_api or "unmapped", "mapped": bool(read_api)},
            "delete": {"api": delete_api or "unmapped", "mapped": bool(delete_api)},
        },
        "writeGate": {
            "enabled": ready,
            "allowedHere": False,
            "blockedReasons": blocked_reasons,
        },
        "requiredFutureBinding": [
            "live SHACL engine such as pyshacl",
            "Hermes RDF graph create/write API or MCP tool",
            "Hermes RDF graph read API or MCP tool",
            "Hermes RDF graph delete/redact API or MCP tool",
            "host-owned persistence runner that supplies SHACL and Hermes read-back evidence",
        ],
    }


def validate_rdf_shacl_live_boundary_report(report: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if report.get("schemaVersion") != SCHEMA_VERSION:
        issues.append("rdf/shacl boundary schemaVersion mismatch")
    if report.get("mapper") != RDF_SHACL_LIVE_BOUNDARY_NAME:
        issues.append("rdf/shacl boundary mapper mismatch")
    if report.get("storageAuthority") != "Hermes":
        issues.append("rdf/shacl boundary storage authority must remain Hermes")
    if report.get("contractAuthority") != "just-chill":
        issues.append("rdf/shacl boundary contract authority must remain just-chill")
    gate = report.get("writeGate", {})
    if gate.get("allowedHere") is not False:
        issues.append("rdf/shacl boundary must not allow local persistence")
    engine = report.get("shaclEngine", {})
    if engine.get("executionAllowedHere") is not False:
        issues.append("rdf/shacl boundary must not allow local SHACL execution")
    apis = report.get("rdfGraphApis", {})
    mapped = all(apis.get(name, {}).get("mapped") for name in ["create", "read", "delete"])
    if gate.get("enabled") and not mapped:
        issues.append("rdf/shacl write gate cannot enable without create/read/delete APIs")
    if report.get("status") == "rdf-shacl-live-ready" and gate.get("blockedReasons"):
        issues.append("ready rdf/shacl boundary cannot have blocked reasons")
    return issues


def _rdf_export_sensitive(export: dict[str, Any]) -> bool:
    for triple in export.get("export", {}).get("triples", []):
        if str(triple.get("predicate", "")).endswith("sensitivity") and triple.get("object") == "sensitive":
            return True
    return False


def build_rdf_shacl_persistence_plan(
    rdf_export: dict[str, Any],
    shacl_export: dict[str, Any],
    live_report: dict[str, Any],
    *,
    approval_token: str | None = None,
) -> dict[str, Any]:
    """Plan host-owned RDF/OWL + SHACL persistence without running the engine or writing Hermes."""

    blocked_reasons: list[str] = []
    rdf_body = rdf_export.get("export", {})
    shacl_manifest = shacl_export.get("shapeManifest", {})
    shacl_report = shacl_export.get("validationReport", {})
    blocked_reasons.extend(validate_rdf_owl_export(rdf_export))
    blocked_reasons.extend(validate_shacl_shape_export(shacl_export))
    blocked_reasons.extend(validate_rdf_shacl_live_boundary_report(live_report))
    if live_report.get("writeGate", {}).get("enabled") is not True:
        blocked_reasons.extend(live_report.get("writeGate", {}).get("blockedReasons", []))
    if rdf_body.get("sourceContractHash") != shacl_manifest.get("sourceContractHash"):
        blocked_reasons.append("RDF export and SHACL manifest source contract hashes must match")
    if rdf_body.get("sourceCandidateId") != shacl_report.get("focusNode"):
        blocked_reasons.append("RDF export candidate and SHACL validation focus node must match")
    if shacl_export.get("validationReport", {}).get("conforms") is not True:
        blocked_reasons.append("SHACL validation report must conform before RDF persistence")
    if _rdf_export_sensitive(rdf_export) and not approval_token:
        blocked_reasons.append("sensitive RDF/OWL persistence requires explicit approval")

    apis = live_report.get("rdfGraphApis", {})
    return {
        "schemaVersion": SCHEMA_VERSION,
        "planner": RDF_SHACL_PERSISTENCE_PLAN_NAME,
        "status": "ready-for-host-rdf-shacl-persistence" if not blocked_reasons else "host-rdf-shacl-persistence-blocked",
        "storageAuthority": "Hermes",
        "contractAuthority": "just-chill",
        "approval": {
            "sensitiveRdfDetected": _rdf_export_sensitive(rdf_export),
            "approvalTokenPresent": bool(approval_token),
        },
        "wouldCall": {
            "create": apis.get("create", {}).get("api", "unmapped"),
            "read": apis.get("read", {}).get("api", "unmapped"),
            "delete": apis.get("delete", {}).get("api", "unmapped"),
            "arguments": {
                "sourceCandidateId": rdf_body.get("sourceCandidateId"),
                "sourceContractHash": rdf_body.get("sourceContractHash"),
                "turtleSha256": rdf_body.get("turtleSha256"),
                "shapesTurtleSha256": shacl_manifest.get("shapesTurtleSha256"),
            },
        },
        "executionBoundary": {
            "allowedHere": False,
            "justChillCallsHermes": False,
            "justChillRunsShaclEngine": False,
            "hostMustRunShaclEngine": True,
            "hostMustExecuteHermesApi": True,
            "hermesOwnsCanonicalStorage": True,
        },
        "persistenceGate": {
            "enabled": not blocked_reasons,
            "blockedReasons": sorted(set(blocked_reasons)),
        },
        "evidenceRequirements": [
            "host/operator live SHACL engine result must be supplied before canonical graph persistence is recorded",
            "Hermes RDF graph create result must be supplied before persistence is recorded",
            "Hermes read-back evidence must match Turtle and SHACL shape hashes",
            "Hermes delete/redact API must be mapped for lifecycle control before persistence is enabled",
            "sensitive graph persistence requires explicit approval",
        ],
    }


def validate_rdf_shacl_persistence_plan(plan: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if plan.get("schemaVersion") != SCHEMA_VERSION:
        issues.append("rdf/shacl persistence plan schemaVersion mismatch")
    if plan.get("planner") != RDF_SHACL_PERSISTENCE_PLAN_NAME:
        issues.append("rdf/shacl persistence planner mismatch")
    if plan.get("storageAuthority") != "Hermes":
        issues.append("rdf/shacl persistence storage authority must remain Hermes")
    if plan.get("contractAuthority") != "just-chill":
        issues.append("rdf/shacl persistence contract authority must remain just-chill")
    boundary = plan.get("executionBoundary", {})
    if boundary.get("allowedHere") is not False:
        issues.append("rdf/shacl persistence plan must not allow local execution")
    if boundary.get("justChillCallsHermes") is not False:
        issues.append("just-chill must not call Hermes RDF graph APIs directly")
    if boundary.get("justChillRunsShaclEngine") is not False:
        issues.append("just-chill must not run the live SHACL engine directly")
    if boundary.get("hermesOwnsCanonicalStorage") is not True:
        issues.append("Hermes must own canonical RDF graph storage")
    gate = plan.get("persistenceGate", {})
    status = plan.get("status")
    if status == "ready-for-host-rdf-shacl-persistence" and gate.get("blockedReasons"):
        issues.append("ready rdf/shacl persistence plan cannot have blocked reasons")
    if status == "ready-for-host-rdf-shacl-persistence" and gate.get("enabled") is not True:
        issues.append("ready rdf/shacl persistence plan requires enabled gate")
    if status == "host-rdf-shacl-persistence-blocked" and gate.get("enabled") is True:
        issues.append("blocked rdf/shacl persistence plan cannot have enabled gate")
    calls = plan.get("wouldCall", {})
    arguments = calls.get("arguments", {})
    for key in ["create", "read", "delete"]:
        if not calls.get(key):
            issues.append(f"rdf/shacl persistence plan missing {key} API placeholder")
    for key in ["sourceCandidateId", "sourceContractHash", "turtleSha256", "shapesTurtleSha256"]:
        if not arguments.get(key):
            issues.append(f"rdf/shacl persistence plan missing argument {key}")
    if not plan.get("evidenceRequirements"):
        issues.append("rdf/shacl persistence plan requires evidence requirements")
    return issues



def build_rdf_owl_export(contract: dict[str, Any]) -> dict[str, Any]:
    """Serialize an ontology contract into deterministic RDF/OWL-like Turtle.

    The export is a local contract artifact only. It deliberately records that no
    RDF store, Hermes write, or canonical ABox persistence has occurred.
    """

    candidate = contract.get("aboxCandidate", {})
    tbox = contract.get("tbox", {})
    candidate_iri = candidate.get("@id") or _urn("memory", stable_id("missing_candidate", contract))
    triples: list[dict[str, Any]] = []

    ontology_iri = tbox.get("iri") or f"{BASE_IRI}JustChillMemoryOntology"
    triples.append(_triple(ontology_iri, f"{RDF_NS}type", f"{OWL_NS}Ontology", object_type="iri"))
    triples.append(_triple(ontology_iri, f"{BASE_IRI}storageAuthority", contract.get("storageAuthority")))
    triples.append(_triple(ontology_iri, f"{BASE_IRI}contractAuthority", contract.get("contractAuthority")))
    triples.append(_triple(ontology_iri, f"{BASE_IRI}liveBindingStatus", contract.get("liveBinding", {}).get("status")))

    for klass in tbox.get("classes", []):
        class_iri = klass.get("id")
        if not class_iri:
            continue
        triples.append(_triple(class_iri, f"{RDF_NS}type", f"{OWL_NS}Class", object_type="iri"))
        triples.append(_triple(class_iri, f"{RDFS_NS}label", klass.get("label")))
        if "explicitConfirmationRequired" in klass:
            triples.append(_triple(class_iri, f"{BASE_IRI}explicitConfirmationRequired", bool(klass["explicitConfirmationRequired"])))
        for criterion in klass.get("autoPromotionCriteria", []):
            triples.append(_triple(class_iri, f"{BASE_IRI}autoPromotionCriterion", criterion))
        if "canonicalPersonalMemory" in klass:
            triples.append(_triple(class_iri, f"{BASE_IRI}canonicalPersonalMemory", bool(klass["canonicalPersonalMemory"])))

    for prop in tbox.get("properties", []):
        prop_iri = prop.get("id")
        if not prop_iri:
            continue
        triples.append(_triple(prop_iri, f"{RDF_NS}type", f"{RDF_NS}Property", object_type="iri"))
        if prop.get("domain"):
            triples.append(_triple(prop_iri, f"{RDFS_NS}domain", f"{BASE_IRI}{prop['domain']}", object_type="iri"))
        if prop.get("range"):
            range_value = prop["range"]
            range_iri = f"{BASE_IRI}{range_value}" if str(range_value)[:1].isupper() else f"{XSD_NS}string"
            triples.append(_triple(prop_iri, f"{RDFS_NS}range", range_iri, object_type="iri"))

    triples.append(_triple(candidate_iri, f"{RDF_NS}type", f"{BASE_IRI}PromotionCandidate", object_type="iri"))
    for candidate_type in candidate.get("@type", []):
        triples.append(_triple(candidate_iri, f"{RDF_NS}type", f"{BASE_IRI}{candidate_type}", object_type="iri"))
    triples.append(_triple(candidate_iri, f"{BASE_IRI}assertionKind", candidate.get("assertionKind")))
    triples.append(_triple(candidate_iri, f"{BASE_IRI}statement", candidate.get("statement")))
    triples.append(_triple(candidate_iri, f"{BASE_IRI}sensitivity", candidate.get("sensitivity")))
    triples.append(_triple(candidate_iri, f"{BASE_IRI}candidateOnly", candidate.get("promotionPolicy", {}).get("candidateOnly")))
    triples.append(_triple(candidate_iri, f"{BASE_IRI}canonicalPromotionEligible", candidate.get("promotionPolicy", {}).get("canonicalPromotionEligible")))
    triples.append(_triple(candidate_iri, f"{BASE_IRI}explicitConfirmationRequired", candidate.get("promotionPolicy", {}).get("explicitConfirmationRequired")))
    triples.append(_triple(candidate_iri, f"{BASE_IRI}explicitConfirmationPresent", candidate.get("promotionPolicy", {}).get("explicitConfirmationPresent")))

    for source_ref in candidate.get("sourceArtifactRefs", []):
        source_iri = _urn("artifact", source_ref)
        triples.append(_triple(candidate_iri, f"{BASE_IRI}sourceArtifactRef", source_iri, object_type="iri"))
    for summary_ref in candidate.get("summaryMemoryRefs", []):
        summary_iri = _urn("summary", summary_ref)
        triples.append(_triple(candidate_iri, f"{BASE_IRI}summaryMemoryRef", summary_iri, object_type="iri"))
    for blocker in candidate.get("promotionPolicy", {}).get("blockedReasons", []):
        triples.append(_triple(candidate_iri, f"{BASE_IRI}hasValidationBlocker", blocker))

    provenance = candidate.get("provenance", {})
    triples.append(_triple(candidate_iri, f"{BASE_IRI}rawContentHash", provenance.get("rawContentHash")))
    triples.append(_triple(candidate_iri, f"{BASE_IRI}summaryHash", provenance.get("summaryHash")))
    triples.append(_triple(candidate_iri, f"{BASE_IRI}hermesBoundaryStatus", provenance.get("hermesBoundaryStatus")))
    for source_record in provenance.get("sourceRecords", []):
        source_iri = _urn("artifact", source_record.get("id"))
        triples.append(_triple(source_iri, f"{RDF_NS}type", f"{BASE_IRI}RawArtifact", object_type="iri"))
        triples.append(_triple(source_iri, f"{BASE_IRI}contentHash", source_record.get("contentHash")))
        triples.append(_triple(source_iri, f"{BASE_IRI}sensitivity", source_record.get("sensitivity")))
        triples.append(_triple(source_iri, f"{BASE_IRI}deletionState", source_record.get("deletionState")))
        triples.append(_triple(source_iri, f"{BASE_IRI}redactionState", source_record.get("redactionState")))

    turtle = _format_turtle(triples)
    source_hash = _sha256_text(_canonical_json(contract))
    return {
        "schemaVersion": SCHEMA_VERSION,
        "contract": RDF_EXPORT_CONTRACT_NAME,
        "storageAuthority": "Hermes",
        "contractAuthority": "just-chill",
        "liveBinding": {
            "status": "contract-only",
            "owner": "Hermes",
            "storageWriteAllowedHere": False,
            "unresolved": "RDF graph persistence is not live-bound in this repo slice",
        },
        "export": {
            "format": "text/turtle; profile=just-chill-contract-v1",
            "baseIri": BASE_IRI,
            "sourceOntologyContract": contract.get("contract"),
            "sourceContractHash": source_hash,
            "sourceCandidateId": candidate_iri,
            "sourceValidationIssues": validate_ontology_contract(contract),
            "tripleCount": len(triples),
            "turtleSha256": _sha256_text(turtle),
            "turtle": turtle,
            "triples": triples,
        },
    }


def validate_rdf_owl_export(export: dict[str, Any], source_contract: dict[str, Any] | None = None) -> list[str]:
    issues: list[str] = []
    if export.get("schemaVersion") != SCHEMA_VERSION:
        issues.append("rdf export schemaVersion mismatch")
    if export.get("contract") != RDF_EXPORT_CONTRACT_NAME:
        issues.append("rdf export contract name mismatch")
    if export.get("storageAuthority") != "Hermes":
        issues.append("rdf export storage authority must remain Hermes")
    if export.get("contractAuthority") != "just-chill":
        issues.append("rdf export contract authority must remain just-chill")
    live = export.get("liveBinding", {})
    if live.get("status") != "contract-only":
        issues.append("rdf export live binding must remain contract-only")
    if live.get("storageWriteAllowedHere") is not False:
        issues.append("rdf export must not allow storage writes")
    body = export.get("export", {})
    turtle = body.get("turtle")
    triples = body.get("triples")
    if not isinstance(turtle, str) or not turtle.strip():
        issues.append("rdf export requires turtle text")
    if not isinstance(triples, list) or not triples:
        issues.append("rdf export requires triples")
    else:
        if body.get("tripleCount") != len(triples):
            issues.append("rdf export tripleCount mismatch")
        for triple in triples:
            if triple.get("objectType") not in {"iri", "literal"}:
                issues.append("rdf export triple objectType must be iri or literal")
        if isinstance(turtle, str):
            try:
                formatted = _format_turtle(triples)
            except Exception as exc:  # defensive: malformed exported triples must fail closed
                issues.append(f"rdf export triples cannot be formatted: {exc}")
            else:
                if turtle != formatted:
                    issues.append("rdf export turtle must match formatted triples")
    if isinstance(turtle, str) and body.get("turtleSha256") != _sha256_text(turtle):
        issues.append("rdf export turtleSha256 mismatch")
    issues.extend(_find_denied_persistence_keys(export))
    if isinstance(turtle, str):
        for denied in DENIED_PERSISTENCE_KEYS:
            if denied in turtle:
                issues.append(f"rdf export turtle must not contain live persistence token {denied}")
    if source_contract is not None:
        source_hash = _sha256_text(_canonical_json(source_contract))
        if body.get("sourceContractHash") != source_hash:
            issues.append("rdf export sourceContractHash mismatch")
        candidate = source_contract.get("aboxCandidate", {})
        candidate_id = candidate.get("@id")
        if candidate_id and isinstance(turtle, str) and candidate_id not in turtle:
            issues.append("rdf export turtle missing source candidate id")
        for source_ref in candidate.get("sourceArtifactRefs", []):
            if isinstance(turtle, str) and _urn("artifact", source_ref) not in turtle:
                issues.append("rdf export turtle missing source artifact ref")
    return issues


def _shape_definitions() -> list[dict[str, Any]]:
    return [
        {
            "id": "SourceProvenanceShape",
            "targetClass": "PromotionCandidate",
            "constraints": [
                "sourceArtifactRefs minCount 1",
                "provenance.rawContentHash minCount 1",
                "provenance.sourceRecords exact sourceArtifactRefs",
                "source deletion/redaction state active/not_redacted",
            ],
        },
        {
            "id": "AssertionKindShape",
            "targetClass": "PromotionCandidate",
            "constraints": [
                "assertionKind in DecisionAssertion PolicyAssertion PreferenceAssertion OperationalEvent",
                "DecisionAssertion explicitConfirmationPresent true",
                "PolicyAssertion explicitConfirmationPresent true",
            ],
        },
        {
            "id": "SensitivityApprovalShape",
            "targetClass": "PromotionCandidate",
            "constraints": [
                "sensitive sources require explicit approval",
                "masked summaries cannot downgrade sensitive raw provenance",
            ],
        },
        {
            "id": "HermesBoundaryShape",
            "targetClass": "PromotionCandidate",
            "constraints": [
                "Hermes write boundary ready before canonical promotion",
                "contract-only exports do not write storage",
            ],
        },
        {
            "id": "PreferencePromotionShape",
            "targetClass": "PromotionCandidate",
            "constraints": [
                "PreferenceAssertion requires repeated-independent-sources",
                "PreferenceAssertion requires non-sensitive non-destructive access-allowed retention-valid conflict-free high-confidence hermes-boundary-ready",
            ],
        },
    ]


def _shape_for_blocker(reason: str) -> str:
    lowered = reason.lower()
    if "preferenceassertion" in lowered or "repeated-independent" in lowered:
        return "PreferencePromotionShape"
    if "decisionassertion" in lowered or "policyassertion" in lowered or "assertionkind" in lowered:
        return "AssertionKindShape"
    if "sensitive" in lowered or "approval" in lowered:
        return "SensitivityApprovalShape"
    if "hermes" in lowered or "boundary" in lowered:
        return "HermesBoundaryShape"
    return "SourceProvenanceShape"


def build_shacl_shape_export(contract: dict[str, Any]) -> dict[str, Any]:
    """Build deterministic SHACL shape and validation-report contracts."""

    candidate = contract.get("aboxCandidate", {})
    candidate_id = candidate.get("@id") or _urn("memory", stable_id("missing_candidate", contract))
    blockers = list(contract.get("shaclValidation", {}).get("blockingReasons", []))
    shape_defs = _shape_definitions()
    triples: list[dict[str, Any]] = []
    for shape in shape_defs:
        shape_iri = _urn("shacl-shape", shape["id"])
        triples.append(_triple(shape_iri, f"{RDF_NS}type", f"{SHACL_NS}NodeShape", object_type="iri"))
        triples.append(_triple(shape_iri, f"{SHACL_NS}targetClass", f"{BASE_IRI}{shape['targetClass']}", object_type="iri"))
        triples.append(_triple(shape_iri, f"{RDFS_NS}label", shape["id"]))
        for constraint in shape["constraints"]:
            triples.append(_triple(shape_iri, f"{SHACL_NS}message", constraint))

    shapes_turtle = _format_turtle(triples)
    validation_results = [
        {
            "focusNode": candidate_id,
            "sourceShape": _shape_for_blocker(reason),
            "severity": "Violation",
            "message": reason,
        }
        for reason in blockers
    ]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "contract": SHACL_EXPORT_CONTRACT_NAME,
        "storageAuthority": "Hermes",
        "contractAuthority": "just-chill",
        "liveBinding": {
            "status": "contract-only",
            "owner": "Hermes",
            "engine": "deterministic-contract-validator",
            "engineExecutionAllowedHere": False,
            "unresolved": "A real SHACL engine is not live-bound in this repo slice",
        },
        "shapeManifest": {
            "format": "text/turtle; profile=just-chill-shacl-contract-v1",
            "sourceOntologyContract": contract.get("contract"),
            "sourceContractHash": _sha256_text(_canonical_json(contract)),
            "shapeCount": len(shape_defs),
            "shapes": [shape["id"] for shape in shape_defs],
            "shapesTurtleSha256": _sha256_text(shapes_turtle),
            "shapesTurtle": shapes_turtle,
        },
        "validationReport": {
            "conforms": not blockers,
            "status": "passed" if not blockers else "blocked",
            "focusNode": candidate_id,
            "resultCount": len(validation_results),
            "results": validation_results,
        },
    }


def validate_shacl_shape_export(export: dict[str, Any], source_contract: dict[str, Any] | None = None) -> list[str]:
    issues: list[str] = []
    if export.get("schemaVersion") != SCHEMA_VERSION:
        issues.append("shacl export schemaVersion mismatch")
    if export.get("contract") != SHACL_EXPORT_CONTRACT_NAME:
        issues.append("shacl export contract name mismatch")
    if export.get("storageAuthority") != "Hermes":
        issues.append("shacl export storage authority must remain Hermes")
    if export.get("contractAuthority") != "just-chill":
        issues.append("shacl export contract authority must remain just-chill")
    live = export.get("liveBinding", {})
    if live.get("status") != "contract-only":
        issues.append("shacl export live binding must remain contract-only")
    if live.get("engineExecutionAllowedHere") is not False:
        issues.append("shacl export must not claim live engine execution")
    manifest = export.get("shapeManifest", {})
    shapes = manifest.get("shapes", [])
    expected_shapes = [shape["id"] for shape in _shape_definitions()]
    if shapes != expected_shapes:
        issues.append("shacl export shape list mismatch")
    if manifest.get("shapeCount") != len(expected_shapes):
        issues.append("shacl export shapeCount mismatch")
    shapes_turtle = manifest.get("shapesTurtle")
    if not isinstance(shapes_turtle, str) or not shapes_turtle.strip():
        issues.append("shacl export requires shapesTurtle")
    elif manifest.get("shapesTurtleSha256") != _sha256_text(shapes_turtle):
        issues.append("shacl export shapesTurtleSha256 mismatch")
    report = export.get("validationReport", {})
    results = report.get("results", [])
    if report.get("resultCount") != len(results):
        issues.append("shacl export resultCount mismatch")
    if report.get("conforms") is True and results:
        issues.append("conforming SHACL export cannot include violation results")
    if report.get("conforms") is False and not results:
        issues.append("non-conforming SHACL export requires violation results")
    for result in results:
        if result.get("sourceShape") not in expected_shapes:
            issues.append("shacl export result sourceShape mismatch")
        if result.get("severity") != "Violation":
            issues.append("shacl export result severity must be Violation")
        if not result.get("message"):
            issues.append("shacl export result requires message")
    issues.extend(_find_denied_persistence_keys(export))
    if source_contract is not None:
        source_hash = _sha256_text(_canonical_json(source_contract))
        if manifest.get("sourceContractHash") != source_hash:
            issues.append("shacl export sourceContractHash mismatch")
        source_blockers = source_contract.get("shaclValidation", {}).get("blockingReasons", [])
        if bool(source_blockers) == bool(report.get("conforms")):
            issues.append("shacl export conformance does not match source blockers")
        candidate_id = source_contract.get("aboxCandidate", {}).get("@id")
        if candidate_id and report.get("focusNode") != candidate_id:
            issues.append("shacl export focusNode mismatch")
    return issues

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build deterministic just-chill ontology contracts.")
    parser.add_argument("request", nargs="*", help="User request text.")
    parser.add_argument("--summary", help="Optional summary memory text to derive an ABox candidate from.")
    parser.add_argument("--assertion-kind", choices=sorted(ASSERTION_KINDS), help="Force an assertion kind for deterministic checks.")
    parser.add_argument("--explicit-confirmation", action="store_true", help="Mark explicit confirmation as present for Decision/Policy assertions.")
    parser.add_argument("--export-rdf", action="store_true", help="Include deterministic RDF/OWL Turtle export contract.")
    parser.add_argument("--export-shacl", action="store_true", help="Include deterministic SHACL shapes and validation report contract.")
    parser.add_argument("--live-boundary", action="store_true", help="Include read-only RDF/SHACL live-boundary discovery.")
    parser.add_argument("--plan-persistence", action="store_true", help="Include a host-owned RDF/SHACL persistence plan without executing it.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    packet = classify_request(" ".join(args.request))
    raw = build_raw_artifact_record(packet)
    summary = build_summary_memory_record(raw, args.summary) if args.summary is not None else None
    contract = build_ontology_contract(
        raw,
        summary,
        assertion_kind=args.assertion_kind,
        explicit_confirmation=args.explicit_confirmation,
    )
    output = {
        "rawArtifact": raw,
        "summaryMemory": summary,
        "ontologyContract": contract,
        "validationIssues": validate_ontology_contract(contract),
    }
    rdf_export = None
    shacl_export = None
    if args.export_rdf or args.plan_persistence:
        rdf_export = build_rdf_owl_export(contract)
        output["rdfOwlExport"] = rdf_export
        output["validationIssues"].extend(validate_rdf_owl_export(rdf_export, contract))
    if args.export_shacl or args.plan_persistence:
        shacl_export = build_shacl_shape_export(contract)
        output["shaclShapeExport"] = shacl_export
        output["validationIssues"].extend(validate_shacl_shape_export(shacl_export, contract))
    if args.live_boundary or args.plan_persistence:
        live_report = build_rdf_shacl_live_boundary_report()
        output["rdfShaclLiveBoundary"] = live_report
        output["validationIssues"].extend(validate_rdf_shacl_live_boundary_report(live_report))
    if args.plan_persistence and rdf_export is not None and shacl_export is not None:
        persistence_plan = build_rdf_shacl_persistence_plan(rdf_export, shacl_export, output["rdfShaclLiveBoundary"])
        output["rdfShaclPersistencePlan"] = persistence_plan
        output["validationIssues"].extend(validate_rdf_shacl_persistence_plan(persistence_plan))
    print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if not output["validationIssues"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
