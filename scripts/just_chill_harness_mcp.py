#!/usr/bin/env python3
"""Hermes-facing MCP wrapper for the just-chill harness.

This stdio MCP server exposes just-chill's routing, memory planning, recall gating,
GJC handoff planning, consent evaluation, full handling, and status contracts to
Hermes. It is a contract/policy server only: it never executes GJC, writes Hermes
memory, runs SHACL, calls coordinator/delegate tools, or searches vector stores.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from just_chill_harness import (
    authority_boundary,
    HARNESS_NAME,
    OP_CONSENT,
    OP_GJC_HANDOFF,
    OP_HANDLE,
    OP_RECALL,
    OP_REMEMBER,
    OP_ROUTE,
    OP_STATUS,
    SCHEMA_VERSION,
    HarnessInputError,
    call_operation,
)

SERVER_NAME = "just-chill-harness"
SERVER_VERSION = "1.0.0"
TOOL_ROUTE = "just_chill.route"
TOOL_REMEMBER = "just_chill.remember.plan"
TOOL_RECALL = "just_chill.recall.gate"
TOOL_GJC_HANDOFF = "just_chill.gjc_handoff.plan"
TOOL_CONSENT = "just_chill.consent.evaluate"
TOOL_HANDLE = "just_chill.handle"
TOOL_STATUS = "just_chill.status"
TOOL_TO_OPERATION = {
    TOOL_ROUTE: OP_ROUTE,
    TOOL_REMEMBER: OP_REMEMBER,
    TOOL_RECALL: OP_RECALL,
    TOOL_GJC_HANDOFF: OP_GJC_HANDOFF,
    TOOL_CONSENT: OP_CONSENT,
    TOOL_HANDLE: OP_HANDLE,
    TOOL_STATUS: OP_STATUS,
}


def tool_names() -> list[str]:
    return list(TOOL_TO_OPERATION.keys())


def object_schema(extra: dict[str, Any] | None = None, *, required: list[str] | None = None) -> dict[str, Any]:
    schema = {
        "type": "object",
        "properties": {
            "caller": {"type": "string", "description": "Calling layer identity; defaults to hermes."},
            "requestId": {"type": "string", "description": "Optional host request correlation id."},
        },
        "additionalProperties": False,
    }
    if extra:
        schema["properties"].update(extra)
    if required:
        schema["required"] = required
    return schema


def tool_manifest() -> list[dict[str, Any]]:
    string = {"type": "string"}
    boolean = {"type": "boolean"}
    object_any = {"type": "object", "additionalProperties": True}
    array_string = {"type": "array", "items": {"type": "string"}}
    return [
        {
            "name": TOOL_ROUTE,
            "description": "Classify a user request and optionally include a non-executing GJC bridge plan.",
            "inputSchema": object_schema({"request": string, "cwd": string, "includeBridge": boolean}, required=["request"]),
        },
        {
            "name": TOOL_REMEMBER,
            "description": "Build raw artifact and optional summary memory contracts without writing Hermes.",
            "inputSchema": object_schema({"request": string, "summary": string, "approvalToken": string, "approvalRegistry": string, "approvalScope": string, "approvalSubject": string, "sourceChannel": string}, required=["request"]),
        },
        {
            "name": TOOL_RECALL,
            "description": "Gate host-owned vector retrieval evidence before memory enters context.",
            "inputSchema": object_schema({
                "query": string,
                "cwd": string,
                "candidate": object_any,
                "retrievalEvidence": object_any,
                "currentSourceHash": string,
                "currentDeletionState": string,
                "currentRedactionState": string,
                "approvalToken": string,
                "approvalRegistry": string,
                "approvalScope": string,
                "approvalSubject": string,
                "probe": boolean,
            }, required=["query"]),
        },
        {
            "name": TOOL_GJC_HANDOFF,
            "description": "Build a non-executing GJC handoff plan for development requests.",
            "inputSchema": object_schema({"request": string, "cwd": string, "allowMutation": boolean}, required=["request"]),
        },
        {
            "name": TOOL_CONSENT,
            "description": "Evaluate coordinator/delegation mutation consent without calling GJC tools.",
            "inputSchema": object_schema({
                "request": string,
                "bridgePlan": object_any,
                "surfaces": object_any,
                "allowMutation": boolean,
                "mutationClasses": array_string,
                "evidencePayload": object_any,
                "cwd": string,
                "probe": boolean,
            }),
        },
        {
            "name": TOOL_HANDLE,
            "description": "Run the Hermes-main request harness: route, then produce memory or GJC handoff/consent contracts.",
            "inputSchema": object_schema({
                "request": string,
                "cwd": string,
                "summary": string,
                "approvalToken": string,
                "approvalRegistry": string,
                "approvalScope": string,
                "approvalSubject": string,
                "allowMutation": boolean,
                "mutationClasses": array_string,
                "evidencePayload": object_any,
                "probe": boolean,
            }, required=["request"]),
        },
        {
            "name": TOOL_STATUS,
            "description": "Report harness status, tool names, and optional read-only live-surface discovery.",
            "inputSchema": object_schema({"cwd": string, "probe": boolean}),
        },
    ]


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    if name not in TOOL_TO_OPERATION:
        raise HarnessInputError(f"unknown tool: {name}")
    args = arguments or {}
    if not isinstance(args, dict):
        raise HarnessInputError("tool arguments must be an object")
    return call_operation(TOOL_TO_OPERATION[name], args)


def mcp_success(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def mcp_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def text_content(data: dict[str, Any], *, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False, sort_keys=True)}],
        "isError": is_error,
    }


def handle_mcp_request(message: dict[str, Any]) -> dict[str, Any] | None:
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
        if not isinstance(params, dict):
            return mcp_success(request_id, text_content({"error": "params must be an object"}, is_error=True))
        try:
            result = call_tool(str(params.get("name")), params.get("arguments") or {})
        except Exception as exc:
            return mcp_success(request_id, text_content({"error": str(exc)}, is_error=True))
        return mcp_success(request_id, text_content(result, is_error=False))
    return mcp_error(request_id, -32601, f"method not found: {method}")


def serve_stdio() -> int:
    for line in sys.stdin:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            message = json.loads(stripped)
            if not isinstance(message, dict):
                raise ValueError("message must be an object")
            response = handle_mcp_request(message)
        except Exception as exc:
            response = mcp_error(None, -32603, str(exc))
        if response is not None:
            print(json.dumps(response, ensure_ascii=False, separators=(",", ":")), flush=True)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes-facing just-chill harness MCP server")
    parser.add_argument("--check", action="store_true", help="Print MCP readiness without registering or serving.")
    parser.add_argument("--list-tools", action="store_true", help="Print tool names.")
    parser.add_argument("--call-tool", help="Call one MCP tool locally for smoke testing.")
    parser.add_argument("--arguments", default="{}", help="JSON object for --call-tool.")
    parser.add_argument("--serve", action="store_true", help="Run stdio MCP server. This is also the default when no CLI action is selected.")
    parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.check:
        output = {
            "schemaVersion": SCHEMA_VERSION,
            "server": SERVER_NAME,
            "version": SERVER_VERSION,
            "transport": "stdio",
            "harness": HARNESS_NAME,
            "tools": tool_names(),
            "authorityBoundary": authority_boundary(),
            "registration": {
                "registeredByThisCommand": False,
                "requiresExplicitApproval": True,
            },
        }
        print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
        return 0
    if args.list_tools:
        print("\n".join(tool_names()))
        return 0
    if args.call_tool:
        try:
            parsed = json.loads(args.arguments)
            if not isinstance(parsed, dict):
                raise HarnessInputError("--arguments must decode to an object")
            output = call_tool(args.call_tool, parsed)
        except Exception as exc:
            print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
            return 1
        print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
        return 0
    return serve_stdio()


if __name__ == "__main__":
    raise SystemExit(main())
