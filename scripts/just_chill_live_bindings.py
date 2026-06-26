#!/usr/bin/env python3
"""Live-binding discovery and safe handoff helpers for just-chill.

This module maps the live GJC/Hermes surfaces available to the local host and
turns an existing just-chill bridge plan into operator-safe handoff instructions.
It does not execute product work, start GJC workflow turns, write Hermes memory,
or treat terminal scrollback as completion evidence.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Sequence

from just_chill_bridge import build_bridge_plan
from just_chill_router import SENSITIVE_KEYWORDS, classify_request
from just_chill_visible_session_helpers import (
    ACCEPTED_EVIDENCE_KINDS,
    HELPER_CONTRACT_VERSION,
    ORCHESTRATION_MODE,
    REJECTED_EVIDENCE_KINDS,
    validate_visible_evidence_payload,
)

SCHEMA_VERSION = 1
LIVE_BINDING_NAME = "just-chill-live-bindings-v1"
HOST_HELPERS = ["create-gjc-session", "prompt-gjc-session", "tail-gjc-session"]
CORE_COMMANDS = ["gjc", "hermes", "tmux"]
REQUIRED_COORDINATOR_TOOLS = [
    "gjc_coordinator_list_sessions",
    "gjc_coordinator_read_turn",
    "gjc_coordinator_await_turn",
    "gjc_coordinator_watch_events",
    "gjc_coordinator_start_session",
    "gjc_coordinator_send_prompt",
    "gjc_coordinator_report_status",
]
DELEGATE_TOOLS = {
    "gjc_delegate_plan": "/skill:ralplan",
    "gjc_delegate_execute": "/skill:ultragoal",
    "gjc_delegate_team": "/skill:team",
}
REDACTION = "[redacted-sensitive]"
READ_ONLY_PROBES = {
    "coordinatorCheck": ["gjc", "mcp-serve", "coordinator", "--check", "--json"],
    "hermesSetupSmoke": ["gjc", "setup", "hermes", "--smoke", "--json"],
    "hermesMemoryStatus": ["hermes", "memory", "status"],
    "hermesMcpList": ["hermes", "mcp", "list"],
}
MEMORY_PROVIDER_TOOL_SURFACES = {
    "holographic": {
        "status": "provider-tool-available",
        "provider": "holographic",
        "storageMode": "local-sqlite-fact-store",
        "rawArtifactApi": "unmapped",
        "rawArtifactReadApi": "unmapped",
        "rawArtifactDeleteApi": "unmapped",
        "summaryMemoryApi": "hermes.summary_memory.provider_tool.fact_store.add",
        "summaryMemoryWriteAvailable": True,
        "tool": {
            "name": "fact_store",
            "writeAction": "add",
            "readActions": ["search", "probe", "related", "reason", "list"],
            "deleteAction": "remove",
        },
        "boundary": "host-owned Hermes memory provider tool; just-chill emits a plan and does not call the tool directly",
        "limitations": [
            "structured fact/summary memory only, not a raw artifact store",
            "standalone local add/remove receipts are available through just_chill_summary_memory_receipts.py, but no Hermes-native receipt API is mapped yet",
            "raw artifact provenance still requires a separate Hermes artifact boundary",
        ],
    },
}
def _just_chill_memory_api_surface(mcp_probe: dict[str, Any]) -> dict[str, Any]:
    stdout = str(mcp_probe.get("stdout", ""))
    if "just_chill_memory_api" not in stdout:
        return {
            "configured": False,
            "tools": [],
            "rawArtifactApi": "unmapped",
            "rawArtifactReadApi": "unmapped",
            "rawArtifactDeleteApi": "unmapped",
            "rdfGraphApi": "unmapped",
            "rdfGraphReadApi": "unmapped",
            "rdfGraphDeleteApi": "unmapped",
            "vectorSidecarCreateApi": "unmapped",
            "vectorSidecarSearchApi": "unmapped",
            "vectorSidecarReadApi": "unmapped",
            "vectorSidecarDeleteApi": "unmapped",
            "vectorSidecarAvailable": False,
            "liveStorageWriteAvailable": False,
        }
    try:
        from just_chill_hermes_memory_mcp import tool_names
    except Exception:
        tools: list[str] = []
    else:
        tools = tool_names()
    return {
        "configured": True,
        "server": "just_chill_memory_api",
        "tools": tools,
        "rawArtifactApi": "hermes.raw_artifact.create" if "hermes.raw_artifact.create" in tools else "unmapped",
        "rawArtifactReadApi": "hermes.raw_artifact.read" if "hermes.raw_artifact.read" in tools else "unmapped",
        "rawArtifactDeleteApi": "hermes.raw_artifact.delete" if "hermes.raw_artifact.delete" in tools else "unmapped",
        "rdfGraphApi": "hermes.rdf_graph.create" if "hermes.rdf_graph.create" in tools else "unmapped",
        "rdfGraphReadApi": "hermes.rdf_graph.read" if "hermes.rdf_graph.read" in tools else "unmapped",
        "rdfGraphDeleteApi": "hermes.rdf_graph.delete" if "hermes.rdf_graph.delete" in tools else "unmapped",
        "vectorSidecarCreateApi": "hermes.vector_sidecar.create" if "hermes.vector_sidecar.create" in tools else "unmapped",
        "vectorSidecarSearchApi": "hermes.vector_sidecar.search" if "hermes.vector_sidecar.search" in tools else "unmapped",
        "vectorSidecarReadApi": "hermes.vector_sidecar.read" if "hermes.vector_sidecar.read" in tools else "unmapped",
        "vectorSidecarDeleteApi": "hermes.vector_sidecar.delete" if "hermes.vector_sidecar.delete" in tools else "unmapped",
        "vectorSidecarAvailable": all(tool in tools for tool in [
            "hermes.vector_sidecar.create",
            "hermes.vector_sidecar.search",
            "hermes.vector_sidecar.read",
            "hermes.vector_sidecar.delete",
        ]),
        "liveStorageWriteAvailable": all(tool in tools for tool in [
            "hermes.raw_artifact.create",
            "hermes.raw_artifact.read",
            "hermes.raw_artifact.delete",
            "hermes.rdf_graph.create",
            "hermes.rdf_graph.read",
            "hermes.rdf_graph.delete",
        ]),
        "boundary": "host-owned Hermes MCP memory API; just-chill emits plans and does not call the tools directly",
    }


Runner = Callable[[Sequence[str], str | None, int], dict[str, Any]]
Which = Callable[[str], str | None]


def stable_suffix(text: str, length: int = 10) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def safe_session_name(request: str, cwd: str | None) -> str:
    base = os.path.basename(os.path.abspath(cwd or os.getcwd())) or "repo"
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", base).strip("-").lower() or "repo"
    return f"just-chill-{slug}-{stable_suffix(request)}"

def _contains_sensitive_text(text: str) -> bool:
    lower = text.lower()
    return any(keyword.lower() in lower for keyword in SENSITIVE_KEYWORDS)


def packet_is_sensitive(packet: dict[str, Any]) -> bool:
    request = str(packet.get("request", ""))
    risk = " ".join(str(item) for item in packet.get("signals", {}).get("risk", []))
    return _contains_sensitive_text(" ".join([request, risk]))


def _redact_prompt_fields(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if key in {"request", "skillPrompt", "task", "taskPrompt"} and isinstance(item, str):
                redacted[key] = REDACTION
            else:
                redacted[key] = _redact_prompt_fields(item)
        return redacted
    if isinstance(value, list):
        return [_redact_prompt_fields(item) for item in value]
    return value


def redact_sensitive_report_payload(value: dict[str, Any], *, sensitive: bool) -> dict[str, Any]:
    if not sensitive:
        return value
    return _redact_prompt_fields(copy.deepcopy(value))


def default_runner(argv: Sequence[str], cwd: str | None, timeout: int) -> dict[str, Any]:
    """Run an allowlisted read-only probe and capture a structured result."""
    completed = subprocess.run(  # noqa: S603 - argv is fixed by READ_ONLY_PROBES callers.
        list(argv),
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    parsed_json: Any | None = None
    if stdout:
        try:
            parsed_json = json.loads(stdout)
        except json.JSONDecodeError:
            parsed_json = None
    return {
        "argv": list(argv),
        "exitCode": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout": stdout,
        "stderr": stderr,
        "json": parsed_json,
    }


def _repo_local_helper_path(name: str, cwd: str | None) -> str | None:
    if not cwd or name not in HOST_HELPERS:
        return None
    candidate = Path(cwd).resolve() / "scripts" / name
    if candidate.exists() and candidate.is_file() and os.access(candidate, os.X_OK):
        return str(candidate)
    return None


def command_availability(cwd: str | None = None, which: Which | None = None) -> dict[str, dict[str, Any]]:
    which = which or shutil.which
    names = [*CORE_COMMANDS, *HOST_HELPERS]
    availability: dict[str, dict[str, Any]] = {}
    for name in names:
        which_path = which(name)
        path = which_path or _repo_local_helper_path(name, cwd)
        availability[name] = {
            "available": bool(path),
            "path": path,
            "source": "path" if which_path else ("repo-scripts" if path else None),
        }
    return availability


def _probe_if_allowed(
    name: str,
    *,
    cwd: str | None,
    probe: bool,
    runner: Runner,
    timeout: int,
) -> dict[str, Any]:
    argv = list(READ_ONLY_PROBES[name])
    if name == "hermesSetupSmoke":
        # Keep this render/smoke-only; it writes no Hermes or repo files.
        argv = ["gjc", "setup", "hermes", "--root", cwd or os.getcwd(), "--smoke", "--json"]
    if not probe:
        return {"argv": argv, "ok": None, "status": "not-probed"}
    try:
        result = runner(argv, cwd, timeout)
        result["status"] = "ok" if result.get("ok") else "failed"
        return result
    except Exception as exc:  # pragma: no cover - exercised through fake runner in checks.
        return {"argv": argv, "ok": False, "status": "error", "error": str(exc)}


def _probe_helper_contracts(
    *,
    commands: dict[str, dict[str, Any]],
    cwd: str | None,
    probe: bool,
    runner: Runner,
    timeout: int,
) -> dict[str, dict[str, Any]]:
    contracts: dict[str, dict[str, Any]] = {}
    for name in HOST_HELPERS:
        path = commands.get(name, {}).get("path") or name
        if not commands.get(name, {}).get("available"):
            contracts[name] = {"argv": [path, "--contract", "--json"], "ok": None, "status": "unavailable"}
            continue
        argv = [path, "--contract", "--json"]
        if not probe:
            contracts[name] = {"argv": argv, "ok": None, "status": "not-probed"}
            continue
        try:
            result = runner(argv, cwd, timeout)
            contract = result.get("json", {}).get("contract") if isinstance(result.get("json"), dict) else None
            result["status"] = "ok" if result.get("ok") and _helper_contract_is_valid(contract, name) else "invalid"
            result["contractValid"] = result["status"] == "ok"
            contracts[name] = result
        except Exception as exc:  # pragma: no cover - exercised through fake runner in checks.
            contracts[name] = {"argv": argv, "ok": False, "status": "error", "error": str(exc), "contractValid": False}
    return contracts


def _helper_contract_is_valid(contract: Any, expected_helper: str) -> bool:
    if not isinstance(contract, dict):
        return False
    planning = contract.get("orchestrationPlanning", {})
    return (
        contract.get("contractVersion") == HELPER_CONTRACT_VERSION
        and contract.get("ownedBy") == "host"
        and contract.get("helper") == expected_helper
        and contract.get("executesGjc") is False
        and contract.get("executesProductWork") is False
        and contract.get("callsGjcDelegateTools") is False
        and contract.get("writesHermesMemory") is False
        and contract.get("scrollbackIsCompletion") is False
        and contract.get("durableEvidenceRequired") is True
        and ORCHESTRATION_MODE in contract.get("supportedModes", [])
        and planning.get("supported") is True
        and planning.get("mode") == ORCHESTRATION_MODE
        and planning.get("emitsArgvPlan") is True
        and planning.get("executesCommands") is False
        and planning.get("helperRunsTmux") is False
        and planning.get("helperInjectsPrompt") is False
        and planning.get("operatorOwnsExecution") is True
        and set(ACCEPTED_EVIDENCE_KINDS).issubset(set(contract.get("acceptedEvidenceKinds", [])))
        and set(REJECTED_EVIDENCE_KINDS).issubset(set(contract.get("rejectedEvidenceKinds", [])))
    )


def _visible_status(commands: dict[str, dict[str, Any]], contracts: dict[str, dict[str, Any]], *, probe: bool) -> str:
    if not all(commands[name]["available"] for name in [*HOST_HELPERS]):
        return "missing-host-helpers"
    if not probe:
        return "host-helpers-present-unverified"
    if not all(contracts.get(name, {}).get("contractValid") for name in HOST_HELPERS):
        return "invalid-host-helper-contracts"
    if commands["tmux"]["available"] and commands["gjc"]["available"]:
        return "orchestration-plan-ready"
    return "metadata-only-ready"


def _memory_provider_tool_surface(memory_provider: str | None) -> dict[str, Any]:
    if not memory_provider or memory_provider.startswith("("):
        return {
            "status": "no-external-provider",
            "provider": memory_provider,
            "rawArtifactApi": "unmapped",
            "rawArtifactReadApi": "unmapped",
            "rawArtifactDeleteApi": "unmapped",
            "summaryMemoryApi": "unmapped",
            "summaryMemoryWriteAvailable": False,
            "limitations": ["no active external Hermes memory provider"],
        }
    surface = MEMORY_PROVIDER_TOOL_SURFACES.get(memory_provider)
    if surface:
        return copy.deepcopy(surface)
    return {
        "status": "provider-unmapped",
        "provider": memory_provider,
        "rawArtifactApi": "unmapped",
        "rawArtifactReadApi": "unmapped",
        "rawArtifactDeleteApi": "unmapped",
        "summaryMemoryApi": "unmapped",
        "summaryMemoryWriteAvailable": False,
        "limitations": ["active provider has not been mapped to a just-chill memory write contract"],
    }

def _parse_memory_provider(memory_status_stdout: str) -> str | None:
    for line in memory_status_stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("Provider:"):
            return stripped.split(":", 1)[1].strip()
    return None


def discover_live_surfaces(
    *,
    cwd: str | None = None,
    probe: bool = False,
    runner: Runner | None = None,
    which: Which | None = None,
    timeout: int = 20,
) -> dict[str, Any]:
    """Discover local integration availability without executing product work."""
    runner = runner or default_runner
    commands = command_availability(cwd=cwd, which=which)

    coordinator_probe = _probe_if_allowed("coordinatorCheck", cwd=cwd, probe=probe, runner=runner, timeout=timeout)
    setup_probe = _probe_if_allowed("hermesSetupSmoke", cwd=cwd, probe=probe, runner=runner, timeout=timeout)
    memory_probe = _probe_if_allowed("hermesMemoryStatus", cwd=cwd, probe=probe, runner=runner, timeout=timeout)
    mcp_probe = _probe_if_allowed("hermesMcpList", cwd=cwd, probe=probe, runner=runner, timeout=timeout)
    helper_contracts = _probe_helper_contracts(commands=commands, cwd=cwd, probe=probe, runner=runner, timeout=timeout)

    coordinator_json = coordinator_probe.get("json") if isinstance(coordinator_probe.get("json"), dict) else {}
    coordinator_tools = list(coordinator_json.get("tools", [])) if coordinator_json else []
    missing_coordinator_tools = [tool for tool in REQUIRED_COORDINATOR_TOOLS if tool not in coordinator_tools]
    missing_delegate_tools = [tool for tool in DELEGATE_TOOLS if tool not in coordinator_tools]
    mutation_env = os.environ.get("GJC_COORDINATOR_MCP_MUTATIONS", "")
    mutation_classes = [part.strip() for part in mutation_env.split(",") if part.strip()]

    memory_provider = None
    if isinstance(memory_probe.get("stdout"), str):
        memory_provider = _parse_memory_provider(memory_probe["stdout"])
    memory_provider_surface = _memory_provider_tool_surface(memory_provider)
    memory_api_surface = _just_chill_memory_api_surface(mcp_probe)

    return {
        "schemaVersion": SCHEMA_VERSION,
        "discoveredBy": LIVE_BINDING_NAME,
        "cwd": cwd,
        "probeMode": "read-only-smoke" if probe else "availability-only",
        "commands": commands,
        "operatorConsent": {
            "allowMutation": False,
            "source": "not-provided",
            "requiredPerMutatingCall": True,
        },
        "visibleRoutedSession": {
            "status": _visible_status(commands, helper_contracts, probe=probe),
            "orchestrationMode": ORCHESTRATION_MODE,
            "orchestrationPlanReady": _visible_status(commands, helper_contracts, probe=probe) == "orchestration-plan-ready",
            "requiredOrchestrationTools": ["tmux", "gjc"],
            "missingOrchestrationTools": [name for name in ["tmux", "gjc"] if not commands[name]["available"]],
            "helpers": {name: commands[name] for name in HOST_HELPERS},
            "helperContracts": helper_contracts,
            "tmux": commands["tmux"],
            "hostOwnsHelperImplementation": True,
            "scrollbackIsCompletion": False,
            "evidencePolicy": {
                "durableEvidenceRequired": True,
                "acceptedEvidenceKinds": ACCEPTED_EVIDENCE_KINDS,
                "rejectedEvidenceKinds": REJECTED_EVIDENCE_KINDS,
                "scrollbackIsCompletion": False,
            },
        },
        "coordinatorMcp": {
            "status": "smoke-ok" if coordinator_probe.get("ok") and not missing_coordinator_tools else ("not-probed" if not probe else "unavailable-or-incomplete"),
            "probe": coordinator_probe,
            "requiredTools": REQUIRED_COORDINATOR_TOOLS,
            "availableTools": coordinator_tools,
            "missingTools": missing_coordinator_tools,
            "mutationClassesEnabled": mutation_classes,
            "mutationClassesRequiredForExecution": ["sessions", "questions", "reports"],
            "failClosedWithoutMutationOptIn": True,
        },
        "gjcDelegation": {
            "status": "delegate-tools-present" if coordinator_tools and not missing_delegate_tools else ("not-probed" if not probe else "unavailable-or-incomplete"),
            "delegateTools": {
                tool: {"skill": skill, "availableViaCoordinator": tool in coordinator_tools}
                for tool, skill in DELEGATE_TOOLS.items()
            },
            "missingTools": missing_delegate_tools,
            "requiresCoordinatorTurnPolling": True,
            "failClosedWithoutAllowMutation": True,
        },
        "rpcHostTools": {
            "status": "contract-only",
            "hostCustomToolsRegistryMapped": False,
            "requiredHostTools": [
                "hermes_route_message",
                "hermes_artifact_read",
                "hermes_memory_recall",
                "just_chill_policy_check",
            ],
            "unresolved": "No live RPC host customTools registry is mapped in this repo slice.",
        },
        "hermes": {
            "status": "provider-status-readable" if memory_probe.get("ok") else ("not-probed" if not probe else "unavailable-or-incomplete"),
            "command": commands["hermes"],
            "memoryProvider": memory_provider,
            "memoryProbe": memory_probe,
            "mcpProbe": mcp_probe,
            "setupSmoke": setup_probe,
            "memoryProviderSurface": memory_provider_surface,
            "rawArtifactApi": memory_api_surface.get("rawArtifactApi") or memory_provider_surface.get("rawArtifactApi", "unmapped"),
            "rawArtifactReadApi": memory_api_surface.get("rawArtifactReadApi") or memory_provider_surface.get("rawArtifactReadApi", "unmapped"),
            "rawArtifactDeleteApi": memory_api_surface.get("rawArtifactDeleteApi") or memory_provider_surface.get("rawArtifactDeleteApi", "unmapped"),
            "rdfGraphApi": memory_api_surface.get("rdfGraphApi", "unmapped"),
            "rdfGraphReadApi": memory_api_surface.get("rdfGraphReadApi", "unmapped"),
            "rdfGraphDeleteApi": memory_api_surface.get("rdfGraphDeleteApi", "unmapped"),
            "vectorSidecarCreateApi": memory_api_surface.get("vectorSidecarCreateApi", "unmapped"),
            "vectorSidecarSearchApi": memory_api_surface.get("vectorSidecarSearchApi", "unmapped"),
            "vectorSidecarReadApi": memory_api_surface.get("vectorSidecarReadApi", "unmapped"),
            "vectorSidecarDeleteApi": memory_api_surface.get("vectorSidecarDeleteApi", "unmapped"),
            "vectorSidecarAvailable": bool(memory_api_surface.get("vectorSidecarAvailable")),
            "summaryMemoryApi": memory_provider_surface.get("summaryMemoryApi", "unmapped"),
            "memoryToolWriteAvailable": bool(memory_provider_surface.get("summaryMemoryWriteAvailable")),
            "liveStorageWriteAvailable": bool(memory_api_surface.get("liveStorageWriteAvailable")),
            "justChillMemoryApiSurface": memory_api_surface,
            "storageAuthority": "Hermes",
        },
    }


def build_visible_session_handoff(bridge_plan: dict[str, Any], surfaces: dict[str, Any]) -> dict[str, Any]:
    """Build operator instructions for Path 1 without launching a session."""
    bridge = bridge_plan.get("bridgePlan", {})
    if bridge.get("bridgePath") != "visible-routed-session":
        raise ValueError("visible session handoff requires a visible-routed-session bridge plan")

    request = bridge_plan.get("request", "")
    cwd = bridge_plan.get("workdir")
    session_name = safe_session_name(request, cwd)
    task_file_hint = f"/tmp/{session_name}-task.md"
    helper_status = surfaces.get("visibleRoutedSession", {})
    helpers = helper_status.get("helpers", {})
    helper_state = helper_status.get("status")
    all_helpers_available = helper_state == "orchestration-plan-ready"
    if helper_state == "missing-host-helpers":
        blocked_status = "blocked-missing-host-helpers"
    elif helper_state == "host-helpers-present-unverified":
        blocked_status = "blocked-unverified-host-helpers"
    elif helper_state == "metadata-only-ready":
        blocked_status = "blocked-missing-orchestration-tools"
    else:
        blocked_status = "blocked-host-helper-contract"
    helper_cmd = lambda name: helpers.get(name, {}).get("path") or name
    tmux_window = "gjc"
    tmux_pane = "0"
    tmux_target = f"{session_name}:{tmux_window}.{tmux_pane}"

    return {
        "schemaVersion": SCHEMA_VERSION,
        "handoffKind": "visible-gjc-session-operator-plan",
        "status": "ready-for-host-execution" if all_helpers_available else blocked_status,
        "executionAllowedHere": False,
        "sessionName": session_name,
        "taskFileHint": task_file_hint,
        "skillPrompt": bridge.get("sessionPlan", {}).get("skillPrompt"),
        "commands": [
            {
                "step": "create",
                "helper": "create-gjc-session",
                "available": helpers.get("create-gjc-session", {}).get("available", False),
                "argv": [
                    helper_cmd("create-gjc-session"),
                    session_name,
                    cwd or "<worktree-path>",
                    "--tmux-plan",
                    "--tmux-session",
                    session_name,
                    "--tmux-window",
                    tmux_window,
                    "--tmux-pane",
                    tmux_pane,
                ],
            },
            {
                "step": "prompt",
                "helper": "prompt-gjc-session",
                "available": helpers.get("prompt-gjc-session", {}).get("available", False),
                "argv": [
                    helper_cmd("prompt-gjc-session"),
                    session_name,
                    f"@{task_file_hint}",
                    "--tmux-plan",
                    "--tmux-session",
                    session_name,
                    "--tmux-window",
                    tmux_window,
                    "--tmux-pane",
                    tmux_pane,
                    "--tui-ready",
                ],
            },
            {
                "step": "tail-debug-only",
                "helper": "tail-gjc-session",
                "available": helpers.get("tail-gjc-session", {}).get("available", False),
                "argv": [
                    helper_cmd("tail-gjc-session"),
                    session_name,
                    "200",
                    "--tmux-plan",
                    "--tmux-session",
                    session_name,
                    "--tmux-window",
                    tmux_window,
                    "--tmux-pane",
                    tmux_pane,
                ],
            },
        ],
        "orchestration": {
            "mode": ORCHESTRATION_MODE,
            "status": helper_state,
            "planOnly": True,
            "target": tmux_target,
            "requiredTools": helper_status.get("requiredOrchestrationTools", ["tmux", "gjc"]),
            "missingTools": helper_status.get("missingOrchestrationTools", []),
            "operatorOwnsExecution": True,
            "helperStartsProductWork": False,
        },
        "readinessGate": [
            "dedicated worktree exists or is created by the host helper",
            "GJC TUI readiness is confirmed before any operator prompt handoff",
            "prompt handoff uses a task file and operator-visible tmux plan, not hidden injection",
            "helper contracts prove no hidden GJC execution and durable evidence requirements",
        ],
        "evidenceGate": [
            "GJC tool call or file read",
            "todo/plan update",
            "diff/test/report/artifact/PR evidence when applicable",
            "terminal GJC turn_id or explicit report when using coordinator-backed paths",
        ],
        "acceptedEvidenceKinds": ACCEPTED_EVIDENCE_KINDS,
        "rejectedEvidenceKinds": REJECTED_EVIDENCE_KINDS,
        "scrollbackIsCompletion": False,
        "fallbackWhenBlocked": ["coordinator-mcp", "gjc-delegation"],
    }


def _mutation_readiness_issues(surfaces: dict[str, Any], *, label: str) -> list[str]:
    coordinator = surfaces.get("coordinatorMcp", {})
    enabled = set(coordinator.get("mutationClassesEnabled", []))
    required = set(coordinator.get("mutationClassesRequiredForExecution", []))
    issues: list[str] = []
    if not required.issubset(enabled):
        issues.append(f"{label} execution requires sessions, questions, reports mutation classes")
    if surfaces.get("operatorConsent", {}).get("allowMutation") is not True:
        issues.append(f"{label} execution requires explicit per-call allow_mutation consent")
    return issues


def validate_bridge_live_readiness(bridge_plan: dict[str, Any], surfaces: dict[str, Any]) -> list[str]:
    """Return fail-closed live-binding issues for the selected bridge path."""
    issues: list[str] = []
    bridge = bridge_plan.get("bridgePlan", {})
    path = bridge.get("bridgePath")

    if path == "visible-routed-session":
        visible = surfaces.get("visibleRoutedSession", {})
        status = visible.get("status")
        if status == "missing-host-helpers":
            issues.append("visible routed-session helpers are not all available")
        elif status == "host-helpers-present-unverified":
            issues.append("visible routed-session helper contracts were not probed")
        elif status == "metadata-only-ready":
            issues.append("visible routed-session orchestration requires tmux and gjc availability")
        elif status != "orchestration-plan-ready":
            issues.append("visible routed-session helper contracts are invalid")
        if visible.get("orchestrationPlanReady") is not True and status == "orchestration-plan-ready":
            issues.append("visible routed-session orchestration readiness flag is inconsistent")
        if visible.get("scrollbackIsCompletion") is not False:
            issues.append("visible routed-session must reject scrollback-only completion")
        policy = visible.get("evidencePolicy", {})
        if policy.get("durableEvidenceRequired") is not True:
            issues.append("visible routed-session must require durable evidence")
        if policy.get("scrollbackIsCompletion") is not False:
            issues.append("visible routed-session evidence policy must reject scrollback-only completion")
        for name, contract_result in visible.get("helperContracts", {}).items():
            if contract_result.get("status") not in {"ok", "not-probed", "unavailable"} and not contract_result.get("contractValid"):
                issues.append(f"visible routed-session helper {name} contract is invalid")
    elif path == "coordinator-mcp":
        coordinator = surfaces.get("coordinatorMcp", {})
        if coordinator.get("status") != "smoke-ok":
            issues.append("coordinator MCP smoke check is not clean")
        issues.extend(_mutation_readiness_issues(surfaces, label="coordinator MCP"))
    elif path == "gjc-delegation":
        delegation = surfaces.get("gjcDelegation", {})
        delegate_tool = bridge.get("delegateTool")
        if not delegation.get("delegateTools", {}).get(delegate_tool, {}).get("availableViaCoordinator"):
            issues.append(f"delegate tool {delegate_tool!r} is not available via coordinator")
        issues.extend(_mutation_readiness_issues(surfaces, label="delegation"))
    elif path == "rpc-host-tools":
        rpc = surfaces.get("rpcHostTools", {})
        if not rpc.get("hostCustomToolsRegistryMapped"):
            issues.append("RPC host customTools registry is not mapped")
    elif path == "host-tool-or-direct":
        # Non-development route; no GJC live binding is expected here.
        pass
    else:
        issues.append(f"unknown bridge path {path!r}")

    if bridge.get("executionAllowedHere") is not False:
        issues.append("bridge plan must not allow local execution")
    if bridge_plan.get("authorityBoundary", {}).get("noExecutionInThisPlan") is not True:
        issues.append("bridge plan must preserve noExecutionInThisPlan")
    return issues


def validate_visible_completion_evidence(payload: dict[str, Any]) -> list[str]:
    """Validate visible routed-session completion evidence using the host helper contract."""
    return validate_visible_evidence_payload(payload)


def build_live_binding_report(
    packet: dict[str, Any],
    *,
    cwd: str | None,
    probe: bool,
    allow_mutation: bool = False,
) -> dict[str, Any]:
    bridge_plan = build_bridge_plan(packet, cwd=cwd)
    surfaces = discover_live_surfaces(cwd=cwd, probe=probe)
    if allow_mutation:
        surfaces["operatorConsent"] = {
            "allowMutation": True,
            "source": "explicit-cli-flag",
            "requiredPerMutatingCall": True,
        }
    sensitive = packet_is_sensitive(packet)
    report: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "reporter": LIVE_BINDING_NAME,
        "packet": redact_sensitive_report_payload(packet, sensitive=sensitive),
        "bridgePlan": redact_sensitive_report_payload(bridge_plan, sensitive=sensitive),
        "surfaces": surfaces,
        "readinessIssues": validate_bridge_live_readiness(bridge_plan, surfaces),
    }
    if bridge_plan.get("bridgePlan", {}).get("bridgePath") == "visible-routed-session":
        report["visibleSessionHandoff"] = redact_sensitive_report_payload(
            build_visible_session_handoff(bridge_plan, surfaces),
            sensitive=sensitive,
        )
    return report


def packet_from_json(raw: str) -> dict[str, Any]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("packet JSON must decode to an object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Map just-chill live bindings and emit safe handoff instructions.")
    parser.add_argument("request", nargs="*", help="User request text. Ignored when --packet-json is provided.")
    parser.add_argument("--packet-json", help="Existing just_chill_router packet JSON.")
    parser.add_argument("--cwd", default=None, help="Target repo/workdir for discovery and handoff planning.")
    parser.add_argument("--probe", action="store_true", help="Run allowlisted read-only smoke probes.")
    parser.add_argument("--allow-mutation", action="store_true", help="Model explicit per-call allow_mutation consent in readiness checks; does not execute anything.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    packet = packet_from_json(args.packet_json) if args.packet_json else classify_request(" ".join(args.request))
    report = build_live_binding_report(packet, cwd=args.cwd, probe=args.probe, allow_mutation=args.allow_mutation)
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
