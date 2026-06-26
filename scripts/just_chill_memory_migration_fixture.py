#!/usr/bin/env python3
"""Host-owned fixture replay for non-sensitive just-chill memory migration.

The replay uses only repository wiki/design facts as fixture candidates. It
exercises host-owned Hermes raw/RDF/vector MCP lifecycles and local summary
contracts without promoting private user memory or making just-chill the storage
authority.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from just_chill_hermes_memory_mcp import (
    TOOL_RAW_CREATE,
    TOOL_RAW_DELETE,
    TOOL_RAW_READ,
    TOOL_RDF_CREATE,
    TOOL_RDF_DELETE,
    TOOL_RDF_READ,
    TOOL_STATUS,
    TOOL_VECTOR_CREATE,
    TOOL_VECTOR_DELETE,
    TOOL_VECTOR_READ,
    TOOL_VECTOR_SEARCH,
    call_tool,
    sha256_text,
)
from just_chill_memory_contracts import (
    build_raw_artifact_record,
    build_summary_memory_record,
    content_hash,
    validate_contract_record,
)
from just_chill_router import classify_request

SCHEMA_VERSION = 1
REPLAY_KIND = "just-chill-memory-migration-fixture-replay-v1"
SUMMARY_RECEIPT_KIND = "just-chill-summary-memory-fixture-receipt-v1"


@dataclass(frozen=True)
class FixtureFact:
    fact_id: str
    source_path: str
    marker: str
    summary: str
    assertion_kind: str


FIXTURE_FACTS: tuple[FixtureFact, ...] = (
    FixtureFact(
        fact_id="jc_dev_routes_to_gjc",
        source_path="wiki/concepts/just-chill-vnext-operating-layer.md",
        marker="route development work to GJC as the development workflow authority",
        summary="Development work routes to GJC as the workflow authority.",
        assertion_kind="routing-policy",
    ),
    FixtureFact(
        fact_id="jc_hermes_memory_authority",
        source_path="wiki/concepts/just-chill-vnext-operating-layer.md",
        marker="make Hermes the state/artifact/memory access authority",
        summary="Hermes is the state, artifact, and memory access authority for just-chill.",
        assertion_kind="authority-boundary",
    ),
    FixtureFact(
        fact_id="jc_operating_console_memory_gate",
        source_path="wiki/concepts/just-chill-vnext-operating-layer.md",
        marker="make just-chill the operating console and memory gate above them",
        summary="just-chill is the operating console and memory gate above GJC and Hermes.",
        assertion_kind="product-role",
    ),
    FixtureFact(
        fact_id="jc_vector_sidecar_noncanonical",
        source_path="wiki/concepts/just-chill-vnext-operating-layer.md",
        marker="do not make just-chill a vector executor or semantic ranking authority",
        summary="Vector sidecars provide recall evidence without making just-chill a vector executor or semantic ranking authority.",
        assertion_kind="memory-boundary",
    ),
)


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def json_text(data: Any, *, pretty: bool = False) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2 if pretty else None, sort_keys=True)


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def source_excerpt(repo_root: Path, fact: FixtureFact) -> dict[str, Any]:
    path = (repo_root / fact.source_path).resolve()
    root = repo_root.resolve()
    if not path.is_file() or root not in path.parents:
        raise ValueError(f"fixture source not found inside repo: {fact.source_path}")
    text = path.read_text(encoding="utf-8")
    index = text.find(fact.marker)
    if index < 0:
        raise ValueError(f"fixture marker not found: {fact.marker}")
    start = max(0, index - 180)
    end = min(len(text), index + len(fact.marker) + 180)
    excerpt = text[start:end].strip()
    line = text[:index].count("\n") + 1
    return {
        "sourcePath": fact.source_path,
        "marker": fact.marker,
        "line": line,
        "excerpt": excerpt,
        "excerptHash": sha256_text(excerpt),
    }


def turtle_literal(value: str) -> str:
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace("\n", "\\n") + '"'


def build_fixture_turtle(summary_receipts: list[dict[str, Any]]) -> str:
    lines = [
        "@prefix jc: <https://just-chill.local/ontology#> .",
        "@prefix fixture: <urn:just-chill:migration-fixture:> .",
        "",
    ]
    for receipt in summary_receipts:
        fact_id = receipt["factId"]
        lines.extend([
            f"fixture:{fact_id} a jc:MigrationFixtureFact ;",
            f"  jc:assertionKind {turtle_literal(receipt['assertionKind'])} ;",
            f"  jc:summary {turtle_literal(receipt['summary'])} ;",
            f"  jc:summaryHash {turtle_literal(receipt['summaryHash'])} ;",
            f"  jc:sourcePath {turtle_literal(receipt['sourcePath'])} ;",
            f"  jc:rawArtifactId {turtle_literal(receipt['rawArtifactId'])} .",
            "",
        ])
    return "\n".join(lines)


def build_fixture_replay(*, repo_root: Path, store_root: Path) -> dict[str, Any]:
    facts: list[dict[str, Any]] = []
    raw_lifecycle: list[dict[str, Any]] = []
    summary_receipts: list[dict[str, Any]] = []
    vector_lifecycle: list[dict[str, Any]] = []
    validation_issues: list[str] = []

    for fact in FIXTURE_FACTS:
        excerpt = source_excerpt(repo_root, fact)
        packet = classify_request(f"summarize repo design fixture: {fact.summary}")
        raw_contract = build_raw_artifact_record(
            packet,
            content=excerpt["excerpt"],
            artifact_type="repo_wiki_design_fixture",
            source_channel="repo-wiki",
        )
        raw_contract["artifact"]["provenance"]["wikiSource"] = {
            "path": excerpt["sourcePath"],
            "line": excerpt["line"],
            "markerHash": sha256_text(fact.marker),
        }
        raw_contract_issues = validate_contract_record(raw_contract)
        if raw_contract_issues:
            validation_issues.extend([f"{fact.fact_id} raw contract: {issue}" for issue in raw_contract_issues])
        artifact = raw_contract["artifact"]
        if artifact["sensitivity"] != "internal":
            raise ValueError(f"{fact.fact_id} is not non-sensitive: {artifact['sensitivity']}")

        raw_id = f"fixture_raw_{fact.fact_id}"
        raw_hash = sha256_text(excerpt["excerpt"])
        raw_create = call_tool(
            TOOL_RAW_CREATE,
            {
                "recordId": raw_id,
                "content": excerpt["excerpt"],
                "contentHash": raw_hash,
                "sensitivity": "internal",
                "provenance": {
                    "sourcePath": excerpt["sourcePath"],
                    "line": excerpt["line"],
                    "markerHash": sha256_text(fact.marker),
                    "factId": fact.fact_id,
                },
                "metadata": {"fixtureOnly": True, "privateMemoryPromotion": False},
            },
            root=store_root,
        )
        raw_read = call_tool(TOOL_RAW_READ, {"recordId": raw_id, "includeContent": True}, root=store_root)
        raw_delete = call_tool(
            TOOL_RAW_DELETE,
            {"recordId": raw_id, "reason": "fixture replay cleanup", "approvalToken": "fixture-approved-cleanup"},
            root=store_root,
        )
        raw_lifecycle.append({
            "factId": fact.fact_id,
            "recordId": raw_id,
            "contract": raw_contract,
            "create": raw_create,
            "readBackHashMatches": raw_read.get("contentHash") == raw_hash and raw_read.get("content") == excerpt["excerpt"],
            "delete": raw_delete,
            "source": excerpt,
        })

        summary_contract = build_summary_memory_record(raw_contract, fact.summary, confidence=0.93)
        summary_contract["summaryMemory"]["provenance"].update({
            "sourcePath": excerpt["sourcePath"],
            "sourceLine": excerpt["line"],
            "sourceExcerptHash": excerpt["excerptHash"],
            "fixtureFactId": fact.fact_id,
        })
        summary_issues = validate_contract_record(summary_contract)
        if summary_issues:
            validation_issues.extend([f"{fact.fact_id} summary contract: {issue}" for issue in summary_issues])
        summary = summary_contract["summaryMemory"]
        summary_receipt = {
            "schemaVersion": SCHEMA_VERSION,
            "receiptKind": SUMMARY_RECEIPT_KIND,
            "factId": fact.fact_id,
            "assertionKind": fact.assertion_kind,
            "summaryId": summary["id"],
            "summary": summary["summary"],
            "summaryHash": summary["summaryHash"],
            "sensitivity": summary["sensitivity"],
            "retention": summary["retention"],
            "accessPolicy": summary["accessPolicy"],
            "deletionState": summary["deletionState"],
            "redactionState": summary["redactionState"],
            "rawArtifactId": raw_id,
            "rawContentHash": raw_hash,
            "sourcePath": excerpt["sourcePath"],
            "sourceLine": excerpt["line"],
            "privateMemoryPromotion": False,
            "canonicalPromotionAllowed": False,
        }
        summary_receipts.append(summary_receipt)
        facts.append({
            "factId": fact.fact_id,
            "assertionKind": fact.assertion_kind,
            "source": excerpt,
            "rawArtifactId": raw_id,
            "summaryId": summary["id"],
            "summaryHash": summary["summaryHash"],
        })

        vector_id = f"fixture_vector_{fact.fact_id}"
        vector_hash = sha256_text("fixture-vector:" + summary["summaryHash"])
        vector_create = call_tool(
            TOOL_VECTOR_CREATE,
            {
                "sidecarId": vector_id,
                "canonicalSourceId": summary["id"],
                "sourceKind": "summary-memory",
                "canonicalContentHash": summary["summaryHash"],
                "observedContentHash": summary["summaryHash"],
                "readBackHashMatches": True,
                "receiptRef": f"fixture-summary-receipt://{summary['id']}",
                "textHash": content_hash(summary["summary"]),
                "vectorHash": vector_hash,
                "embeddingModel": "fixture-deterministic-hash-model",
                "embeddingDimensions": 8,
                "sensitivity": summary["sensitivity"],
                "deletionState": summary["deletionState"],
                "redactionState": summary["redactionState"],
                "accessPolicy": summary["accessPolicy"],
                "retention": summary["retention"],
                "provenance": {"summaryReceiptKind": SUMMARY_RECEIPT_KIND, "factId": fact.fact_id},
            },
            root=store_root,
        )
        vector_read = call_tool(TOOL_VECTOR_READ, {"sidecarId": vector_id}, root=store_root)
        vector_search = call_tool(
            TOOL_VECTOR_SEARCH,
            {"queryTextHash": content_hash(summary["summary"]), "requestedScope": summary["accessPolicy"]["scope"]},
            root=store_root,
        )
        vector_delete = call_tool(
            TOOL_VECTOR_DELETE,
            {"sidecarId": vector_id, "reason": "fixture replay cleanup", "approvalToken": "fixture-approved-cleanup"},
            root=store_root,
        )
        vector_lifecycle.append({
            "factId": fact.fact_id,
            "sidecarId": vector_id,
            "create": vector_create,
            "readBackHashMatches": (
                vector_read.get("observedContentHash") == summary["summaryHash"]
                and vector_read.get("textHash") == content_hash(summary["summary"])
                and vector_read.get("vectorHash") == vector_hash
            ),
            "searchReturnedCandidate": bool(vector_search.get("results")) and vector_search["results"][0].get("resultId") == vector_id,
            "searchReceiptRef": vector_search.get("results", [{}])[0].get("receiptRef") if vector_search.get("results") else None,
            "delete": vector_delete,
        })

    turtle = build_fixture_turtle(summary_receipts)
    source_contract_hash = sha256_text(canonical_json(summary_receipts))
    graph_id = "fixture_just_chill_design_replay"
    rdf_create = call_tool(
        TOOL_RDF_CREATE,
        {
            "graphId": graph_id,
            "sourceCandidateId": graph_id,
            "sourceContractHash": source_contract_hash,
            "turtle": turtle,
            "turtleSha256": sha256_text(turtle),
            "shaclResult": {"conforms": True, "engine": "fixture-non-sensitive-policy-check", "factCount": len(summary_receipts)},
            "metadata": {"fixtureOnly": True, "privateMemoryPromotion": False},
        },
        root=store_root,
    )
    rdf_read = call_tool(TOOL_RDF_READ, {"graphId": graph_id, "includeTurtle": True}, root=store_root)
    rdf_delete = call_tool(
        TOOL_RDF_DELETE,
        {"graphId": graph_id, "reason": "fixture replay cleanup", "approvalToken": "fixture-approved-cleanup"},
        root=store_root,
    )
    status_after = call_tool(TOOL_STATUS, {}, root=store_root)

    replay = {
        "schemaVersion": SCHEMA_VERSION,
        "replayKind": REPLAY_KIND,
        "executionOwner": "host-memory-migration-fixture-runner",
        "storageAuthority": "Hermes",
        "canonicalMemoryAuthority": "Hermes",
        "justChillCallsHermes": False,
        "privateMemoryPromotion": False,
        "repoRoot": str(repo_root.resolve()),
        "storeRoot": str(store_root.resolve()),
        "facts": facts,
        "rawArtifactLifecycle": raw_lifecycle,
        "summaryReceipts": summary_receipts,
        "rdfGraphLifecycle": {
            "graphId": graph_id,
            "sourceContractHash": source_contract_hash,
            "turtleSha256": sha256_text(turtle),
            "create": rdf_create,
            "readBackHashMatches": rdf_read.get("turtleSha256") == sha256_text(turtle) and rdf_read.get("turtle") == turtle,
            "delete": rdf_delete,
        },
        "vectorSidecarLifecycle": vector_lifecycle,
        "statusAfterCleanup": status_after,
        "validationIssues": validation_issues,
    }
    replay["validationIssues"] = validate_fixture_replay(replay)
    return replay


def validate_fixture_replay(replay: dict[str, Any]) -> list[str]:
    issues = list(replay.get("validationIssues", []))
    if replay.get("replayKind") != REPLAY_KIND:
        issues.append("unexpected replay kind")
    if replay.get("justChillCallsHermes") is not False:
        issues.append("just-chill must not call Hermes during fixture replay")
    if replay.get("privateMemoryPromotion") is not False:
        issues.append("fixture replay must not promote private memory")
    facts = replay.get("facts", [])
    if len(facts) != len(FIXTURE_FACTS):
        issues.append("fixture fact count mismatch")
    for receipt in replay.get("summaryReceipts", []):
        if receipt.get("receiptKind") != SUMMARY_RECEIPT_KIND:
            issues.append(f"{receipt.get('factId')} summary receipt kind mismatch")
        if receipt.get("sensitivity") != "internal":
            issues.append(f"{receipt.get('factId')} summary is not internal")
        if receipt.get("privateMemoryPromotion") is not False or receipt.get("canonicalPromotionAllowed") is not False:
            issues.append(f"{receipt.get('factId')} summary promotion flags must remain false")
        if receipt.get("retention", {}).get("autoPersistAllowed") is not True:
            issues.append(f"{receipt.get('factId')} standard retention missing")
        if receipt.get("accessPolicy", {}).get("scope") != "private-user":
            issues.append(f"{receipt.get('factId')} access scope mismatch")
        if receipt.get("deletionState") != "active" or receipt.get("redactionState") != "not_redacted":
            issues.append(f"{receipt.get('factId')} lifecycle state invalid")
    for raw in replay.get("rawArtifactLifecycle", []):
        if raw.get("readBackHashMatches") is not True:
            issues.append(f"{raw.get('factId')} raw read-back mismatch")
        if raw.get("delete", {}).get("status") != "deleted":
            issues.append(f"{raw.get('factId')} raw delete receipt missing")
    rdf = replay.get("rdfGraphLifecycle", {})
    if rdf.get("readBackHashMatches") is not True:
        issues.append("RDF read-back mismatch")
    if rdf.get("delete", {}).get("status") != "deleted":
        issues.append("RDF delete receipt missing")
    for vector in replay.get("vectorSidecarLifecycle", []):
        if vector.get("readBackHashMatches") is not True:
            issues.append(f"{vector.get('factId')} vector read-back mismatch")
        if vector.get("searchReturnedCandidate") is not True:
            issues.append(f"{vector.get('factId')} vector search receipt missing candidate")
        if not vector.get("searchReceiptRef"):
            issues.append(f"{vector.get('factId')} vector search receipt ref missing")
        if vector.get("delete", {}).get("status") != "deleted":
            issues.append(f"{vector.get('factId')} vector delete receipt missing")
    counts = replay.get("statusAfterCleanup", {}).get("counts", {})
    if counts.get("raw") != 0 or counts.get("rdf") != 0 or counts.get("vector") != 0:
        issues.append("fixture store must have no active raw/RDF/vector records after cleanup")
    if counts.get("deletions", 0) < len(FIXTURE_FACTS) * 2 + 1:
        issues.append("fixture delete receipt count is incomplete")
    return list(dict.fromkeys(issues))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay non-sensitive just-chill design facts through host-owned Hermes memory fixtures.")
    parser.add_argument("--repo-root", default=str(default_repo_root()), help="Repository root containing wiki source docs.")
    parser.add_argument("--store-root", help="MCP fixture store root. Defaults to a temporary directory.")
    parser.add_argument("--keep-store", action="store_true", help="Keep the temporary store root printed in output for inspection.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).expanduser().resolve()
    if args.store_root:
        replay = build_fixture_replay(repo_root=repo_root, store_root=Path(args.store_root).expanduser().resolve())
        print(json_text(replay, pretty=args.pretty))
        return 0 if not replay.get("validationIssues") else 1

    with tempfile.TemporaryDirectory(prefix="just-chill-memory-fixture-") as tmp:
        replay = build_fixture_replay(repo_root=repo_root, store_root=Path(tmp).resolve())
        print(json_text(replay, pretty=args.pretty))
        if args.keep_store:
            print(f"temporary store was cleaned up: {tmp}")
        return 0 if not replay.get("validationIssues") else 1


if __name__ == "__main__":
    raise SystemExit(main())
