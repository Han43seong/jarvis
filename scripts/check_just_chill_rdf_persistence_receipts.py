#!/usr/bin/env python3
"""Acceptance checks for host-owned RDF/SHACL persistence receipts."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from just_chill_rdf_persistence_receipts import (
    RECEIPT_KIND,
    build_rdf_persistence_receipt,
    run_live_pyshacl,
    validate_rdf_persistence_receipt,
)


def require(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle, haystack) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


cases: list[str] = []

with TemporaryDirectory() as temp_root:
    receipt = build_rdf_persistence_receipt(
        statement="Remember that concise Korean status updates are preferred.",
        store_root=Path(temp_root),
    )
    require("receipt kind", receipt["receiptKind"], RECEIPT_KIND)
    require("host owned", receipt["executionOwner"], "host-rdf-shacl-persistence-runner")
    require("just-chill does not run shacl", receipt["justChillRunsShaclEngine"], False)
    require("just-chill does not call hermes", receipt["justChillCallsHermes"], False)
    require("live shacl available", receipt["liveShaclResult"]["available"], True)
    require("live shacl conforms", receipt["liveShaclResult"]["conforms"], True)
    require("plan ready", receipt["persistencePlan"]["status"], "ready-for-host-rdf-shacl-persistence")
    require("graph readback", receipt["rdfGraphLifecycle"]["readBackHashMatches"], True)
    require("graph deleted", receipt["rdfGraphLifecycle"]["delete"]["status"], "deleted")
    require("graph read after delete blocked", receipt["rdfGraphLifecycle"]["readAfterDeleteBlocked"], True)
    require("validation clean", receipt["validationIssues"], [])
    cases.append("rdf-persistence-receipt")

    broken = {**receipt, "justChillCallsHermes": True}
    issues = validate_rdf_persistence_receipt(broken)
    require_in("direct Hermes validation", "just-chill must not call Hermes RDF APIs", issues)
    cases.append("boundary-fail-closed")

    broken_shacl = {**receipt, "liveShaclResult": {**receipt["liveShaclResult"], "conforms": False}}
    issues = validate_rdf_persistence_receipt(broken_shacl)
    require_in("shacl validation", "live SHACL evidence must conform", issues)
    cases.append("shacl-fail-closed")

bad_engine_result = run_live_pyshacl("this is not turtle", "this is not turtle")
require("bad shacl available", bad_engine_result["available"], True)
require("bad shacl conforms false", bad_engine_result["conforms"], False)
require("bad shacl error present", "error" in bad_engine_result, True)
cases.append("shacl-engine-exception-fail-closed")

print(f"PASS: {len(cases)} just-chill RDF persistence receipt cases passed")
