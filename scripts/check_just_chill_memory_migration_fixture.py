#!/usr/bin/env python3
"""Acceptance checks for the just-chill non-sensitive memory migration fixture replay."""
from __future__ import annotations
import copy

from pathlib import Path
from tempfile import TemporaryDirectory

from just_chill_memory_migration_fixture import (
    FIXTURE_FACTS,
    REPLAY_KIND,
    SUMMARY_RECEIPT_KIND,
    FixtureFact,
    build_fixture_replay,
    validate_fixture_replay,
    source_excerpt,
)


def require(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle, haystack) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


def require_raises(name: str, expected: str, fn) -> None:
    try:
        fn()
    except Exception as exc:
        require_in(name, expected, str(exc))
        return
    raise AssertionError(f"{name}: expected exception containing {expected!r}")

cases: list[str] = []
repo_root = Path(__file__).resolve().parents[1]

with TemporaryDirectory() as temp_root:
    replay = build_fixture_replay(repo_root=repo_root, store_root=Path(temp_root))
    require("replay kind", replay["replayKind"], REPLAY_KIND)
    require("storage authority", replay["storageAuthority"], "Hermes")
    require("canonical authority", replay["canonicalMemoryAuthority"], "Hermes")
    require("just-chill no Hermes call", replay["justChillCallsHermes"], False)
    require("no private promotion", replay["privateMemoryPromotion"], False)
    require("validation clean", replay["validationIssues"], [])
    require("fact count", len(replay["facts"]), len(FIXTURE_FACTS))
    cases.append("replay-header")

    expected_fact_ids = {fact.fact_id for fact in FIXTURE_FACTS}
    require("fact ids", {fact["factId"] for fact in replay["facts"]}, expected_fact_ids)
    for fact in replay["facts"]:
        require("wiki source path", fact["source"]["sourcePath"], "wiki/concepts/just-chill-vnext-operating-layer.md")
        require("source marker present", bool(fact["source"]["marker"]), True)
        require("source excerpt hash", fact["source"]["excerptHash"].startswith("sha256:"), True)
    cases.append("source-selection")
    require_raises(
        "missing source marker fails closed",
        "fixture marker not found",
        lambda: source_excerpt(
            repo_root,
            FixtureFact(
                fact_id="missing_marker",
                source_path="wiki/concepts/just-chill-vnext-operating-layer.md",
                marker="this marker must not exist in the fixture source",
                summary="missing marker",
                assertion_kind="test",
            ),
        ),
    )
    cases.append("missing-marker-fail-closed")

    for raw in replay["rawArtifactLifecycle"]:
        require("raw create authority", raw["create"]["storageAuthority"], "Hermes")
        require("raw readback", raw["readBackHashMatches"], True)
        require("raw deleted", raw["delete"]["status"], "deleted")
        require("raw content hash", raw["create"]["contentHash"].startswith("sha256:"), True)
        require("raw contract internal", raw["contract"]["artifact"]["sensitivity"], "internal")
        require("raw contract active", raw["contract"]["artifact"]["deletionState"], "active")
    cases.append("raw-lifecycle")

    for receipt in replay["summaryReceipts"]:
        require("summary receipt kind", receipt["receiptKind"], SUMMARY_RECEIPT_KIND)
        require("summary internal", receipt["sensitivity"], "internal")
        require("summary not redacted", receipt["redactionState"], "not_redacted")
        require("summary active", receipt["deletionState"], "active")
        require("summary no private promotion", receipt["privateMemoryPromotion"], False)
        require("summary canonical promotion false", receipt["canonicalPromotionAllowed"], False)
        require("summary retention standard", receipt["retention"]["class"], "standard")
        require("summary access scope", receipt["accessPolicy"]["scope"], "private-user")
        require_in("summary raw hash", "sha256:", receipt["rawContentHash"])
    cases.append("summary-receipts")

    rdf = replay["rdfGraphLifecycle"]
    require("rdf create authority", rdf["create"]["storageAuthority"], "Hermes")
    require("rdf source contract hash", rdf["sourceContractHash"].startswith("sha256:"), True)
    require("rdf turtle hash", rdf["turtleSha256"].startswith("sha256:"), True)
    require("rdf readback", rdf["readBackHashMatches"], True)
    require("rdf deleted", rdf["delete"]["status"], "deleted")
    cases.append("rdf-lifecycle")

    for vector in replay["vectorSidecarLifecycle"]:
        require("vector create authority", vector["create"]["storageAuthority"], "Hermes")
        require("vector sidecar authority", vector["create"]["sidecarAuthority"], "host-vector-sidecar")
        require("vector readback", vector["readBackHashMatches"], True)
        require("vector search candidate", vector["searchReturnedCandidate"], True)
        require("vector search receipt", vector["searchReceiptRef"].startswith("host-vector-search-receipt:"), True)
        require("vector deleted", vector["delete"]["status"], "deleted")
    cases.append("vector-lifecycle")

    counts = replay["statusAfterCleanup"]["counts"]
    require("active raw zero", counts["raw"], 0)
    require("active rdf zero", counts["rdf"], 0)
    require("active vector zero", counts["vector"], 0)
    require("delete receipts", counts["deletions"] >= len(FIXTURE_FACTS) * 2 + 1, True)
    cases.append("cleanup-state")

    broken = {**replay, "privateMemoryPromotion": True}
    issues = validate_fixture_replay(broken)
    require_in("promotion fail closed", "fixture replay must not promote private memory", issues)
    cases.append("validation-fail-closed")
    broken_exec = copy.deepcopy(replay)
    broken_exec["justChillCallsHermes"] = True
    issues = validate_fixture_replay(broken_exec)
    require_in("direct execution fail closed", "just-chill must not call Hermes during fixture replay", issues)

    broken_raw = copy.deepcopy(replay)
    broken_raw["rawArtifactLifecycle"][0]["readBackHashMatches"] = False
    broken_raw["rawArtifactLifecycle"][1]["delete"]["status"] = "active"
    issues = validate_fixture_replay(broken_raw)
    require_in("raw readback fail closed", f"{broken_raw['rawArtifactLifecycle'][0]['factId']} raw read-back mismatch", issues)
    require_in("raw delete fail closed", f"{broken_raw['rawArtifactLifecycle'][1]['factId']} raw delete receipt missing", issues)

    broken_summary = copy.deepcopy(replay)
    broken_summary["summaryReceipts"][0]["retention"]["autoPersistAllowed"] = False
    broken_summary["summaryReceipts"][1]["accessPolicy"]["scope"] = "workspace"
    broken_summary["summaryReceipts"][2]["deletionState"] = "deleted"
    issues = validate_fixture_replay(broken_summary)
    require_in("summary retention fail closed", f"{broken_summary['summaryReceipts'][0]['factId']} standard retention missing", issues)
    require_in("summary scope fail closed", f"{broken_summary['summaryReceipts'][1]['factId']} access scope mismatch", issues)
    require_in("summary state fail closed", f"{broken_summary['summaryReceipts'][2]['factId']} lifecycle state invalid", issues)

    broken_rdf_vector = copy.deepcopy(replay)
    broken_rdf_vector["rdfGraphLifecycle"]["readBackHashMatches"] = False
    broken_rdf_vector["vectorSidecarLifecycle"][0]["searchReceiptRef"] = None
    broken_rdf_vector["vectorSidecarLifecycle"][1]["searchReturnedCandidate"] = False
    broken_rdf_vector["vectorSidecarLifecycle"][2]["delete"]["status"] = "active"
    issues = validate_fixture_replay(broken_rdf_vector)
    require_in("rdf readback fail closed", "RDF read-back mismatch", issues)
    require_in("vector receipt fail closed", f"{broken_rdf_vector['vectorSidecarLifecycle'][0]['factId']} vector search receipt ref missing", issues)
    require_in("vector search fail closed", f"{broken_rdf_vector['vectorSidecarLifecycle'][1]['factId']} vector search receipt missing candidate", issues)
    require_in("vector delete fail closed", f"{broken_rdf_vector['vectorSidecarLifecycle'][2]['factId']} vector delete receipt missing", issues)

    broken_cleanup = copy.deepcopy(replay)
    broken_cleanup["statusAfterCleanup"]["counts"]["vector"] = 1
    broken_cleanup["statusAfterCleanup"]["counts"]["deletions"] = 0
    issues = validate_fixture_replay(broken_cleanup)
    require_in("cleanup active fail closed", "fixture store must have no active raw/RDF/vector records after cleanup", issues)
    require_in("cleanup delete receipts fail closed", "fixture delete receipt count is incomplete", issues)
    cases.append("validator-branch-fail-closed")

print(f"PASS: {len(cases)} just-chill memory migration fixture cases passed")
