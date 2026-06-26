#!/usr/bin/env python3
"""Host-owned Hermes MCP memory API for just-chill.

This server exposes live raw-artifact, RDF graph, and vector sidecar lifecycle tools through a
Hermes-compatible MCP stdio boundary. It is deliberately outside just-chill's
router/contract layer: just-chill may discover and plan against these tools, but
host/Hermes execution owns every create/search/read/delete call and every receipt.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
SERVER_NAME = "just-chill-hermes-memory-api"
SERVER_VERSION = "1.1.0"
DEFAULT_STORE_ROOT = "~/.local/share/jarvis/just-chill-hermes-memory-api"
TOOL_RAW_CREATE = "hermes.raw_artifact.create"
TOOL_RAW_READ = "hermes.raw_artifact.read"
TOOL_RAW_DELETE = "hermes.raw_artifact.delete"
TOOL_RDF_CREATE = "hermes.rdf_graph.create"
TOOL_RDF_READ = "hermes.rdf_graph.read"
TOOL_RDF_DELETE = "hermes.rdf_graph.delete"
TOOL_VECTOR_CREATE = "hermes.vector_sidecar.create"
TOOL_VECTOR_SEARCH = "hermes.vector_sidecar.search"
TOOL_VECTOR_READ = "hermes.vector_sidecar.read"
TOOL_VECTOR_DELETE = "hermes.vector_sidecar.delete"
TOOL_STATUS = "hermes.memory_api.status"
TOOL_NAMES = [
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
]
SAFE_ID = re.compile(r"^[A-Za-z0-9_.:#-]{1,256}$")


class MemoryApiError(ValueError):
    """Returned as an MCP tool error instead of crashing the server."""


def now_iso() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def require_safe_id(label: str, value: Any) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise MemoryApiError(f"{label} must be a stable safe identifier")
    return value


def require_sha256(label: str, value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        raise MemoryApiError(f"{label} must be sha256:<64 hex chars>")
    return value


def require_hash_match(label: str, content: str, expected: Any) -> str:
    if not isinstance(expected, str) or not expected.startswith("sha256:"):
        raise MemoryApiError(f"{label} hash must be sha256:<hex>")
    actual = sha256_text(content)
    if actual != expected:
        raise MemoryApiError(f"{label} hash mismatch: expected {expected}, got {actual}")
    return actual


def store_root(root: str | None = None) -> Path:
    selected = root or os.environ.get("JUST_CHILL_HERMES_MEMORY_STORE") or DEFAULT_STORE_ROOT
    return Path(selected).expanduser().resolve()


def ensure_store(root: Path) -> None:
    for child in ["raw", "rdf", "vector", "deletions"]:
        (root / child).mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise MemoryApiError("record not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise MemoryApiError("stored metadata is invalid")
    return data

def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(content, encoding="utf-8")
    os.replace(tmp_path, path)


def write_json(path: Path, data: dict[str, Any]) -> None:
    write_text_atomic(path, json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def raw_paths(root: Path, record_id: str) -> tuple[Path, Path]:
    digest = digest_id(record_id)
    return root / "raw" / f"{digest}.json", root / "raw" / f"{digest}.content"


def rdf_paths(root: Path, graph_id: str) -> tuple[Path, Path]:
    digest = digest_id(graph_id)
    return root / "rdf" / f"{digest}.json", root / "rdf" / f"{digest}.ttl"

def vector_paths(root: Path, sidecar_id: str) -> tuple[Path, Path]:
    digest = digest_id(sidecar_id)
    return root / "vector" / f"{digest}.json", root / "vector" / f"{digest}.search.jsonl"


def tombstone_path(root: Path, kind: str, item_id: str) -> Path:
    return root / "deletions" / f"{kind}-{digest_id(item_id)}-{now_iso().replace(':', '')}.json"


def tool_names() -> list[str]:
    return list(TOOL_NAMES)


def tool_manifest() -> list[dict[str, Any]]:
    string_schema = {"type": "string"}
    boolean_schema = {"type": "boolean"}
    object_schema = {"type": "object", "additionalProperties": True}
    return [
        {
            "name": TOOL_RAW_CREATE,
            "description": "Create a canonical Hermes raw artifact from host-supplied content and matching sha256 hash.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "recordId": string_schema,
                    "content": string_schema,
                    "contentHash": string_schema,
                    "sensitivity": string_schema,
                    "approvalToken": string_schema,
                    "provenance": object_schema,
                    "metadata": object_schema,
                },
                "required": ["recordId", "content", "contentHash"],
                "additionalProperties": False,
            },
        },
        {
            "name": TOOL_RAW_READ,
            "description": "Read raw artifact metadata and hash; content is opt-in and sensitive content requires approval.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "recordId": string_schema,
                    "includeContent": boolean_schema,
                    "approvalToken": string_schema,
                },
                "required": ["recordId"],
                "additionalProperties": False,
            },
        },
        {
            "name": TOOL_RAW_DELETE,
            "description": "Mark a raw artifact deleted and write a deletion receipt.",
            "inputSchema": {
                "type": "object",
                "properties": {"recordId": string_schema, "reason": string_schema, "approvalToken": string_schema},
                "required": ["recordId", "reason", "approvalToken"],
                "additionalProperties": False,
            },
        },
        {
            "name": TOOL_RDF_CREATE,
            "description": "Create a canonical Hermes RDF graph from Turtle text and matching sha256 hash after host SHACL validation.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "graphId": string_schema,
                    "sourceCandidateId": string_schema,
                    "sourceContractHash": string_schema,
                    "turtle": string_schema,
                    "turtleSha256": string_schema,
                    "shapesTurtleSha256": string_schema,
                    "shaclResult": object_schema,
                    "sensitiveRdfDetected": boolean_schema,
                    "approvalToken": string_schema,
                    "metadata": object_schema,
                },
                "required": ["sourceCandidateId", "sourceContractHash", "turtle", "turtleSha256", "shaclResult"],
                "additionalProperties": False,
            },
        },
        {
            "name": TOOL_RDF_READ,
            "description": "Read RDF graph metadata and hashes; Turtle text is opt-in.",
            "inputSchema": {
                "type": "object",
                "properties": {"graphId": string_schema, "sourceCandidateId": string_schema, "includeTurtle": boolean_schema},
                "additionalProperties": False,
            },
        },
        {
            "name": TOOL_RDF_DELETE,
            "description": "Mark an RDF graph deleted and write a deletion receipt.",
            "inputSchema": {
                "type": "object",
                "properties": {"graphId": string_schema, "sourceCandidateId": string_schema, "reason": string_schema, "approvalToken": string_schema},
                "required": ["reason", "approvalToken"],
                "additionalProperties": False,
            },
        },
        {
            "name": TOOL_VECTOR_CREATE,
            "description": "Create a host-owned vector sidecar record over a Hermes-canonical memory source without storing plaintext.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "sidecarId": string_schema,
                    "canonicalSourceId": string_schema,
                    "sourceKind": string_schema,
                    "canonicalContentHash": string_schema,
                    "observedContentHash": string_schema,
                    "readBackHashMatches": boolean_schema,
                    "receiptRef": string_schema,
                    "textHash": string_schema,
                    "vectorHash": string_schema,
                    "embeddingModel": string_schema,
                    "embeddingDimensions": {"type": "integer"},
                    "sensitivity": string_schema,
                    "approvalToken": string_schema,
                    "deletionState": string_schema,
                    "redactionState": string_schema,
                    "accessPolicy": object_schema,
                    "retention": object_schema,
                    "provenance": object_schema,
                    "metadata": object_schema,
                },
                "required": [
                    "sidecarId",
                    "canonicalSourceId",
                    "sourceKind",
                    "canonicalContentHash",
                    "observedContentHash",
                    "readBackHashMatches",
                    "receiptRef",
                    "textHash",
                    "vectorHash",
                    "embeddingModel",
                    "embeddingDimensions",
                ],
                "additionalProperties": False,
            },
        },
        {
            "name": TOOL_VECTOR_SEARCH,
            "description": "Search host-owned vector sidecar metadata by exact query hash or canonical source id and emit durable retrieval evidence.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "queryTextHash": string_schema,
                    "canonicalSourceId": string_schema,
                    "requestedScope": string_schema,
                    "minScore": {"type": "number"},
                    "approvalToken": string_schema,
                    "limit": {"type": "integer"},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": TOOL_VECTOR_READ,
            "description": "Read vector sidecar metadata; sensitive sidecar metadata requires approval.",
            "inputSchema": {
                "type": "object",
                "properties": {"sidecarId": string_schema, "approvalToken": string_schema},
                "required": ["sidecarId"],
                "additionalProperties": False,
            },
        },
        {
            "name": TOOL_VECTOR_DELETE,
            "description": "Mark a vector sidecar deleted and write a deletion receipt.",
            "inputSchema": {
                "type": "object",
                "properties": {"sidecarId": string_schema, "reason": string_schema, "approvalToken": string_schema},
                "required": ["sidecarId", "reason", "approvalToken"],
                "additionalProperties": False,
            },
        },
        {
            "name": TOOL_STATUS,
            "description": "Return store status, server version, and tool names without mutating storage.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    ]


def raw_create(args: dict[str, Any], root: Path) -> dict[str, Any]:
    record_id = require_safe_id("recordId", args.get("recordId"))
    content = args.get("content")
    if not isinstance(content, str):
        raise MemoryApiError("content is required")
    content_hash = require_hash_match("raw artifact content", content, args.get("contentHash"))
    sensitivity = args.get("sensitivity") or "internal"
    if sensitivity == "sensitive" and not args.get("approvalToken"):
        raise MemoryApiError("sensitive raw artifact create requires approvalToken")
    meta_path, content_path = raw_paths(root, record_id)
    if meta_path.exists():
        raise MemoryApiError("raw artifact already exists")
    metadata = {
        "schemaVersion": SCHEMA_VERSION,
        "api": TOOL_RAW_CREATE,
        "storageAuthority": "Hermes",
        "recordId": record_id,
        "contentHash": content_hash,
        "sensitivity": sensitivity,
        "status": "active",
        "createdAt": now_iso(),
        "provenance": args.get("provenance") or {},
        "metadata": args.get("metadata") or {},
        "contentPath": str(content_path),
    }
    write_text_atomic(content_path, content)
    write_json(meta_path, metadata)
    return {k: metadata[k] for k in ["schemaVersion", "api", "storageAuthority", "recordId", "contentHash", "sensitivity", "status", "createdAt"]}


def raw_read(args: dict[str, Any], root: Path) -> dict[str, Any]:
    record_id = require_safe_id("recordId", args.get("recordId"))
    meta_path, content_path = raw_paths(root, record_id)
    metadata = read_json(meta_path)
    if metadata.get("status") != "active":
        raise MemoryApiError("raw artifact is not active")
    include_content = bool(args.get("includeContent"))
    if include_content and metadata.get("sensitivity") == "sensitive" and not args.get("approvalToken"):
        raise MemoryApiError("sensitive raw artifact read requires approvalToken")
    result = {k: metadata.get(k) for k in ["schemaVersion", "storageAuthority", "recordId", "contentHash", "sensitivity", "status", "createdAt"]}
    result["api"] = TOOL_RAW_READ
    if include_content:
        result["content"] = content_path.read_text(encoding="utf-8")
    return result


def raw_delete(args: dict[str, Any], root: Path) -> dict[str, Any]:
    record_id = require_safe_id("recordId", args.get("recordId"))
    reason = args.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise MemoryApiError("delete reason is required")
    if not args.get("approvalToken"):
        raise MemoryApiError("raw artifact delete requires approvalToken")
    meta_path, content_path = raw_paths(root, record_id)
    metadata = read_json(meta_path)
    if metadata.get("status") != "active":
        raise MemoryApiError("raw artifact is not active")
    metadata["status"] = "deleted"
    metadata["deletedAt"] = now_iso()
    metadata["deleteReason"] = reason
    write_json(meta_path, metadata)
    if content_path.exists():
        content_path.unlink()
        metadata["payloadRemoved"] = True
        write_json(meta_path, metadata)
    receipt = {
        "schemaVersion": SCHEMA_VERSION,
        "api": TOOL_RAW_DELETE,
        "storageAuthority": "Hermes",
        "recordId": record_id,
        "contentHash": metadata.get("contentHash"),
        "status": "deleted",
        "reason": reason,
        "deletedAt": metadata["deletedAt"],
    }
    write_json(tombstone_path(root, "raw", record_id), receipt)
    return receipt


def graph_id_from_args(args: dict[str, Any]) -> str:
    graph_id = args.get("graphId") or args.get("sourceCandidateId")
    return require_safe_id("graphId/sourceCandidateId", graph_id)


def rdf_create(args: dict[str, Any], root: Path) -> dict[str, Any]:
    source_candidate_id = require_safe_id("sourceCandidateId", args.get("sourceCandidateId"))
    graph_id = require_safe_id("graphId", args.get("graphId") or source_candidate_id)
    turtle = args.get("turtle")
    if not isinstance(turtle, str) or not turtle.strip():
        raise MemoryApiError("turtle is required")
    turtle_hash = require_hash_match("RDF turtle", turtle, args.get("turtleSha256"))
    source_contract_hash = require_sha256("sourceContractHash", args.get("sourceContractHash"))
    shapes_turtle_hash = args.get("shapesTurtleSha256")
    if shapes_turtle_hash is not None:
        shapes_turtle_hash = require_sha256("shapesTurtleSha256", shapes_turtle_hash)
    shacl_result = args.get("shaclResult")
    if not isinstance(shacl_result, dict) or shacl_result.get("conforms") is not True:
        raise MemoryApiError("conforming live SHACL result is required")
    if args.get("sensitiveRdfDetected") is True and not args.get("approvalToken"):
        raise MemoryApiError("sensitive RDF graph create requires approvalToken")
    meta_path, turtle_path = rdf_paths(root, graph_id)
    if meta_path.exists():
        raise MemoryApiError("RDF graph already exists")
    metadata = {
        "schemaVersion": SCHEMA_VERSION,
        "api": TOOL_RDF_CREATE,
        "storageAuthority": "Hermes",
        "graphId": graph_id,
        "sourceCandidateId": source_candidate_id,
        "sourceContractHash": source_contract_hash,
        "turtleSha256": turtle_hash,
        "shapesTurtleSha256": shapes_turtle_hash,
        "shaclResultHash": sha256_text(canonical_json(shacl_result)),
        "status": "active",
        "createdAt": now_iso(),
        "metadata": args.get("metadata") or {},
        "turtlePath": str(turtle_path),
    }
    write_text_atomic(turtle_path, turtle)
    write_json(meta_path, metadata)
    return {k: metadata[k] for k in ["schemaVersion", "api", "storageAuthority", "graphId", "sourceCandidateId", "sourceContractHash", "turtleSha256", "status", "createdAt"]}


def rdf_read(args: dict[str, Any], root: Path) -> dict[str, Any]:
    graph_id = graph_id_from_args(args)
    meta_path, turtle_path = rdf_paths(root, graph_id)
    metadata = read_json(meta_path)
    if metadata.get("status") != "active":
        raise MemoryApiError("RDF graph is not active")
    result = {k: metadata.get(k) for k in ["schemaVersion", "storageAuthority", "graphId", "sourceCandidateId", "sourceContractHash", "turtleSha256", "shapesTurtleSha256", "status", "createdAt"]}
    result["api"] = TOOL_RDF_READ
    if args.get("includeTurtle"):
        result["turtle"] = turtle_path.read_text(encoding="utf-8")
    return result


def rdf_delete(args: dict[str, Any], root: Path) -> dict[str, Any]:
    graph_id = graph_id_from_args(args)
    reason = args.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise MemoryApiError("delete reason is required")
    if not args.get("approvalToken"):
        raise MemoryApiError("RDF graph delete requires approvalToken")
    meta_path, turtle_path = rdf_paths(root, graph_id)
    metadata = read_json(meta_path)
    if metadata.get("status") != "active":
        raise MemoryApiError("RDF graph is not active")
    metadata["status"] = "deleted"
    metadata["deletedAt"] = now_iso()
    metadata["deleteReason"] = reason
    write_json(meta_path, metadata)
    if turtle_path.exists():
        turtle_path.unlink()
        metadata["payloadRemoved"] = True
        write_json(meta_path, metadata)
    receipt = {
        "schemaVersion": SCHEMA_VERSION,
        "api": TOOL_RDF_DELETE,
        "storageAuthority": "Hermes",
        "graphId": graph_id,
        "sourceCandidateId": metadata.get("sourceCandidateId"),
        "turtleSha256": metadata.get("turtleSha256"),
        "status": "deleted",
        "reason": reason,
        "deletedAt": metadata["deletedAt"],
    }
    write_json(tombstone_path(root, "rdf", graph_id), receipt)
    return receipt
def vector_create(args: dict[str, Any], root: Path) -> dict[str, Any]:
    sidecar_id = require_safe_id("sidecarId", args.get("sidecarId"))
    canonical_source_id = require_safe_id("canonicalSourceId", args.get("canonicalSourceId"))
    source_kind = args.get("sourceKind")
    if not isinstance(source_kind, str) or not source_kind.strip():
        raise MemoryApiError("sourceKind is required")
    canonical_hash = require_sha256("canonicalContentHash", args.get("canonicalContentHash"))
    observed_hash = require_sha256("observedContentHash", args.get("observedContentHash"))
    if observed_hash != canonical_hash or args.get("readBackHashMatches") is not True:
        raise MemoryApiError("canonical source read-back hash must match before vector sidecar create")
    receipt_ref = args.get("receiptRef")
    if not isinstance(receipt_ref, str) or not receipt_ref.strip():
        raise MemoryApiError("canonical source receiptRef is required")
    text_hash = require_sha256("textHash", args.get("textHash"))
    vector_hash = require_sha256("vectorHash", args.get("vectorHash"))
    embedding_model = args.get("embeddingModel")
    if not isinstance(embedding_model, str) or not embedding_model.strip():
        raise MemoryApiError("embeddingModel is required")
    embedding_dimensions = args.get("embeddingDimensions")
    if not isinstance(embedding_dimensions, int) or embedding_dimensions <= 0:
        raise MemoryApiError("embeddingDimensions must be a positive integer")
    sensitivity = args.get("sensitivity") or "internal"
    if sensitivity == "sensitive" and not args.get("approvalToken"):
        raise MemoryApiError("sensitive vector sidecar create requires approvalToken")
    deletion_state = args.get("deletionState") or "active"
    redaction_state = args.get("redactionState") or "not_redacted"
    if deletion_state != "active":
        raise MemoryApiError("deleted canonical source cannot be indexed")
    if redaction_state != "not_redacted":
        raise MemoryApiError("redacted canonical source cannot be indexed")
    access_policy = args.get("accessPolicy") if isinstance(args.get("accessPolicy"), dict) else {}
    if not isinstance(access_policy.get("scope"), str) or not access_policy["scope"].strip():
        raise MemoryApiError("vector sidecar accessPolicy.scope is required")
    meta_path, _search_log_path = vector_paths(root, sidecar_id)
    if meta_path.exists():
        raise MemoryApiError("vector sidecar already exists")
    metadata = {
        "schemaVersion": SCHEMA_VERSION,
        "api": TOOL_VECTOR_CREATE,
        "storageAuthority": "Hermes",
        "canonicalMemoryAuthority": "Hermes",
        "sidecarAuthority": "host-vector-sidecar",
        "sidecarId": sidecar_id,
        "canonicalSourceId": canonical_source_id,
        "sourceKind": source_kind,
        "canonicalContentHash": canonical_hash,
        "observedContentHash": observed_hash,
        "readBackHashMatches": True,
        "receiptRef": receipt_ref,
        "textHash": text_hash,
        "vectorHash": vector_hash,
        "embeddingModel": embedding_model,
        "embeddingDimensions": embedding_dimensions,
        "sensitivity": sensitivity,
        "deletionState": deletion_state,
        "redactionState": redaction_state,
        "accessPolicy": access_policy,
        "retention": args.get("retention") or {},
        "provenance": args.get("provenance") or {},
        "metadata": args.get("metadata") or {},
        "status": "active",
        "createdAt": now_iso(),
    }
    write_json(meta_path, metadata)
    return {k: metadata[k] for k in ["schemaVersion", "api", "storageAuthority", "canonicalMemoryAuthority", "sidecarAuthority", "sidecarId", "canonicalSourceId", "observedContentHash", "textHash", "vectorHash", "status", "createdAt"]}


def vector_read(args: dict[str, Any], root: Path) -> dict[str, Any]:
    sidecar_id = require_safe_id("sidecarId", args.get("sidecarId"))
    meta_path, _search_log_path = vector_paths(root, sidecar_id)
    metadata = read_json(meta_path)
    if metadata.get("status") != "active":
        raise MemoryApiError("vector sidecar is not active")
    if metadata.get("sensitivity") == "sensitive" and not args.get("approvalToken"):
        raise MemoryApiError("sensitive vector sidecar read requires approvalToken")
    result = {k: metadata.get(k) for k in [
        "schemaVersion",
        "storageAuthority",
        "canonicalMemoryAuthority",
        "sidecarAuthority",
        "sidecarId",
        "canonicalSourceId",
        "sourceKind",
        "canonicalContentHash",
        "observedContentHash",
        "receiptRef",
        "textHash",
        "vectorHash",
        "embeddingModel",
        "embeddingDimensions",
        "sensitivity",
        "deletionState",
        "redactionState",
        "accessPolicy",
        "retention",
        "provenance",
        "status",
        "createdAt",
    ]}
    result["api"] = TOOL_VECTOR_READ
    return result


def _vector_score(metadata: dict[str, Any], *, query_text_hash: str | None, canonical_source_id: str | None) -> tuple[float, str]:
    if query_text_hash and query_text_hash == metadata.get("textHash"):
        return 1.0, "exact-text-hash"
    if canonical_source_id and canonical_source_id == metadata.get("canonicalSourceId"):
        return 0.91, "canonical-source-id"
    return 0.0, "no-match"


def vector_search(args: dict[str, Any], root: Path) -> dict[str, Any]:
    query_text_hash = args.get("queryTextHash")
    if query_text_hash is not None:
        query_text_hash = require_sha256("queryTextHash", query_text_hash)
    canonical_source_id = args.get("canonicalSourceId")
    if canonical_source_id is not None:
        canonical_source_id = require_safe_id("canonicalSourceId", canonical_source_id)
    if not query_text_hash and not canonical_source_id:
        raise MemoryApiError("queryTextHash or canonicalSourceId is required")
    requested_scope = args.get("requestedScope") or "private-user"
    min_score = args.get("minScore", 0.72)
    if not isinstance(min_score, (int, float)) or min_score < 0 or min_score > 1:
        raise MemoryApiError("minScore must be between 0 and 1")
    limit = args.get("limit", 10)
    if not isinstance(limit, int) or limit <= 0:
        raise MemoryApiError("limit must be a positive integer")
    results: list[dict[str, Any]] = []
    for metadata_path in sorted((root / "vector").glob("*.json")):
        metadata = read_json(metadata_path)
        if metadata.get("status") != "active":
            continue
        if metadata.get("deletionState") != "active" or metadata.get("redactionState") != "not_redacted":
            continue
        if metadata.get("sensitivity") == "sensitive" and not args.get("approvalToken"):
            continue
        access_policy = metadata.get("accessPolicy") if isinstance(metadata.get("accessPolicy"), dict) else {}
        if access_policy.get("scope") and access_policy.get("scope") != requested_scope:
            continue
        score, match_kind = _vector_score(metadata, query_text_hash=query_text_hash, canonical_source_id=canonical_source_id)
        if score < float(min_score):
            continue
        evidence = {
            "provider": "host-vector-sidecar",
            "retrievalKind": "host-vector-sidecar-search-result",
            "resultId": metadata.get("sidecarId"),
            "canonicalSourceId": metadata.get("canonicalSourceId"),
            "observedContentHash": metadata.get("observedContentHash"),
            "score": score,
            "matchKind": match_kind,
            "receiptRef": "host-vector-search-receipt:" + digest_id(canonical_json({
                "sidecarId": metadata.get("sidecarId"),
                "queryTextHash": query_text_hash,
                "canonicalSourceId": canonical_source_id,
                "requestedScope": requested_scope,
                "score": score,
            }))[:24],
        }
        results.append(evidence)
    results = sorted(results, key=lambda item: (-float(item["score"]), str(item["resultId"])))[:limit]
    receipt = {
        "schemaVersion": SCHEMA_VERSION,
        "api": TOOL_VECTOR_SEARCH,
        "storageAuthority": "Hermes",
        "canonicalMemoryAuthority": "Hermes",
        "sidecarAuthority": "host-vector-sidecar",
        "queryTextHash": query_text_hash,
        "canonicalSourceId": canonical_source_id,
        "requestedScope": requested_scope,
        "minScore": float(min_score),
        "results": results,
        "status": "ok",
        "searchedAt": now_iso(),
    }
    search_log_path = root / "vector" / "search-receipts.jsonl"
    write_text_atomic(search_log_path, (search_log_path.read_text(encoding="utf-8") if search_log_path.exists() else "") + canonical_json(receipt) + "\n")
    return receipt


def vector_delete(args: dict[str, Any], root: Path) -> dict[str, Any]:
    sidecar_id = require_safe_id("sidecarId", args.get("sidecarId"))
    reason = args.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise MemoryApiError("delete reason is required")
    if not args.get("approvalToken"):
        raise MemoryApiError("vector sidecar delete requires approvalToken")
    meta_path, _search_log_path = vector_paths(root, sidecar_id)
    metadata = read_json(meta_path)
    if metadata.get("status") != "active":
        raise MemoryApiError("vector sidecar is not active")
    metadata["status"] = "deleted"
    metadata["deletedAt"] = now_iso()
    metadata["deleteReason"] = reason
    write_json(meta_path, metadata)
    receipt = {
        "schemaVersion": SCHEMA_VERSION,
        "api": TOOL_VECTOR_DELETE,
        "storageAuthority": "Hermes",
        "canonicalMemoryAuthority": "Hermes",
        "sidecarAuthority": "host-vector-sidecar",
        "sidecarId": sidecar_id,
        "canonicalSourceId": metadata.get("canonicalSourceId"),
        "observedContentHash": metadata.get("observedContentHash"),
        "vectorHash": metadata.get("vectorHash"),
        "status": "deleted",
        "reason": reason,
        "deletedAt": metadata["deletedAt"],
    }
    write_json(tombstone_path(root, "vector", sidecar_id), receipt)
    return receipt




def count_active_metadata(directory: Path) -> int:
    active = 0
    for metadata_path in directory.glob("*.json"):
        try:
            if read_json(metadata_path).get("status") == "active":
                active += 1
        except Exception:
            continue
    return active


def status(root: Path) -> dict[str, Any]:
    ensure_store(root)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "server": SERVER_NAME,
        "version": SERVER_VERSION,
        "storageAuthority": "Hermes",
        "storeRoot": str(root),
        "tools": tool_names(),
        "counts": {
            "raw": count_active_metadata(root / "raw"),
            "rdf": count_active_metadata(root / "rdf"),
            "vector": count_active_metadata(root / "vector"),
            "deletions": len(list((root / "deletions").glob("*.json"))),
        },
    }


def call_tool(name: str, args: dict[str, Any] | None = None, *, root: Path | str | None = None) -> dict[str, Any]:
    args = args or {}
    root = Path(root).expanduser().resolve() if root is not None else store_root()
    ensure_store(root)
    if name == TOOL_RAW_CREATE:
        return raw_create(args, root)
    if name == TOOL_RAW_READ:
        return raw_read(args, root)
    if name == TOOL_RAW_DELETE:
        return raw_delete(args, root)
    if name == TOOL_RDF_CREATE:
        return rdf_create(args, root)
    if name == TOOL_RDF_READ:
        return rdf_read(args, root)
    if name == TOOL_RDF_DELETE:
        return rdf_delete(args, root)
    if name == TOOL_VECTOR_CREATE:
        return vector_create(args, root)
    if name == TOOL_VECTOR_SEARCH:
        return vector_search(args, root)
    if name == TOOL_VECTOR_READ:
        return vector_read(args, root)
    if name == TOOL_VECTOR_DELETE:
        return vector_delete(args, root)
    if name == TOOL_STATUS:
        return status(root)
    raise MemoryApiError(f"unknown tool: {name}")


def mcp_success(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def mcp_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle_mcp_request(message: dict[str, Any], root: Path) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    if request_id is None and method and method.startswith("notifications/"):
        return None
    if method == "initialize":
        return mcp_success(request_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })
    if method == "ping":
        return mcp_success(request_id, {})
    if method == "tools/list":
        return mcp_success(request_id, {"tools": tool_manifest()})
    if method == "tools/call":
        params = message.get("params") or {}
        try:
            result = call_tool(str(params.get("name")), params.get("arguments") or {}, root=root)
        except Exception as exc:
            return mcp_success(request_id, {"content": [{"type": "text", "text": json.dumps({"error": str(exc)}, ensure_ascii=False, sort_keys=True)}], "isError": True})
        return mcp_success(request_id, {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, sort_keys=True)}], "isError": False})
    return mcp_error(request_id, -32601, f"method not found: {method}")


def serve_stdio(root: Path) -> int:
    ensure_store(root)
    for line in sys.stdin:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            message = json.loads(stripped)
            if not isinstance(message, dict):
                raise ValueError("message must be an object")
            response = handle_mcp_request(message, root)
        except Exception as exc:  # fail closed for malformed host requests
            response = mcp_error(None, -32603, str(exc))
        if response is not None:
            print(json.dumps(response, ensure_ascii=False, separators=(",", ":")), flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="just-chill Hermes memory MCP server")
    parser.add_argument("--store-root", default=None, help="Canonical host-owned store root. Defaults to JUST_CHILL_HERMES_MEMORY_STORE or ~/.local/share/jarvis/just-chill-hermes-memory-api.")
    parser.add_argument("--check", action="store_true", help="Print server/tool readiness without mutating storage.")
    parser.add_argument("--list-tools", action="store_true", help="Print tool names without mutating storage.")
    parser.add_argument("--call-tool", help="Call one tool from the CLI for smoke testing.")
    parser.add_argument("--arguments", default="{}", help="JSON object for --call-tool.")
    parser.add_argument("--serve", action="store_true", help="Run stdio MCP server. This is also the default when no CLI action is selected.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print CLI JSON output.")
    args = parser.parse_args(argv)
    root = store_root(args.store_root)

    if args.check:
        output = {
            "schemaVersion": SCHEMA_VERSION,
            "server": SERVER_NAME,
            "version": SERVER_VERSION,
            "transport": "stdio",
            "storageAuthority": "Hermes",
            "storeRoot": str(root),
            "tools": tool_names(),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
        return 0
    if args.list_tools:
        print("\n".join(tool_names()))
        return 0
    if args.call_tool:
        try:
            parsed_args = json.loads(args.arguments)
            if not isinstance(parsed_args, dict):
                raise MemoryApiError("--arguments must decode to an object")
            result = call_tool(args.call_tool, parsed_args, root=root)
        except Exception as exc:
            print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
            return 1
        print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
        return 0
    return serve_stdio(root)


if __name__ == "__main__":
    raise SystemExit(main())
