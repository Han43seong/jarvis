#!/usr/bin/env python3
"""Host-owned RDF/SHACL persistence receipt bridge for just-chill.

This runner combines deterministic just-chill ontology exports, a live host SHACL
engine, and the host-owned Hermes RDF graph MCP lifecycle. It emits evidence for
canonical RDF persistence while preserving the boundary that just-chill itself
neither runs SHACL nor calls Hermes.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from just_chill_hermes_mcp_receipts import StdioMcpClient, default_server_script, read_tool_payload
from just_chill_hermes_memory_mcp import TOOL_RDF_CREATE, TOOL_RDF_DELETE, TOOL_RDF_READ, sha256_text
from just_chill_memory_contracts import build_raw_artifact_record
from just_chill_ontology_contracts import (
    build_ontology_contract,
    build_rdf_owl_export,
    build_rdf_shacl_live_boundary_report,
    build_rdf_shacl_persistence_plan,
    build_shacl_shape_export,
    validate_rdf_owl_export,
    validate_rdf_shacl_live_boundary_report,
    validate_rdf_shacl_persistence_plan,
    validate_shacl_shape_export,
)
from just_chill_router import classify_request

SCHEMA_VERSION = 1
RECEIPT_KIND = "just-chill-rdf-shacl-persistence-receipt-v1"


class RdfPersistenceError(RuntimeError):
    """Raised when host-owned RDF persistence evidence cannot be produced."""


def json_text(data: Any, *, pretty: bool = False) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2 if pretty else None, sort_keys=True)


def make_ready_boundary() -> dict[str, Any]:
    return {
        "status": "ready-for-hermes-write",
        "writeGate": {"allowedHere": False, "enabled": True, "blockedReasons": []},
        "approval": {"sensitiveApproved": True, "approvalTokenPresent": False, "sensitivity": "internal"},
    }


def build_ready_raw_record(statement: str) -> dict[str, Any]:
    packet = classify_request(statement)
    raw = build_raw_artifact_record(packet, content=statement)
    raw["artifact"]["memoryPolicy"]["blockedReasons"] = []
    raw["artifact"]["memoryPolicy"]["canonicalPromotionAllowed"] = True
    raw["artifact"]["memoryPolicy"]["candidateCreationAllowed"] = True
    return raw


def run_live_pyshacl(data_turtle: str, shapes_turtle: str) -> dict[str, Any]:
    try:
        from pyshacl import validate  # type: ignore
    except Exception as exc:  # pragma: no cover - exercised on hosts without pyshacl
        return {
            "available": False,
            "conforms": False,
            "engine": "pyshacl",
            "error": str(exc),
        }

    try:
        conforms, _results_graph, results_text = validate(
            data_graph=data_turtle,
            shacl_graph=shapes_turtle,
            data_graph_format="turtle",
            shacl_graph_format="turtle",
            inference="rdfs",
            abort_on_first=False,
            allow_infos=True,
            allow_warnings=True,
        )
    except Exception as exc:
        return {
            "available": True,
            "conforms": False,
            "engine": "pyshacl",
            "error": str(exc),
        }
    return {
        "available": True,
        "conforms": bool(conforms),
        "engine": "pyshacl",
        "resultsTextHash": sha256_text(str(results_text)),
        "resultsTextPreview": str(results_text)[:500],
    }


def build_rdf_persistence_receipt(
    *,
    statement: str,
    store_root: Path,
    server_script: Path | None = None,
    timeout: float = 5.0,
) -> dict[str, Any]:
    server_script = server_script or default_server_script()
    raw = build_ready_raw_record(statement)
    contract = build_ontology_contract(
        raw,
        assertion_kind="OperationalEvent",
        confidence=0.95,
        hermes_boundary_report=make_ready_boundary(),
    )
    rdf_export = build_rdf_owl_export(contract)
    shacl_export = build_shacl_shape_export(contract)
    live_report = build_rdf_shacl_live_boundary_report()
    live_shacl = run_live_pyshacl(
        rdf_export["export"]["turtle"],
        shacl_export["shapeManifest"]["shapesTurtle"],
    )
    plan = build_rdf_shacl_persistence_plan(rdf_export, shacl_export, live_report)

    receipt: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "receiptKind": RECEIPT_KIND,
        "executionOwner": "host-rdf-shacl-persistence-runner",
        "storageAuthority": "Hermes",
        "contractAuthority": "just-chill",
        "justChillRunsShaclEngine": False,
        "justChillCallsHermes": False,
        "server": {
            "script": str(server_script),
            "storeRoot": str(store_root),
            "transport": "stdio-jsonrpc",
        },
        "source": {
            "statement": statement,
            "candidateId": rdf_export["export"].get("sourceCandidateId"),
            "sourceContractHash": rdf_export["export"].get("sourceContractHash"),
            "turtleSha256": rdf_export["export"].get("turtleSha256"),
            "shapesTurtleSha256": shacl_export["shapeManifest"].get("shapesTurtleSha256"),
        },
        "liveBoundary": live_report,
        "persistencePlan": plan,
        "liveShaclResult": live_shacl,
        "rdfGraphLifecycle": {},
        "validationIssues": [],
    }

    issues = [
        *validate_rdf_owl_export(rdf_export, contract),
        *validate_shacl_shape_export(shacl_export, contract),
        *validate_rdf_shacl_live_boundary_report(live_report),
        *validate_rdf_shacl_persistence_plan(plan),
    ]
    if not live_shacl.get("available"):
        issues.append("live SHACL engine is not available")
    if live_shacl.get("conforms") is not True:
        issues.append("live SHACL engine did not conform")
    if plan.get("status") != "ready-for-host-rdf-shacl-persistence":
        issues.append("RDF persistence plan is not ready")

    if issues:
        receipt["validationIssues"] = sorted(set(issues))
        return receipt

    with StdioMcpClient(server_script, store_root, timeout=timeout) as client:
        client.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "just-chill-rdf-persistence-runner", "version": "1.0"}})
        create = read_tool_payload(client.call_tool(TOOL_RDF_CREATE, {
            "graphId": "rdf_persistence_receipt_001",
            "sourceCandidateId": rdf_export["export"]["sourceCandidateId"],
            "sourceContractHash": rdf_export["export"]["sourceContractHash"],
            "turtle": rdf_export["export"]["turtle"],
            "turtleSha256": rdf_export["export"]["turtleSha256"],
            "shapesTurtleSha256": shacl_export["shapeManifest"]["shapesTurtleSha256"],
            "shaclResult": live_shacl,
            "metadata": {"runner": "just-chill-rdf-shacl-persistence-receipt-v1"},
        }))
        read = read_tool_payload(client.call_tool(TOOL_RDF_READ, {"graphId": "rdf_persistence_receipt_001", "includeTurtle": True}))
        delete = read_tool_payload(client.call_tool(TOOL_RDF_DELETE, {"graphId": "rdf_persistence_receipt_001", "reason": "receipt lifecycle cleanup", "approvalToken": "host-approved"}))
        read_after_delete = read_tool_payload(client.call_tool(TOOL_RDF_READ, {"graphId": "rdf_persistence_receipt_001", "includeTurtle": True}))

    receipt["rdfGraphLifecycle"] = {
        "graphId": "rdf_persistence_receipt_001",
        "create": create,
        "readBack": {k: read.get(k) for k in ["api", "graphId", "sourceCandidateId", "sourceContractHash", "turtleSha256", "status", "_mcpIsError"]},
        "readBackHashMatches": read.get("turtleSha256") == rdf_export["export"]["turtleSha256"] and read.get("turtle") == rdf_export["export"]["turtle"],
        "delete": delete,
        "readAfterDelete": read_after_delete,
        "readAfterDeleteBlocked": read_after_delete.get("_mcpIsError") is True,
    }
    receipt["validationIssues"] = validate_rdf_persistence_receipt(receipt)
    return receipt


def validate_rdf_persistence_receipt(receipt: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if receipt.get("receiptKind") != RECEIPT_KIND:
        issues.append("unexpected RDF persistence receipt kind")
    if receipt.get("executionOwner") != "host-rdf-shacl-persistence-runner":
        issues.append("RDF persistence receipt must be host-owned")
    if receipt.get("justChillRunsShaclEngine") is not False:
        issues.append("just-chill must not run live SHACL engine")
    if receipt.get("justChillCallsHermes") is not False:
        issues.append("just-chill must not call Hermes RDF APIs")
    if receipt.get("liveShaclResult", {}).get("conforms") is not True:
        issues.append("live SHACL evidence must conform")
    if receipt.get("persistencePlan", {}).get("status") != "ready-for-host-rdf-shacl-persistence":
        issues.append("persistence plan must be ready")
    lifecycle = receipt.get("rdfGraphLifecycle", {})
    if lifecycle.get("readBackHashMatches") is not True:
        issues.append("RDF graph read-back hash/content mismatch")
    if lifecycle.get("delete", {}).get("status") != "deleted":
        issues.append("RDF graph delete receipt missing")
    if lifecycle.get("readAfterDeleteBlocked") is not True:
        issues.append("RDF graph read after delete must be blocked")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build host-owned RDF/SHACL persistence receipts for just-chill.")
    parser.add_argument("statement", nargs="?", default="Remember that concise Korean status updates are preferred.")
    parser.add_argument("--store-root", help="Store root for the MCP server. Defaults to a temporary directory.")
    parser.add_argument("--server-script", default=str(default_server_script()), help="Path to just_chill_hermes_memory_mcp.py")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    if args.store_root:
        receipt = build_rdf_persistence_receipt(
            statement=args.statement,
            store_root=Path(args.store_root).expanduser().resolve(),
            server_script=Path(args.server_script).expanduser().resolve(),
        )
        print(json_text(receipt, pretty=args.pretty))
        return 0 if not receipt.get("validationIssues") else 1

    with tempfile.TemporaryDirectory(prefix="just-chill-rdf-persistence-") as tmp:
        receipt = build_rdf_persistence_receipt(
            statement=args.statement,
            store_root=Path(tmp).resolve(),
            server_script=Path(args.server_script).expanduser().resolve(),
        )
        print(json_text(receipt, pretty=args.pretty))
        return 0 if not receipt.get("validationIssues") else 1


if __name__ == "__main__":
    raise SystemExit(main())
