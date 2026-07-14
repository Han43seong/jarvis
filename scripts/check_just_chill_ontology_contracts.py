#!/usr/bin/env python3
"""Acceptance checks for just-chill ontology contract skeletons."""
from __future__ import annotations
import copy
import hashlib

from just_chill_hermes_adapter import build_hermes_live_boundary_report
from just_chill_memory_contracts import build_raw_artifact_record, build_summary_memory_record
from just_chill_ontology_contracts import (
    build_ontology_contract,
    build_rdf_owl_export,
    build_shacl_shape_export,
    build_rdf_shacl_live_boundary_report,
    build_rdf_shacl_persistence_plan,
    validate_ontology_contract,
    validate_rdf_owl_export,
    validate_shacl_shape_export,
    validate_rdf_shacl_live_boundary_report,
    validate_rdf_shacl_persistence_plan,
)
from just_chill_router import classify_request


def require(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle, haystack) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


def require_truthy(name: str, value) -> None:
    if not value:
        raise AssertionError(f"{name}: expected truthy value, got {value!r}")


def fake_write_ready_surfaces() -> dict:
    return {
        "hermes": {
            "memoryProvider": "test-provider",
            "memoryProbe": {"ok": True, "stdout": "Provider: test-provider"},
            "mcpProbe": {"ok": True, "stdout": "test mcp configured"},
            "setupSmoke": {"ok": True, "json": {"files_written": []}},
            "rawArtifactApi": "hermes.raw_artifact.create",
            "summaryMemoryApi": "hermes.summary_memory.create",
            "liveStorageWriteAvailable": True,
            "storageAuthority": "Hermes",
        }
    }


def ready_boundary(record: dict, approval_token: str | None = None) -> dict:
    return build_hermes_live_boundary_report(
        record,
        surfaces=fake_write_ready_surfaces(),
        approval_token=approval_token,
    )
def fake_which_rdf_only(name: str) -> str | None:
    return f"/usr/bin/{name}" if name in {"rdfpipe", "hermes"} else None


def fake_which_rdf_shacl(name: str) -> str | None:
    return f"/usr/bin/{name}" if name in {"rdfpipe", "pyshacl", "hermes"} else None


def fake_module_available_rdf_only(name: str) -> bool:
    return name == "rdflib"


def fake_module_available_rdf_shacl(name: str) -> bool:
    return name in {"rdflib", "pyshacl"}


def fake_rdf_graph_surfaces() -> dict:
    return {
        "hermes": {
            "rdfGraphApi": "hermes.rdf_graph.create",
            "rdfGraphReadApi": "hermes.rdf_graph.read",
            "rdfGraphDeleteApi": "hermes.rdf_graph.delete",
        }
    }


cases: list[str] = []

packet = classify_request("remember that GJC should use visible routed sessions by default")
raw = build_raw_artifact_record(packet)
summary = build_summary_memory_record(raw, "User prefers visible routed GJC sessions for development routing.", confidence=0.92)
contract = build_ontology_contract(raw, summary, assertion_kind="PreferenceAssertion")
require("ontology contract name", contract["contract"], "just-chill-ontology-contract-v1")
require("ontology storage authority", contract["storageAuthority"], "Hermes")
require("ontology contract authority", contract["contractAuthority"], "just-chill")
require_truthy("tbox classes", contract["tbox"]["classes"])
require_truthy("candidate id", contract["aboxCandidate"]["@id"])
require("contract validation", validate_ontology_contract(contract), [])
require("real boundary blocks promotion", contract["aboxCandidate"]["promotionPolicy"]["canonicalPromotionEligible"], False)
require_in("real boundary blocker", "Hermes live write boundary is not ready", contract["shaclValidation"]["blockingReasons"])
cases.append("candidate-json-and-real-boundary-block")

decision = build_ontology_contract(
    raw,
    summary,
    assertion_kind="DecisionAssertion",
    hermes_boundary_report=ready_boundary(summary),
)
require("decision promotion blocked", decision["aboxCandidate"]["promotionPolicy"]["canonicalPromotionEligible"], False)
require_in("decision confirmation blocker", "DecisionAssertion requires explicit confirmation", decision["shaclValidation"]["blockingReasons"])
cases.append("decision-confirmation-block")

policy = build_ontology_contract(
    raw,
    summary,
    assertion_kind="PolicyAssertion",
    hermes_boundary_report=ready_boundary(summary),
)
require("policy promotion blocked", policy["aboxCandidate"]["promotionPolicy"]["canonicalPromotionEligible"], False)
require_in("policy confirmation blocker", "PolicyAssertion requires explicit confirmation", policy["shaclValidation"]["blockingReasons"])
cases.append("policy-confirmation-block")

preference_missing_repetition = build_ontology_contract(
    raw,
    summary,
    assertion_kind="PreferenceAssertion",
    repeated_sources=1,
    confidence=0.95,
    hermes_boundary_report=ready_boundary(summary),
)
require("preference missing repetition blocked", preference_missing_repetition["aboxCandidate"]["promotionPolicy"]["canonicalPromotionEligible"], False)
require_in("preference repetition blocker", "PreferenceAssertion auto-promotion requires repeated-independent-sources", preference_missing_repetition["shaclValidation"]["blockingReasons"])
cases.append("preference-repetition-block")
independent_packet = classify_request("remember that visible routed GJC sessions remain the preferred default")
independent_raw = build_raw_artifact_record(independent_packet)


preference_ready = build_ontology_contract(
    raw,
    summary,
    assertion_kind="PreferenceAssertion",
    repeated_sources=2,
    confidence=0.95,
    hermes_boundary_report=ready_boundary(summary),
    independent_source_records=[independent_raw],
)
require("preference ready eligible", preference_ready["aboxCandidate"]["promotionPolicy"]["canonicalPromotionEligible"], True)
require("preference shacl passed", preference_ready["shaclValidation"]["status"], "passed")
require("preference validation", validate_ontology_contract(preference_ready), [])
cases.append("preference-auto-promotion-ready")
bare_ref_preference = build_ontology_contract(
    raw,
    summary,
    assertion_kind="PreferenceAssertion",
    repeated_sources=2,
    confidence=0.95,
    hermes_boundary_report=ready_boundary(summary),
    independent_source_refs=["raw_unvalidated_ref"],
)
require("bare ref preference blocked", bare_ref_preference["aboxCandidate"]["promotionPolicy"]["canonicalPromotionEligible"], False)
require_in("bare ref provenance blocker", "independent source refs require raw artifact record provenance", bare_ref_preference["shaclValidation"]["blockingReasons"])
cases.append("bare-independent-ref-block")
duplicate_source_record = build_ontology_contract(
    raw,
    summary,
    assertion_kind="PreferenceAssertion",
    repeated_sources=2,
    confidence=0.95,
    hermes_boundary_report=ready_boundary(summary),
    independent_source_records=[independent_raw],
)
records = duplicate_source_record["aboxCandidate"]["provenance"]["sourceRecords"]
records[1] = dict(records[0])
require_in(
    "duplicate source record validation",
    "candidate provenance sourceRecord ids must be unique",
    validate_ontology_contract(duplicate_source_record),
)
require_in(
    "source record set validation",
    "candidate provenance sourceRecord ids must exactly match sourceArtifactRefs",
    validate_ontology_contract(duplicate_source_record),
)
cases.append("duplicate-source-record-validation")
tampered_source_state = build_ontology_contract(
    raw,
    summary,
    assertion_kind="PreferenceAssertion",
    repeated_sources=2,
    confidence=0.95,
    hermes_boundary_report=ready_boundary(summary),
    independent_source_records=[independent_raw],
)
tampered_source_state["aboxCandidate"]["provenance"]["sourceRecords"][0]["deletionState"] = "deleted"
tampered_source_state["aboxCandidate"]["provenance"]["sourceRecords"][1]["redactionState"] = "redacted"
state_issues = validate_ontology_contract(tampered_source_state)
require_in("source record active validation", "candidate provenance sourceRecord must be active", state_issues)
require_in("source record redaction validation", "candidate provenance sourceRecord must be not_redacted", state_issues)
cases.append("source-record-state-validation")

missing_source = build_ontology_contract(raw, summary, assertion_kind="PreferenceAssertion", hermes_boundary_report=ready_boundary(summary))
missing_source["aboxCandidate"]["sourceArtifactRefs"] = []
require_in("missing source validation", "candidate requires sourceArtifactRefs", validate_ontology_contract(missing_source))
missing_provenance = build_ontology_contract(raw, summary, assertion_kind="PreferenceAssertion", hermes_boundary_report=ready_boundary(summary))
missing_provenance["aboxCandidate"].pop("provenance", None)
require_in("missing provenance validation", "candidate requires provenance", validate_ontology_contract(missing_provenance))
cases.append("source-provenance-validation")

sensitive_packet = classify_request("remember my API key <example-api-key>")
sensitive_raw = build_raw_artifact_record(sensitive_packet)
sensitive_summary = build_summary_memory_record(sensitive_raw, "API key <example-api-key> must not be persisted.")
sensitive_contract = build_ontology_contract(
    sensitive_raw,
    sensitive_summary,
    assertion_kind="PreferenceAssertion",
    repeated_sources=2,
    confidence=0.95,
    hermes_boundary_report=ready_boundary(sensitive_summary),
)
require("sensitive promotion blocked", sensitive_contract["aboxCandidate"]["promotionPolicy"]["canonicalPromotionEligible"], False)
require_in("sensitive approval blocker", "sensitive source requires explicit approval", sensitive_contract["shaclValidation"]["blockingReasons"])
require_in("sensitive auto blocker", "PreferenceAssertion auto-promotion requires non-sensitive", sensitive_contract["shaclValidation"]["blockingReasons"])
cases.append("sensitive-source-block")
masked_sensitive_summary = build_summary_memory_record(sensitive_raw, "Sanitized-looking summary.")
masked_sensitive_summary["summaryMemory"]["sensitivity"] = "internal"
masked_sensitive_summary["summaryMemory"]["summary"] = "Sanitized-looking summary."
masked_sensitive_summary["summaryMemory"]["redactionState"] = "not_redacted"
masked_sensitive_contract = build_ontology_contract(
    sensitive_raw,
    masked_sensitive_summary,
    assertion_kind="PreferenceAssertion",
    repeated_sources=2,
    confidence=0.95,
    hermes_boundary_report=ready_boundary(sensitive_raw),
    independent_source_refs=["raw_independent_sensitive_source"],
)
require("masked raw sensitivity preserved", masked_sensitive_contract["aboxCandidate"]["sensitivity"], "sensitive")
require_in("masked sensitive blocker", "sensitive source requires explicit approval", masked_sensitive_contract["shaclValidation"]["blockingReasons"])
cases.append("masked-sensitive-source-block")

deleted_raw = build_raw_artifact_record(packet)
deleted_raw["artifact"]["deletionState"] = "deleted"
deleted_contract = build_ontology_contract(
    deleted_raw,
    build_summary_memory_record(deleted_raw, "Deleted source must not promote.", confidence=0.95),
    assertion_kind="PreferenceAssertion",
    repeated_sources=2,
    confidence=0.95,
    hermes_boundary_report=ready_boundary(summary),
)
require("deleted source blocked", deleted_contract["aboxCandidate"]["promotionPolicy"]["canonicalPromotionEligible"], False)
require_in("deleted source blocker", "source artifact is not active", deleted_contract["shaclValidation"]["blockingReasons"])
cases.append("deleted-source-block")

redacted_raw = build_raw_artifact_record(packet)
redacted_raw["artifact"]["redactionState"] = "redacted"
redacted_contract = build_ontology_contract(
    redacted_raw,
    build_summary_memory_record(redacted_raw, "Redacted source must not promote.", confidence=0.95),
    assertion_kind="PreferenceAssertion",
    repeated_sources=2,
    confidence=0.95,
    hermes_boundary_report=ready_boundary(summary),
)
require("redacted source blocked", redacted_contract["aboxCandidate"]["promotionPolicy"]["canonicalPromotionEligible"], False)
require_in("redacted source blocker", "source artifact is redacted", redacted_contract["shaclValidation"]["blockingReasons"])
cases.append("redacted-source-block")

rdf_export = build_rdf_owl_export(preference_ready)
require("rdf export validation", validate_rdf_owl_export(rdf_export, preference_ready), [])
require_in("rdf export candidate", preference_ready["aboxCandidate"]["@id"], rdf_export["export"]["turtle"])
require_in("rdf export source", preference_ready["aboxCandidate"]["sourceArtifactRefs"][0], rdf_export["export"]["turtle"])
repeat_rdf_export = build_rdf_owl_export(preference_ready)
require("rdf export stable turtle", repeat_rdf_export["export"]["turtle"], rdf_export["export"]["turtle"])
require("rdf export stable hash", repeat_rdf_export["export"]["turtleSha256"], rdf_export["export"]["turtleSha256"])
cases.append("rdf-export-stable-and-valid")

tampered_rdf = copy.deepcopy(rdf_export)
tampered_rdf["storageAuthority"] = "just-chill"
require_in("rdf authority guard", "rdf export storage authority must remain Hermes", validate_rdf_owl_export(tampered_rdf, preference_ready))
tampered_rdf = copy.deepcopy(rdf_export)
tampered_rdf["liveBinding"]["storageWriteAllowedHere"] = True
require_in("rdf write guard", "rdf export must not allow storage writes", validate_rdf_owl_export(tampered_rdf, preference_ready))
cases.append("rdf-export-authority-and-write-guards")

tampered_rdf = copy.deepcopy(rdf_export)
tampered_rdf["export"]["triples"][0]["objectType"] = "blank-node"
require_in("rdf object type guard", "rdf export triple objectType must be iri or literal", validate_rdf_owl_export(tampered_rdf, preference_ready))
tampered_rdf = copy.deepcopy(rdf_export)
tampered_rdf["export"]["persistedAt"] = "fake-live-store"
require_in("rdf persistence key guard", "export must not contain live persistence key $.export.persistedAt", validate_rdf_owl_export(tampered_rdf, preference_ready))
tampered_rdf = copy.deepcopy(rdf_export)
tampered_rdf["export"]["turtle"] = tampered_rdf["export"]["turtle"].replace("PromotionCandidate", "TamperedPromotionCandidate", 1)
tampered_rdf["export"]["turtleSha256"] = "sha256:" + hashlib.sha256(tampered_rdf["export"]["turtle"].encode("utf-8")).hexdigest()
require_in("rdf turtle/triple consistency guard", "rdf export turtle must match formatted triples", validate_rdf_owl_export(tampered_rdf, preference_ready))
cases.append("rdf-export-malformed-and-persistence-guards")

blocked_shacl_export = build_shacl_shape_export(contract)
require("blocked shacl export validation", validate_shacl_shape_export(blocked_shacl_export, contract), [])
require("blocked shacl conforms", blocked_shacl_export["validationReport"]["conforms"], False)
require_truthy("blocked shacl results", blocked_shacl_export["validationReport"]["results"])
require_in(
    "blocked shacl boundary shape",
    "HermesBoundaryShape",
    [result["sourceShape"] for result in blocked_shacl_export["validationReport"]["results"]],
)
cases.append("shacl-export-blocked-report")

passed_shacl_export = build_shacl_shape_export(preference_ready)
require("passed shacl export validation", validate_shacl_shape_export(passed_shacl_export, preference_ready), [])
require("passed shacl conforms", passed_shacl_export["validationReport"]["conforms"], True)
require("passed shacl result count", passed_shacl_export["validationReport"]["resultCount"], 0)
cases.append("shacl-export-passed-report")

tampered_shacl = copy.deepcopy(passed_shacl_export)
tampered_shacl["liveBinding"]["engineExecutionAllowedHere"] = True
require_in("shacl engine guard", "shacl export must not claim live engine execution", validate_shacl_shape_export(tampered_shacl, preference_ready))
tampered_shacl = copy.deepcopy(passed_shacl_export)
tampered_shacl["shapeManifest"]["sourceContractHash"] = "sha256:wrong"
require_in("shacl source hash guard", "shacl export sourceContractHash mismatch", validate_shacl_shape_export(tampered_shacl, preference_ready))
cases.append("shacl-export-live-and-source-guards")
rdf_only_boundary = build_rdf_shacl_live_boundary_report(
    which=fake_which_rdf_only,
    module_available=fake_module_available_rdf_only,
)
require("rdf-only boundary partial", rdf_only_boundary["status"], "rdf-shacl-partial")
require("rdf parser available", rdf_only_boundary["rdfParser"]["available"], True)
require("shacl engine unavailable", rdf_only_boundary["shaclEngine"]["available"], False)
require_in("shacl engine blocker", "live SHACL engine is not mapped", rdf_only_boundary["writeGate"]["blockedReasons"])
require("rdf-only boundary validation", validate_rdf_shacl_live_boundary_report(rdf_only_boundary), [])
cases.append("rdf-shacl-boundary-fail-closed")

ready_rdf_boundary = build_rdf_shacl_live_boundary_report(
    surfaces=fake_rdf_graph_surfaces(),
    which=fake_which_rdf_shacl,
    module_available=fake_module_available_rdf_shacl,
)
require("ready rdf/shacl boundary", ready_rdf_boundary["status"], "rdf-shacl-live-ready")
require("ready rdf/shacl write gate", ready_rdf_boundary["writeGate"]["enabled"], True)
require("ready rdf/shacl validation", validate_rdf_shacl_live_boundary_report(ready_rdf_boundary), [])
cases.append("rdf-shacl-boundary-ready")

ready_persistence_plan = build_rdf_shacl_persistence_plan(rdf_export, passed_shacl_export, ready_rdf_boundary)
require("rdf/shacl persistence ready", ready_persistence_plan["status"], "ready-for-host-rdf-shacl-persistence")
require("rdf/shacl no local execution", ready_persistence_plan["executionBoundary"]["allowedHere"], False)
require("rdf/shacl no local Hermes calls", ready_persistence_plan["executionBoundary"]["justChillCallsHermes"], False)
require("rdf/shacl no local engine", ready_persistence_plan["executionBoundary"]["justChillRunsShaclEngine"], False)
require("rdf/shacl persistence validation", validate_rdf_shacl_persistence_plan(ready_persistence_plan), [])
cases.append("rdf-shacl-persistence-plan-ready")

blocked_persistence_plan = build_rdf_shacl_persistence_plan(rdf_export, blocked_shacl_export, rdf_only_boundary)
require("rdf/shacl persistence blocked", blocked_persistence_plan["status"], "host-rdf-shacl-persistence-blocked")
require_in("rdf/shacl live blocker", "live SHACL engine is not mapped", blocked_persistence_plan["persistenceGate"]["blockedReasons"])
require_in("rdf/shacl conform blocker", "SHACL validation report must conform before RDF persistence", blocked_persistence_plan["persistenceGate"]["blockedReasons"])
require("rdf/shacl blocked validation", validate_rdf_shacl_persistence_plan(blocked_persistence_plan), [])
cases.append("rdf-shacl-persistence-fail-closed")
mismatched_shacl_export = copy.deepcopy(passed_shacl_export)
mismatched_shacl_export["shapeManifest"]["sourceContractHash"] = "sha256:other"
mismatched_plan = build_rdf_shacl_persistence_plan(rdf_export, mismatched_shacl_export, ready_rdf_boundary)
require("rdf/shacl mismatched plan blocked", mismatched_plan["status"], "host-rdf-shacl-persistence-blocked")
require_in(
    "rdf/shacl source hash match guard",
    "RDF export and SHACL manifest source contract hashes must match",
    mismatched_plan["persistenceGate"]["blockedReasons"],
)
cases.append("rdf-shacl-persistence-source-match-guard")


tampered_persistence_plan = copy.deepcopy(ready_persistence_plan)
tampered_persistence_plan["executionBoundary"]["justChillRunsShaclEngine"] = True
require_in(
    "rdf/shacl engine execution guard",
    "just-chill must not run the live SHACL engine directly",
    validate_rdf_shacl_persistence_plan(tampered_persistence_plan),
)
cases.append("rdf-shacl-persistence-guards")
tampered_persistence_plan = copy.deepcopy(ready_persistence_plan)
tampered_persistence_plan["persistenceGate"]["enabled"] = False
require_in(
    "rdf/shacl ready gate guard",
    "ready rdf/shacl persistence plan requires enabled gate",
    validate_rdf_shacl_persistence_plan(tampered_persistence_plan),
)
print(f"PASS: {len(cases)} just-chill ontology contract cases passed")
