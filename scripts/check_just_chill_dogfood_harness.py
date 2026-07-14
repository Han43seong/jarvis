#!/usr/bin/env python3
"""Acceptance checks for the just-chill deterministic e2e dogfood harness."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from just_chill_dogfood_harness import build_dogfood_harness

ROOT = Path(__file__).resolve().parents[1]
DOGFOOD_SCRIPT = ROOT / "scripts" / "just_chill_dogfood_harness.py"


def require(name: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle: Any, haystack: Any) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


def require_truthy(name: str, value: Any) -> None:
    if not value:
        raise AssertionError(f"{name}: expected truthy value, got {value!r}")


def run_json(argv: list[str]) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(DOGFOOD_SCRIPT), *argv],
        text=True,
        capture_output=True,
        check=True,
        cwd=ROOT,
    )
    return json.loads(result.stdout)


cases: list[str] = []

report = build_dogfood_harness(cwd=str(ROOT))
require("dogfood status", report["status"], "passed")
require("dogfood validation", report["validationIssues"], [])
require("dogfood schema", report["schemaVersion"], 1)
require("dogfood no execution", report["authorityBoundary"]["executionAllowedHere"], False)
require("dogfood no GJC", report["authorityBoundary"]["justChillExecutesGjc"], False)
require("dogfood no Hermes", report["authorityBoundary"]["justChillWritesHermes"], False)
cases.append("dogfood-report-passed")

route = report["routeFlow"]
require("route ready", route["status"], "route-ready")
require("route dev", route["routerPacket"]["classification"]["isDevelopment"], True)
require("route target", route["routerPacket"]["routing"]["target"], "GJC")
require("route bridge visible", route["bridgePlan"]["bridgePlan"]["bridgePath"], "visible-routed-session")
require("route no execution", route["executionAllowedHere"], False)
cases.append("route-to-gjc-visible")

handoff = report["handoffFlow"]
require("handoff ready", handoff["status"], "handoff-plan-ready")
require("handoff bridge target", handoff["bridgePlan"]["target"], "GJC")
require("handoff no execution", handoff["bridgePlan"]["authorityBoundary"]["noExecutionInThisPlan"], True)
require_in("handoff reminder", "do not treat tmux scrollback as completion evidence", handoff["operatorReminder"])
cases.append("handoff-plan-safe")

memory = report["memoryFlow"]
raw = memory["rawArtifactContract"]
summary = memory["summaryMemoryContract"]
require("memory ready", memory["status"], "memory-candidate-ready")
require("raw kind", raw["recordKind"], "raw-artifact-contract")
require("raw sensitivity", raw["artifact"]["sensitivity"], "internal")
require("summary kind", summary["recordKind"], "summary-memory-contract")
require("memory no canonical ownership", memory["authorityBoundary"]["justChillOwnsCanonicalMemory"], False)
cases.append("memory-contracts-ready")

ontology_flow = report["ontologyFlow"]
ontology = ontology_flow["contract"]
rdf_export = ontology_flow["rdfExport"]
shacl_export = ontology_flow["shaclExport"]
require("ontology storage authority", ontology["storageAuthority"], "Hermes")
require("ontology validation status", ontology["shaclValidation"]["status"], "passed")
require("ontology canonical eligible", ontology["aboxCandidate"]["promotionPolicy"]["canonicalPromotionEligible"], True)
require("rdf contract-only", rdf_export["liveBinding"]["status"], "contract-only")
require("shacl contract-only", shacl_export["liveBinding"]["status"], "contract-only")
require_truthy("rdf turtle", rdf_export["export"]["turtle"])
require_truthy("shacl turtle", shacl_export["shapeManifest"]["shapesTurtle"])
cases.append("rdf-shacl-contracts-ready")

vector = report["vectorFlow"]["candidate"]
retrieval = report["vectorFlow"]["retrievalEvidence"]
recall = report["recallFlow"]
require("vector candidate ready", vector["status"], "ready-for-host-vector-index")
require("vector authority", vector["canonicalMemoryAuthority"], "Hermes")
require("retrieval provider", retrieval["provider"], "host-vector-sidecar")
require("recall allowed status", recall["status"], "recall-allowed")
require("recall allowed", recall["recallGateDecision"]["allowRecall"], True)
require("recall no blockers", recall["blockedReasons"], [])
cases.append("vector-recall-gate-ready")

consent = report["consentFlow"]
require("consent visible first", consent["status"], "visible-session-preferred")
require("consent no mutation", consent["mutationConsentGate"]["approvedForHostMutation"], False)
require("consent no local coordinator", consent["authorityBoundary"]["justChillCallsCoordinator"], False)
require("consent no blockers", consent["blockers"], [])
cases.append("consent-visible-first")

for name, passed in report["assertions"].items():
    require(f"assertion {name}", passed, True)
cases.append("assertion-map-complete")

stale = build_dogfood_harness(cwd=str(ROOT), recall_source_hash_override="sha256:stale")
require("stale dogfood blocked", stale["status"], "blocked")
require("stale recall blocked", stale["recallFlow"]["status"], "recall-blocked")
require_in("stale blocker", "current canonical source hash is stale relative to sidecar", stale["recallFlow"]["blockedReasons"])
require_in("stale assertion", "assertion failed: recallAllowed", stale["validationIssues"])
cases.append("stale-recall-fails-e2e")
deleted = build_dogfood_harness(cwd=str(ROOT), current_deletion_state="deleted")
require("deleted dogfood blocked", deleted["status"], "blocked")
require("deleted recall blocked", deleted["recallFlow"]["status"], "recall-blocked")
require_in("deleted recall drift", "current canonical source deletion state differs from sidecar", deleted["recallFlow"]["blockedReasons"])
require_in("deleted recall blocker", "deleted source cannot be recalled", deleted["recallFlow"]["blockedReasons"])
require_in("deleted assertion", "assertion failed: recallAllowed", deleted["validationIssues"])
cases.append("deleted-recall-fails-e2e")

redacted = build_dogfood_harness(cwd=str(ROOT), current_redaction_state="redacted")
require("redacted dogfood blocked", redacted["status"], "blocked")
require("redacted recall blocked", redacted["recallFlow"]["status"], "recall-blocked")
require_in("redacted recall drift", "current canonical source redaction state differs from sidecar", redacted["recallFlow"]["blockedReasons"])
require_in("redacted recall blocker", "redacted source cannot be recalled", redacted["recallFlow"]["blockedReasons"])
require_in("redacted assertion", "assertion failed: recallAllowed", redacted["validationIssues"])
cases.append("redacted-recall-fails-e2e")

sensitive = build_dogfood_harness(
    cwd=str(ROOT),
    memory_request="remember my API key <example-api-key> for later",
    summary="API key <example-api-key>",
)
require("sensitive dogfood blocked", sensitive["status"], "blocked")
require("sensitive memory blocked", sensitive["memoryFlow"]["status"], "memory-candidate-blocked")
require_in("sensitive memory blocker", "sensitive memory requires explicit approval before host-owned persistence", sensitive["memoryFlow"]["blockedReasons"])
require_in("sensitive assertion", "assertion failed: memoryContractsReady", sensitive["validationIssues"])
cases.append("sensitive-memory-fails-e2e")

cli = run_json(["--cwd", str(ROOT)])
require("CLI status", cli["status"], "passed")
require("CLI route", cli["routeFlow"]["routerPacket"]["routing"]["target"], "GJC")
require("CLI no hidden execution", cli["authorityBoundary"]["executionAllowedHere"], False)
cases.append("dogfood-cli-json")

print(f"PASS: {len(cases)} just-chill dogfood harness cases passed")
