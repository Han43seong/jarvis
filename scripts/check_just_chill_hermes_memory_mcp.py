#!/usr/bin/env python3
"""Acceptance checks for the host-owned just-chill Hermes memory MCP API."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

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
    MemoryApiError,
    call_tool,
    handle_mcp_request,
    raw_paths,
    sha256_text,
    tool_names,
    rdf_paths,
    vector_paths,
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
    except MemoryApiError as exc:
        require_in(name, expected, str(exc))
        return
    raise AssertionError(f"{name}: expected MemoryApiError")


cases: list[str] = []

required_tools = {
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
require("tool manifest", required_tools.issubset(set(tool_names())), True)
cases.append("tool-manifest")

with TemporaryDirectory() as temp_root:
    content = "Hermes owns canonical raw artifacts."
    raw_args = {
        "recordId": "raw_test_001",
        "content": content,
        "contentHash": sha256_text(content),
        "sensitivity": "internal",
        "provenance": {"source": "check"},
    }
    created = call_tool(TOOL_RAW_CREATE, raw_args, root=temp_root)
    require("raw create api", created["api"], TOOL_RAW_CREATE)
    require("raw create authority", created["storageAuthority"], "Hermes")
    require("raw create hash", created["contentHash"], sha256_text(content))
    raw_meta_path, raw_content_path = raw_paths(Path(temp_root), "raw_test_001")
    require("raw content payload exists", raw_content_path.exists(), True)

    read = call_tool(TOOL_RAW_READ, {"recordId": "raw_test_001"}, root=temp_root)
    require("raw read api", read["api"], TOOL_RAW_READ)
    require("raw read no content", "content" in read, False)
    read_content = call_tool(TOOL_RAW_READ, {"recordId": "raw_test_001", "includeContent": True}, root=temp_root)
    require("raw read content", read_content["content"], content)

    require_raises(
        "raw duplicate blocked",
        "raw artifact already exists",
        lambda: call_tool(TOOL_RAW_CREATE, raw_args, root=temp_root),
    )
    require_raises(
        "raw hash mismatch blocked",
        "hash mismatch",
        lambda: call_tool(TOOL_RAW_CREATE, {**raw_args, "recordId": "raw_bad_hash", "contentHash": "sha256:bad"}, root=temp_root),
    )
    require_raises(
        "sensitive raw approval blocked",
        "approvalToken",
        lambda: call_tool(TOOL_RAW_CREATE, {**raw_args, "recordId": "raw_sensitive", "sensitivity": "sensitive"}, root=temp_root),
    )
    sensitive_created = call_tool(
        TOOL_RAW_CREATE,
        {**raw_args, "recordId": "raw_sensitive_approved", "sensitivity": "sensitive", "approvalToken": "approved"},
        root=temp_root,
    )
    require("sensitive raw created", sensitive_created["sensitivity"], "sensitive")
    require_raises(
        "sensitive raw read approval blocked",
        "approvalToken",
        lambda: call_tool(TOOL_RAW_READ, {"recordId": "raw_sensitive_approved", "includeContent": True}, root=temp_root),
    )
    require_raises(
        "raw delete approval blocked",
        "approvalToken",
        lambda: call_tool(TOOL_RAW_DELETE, {"recordId": "raw_test_001", "reason": "cleanup"}, root=temp_root),
    )
    deleted = call_tool(TOOL_RAW_DELETE, {"recordId": "raw_test_001", "reason": "cleanup", "approvalToken": "approved"}, root=temp_root)
    require("raw deleted", deleted["status"], "deleted")
    require("raw content payload removed", raw_content_path.exists(), False)
    raw_status = call_tool(TOOL_STATUS, {}, root=temp_root)
    require("status excludes deleted raw metadata", raw_status["counts"]["raw"], 1)
    require_raises(
        "raw double delete blocked",
        "raw artifact is not active",
        lambda: call_tool(TOOL_RAW_DELETE, {"recordId": "raw_test_001", "reason": "cleanup again", "approvalToken": "approved"}, root=temp_root),
    )
    cases.append("raw-lifecycle")

with TemporaryDirectory() as temp_root:
    turtle = "@prefix jc: <https://just-chill.local/ontology#> .\n<urn:test> jc:statement \"ok\" .\n"
    rdf_args = {
        "sourceCandidateId": "urn:just-chill:memory:test_candidate",
        "sourceContractHash": "sha256:" + "a" * 64,
        "turtle": turtle,
        "turtleSha256": sha256_text(turtle),
        "shapesTurtleSha256": "sha256:" + "b" * 64,
        "shaclResult": {"conforms": True, "engine": "pyshacl-test"},
    }
    graph = call_tool(TOOL_RDF_CREATE, rdf_args, root=temp_root)
    require("rdf create api", graph["api"], TOOL_RDF_CREATE)
    require("rdf graph id default", graph["graphId"], rdf_args["sourceCandidateId"])
    require("rdf hash", graph["turtleSha256"], sha256_text(turtle))
    rdf_meta_path, rdf_turtle_path = rdf_paths(Path(temp_root), rdf_args["sourceCandidateId"])
    require("rdf turtle payload exists", rdf_turtle_path.exists(), True)

    read_graph = call_tool(TOOL_RDF_READ, {"sourceCandidateId": rdf_args["sourceCandidateId"]}, root=temp_root)
    require("rdf read api", read_graph["api"], TOOL_RDF_READ)
    require("rdf read no turtle", "turtle" in read_graph, False)

    require_raises(
        "rdf shacl blocked",
        "conforming live SHACL result is required",
        lambda: call_tool(TOOL_RDF_CREATE, {**rdf_args, "graphId": "bad_shacl", "shaclResult": {"conforms": False}}, root=temp_root),
    )
    require_raises(
        "rdf hash mismatch blocked",
        "hash mismatch",
        lambda: call_tool(TOOL_RDF_CREATE, {**rdf_args, "graphId": "bad_hash", "turtleSha256": "sha256:bad"}, root=temp_root),
    )
    require_raises(
        "rdf source contract hash format blocked",
        "sourceContractHash",
        lambda: call_tool(TOOL_RDF_CREATE, {**rdf_args, "graphId": "bad_contract_hash", "sourceContractHash": "not-a-sha"}, root=temp_root),
    )
    require_raises(
        "rdf shapes hash format blocked",
        "shapesTurtleSha256",
        lambda: call_tool(TOOL_RDF_CREATE, {**rdf_args, "graphId": "bad_shapes_hash", "shapesTurtleSha256": "sha256:bad"}, root=temp_root),
    )
    require_raises(
        "sensitive rdf approval blocked",
        "approvalToken",
        lambda: call_tool(TOOL_RDF_CREATE, {**rdf_args, "graphId": "bad_sensitive_rdf", "sensitiveRdfDetected": True}, root=temp_root),
    )
    require_raises(
        "rdf delete approval blocked",
        "approvalToken",
        lambda: call_tool(TOOL_RDF_DELETE, {"sourceCandidateId": rdf_args["sourceCandidateId"], "reason": "cleanup"}, root=temp_root),
    )
    deleted_graph = call_tool(TOOL_RDF_DELETE, {"sourceCandidateId": rdf_args["sourceCandidateId"], "reason": "cleanup", "approvalToken": "approved"}, root=temp_root)
    require("rdf deleted", deleted_graph["status"], "deleted")
    require("rdf turtle payload removed", rdf_turtle_path.exists(), False)
    require_raises(
        "rdf double delete blocked",
        "RDF graph is not active",
        lambda: call_tool(TOOL_RDF_DELETE, {"sourceCandidateId": rdf_args["sourceCandidateId"], "reason": "cleanup again", "approvalToken": "approved"}, root=temp_root),
    )
    cases.append("rdf-lifecycle")

with TemporaryDirectory() as temp_root:
    source_hash = sha256_text("canonical summary memory")
    text_hash = sha256_text("development routes to GJC")
    vector_hash = sha256_text("host-owned-vector-payload")
    vector_args = {
        "sidecarId": "vector_test_001",
        "canonicalSourceId": "summary_test_001",
        "sourceKind": "summary-memory",
        "canonicalContentHash": source_hash,
        "observedContentHash": source_hash,
        "readBackHashMatches": True,
        "receiptRef": "host-hermes-receipt://summary-test-001",
        "textHash": text_hash,
        "vectorHash": vector_hash,
        "embeddingModel": "local-test-embedding",
        "embeddingDimensions": 384,
        "sensitivity": "internal",
        "deletionState": "active",
        "redactionState": "not_redacted",
        "accessPolicy": {"scope": "private-user"},
        "provenance": {"source": "check"},
    }
    vector_created = call_tool(TOOL_VECTOR_CREATE, vector_args, root=temp_root)
    require("vector create api", vector_created["api"], TOOL_VECTOR_CREATE)
    require("vector create sidecar authority", vector_created["sidecarAuthority"], "host-vector-sidecar")
    vector_meta_path, _vector_search_path = vector_paths(Path(temp_root), "vector_test_001")
    require("vector metadata exists", vector_meta_path.exists(), True)
    require_raises(
        "vector duplicate blocked",
        "vector sidecar already exists",
        lambda: call_tool(TOOL_VECTOR_CREATE, vector_args, root=temp_root),
    )

    vector_read = call_tool(TOOL_VECTOR_READ, {"sidecarId": "vector_test_001"}, root=temp_root)
    require("vector read api", vector_read["api"], TOOL_VECTOR_READ)
    require("vector read hash", vector_read["vectorHash"], vector_hash)

    vector_search = call_tool(TOOL_VECTOR_SEARCH, {"queryTextHash": text_hash, "requestedScope": "private-user"}, root=temp_root)
    require("vector search api", vector_search["api"], TOOL_VECTOR_SEARCH)
    require("vector search result count", len(vector_search["results"]), 1)
    require("vector retrieval provider", vector_search["results"][0]["provider"], "host-vector-sidecar")
    require("vector retrieval kind", vector_search["results"][0]["retrievalKind"], "host-vector-sidecar-search-result")
    vector_search_log = Path(temp_root) / "vector" / "search-receipts.jsonl"
    require("vector search receipt log exists", vector_search_log.exists(), True)
    vector_search_log_text = vector_search_log.read_text(encoding="utf-8")
    require_in("vector search receipt api", TOOL_VECTOR_SEARCH, vector_search_log_text)
    require_in("vector search receipt sidecar", "vector_test_001", vector_search_log_text)
    vector_by_source = call_tool(TOOL_VECTOR_SEARCH, {"canonicalSourceId": "summary_test_001", "requestedScope": "private-user"}, root=temp_root)
    require("vector canonical-source search result count", len(vector_by_source["results"]), 1)
    require("vector canonical-source match kind", vector_by_source["results"][0]["matchKind"], "canonical-source-id")
    vector_wrong_scope = call_tool(TOOL_VECTOR_SEARCH, {"queryTextHash": text_hash, "requestedScope": "workspace"}, root=temp_root)
    require("vector wrong-scope search hidden", len(vector_wrong_scope["results"]), 0)
    vector_no_match = call_tool(TOOL_VECTOR_SEARCH, {"queryTextHash": sha256_text("not indexed"), "requestedScope": "private-user"}, root=temp_root)
    require("vector no-match search empty", len(vector_no_match["results"]), 0)

    require_raises(
        "vector missing query blocked",
        "queryTextHash or canonicalSourceId is required",
        lambda: call_tool(TOOL_VECTOR_SEARCH, {}, root=temp_root),
    )
    require_raises(
        "vector hash mismatch blocked",
        "read-back hash must match",
        lambda: call_tool(TOOL_VECTOR_CREATE, {**vector_args, "sidecarId": "vector_bad_hash", "observedContentHash": "sha256:" + "0" * 64}, root=temp_root),
    )
    require_raises(
        "vector sensitive approval blocked",
        "approvalToken",
        lambda: call_tool(TOOL_VECTOR_CREATE, {**vector_args, "sidecarId": "vector_sensitive", "sensitivity": "sensitive"}, root=temp_root),
    )
    sensitive_text_hash = sha256_text("sensitive vector text")
    sensitive_vector_hash = sha256_text("sensitive vector payload")
    sensitive_vector = call_tool(
        TOOL_VECTOR_CREATE,
        {
            **vector_args,
            "sidecarId": "vector_sensitive_approved",
            "canonicalSourceId": "summary_sensitive_001",
            "textHash": sensitive_text_hash,
            "vectorHash": sensitive_vector_hash,
            "sensitivity": "sensitive",
            "approvalToken": "approved",
        },
        root=temp_root,
    )
    require("sensitive vector create approved", sensitive_vector["status"], "active")
    require_raises(
        "sensitive vector read approval blocked",
        "approvalToken",
        lambda: call_tool(TOOL_VECTOR_READ, {"sidecarId": "vector_sensitive_approved"}, root=temp_root),
    )
    sensitive_vector_read = call_tool(TOOL_VECTOR_READ, {"sidecarId": "vector_sensitive_approved", "approvalToken": "approved"}, root=temp_root)
    require("sensitive vector read approved", sensitive_vector_read["vectorHash"], sensitive_vector_hash)
    sensitive_search_without = call_tool(TOOL_VECTOR_SEARCH, {"queryTextHash": sensitive_text_hash, "requestedScope": "private-user"}, root=temp_root)
    require("sensitive vector hidden without approval", len(sensitive_search_without["results"]), 0)
    sensitive_search_with = call_tool(TOOL_VECTOR_SEARCH, {"queryTextHash": sensitive_text_hash, "requestedScope": "private-user", "approvalToken": "approved"}, root=temp_root)
    require("sensitive vector search approved", len(sensitive_search_with["results"]), 1)
    require_raises(
        "vector deleted source blocked",
        "deleted canonical source cannot be indexed",
        lambda: call_tool(TOOL_VECTOR_CREATE, {**vector_args, "sidecarId": "vector_deleted", "deletionState": "deleted"}, root=temp_root),
    )
    require_raises(
        "vector redacted source blocked",
        "redacted canonical source cannot be indexed",
        lambda: call_tool(TOOL_VECTOR_CREATE, {**vector_args, "sidecarId": "vector_redacted", "redactionState": "redacted"}, root=temp_root),
    )
    require_raises(
        "vector missing scope blocked",
        "accessPolicy.scope",
        lambda: call_tool(TOOL_VECTOR_CREATE, {**vector_args, "sidecarId": "vector_no_scope", "accessPolicy": {}}, root=temp_root),
    )
    require_raises(
        "vector delete approval blocked",
        "approvalToken",
        lambda: call_tool(TOOL_VECTOR_DELETE, {"sidecarId": "vector_test_001", "reason": "cleanup"}, root=temp_root),
    )
    vector_deleted = call_tool(TOOL_VECTOR_DELETE, {"sidecarId": "vector_test_001", "reason": "cleanup", "approvalToken": "approved"}, root=temp_root)
    sensitive_vector_deleted = call_tool(TOOL_VECTOR_DELETE, {"sidecarId": "vector_sensitive_approved", "reason": "cleanup", "approvalToken": "approved"}, root=temp_root)
    require("sensitive vector deleted", sensitive_vector_deleted["status"], "deleted")
    require("vector deleted", vector_deleted["status"], "deleted")
    require_raises(
        "vector read after delete blocked",
        "vector sidecar is not active",
        lambda: call_tool(TOOL_VECTOR_READ, {"sidecarId": "vector_test_001"}, root=temp_root),
    )
    vector_status = call_tool(TOOL_STATUS, {}, root=temp_root)
    require("status excludes deleted vector metadata", vector_status["counts"]["vector"], 0)
    cases.append("vector-lifecycle")

with TemporaryDirectory() as temp_root:
    init_response = handle_mcp_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}, temp_root)
    require("mcp initialize", init_response["result"]["serverInfo"]["name"], "just-chill-hermes-memory-api")
    tools_response = handle_mcp_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, temp_root)
    require("mcp tools listed", required_tools.issubset({tool["name"] for tool in tools_response["result"]["tools"]}), True)
    call_response = handle_mcp_request({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": TOOL_STATUS, "arguments": {}}}, temp_root)
    payload = json.loads(call_response["result"]["content"][0]["text"])
    require("mcp status tool", payload["server"], "just-chill-hermes-memory-api")
    cases.append("mcp-jsonrpc")
    error_response = handle_mcp_request({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": TOOL_RDF_READ, "arguments": {"sourceCandidateId": "missing"}}}, temp_root)
    require("mcp error id preserved", error_response["id"], 4)
    require("mcp tool error flag", error_response["result"]["isError"], True)

print(f"PASS: {len(cases)} just-chill Hermes memory MCP cases passed")
