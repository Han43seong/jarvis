#!/usr/bin/env python3
"""Acceptance checks for the Hermes-facing just-chill harness MCP server."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from just_chill_approval_registry import issue_approval
from just_chill_harness_mcp import (
    SERVER_NAME,
    TOOL_CONSENT,
    TOOL_GJC_HANDOFF,
    TOOL_HANDLE,
    TOOL_RECALL,
    TOOL_REMEMBER,
    TOOL_ROUTE,
    TOOL_STATUS,
    call_tool,
    handle_mcp_request,
    tool_manifest,
    tool_names,
)

ROOT = Path(__file__).resolve().parents[1]
MCP_SCRIPT = ROOT / "scripts" / "just_chill_harness_mcp.py"


def require(name: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle: Any, haystack: Any) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


def require_truthy(name: str, value: Any) -> None:
    if not value:
        raise AssertionError(f"{name}: expected truthy, got {value!r}")


def parse_tool_response(response: dict[str, Any]) -> dict[str, Any]:
    result = response["result"]
    require("tool isError", result["isError"], False)
    return json.loads(result["content"][0]["text"])


def run_cli_json(argv: list[str]) -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(MCP_SCRIPT), *argv], cwd=ROOT, text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def run_stdio(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payload = "".join(json.dumps(message, ensure_ascii=False, sort_keys=True) + "\n" for message in messages)
    result = subprocess.run([sys.executable, str(MCP_SCRIPT)], cwd=ROOT, input=payload, text=True, capture_output=True, check=True)
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]

def run_stdio_raw(payload: str) -> list[dict[str, Any]]:
    result = subprocess.run([sys.executable, str(MCP_SCRIPT)], cwd=ROOT, input=payload, text=True, capture_output=True, check=True)
    return [json.loads(line) for line in result.stdout.splitlines() if line.strip()]



cases: list[str] = []

names = tool_names()
require("tool names", names, [TOOL_ROUTE, TOOL_REMEMBER, TOOL_RECALL, TOOL_GJC_HANDOFF, TOOL_CONSENT, TOOL_HANDLE, TOOL_STATUS])
manifest = tool_manifest()
require("manifest len", len(manifest), len(names))
for tool in manifest:
    require_in("manifest tool", tool["name"], names)
    require("schema type", tool["inputSchema"]["type"], "object")
    require("schema additional props", tool["inputSchema"].get("additionalProperties"), False)
cases.append("tool-manifest")
tool_schema = {tool["name"]: tool["inputSchema"]["properties"] for tool in manifest}
for field in ["approvalToken", "approvalRegistry", "approvalScope", "approvalSubject"]:
    require_in("remember approval schema", field, tool_schema[TOOL_REMEMBER])
    require_in("recall approval schema", field, tool_schema[TOOL_RECALL])
    require_in("handle approval schema", field, tool_schema[TOOL_HANDLE])
cases.append("approval-registry-schema")


check = run_cli_json(["--check"])
require("check server", check["server"], SERVER_NAME)
require("check registered", check["registration"]["registeredByThisCommand"], False)
require("check approval", check["registration"]["requiresExplicitApproval"], True)
require("check no execution", check["authorityBoundary"]["executionAllowedHere"], False)
require("check no SHACL", check["authorityBoundary"]["justChillRunsShaclEngine"], False)
require("check no vector", check["authorityBoundary"]["justChillSearchesVectorStore"], False)
cases.append("check-json")

listed = subprocess.run([sys.executable, str(MCP_SCRIPT), "--list-tools"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
require("listed tools", listed, names)
cases.append("list-tools-cli")

route = call_tool(TOOL_ROUTE, {"request": "fix src/hooks/bridge.ts", "cwd": str(ROOT)})
require("route op", route["operation"], "route")
require("route dev", route["routerPacket"]["classification"]["isDevelopment"], True)
require("route execution", route["executionAllowedHere"], False)
cases.append("call-route")

remember = call_tool(TOOL_REMEMBER, {"request": "remember that Hermes is the main user layer", "summary": "Hermes is the main user layer."})
require("remember status", remember["status"], "memory-candidate-ready")
require("remember no write", remember["authorityBoundary"]["justChillWritesHermes"], False)
cases.append("call-remember")

sensitive = call_tool(TOOL_REMEMBER, {"request": "remember my API key <example-api-key>"})
require("sensitive blocked", sensitive["status"], "memory-candidate-blocked")
require_in("sensitive blocker", "sensitive memory requires explicit approval before host-owned persistence", sensitive["blockedReasons"])
cases.append("call-sensitive-remember")
with TemporaryDirectory() as tmp:
    sensitive_request = "remember my API key <example-api-key>"
    registry_path = str(Path(tmp) / "approvals.jsonl")
    issued = issue_approval(
        scope="memory.write",
        subject=sensitive_request,
        actor="example-user",
        reason="MCP registry acceptance test",
        registry=registry_path,
    )
    registry_remember = call_tool(TOOL_REMEMBER, {
        "request": sensitive_request,
        "approvalToken": issued["approvalToken"],
        "approvalRegistry": registry_path,
    })
    require("registry remember status", registry_remember["status"], "memory-candidate-ready")
    require("registry remember mode", registry_remember["approvalVerification"]["mode"], "registry")
    require("registry remember accepted", registry_remember["approvalTokenAccepted"], True)
    cases.append("call-sensitive-remember-registry-approved")


recall_default = call_tool(TOOL_RECALL, {"query": "How should dev route?", "cwd": str(ROOT)})
require("recall default", recall_default["status"], "host-retrieval-required")
require("recall no probe", recall_default["vectorBoundary"]["probeMode"], "availability-only")
cases.append("call-recall-default")

handoff = call_tool(TOOL_GJC_HANDOFF, {"request": "fix src/hooks/bridge.ts", "cwd": str(ROOT), "allowMutation": True})
require("handoff ready", handoff["status"], "handoff-plan-ready")
require("handoff mutation local", handoff["mutationConsent"]["allowedHere"], False)
cases.append("call-handoff")

consent = call_tool(TOOL_CONSENT, {"bridgePlan": handoff["bridgePlan"], "surfaces": {
    "visibleRoutedSession": {"status": "orchestration-plan-ready", "scrollbackIsCompletion": False, "evidencePolicy": {"durableEvidenceRequired": True, "scrollbackIsCompletion": False}},
    "operatorConsent": {"allowMutation": False, "source": "not-needed-visible", "requiredPerMutatingCall": True},
    "coordinatorMcp": {"status": "not-used", "missingTools": [], "mutationClassesEnabled": [], "mutationClassesRequiredForExecution": ["sessions", "questions", "reports"]},
    "gjcDelegation": {"delegateTools": {}},
}, "evidencePayload": {"kind": "test", "command": ["python3", "scripts/check_just_chill_harness_mcp.py"]}})
require("consent visible", consent["status"], "visible-session-preferred")
require("consent blockers", consent["blockedReasons"], [])
cases.append("call-consent")

handled = call_tool(TOOL_HANDLE, {"request": "remember that just-chill is a Hermes harness", "summary": "just-chill is a Hermes harness"})
require("handle status", handled["status"], "handled-contract-ready")
require_truthy("handle memory", handled["memoryPlan"])
require("handle no GJC", handled["authorityBoundary"]["justChillExecutesGjc"], False)
cases.append("call-handle")

status = call_tool(TOOL_STATUS, {"cwd": str(ROOT)})
require("status ready", status["status"], "ready")
require("status user layer", status["userFacingLayer"], "Hermes")
require("status bridge mode", status["executionBridge"]["mode"], "visible-session-only")
require("status bridge enabled", status["executionBridge"]["enabled"], True)
cases.append("call-status")

cli_call = run_cli_json(["--call-tool", TOOL_HANDLE, "--arguments", json.dumps({"request": "fix src/hooks/bridge.ts"}, sort_keys=True)])
require("cli call op", cli_call["operation"], "handle")
require_truthy("cli handoff", cli_call["gjcHandoffPlan"])
cases.append("cli-call-tool")

init_response = handle_mcp_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
require("init id", init_response["id"], 1)
require("init server", init_response["result"]["serverInfo"]["name"], SERVER_NAME)
cases.append("initialize")

list_response = handle_mcp_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
require("list id", list_response["id"], 2)
require("list tools", [tool["name"] for tool in list_response["result"]["tools"]], names)
cases.append("tools-list")

call_response = handle_mcp_request({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": TOOL_ROUTE, "arguments": {"request": "fix src/hooks/bridge.ts"}}})
require("call id", call_response["id"], 3)
parsed = parse_tool_response(call_response)
require("call parsed route", parsed["operation"], "route")
cases.append("tools-call")

error_response = handle_mcp_request({"jsonrpc": "2.0", "id": "err-1", "method": "tools/call", "params": {"name": "just_chill.nope", "arguments": {}}})
require("error id preserved", error_response["id"], "err-1")
require("error isError", error_response["result"]["isError"], True)
require_in("error text", "unknown tool", json.loads(error_response["result"]["content"][0]["text"])["error"])
cases.append("tools-call-error-preserves-id")
params_error = handle_mcp_request({"jsonrpc": "2.0", "id": "params-1", "method": "tools/call", "params": ["not", "object"]})
require("params error id", params_error["id"], "params-1")
require("params error isError", params_error["result"]["isError"], True)
require_in("params error text", "params must be an object", json.loads(params_error["result"]["content"][0]["text"])["error"])
cases.append("tools-call-non-object-params")

method_error = handle_mcp_request({"jsonrpc": "2.0", "id": "method-1", "method": "unknown/method"})
require("method error id", method_error["id"], "method-1")
require("method error code", method_error["error"]["code"], -32601)
cases.append("unknown-method-error-preserves-id")

bad_stdio = run_stdio_raw("{not-json}\n")
require("bad stdio count", len(bad_stdio), 1)
require("bad stdio id", bad_stdio[0]["id"], None)
require("bad stdio code", bad_stdio[0]["error"]["code"], -32603)
cases.append("stdio-malformed-line-blocked")

bad_cli_call = subprocess.run(
    [sys.executable, str(MCP_SCRIPT), "--call-tool", TOOL_ROUTE, "--arguments", "{bad-json}"],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=False,
)
require("bad CLI return", bad_cli_call.returncode, 1)
bad_cli_output = json.loads(bad_cli_call.stdout)
require_truthy("bad CLI error", bad_cli_output.get("error"))
cases.append("cli-call-tool-malformed-arguments")


stdio_responses = run_stdio([
    {"jsonrpc": "2.0", "id": 10, "method": "initialize", "params": {}},
    {"jsonrpc": "2.0", "id": 11, "method": "tools/call", "params": {"name": TOOL_STATUS, "arguments": {"cwd": str(ROOT)}}},
])
require("stdio count", len(stdio_responses), 2)
require("stdio init", stdio_responses[0]["result"]["serverInfo"]["name"], SERVER_NAME)
status_text = json.loads(stdio_responses[1]["result"]["content"][0]["text"])
require("stdio status", status_text["status"], "ready")
cases.append("stdio-server")

for idx, output in enumerate([route, remember, sensitive, registry_remember, recall_default, handoff, consent, handled, status, cli_call, parsed, status_text], start=1):
    require(f"output {idx} execution", output["executionAllowedHere"], False)
    boundary = output["authorityBoundary"]
    for key in [
        "justChillExecutesGjc",
        "justChillWritesHermes",
        "justChillOwnsCanonicalMemory",
        "justChillRunsShaclEngine",
        "justChillSearchesVectorStore",
        "justChillCallsCoordinator",
        "justChillCallsDelegateTools",
    ]:
        require(f"output {idx} {key}", boundary[key], False)
cases.append("authority-boundary-invariant")

print(f"PASS: {len(cases)} just-chill harness MCP cases passed")
