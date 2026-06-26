#!/usr/bin/env python3
"""Host-owned MCP lifecycle receipt runner for just-chill Hermes memory APIs.

This module exercises the registered `just_chill_memory_api` stdio MCP server
through JSON-RPC and records deterministic raw-artifact / RDF-graph lifecycle
receipts. It is intentionally host-owned: just-chill may consume the receipts as
evidence, but just-chill does not call Hermes storage tools directly.
"""
from __future__ import annotations

import argparse
import json
import selectors
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from just_chill_hermes_memory_mcp import (
    TOOL_RAW_CREATE,
    TOOL_RAW_DELETE,
    TOOL_RAW_READ,
    TOOL_RDF_CREATE,
    TOOL_RDF_DELETE,
    TOOL_RDF_READ,
    TOOL_VECTOR_CREATE,
    TOOL_VECTOR_DELETE,
    TOOL_VECTOR_READ,
    TOOL_VECTOR_SEARCH,
    TOOL_STATUS,
    sha256_text,
)

SCHEMA_VERSION = 1
RECEIPT_KIND = "just-chill-hermes-mcp-lifecycle-receipt-v1"
SERVER_NAME = "just_chill_memory_api"
REQUIRED_TOOLS = {
    TOOL_RAW_CREATE,
    TOOL_RAW_READ,
    TOOL_RAW_DELETE,
    TOOL_RDF_CREATE,
    TOOL_RDF_READ,
    TOOL_RDF_DELETE,
    TOOL_VECTOR_CREATE,
    TOOL_VECTOR_SEARCH,
    TOOL_VECTOR_READ,
    TOOL_VECTOR_DELETE,
    TOOL_STATUS,
}


class McpInvocationError(RuntimeError):
    """Raised when the host-owned MCP runner cannot produce a valid receipt."""


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def json_text(data: Any, *, pretty: bool = False) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2 if pretty else None, sort_keys=True)


def default_server_script() -> Path:
    return Path(__file__).with_name("just_chill_hermes_memory_mcp.py")


def read_tool_payload(response: dict[str, Any]) -> dict[str, Any]:
    result = response.get("result")
    if not isinstance(result, dict):
        raise McpInvocationError(f"invalid MCP response result: {response}")
    content = result.get("content")
    if not isinstance(content, list) or not content:
        raise McpInvocationError(f"invalid MCP tool content: {response}")
    text = content[0].get("text") if isinstance(content[0], dict) else None
    if not isinstance(text, str):
        raise McpInvocationError(f"invalid MCP tool text: {response}")
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise McpInvocationError(f"invalid MCP tool payload: {response}")
    payload["_mcpIsError"] = bool(result.get("isError"))
    return payload


class StdioMcpClient:
    def __init__(self, server_script: Path, store_root: Path, *, timeout: float = 5.0) -> None:
        self.server_script = server_script
        self.store_root = store_root
        self.timeout = timeout
        self.next_id = 1
        self.process: subprocess.Popen[str] | None = None
        self.selector: selectors.DefaultSelector | None = None

    def __enter__(self) -> "StdioMcpClient":
        argv = [sys.executable, str(self.server_script), "--store-root", str(self.store_root), "--serve"]
        self.process = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(self.server_script.parent),
        )
        if self.process.stdout is None:
            raise McpInvocationError("MCP server stdout is unavailable")
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        if self.selector:
            self.selector.close()
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.process or not self.process.stdin or not self.process.stdout or not self.selector:
            raise McpInvocationError("MCP client is not started")
        request_id = self.next_id
        self.next_id += 1
        message = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}
        self.process.stdin.write(json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n")
        self.process.stdin.flush()
        events = self.selector.select(self.timeout)
        if not events:
            stderr = self.process.stderr.read() if self.process.stderr and self.process.poll() is not None else ""
            raise McpInvocationError(f"MCP request timed out for {method}; stderr={stderr}")
        line = self.process.stdout.readline()
        if not line:
            stderr = self.process.stderr.read() if self.process.stderr else ""
            raise McpInvocationError(f"MCP server closed before response for {method}; stderr={stderr}")
        response = json.loads(line)
        if response.get("id") != request_id:
            raise McpInvocationError(f"MCP request id mismatch: expected {request_id}, got {response.get('id')}")
        return response

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.request("tools/call", {"name": name, "arguments": arguments})


def hermes_registration_status() -> dict[str, Any]:
    try:
        proc = subprocess.run(["hermes", "mcp", "list"], text=True, capture_output=True, timeout=10, check=False)
    except FileNotFoundError:
        return {"checked": True, "available": False, "configured": False, "reason": "hermes command not found"}
    configured = SERVER_NAME in proc.stdout and "enabled" in proc.stdout.lower()
    return {
        "checked": True,
        "available": proc.returncode == 0,
        "configured": configured,
        "exitCode": proc.returncode,
        "stdoutPreview": proc.stdout.strip()[:500],
    }


def build_lifecycle_receipt(
    *,
    store_root: Path,
    server_script: Path | None = None,
    require_registration: bool = False,
    timeout: float = 5.0,
) -> dict[str, Any]:
    server_script = server_script or default_server_script()
    registration = hermes_registration_status()
    if require_registration and not registration.get("configured"):
        raise McpInvocationError("Hermes MCP server just_chill_memory_api is not configured/enabled")

    raw_content = "Host-owned raw artifact lifecycle receipt."
    raw_hash = sha256_text(raw_content)
    turtle = "@prefix jc: <https://just-chill.local/ontology#> .\n<urn:receipt> jc:statement \"ok\" .\n"
    turtle_hash = sha256_text(turtle)
    source_contract_hash = sha256_text("receipt-source-contract")
    shapes_hash = sha256_text("receipt-shapes")

    receipt: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "receiptKind": RECEIPT_KIND,
        "executionOwner": "host-hermes-mcp-runner",
        "storageAuthority": "Hermes",
        "justChillCallsHermes": False,
        "justChillExecutionAllowedHere": False,
        "server": {
            "name": SERVER_NAME,
            "script": str(server_script),
            "transport": "stdio-jsonrpc",
            "storeRoot": str(store_root),
            "registration": registration,
        },
        "toolManifest": {},
        "rawArtifactLifecycle": {},
        "rdfGraphLifecycle": {},
        "vectorSidecarLifecycle": {},
        "negativeChecks": {},
        "validationIssues": [],
    }

    with StdioMcpClient(server_script, store_root, timeout=timeout) as client:
        initialize = client.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "just-chill-host-receipt-runner", "version": "1.0"}})
        tools_response = client.request("tools/list")
        tool_names = sorted(tool.get("name") for tool in tools_response.get("result", {}).get("tools", []) if isinstance(tool, dict))
        missing_tools = sorted(REQUIRED_TOOLS.difference(tool_names))
        receipt["toolManifest"] = {
            "initializeServer": initialize.get("result", {}).get("serverInfo", {}),
            "tools": tool_names,
            "missingTools": missing_tools,
        }
        if missing_tools:
            receipt["validationIssues"].append(f"missing required tools: {missing_tools}")
            return receipt

        raw_create = read_tool_payload(client.call_tool(TOOL_RAW_CREATE, {
            "recordId": "receipt_raw_001",
            "content": raw_content,
            "contentHash": raw_hash,
            "sensitivity": "internal",
            "provenance": {"source": "just-chill-host-receipt-runner"},
        }))
        raw_read = read_tool_payload(client.call_tool(TOOL_RAW_READ, {"recordId": "receipt_raw_001", "includeContent": True}))
        raw_delete = read_tool_payload(client.call_tool(TOOL_RAW_DELETE, {"recordId": "receipt_raw_001", "reason": "receipt lifecycle cleanup", "approvalToken": "host-approved"}))
        raw_read_after_delete = read_tool_payload(client.call_tool(TOOL_RAW_READ, {"recordId": "receipt_raw_001", "includeContent": True}))
        receipt["rawArtifactLifecycle"] = {
            "recordId": "receipt_raw_001",
            "expectedContentHash": raw_hash,
            "create": raw_create,
            "readBack": {k: raw_read.get(k) for k in ["api", "recordId", "contentHash", "status", "_mcpIsError"]},
            "readBackHashMatches": raw_read.get("contentHash") == raw_hash and raw_read.get("content") == raw_content,
            "delete": raw_delete,
            "readAfterDelete": raw_read_after_delete,
            "readAfterDeleteBlocked": raw_read_after_delete.get("_mcpIsError") is True,
        }

        rdf_create = read_tool_payload(client.call_tool(TOOL_RDF_CREATE, {
            "graphId": "receipt_rdf_001",
            "sourceCandidateId": "receipt_rdf_candidate_001",
            "sourceContractHash": source_contract_hash,
            "turtle": turtle,
            "turtleSha256": turtle_hash,
            "shapesTurtleSha256": shapes_hash,
            "shaclResult": {"conforms": True, "engine": "host-owned-receipt-fixture", "evidenceKind": "test-only"},
            "metadata": {"source": "just-chill-host-receipt-runner"},
        }))
        rdf_read = read_tool_payload(client.call_tool(TOOL_RDF_READ, {"graphId": "receipt_rdf_001", "includeTurtle": True}))
        rdf_delete = read_tool_payload(client.call_tool(TOOL_RDF_DELETE, {"graphId": "receipt_rdf_001", "reason": "receipt lifecycle cleanup", "approvalToken": "host-approved"}))
        rdf_read_after_delete = read_tool_payload(client.call_tool(TOOL_RDF_READ, {"graphId": "receipt_rdf_001", "includeTurtle": True}))
        receipt["rdfGraphLifecycle"] = {
            "graphId": "receipt_rdf_001",
            "expectedTurtleSha256": turtle_hash,
            "sourceContractHash": source_contract_hash,
            "shaclEvidenceKind": "host-asserted-test-only",
            "create": rdf_create,
            "readBack": {k: rdf_read.get(k) for k in ["api", "graphId", "sourceCandidateId", "sourceContractHash", "turtleSha256", "status", "_mcpIsError"]},
            "readBackHashMatches": rdf_read.get("turtleSha256") == turtle_hash and rdf_read.get("turtle") == turtle,
            "delete": rdf_delete,
            "readAfterDelete": rdf_read_after_delete,
            "readAfterDeleteBlocked": rdf_read_after_delete.get("_mcpIsError") is True,
        }

        source_hash = sha256_text("receipt canonical summary")
        text_hash = sha256_text("receipt vector search text")
        vector_hash = sha256_text("receipt vector payload")
        vector_create = read_tool_payload(client.call_tool(TOOL_VECTOR_CREATE, {
            "sidecarId": "receipt_vector_001",
            "canonicalSourceId": "receipt_summary_001",
            "sourceKind": "summary-memory",
            "canonicalContentHash": source_hash,
            "observedContentHash": source_hash,
            "readBackHashMatches": True,
            "receiptRef": "host-hermes-receipt://receipt-summary-001",
            "textHash": text_hash,
            "vectorHash": vector_hash,
            "embeddingModel": "local-test-embedding",
            "embeddingDimensions": 384,
            "sensitivity": "internal",
            "deletionState": "active",
            "redactionState": "not_redacted",
            "accessPolicy": {"scope": "private-user"},
            "provenance": {"source": "just-chill-host-receipt-runner"},
        }))
        vector_read = read_tool_payload(client.call_tool(TOOL_VECTOR_READ, {"sidecarId": "receipt_vector_001"}))
        vector_search = read_tool_payload(client.call_tool(TOOL_VECTOR_SEARCH, {"queryTextHash": text_hash, "requestedScope": "private-user"}))
        search_receipt_path = store_root / "vector" / "search-receipts.jsonl"
        search_receipt_text = search_receipt_path.read_text(encoding="utf-8") if search_receipt_path.exists() else ""
        search_receipt_recorded = (
            TOOL_VECTOR_SEARCH in search_receipt_text
            and "receipt_vector_001" in search_receipt_text
            and text_hash in search_receipt_text
        )
        vector_delete = read_tool_payload(client.call_tool(TOOL_VECTOR_DELETE, {"sidecarId": "receipt_vector_001", "reason": "receipt lifecycle cleanup", "approvalToken": "host-approved"}))
        vector_read_after_delete = read_tool_payload(client.call_tool(TOOL_VECTOR_READ, {"sidecarId": "receipt_vector_001"}))
        receipt["vectorSidecarLifecycle"] = {
            "sidecarId": "receipt_vector_001",
            "expectedTextHash": text_hash,
            "expectedVectorHash": vector_hash,
            "expectedSourceHash": source_hash,
            "create": vector_create,
            "readBack": {k: vector_read.get(k) for k in ["api", "sidecarId", "canonicalSourceId", "observedContentHash", "textHash", "vectorHash", "status", "_mcpIsError"]},
            "readBackHashMatches": (
                vector_read.get("observedContentHash") == source_hash
                and vector_read.get("textHash") == text_hash
                and vector_read.get("vectorHash") == vector_hash
            ),
            "search": vector_search,
            "searchReceiptRecorded": search_receipt_recorded,
            "searchReceiptLineCount": len([line for line in search_receipt_text.splitlines() if line.strip()]),
            "searchReturnedCandidate": bool(vector_search.get("results")) and vector_search["results"][0].get("resultId") == "receipt_vector_001",
            "delete": vector_delete,
            "readAfterDelete": vector_read_after_delete,
            "readAfterDeleteBlocked": vector_read_after_delete.get("_mcpIsError") is True,
        }

        sensitive_raw = read_tool_payload(client.call_tool(TOOL_RAW_CREATE, {
            "recordId": "receipt_sensitive_raw_blocked",
            "content": raw_content,
            "contentHash": raw_hash,
            "sensitivity": "sensitive",
        }))
        hash_mismatch = read_tool_payload(client.call_tool(TOOL_RAW_CREATE, {
            "recordId": "receipt_hash_mismatch_blocked",
            "content": raw_content,
            "contentHash": "sha256:" + "0" * 64,
        }))
        sensitive_rdf = read_tool_payload(client.call_tool(TOOL_RDF_CREATE, {
            "graphId": "receipt_sensitive_rdf_blocked",
            "sourceCandidateId": "receipt_sensitive_rdf_candidate",
            "sourceContractHash": source_contract_hash,
            "turtle": turtle,
            "turtleSha256": turtle_hash,
            "shaclResult": {"conforms": True},
            "sensitiveRdfDetected": True,
        }))
        sensitive_vector = read_tool_payload(client.call_tool(TOOL_VECTOR_CREATE, {
            "sidecarId": "receipt_sensitive_vector_blocked",
            "canonicalSourceId": "receipt_sensitive_summary",
            "sourceKind": "summary-memory",
            "canonicalContentHash": source_hash,
            "observedContentHash": source_hash,
            "readBackHashMatches": True,
            "receiptRef": "host-hermes-receipt://receipt-sensitive-summary",
            "textHash": text_hash,
            "vectorHash": vector_hash,
            "embeddingModel": "local-test-embedding",
            "embeddingDimensions": 384,
            "sensitivity": "sensitive",
            "accessPolicy": {"scope": "private-user"},
        }))
        deleted_vector_source = read_tool_payload(client.call_tool(TOOL_VECTOR_CREATE, {
            "sidecarId": "receipt_deleted_vector_source_blocked",
            "canonicalSourceId": "receipt_deleted_summary",
            "sourceKind": "summary-memory",
            "canonicalContentHash": source_hash,
            "observedContentHash": source_hash,
            "readBackHashMatches": True,
            "receiptRef": "host-hermes-receipt://receipt-deleted-summary",
            "textHash": text_hash,
            "vectorHash": vector_hash,
            "embeddingModel": "local-test-embedding",
            "embeddingDimensions": 384,
            "deletionState": "deleted",
            "accessPolicy": {"scope": "private-user"},
        }))
        redacted_vector_source = read_tool_payload(client.call_tool(TOOL_VECTOR_CREATE, {
            "sidecarId": "receipt_redacted_vector_source_blocked",
            "canonicalSourceId": "receipt_redacted_summary",
            "sourceKind": "summary-memory",
            "canonicalContentHash": source_hash,
            "observedContentHash": source_hash,
            "readBackHashMatches": True,
            "receiptRef": "host-hermes-receipt://receipt-redacted-summary",
            "textHash": text_hash,
            "vectorHash": vector_hash,
            "embeddingModel": "local-test-embedding",
            "embeddingDimensions": 384,
            "redactionState": "redacted",
            "accessPolicy": {"scope": "private-user"},
        }))
        status_after = read_tool_payload(client.call_tool(TOOL_STATUS, {}))
        receipt["negativeChecks"] = {
            "sensitiveRawCreateWithoutApprovalBlocked": sensitive_raw.get("_mcpIsError") is True,
            "hashMismatchBlocked": hash_mismatch.get("_mcpIsError") is True,
            "sensitiveRdfCreateWithoutApprovalBlocked": sensitive_rdf.get("_mcpIsError") is True,
            "sensitiveVectorCreateWithoutApprovalBlocked": sensitive_vector.get("_mcpIsError") is True,
            "deletedVectorSourceBlocked": deleted_vector_source.get("_mcpIsError") is True,
            "redactedVectorSourceBlocked": redacted_vector_source.get("_mcpIsError") is True,
            "toolErrors": {
                "sensitiveRaw": sensitive_raw,
                "hashMismatch": hash_mismatch,
                "sensitiveRdf": sensitive_rdf,
                "sensitiveVector": sensitive_vector,
                "deletedVectorSource": deleted_vector_source,
                "redactedVectorSource": redacted_vector_source,
            },
        }
        receipt["statusAfterLifecycle"] = status_after

    receipt["validationIssues"] = validate_lifecycle_receipt(receipt)
    return receipt


def validate_lifecycle_receipt(receipt: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if receipt.get("receiptKind") != RECEIPT_KIND:
        issues.append("unexpected receipt kind")
    if receipt.get("executionOwner") != "host-hermes-mcp-runner":
        issues.append("execution owner must be host-hermes-mcp-runner")
    if receipt.get("justChillCallsHermes") is not False:
        issues.append("just-chill must not call Hermes in this receipt")
    if receipt.get("justChillExecutionAllowedHere") is not False:
        issues.append("just-chill execution must not be allowed in this receipt")
    missing_tools = receipt.get("toolManifest", {}).get("missingTools", [])
    if missing_tools:
        issues.append(f"missing required MCP tools: {missing_tools}")
    raw = receipt.get("rawArtifactLifecycle", {})
    if raw.get("readBackHashMatches") is not True:
        issues.append("raw artifact read-back hash/content mismatch")
    if raw.get("delete", {}).get("status") != "deleted":
        issues.append("raw artifact delete receipt missing")
    if raw.get("readAfterDeleteBlocked") is not True:
        issues.append("raw artifact read after delete must be blocked")
    rdf = receipt.get("rdfGraphLifecycle", {})
    if rdf.get("readBackHashMatches") is not True:
        issues.append("RDF graph read-back hash/content mismatch")
    if rdf.get("delete", {}).get("status") != "deleted":
        issues.append("RDF graph delete receipt missing")
    if rdf.get("readAfterDeleteBlocked") is not True:
        issues.append("RDF graph read after delete must be blocked")
    vector = receipt.get("vectorSidecarLifecycle", {})
    if vector.get("readBackHashMatches") is not True:
        issues.append("vector sidecar read-back hash mismatch")
    if vector.get("searchReturnedCandidate") is not True:
        issues.append("vector sidecar search did not return candidate")
    if vector.get("searchReceiptRecorded") is not True:
        issues.append("vector sidecar search receipt was not durably recorded")
    if vector.get("delete", {}).get("status") != "deleted":
        issues.append("vector sidecar delete receipt missing")
    if vector.get("readAfterDeleteBlocked") is not True:
        issues.append("vector sidecar read after delete must be blocked")
    negative = receipt.get("negativeChecks", {})
    for key in [
        "sensitiveRawCreateWithoutApprovalBlocked",
        "hashMismatchBlocked",
        "sensitiveRdfCreateWithoutApprovalBlocked",
        "sensitiveVectorCreateWithoutApprovalBlocked",
        "deletedVectorSourceBlocked",
        "redactedVectorSourceBlocked",
    ]:
        if negative.get(key) is not True:
            issues.append(f"negative check failed: {key}")
    counts = receipt.get("statusAfterLifecycle", {}).get("counts", {})
    if counts.get("deletions", 0) < 3:
        issues.append("delete receipt count is missing raw/RDF/vector tombstones")
    if counts.get("raw") != 0:
        issues.append("raw active count must be zero after delete")
    if counts.get("rdf") != 0:
        issues.append("rdf active count must be zero after delete")
    if counts.get("vector") != 0:
        issues.append("vector active count must be zero after delete")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Exercise host-owned just-chill Hermes MCP lifecycle and emit receipts.")
    parser.add_argument("--store-root", help="Store root for the MCP server. Defaults to a temporary directory.")
    parser.add_argument("--server-script", default=str(default_server_script()), help="Path to just_chill_hermes_memory_mcp.py")
    parser.add_argument("--require-registration", action="store_true", help="Fail if hermes mcp list does not show just_chill_memory_api enabled.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    if args.store_root:
        receipt = build_lifecycle_receipt(
            store_root=Path(args.store_root).expanduser().resolve(),
            server_script=Path(args.server_script).expanduser().resolve(),
            require_registration=args.require_registration,
        )
        print(json_text(receipt, pretty=args.pretty))
        return 0 if not receipt.get("validationIssues") else 1

    with tempfile.TemporaryDirectory(prefix="just-chill-hermes-mcp-receipts-") as tmp:
        receipt = build_lifecycle_receipt(
            store_root=Path(tmp).resolve(),
            server_script=Path(args.server_script).expanduser().resolve(),
            require_registration=args.require_registration,
        )
        print(json_text(receipt, pretty=args.pretty))
        return 0 if not receipt.get("validationIssues") else 1


if __name__ == "__main__":
    raise SystemExit(main())
