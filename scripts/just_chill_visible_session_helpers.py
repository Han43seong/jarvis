#!/usr/bin/env python3
"""Host-owned visible routed-session helper contracts for just-chill.

These helpers intentionally keep the visible routed-session lane observable and
fail-closed. They write small host metadata records and emit JSON instructions;
they do not start hidden GJC work, do not call GJC delegation tools, and never
accept tmux scrollback as completion evidence.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
HELPER_CONTRACT_VERSION = "just-chill-visible-session-helper-v1"
DEFAULT_STATE_DIRNAME = "just-chill-visible-sessions"
ORCHESTRATION_MODE = "tmux-orchestration-plan-v1"
SUPPORTED_HELPER_MODES = ["metadata-only-visible-session-v1", ORCHESTRATION_MODE]
TMUX_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
TMUX_PANE_PATTERN = re.compile(r"^[0-9]{1,4}$")
SAFE_COMMAND_PATTERN = re.compile(r"^[A-Za-z0-9_./-]+$")
SESSION_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,95}$")

ACCEPTED_EVIDENCE_KINDS = [
    "tool_call",
    "file_read",
    "todo_update",
    "plan_update",
    "diff",
    "test",
    "report",
    "artifact",
    "pr",
    "turn_id",
    "coordination_report",
]
REJECTED_EVIDENCE_KINDS = [
    "scrollback",
    "tmux_scrollback",
    "tmux-scrollback",
    "tail",
    "pane_capture",
    "pane-capture",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def default_state_dir() -> Path:
    configured = os.environ.get("JUST_CHILL_VISIBLE_SESSION_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(tempfile.gettempdir(), DEFAULT_STATE_DIRNAME).resolve()


def session_record_path(session_name: str, state_dir: Path | None = None) -> Path:
    root = (state_dir or default_state_dir()).resolve()
    return root / f"{session_name}.json"


def validate_session_name(session_name: str) -> list[str]:
    issues: list[str] = []
    if not SESSION_NAME_PATTERN.match(session_name):
        issues.append("session name must be 3-96 chars of letters, numbers, dot, underscore, or dash and start alphanumeric")
    if ".." in session_name:
        issues.append("session name must not contain '..'")
    return issues


def validate_worktree_path(worktree_path: str) -> list[str]:
    issues: list[str] = []
    path = Path(worktree_path).expanduser()
    if not path.is_absolute():
        issues.append("worktree path must be absolute")
    resolved = path.resolve()
    if not resolved.exists():
        issues.append("worktree path must exist before helper metadata is recorded")
    elif not resolved.is_dir():
        issues.append("worktree path must be a directory")
    return issues
def validate_tmux_target(tmux_session: str, tmux_window: str, tmux_pane: str) -> list[str]:
    issues: list[str] = []
    if not TMUX_NAME_PATTERN.match(tmux_session):
        issues.append("tmux session must be 1-96 chars of letters, numbers, dot, underscore, or dash and start alphanumeric")
    if not TMUX_NAME_PATTERN.match(tmux_window):
        issues.append("tmux window must be 1-96 chars of letters, numbers, dot, underscore, or dash and start alphanumeric")
    if not TMUX_PANE_PATTERN.match(tmux_pane):
        issues.append("tmux pane must be a numeric pane id")
    return issues


def _command_readiness(command_name: str) -> dict[str, Any]:
    if not SAFE_COMMAND_PATTERN.match(command_name):
        return {
            "command": command_name,
            "available": False,
            "path": None,
            "issues": ["command must be an argv-safe binary name or absolute path"],
        }
    path = shutil.which(command_name) if "/" not in command_name else command_name
    available = bool(path and (Path(path).exists() if "/" in command_name else True))
    return {
        "command": command_name,
        "available": available,
        "path": path if available else None,
        "issues": [] if available else [f"{command_name} is not available on PATH"],
    }


def build_tmux_orchestration_plan(
    session_name: str,
    worktree_path: str,
    *,
    tmux_session: str | None = None,
    tmux_window: str = "gjc",
    tmux_pane: str = "0",
    gjc_command: str = "gjc",
    task_path: str | None = None,
    lines: int = 200,
) -> dict[str, Any]:
    """Build a deterministic tmux/GJC plan without running tmux or GJC."""

    target_session = tmux_session or session_name
    issues = [
        *validate_tmux_target(target_session, tmux_window, tmux_pane),
        *validate_worktree_path(worktree_path),
    ]
    if not SAFE_COMMAND_PATTERN.match(gjc_command):
        issues.append("gjc command must be an argv-safe binary name or absolute path")

    tmux_ready = _command_readiness("tmux")
    gjc_ready = _command_readiness(gjc_command)
    if tmux_ready["issues"]:
        issues.extend(tmux_ready["issues"])
    if gjc_ready["issues"]:
        issues.extend(gjc_ready["issues"])

    target = f"{target_session}:{tmux_window}.{tmux_pane}"
    status = "orchestration-plan-ready" if not issues else "orchestration-plan-unavailable"
    task_display = task_path or "<absolute-task-file>"

    return {
        "schemaVersion": SCHEMA_VERSION,
        "mode": ORCHESTRATION_MODE,
        "status": status,
        "issues": issues,
        "executesCommands": False,
        "executesGjc": False,
        "executesProductWork": False,
        "operatorOwnsExecution": True,
        "executionAllowedHere": False,
        "scrollbackIsCompletion": False,
        "durableEvidenceRequired": True,
        "tmuxTarget": {
            "session": target_session,
            "window": tmux_window,
            "pane": tmux_pane,
            "target": target,
        },
        "toolReadiness": {
            "tmux": tmux_ready,
            "gjc": gjc_ready,
        },
        "argvPlan": [
            {
                "step": "create-visible-gjc-tui",
                "operatorRuns": True,
                "helperRuns": False,
                "argv": ["tmux", "new-session", "-d", "-s", target_session, "-n", tmux_window, "-c", str(Path(worktree_path).expanduser().resolve()), gjc_command],
                "purpose": "create a visible host-owned GJC TUI session; this starts no hidden product work from just-chill",
            },
            {
                "step": "attach-visible-gjc-tui",
                "operatorRuns": True,
                "helperRuns": False,
                "argv": ["tmux", "attach-session", "-t", f"{target_session}:{tmux_window}"],
                "purpose": "make the routed session visible to the operator before any prompt handoff",
            },
            {
                "step": "verify-visible-pane",
                "operatorRuns": True,
                "helperRuns": False,
                "argv": ["tmux", "has-session", "-t", target],
                "purpose": "confirm the target visible pane exists before prompt delivery",
            },
            {
                "step": "prompt-handoff",
                "operatorRuns": True,
                "helperRuns": False,
                "argv": ["tmux", "display-message", "-t", target, f"just-chill prompt ready at @{task_display}; paste into visible GJC only after TUI readiness"],
                "purpose": "notify the visible pane about a prompt file; this is not hidden prompt injection",
            },
            {
                "step": "tail-debug-only",
                "operatorRuns": True,
                "helperRuns": False,
                "argv": ["tmux", "capture-pane", "-p", "-t", target, "-S", f"-{lines}"],
                "purpose": "debug-only pane capture; never accepted as completion evidence",
            },
        ],
        "operatorInstructions": [
            "Run only the argv plan steps the operator explicitly chooses.",
            "Do not treat pane capture or scrollback as completion evidence.",
            "Collect durable GJC evidence: tool calls, file reads, diffs, tests, reports, artifacts, PRs, or turn_id receipts.",
        ],
    }



def _jsonable_path(path: Path) -> str:
    return str(path.resolve())


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp_path, path)


def load_session_record(session_name: str, state_dir: Path | None = None) -> dict[str, Any]:
    path = session_record_path(session_name, state_dir)
    return json.loads(path.read_text(encoding="utf-8"))


def helper_contract(helper_name: str) -> dict[str, Any]:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "contractVersion": HELPER_CONTRACT_VERSION,
        "helper": helper_name,
        "ownedBy": "host",
        "mode": "metadata-only-visible-session-v1",
        "supportedModes": SUPPORTED_HELPER_MODES,
        "executesGjc": False,
        "executesProductWork": False,
        "callsGjcDelegateTools": False,
        "writesHermesMemory": False,
        "scrollbackIsCompletion": False,
        "durableEvidenceRequired": True,
        "acceptedEvidenceKinds": ACCEPTED_EVIDENCE_KINDS,
        "rejectedEvidenceKinds": REJECTED_EVIDENCE_KINDS,
        "stateDirEnv": "JUST_CHILL_VISIBLE_SESSION_DIR",
        "orchestrationPlanning": {
            "supported": True,
            "mode": ORCHESTRATION_MODE,
            "emitsArgvPlan": True,
            "executesCommands": False,
            "helperRunsTmux": False,
            "helperInjectsPrompt": False,
            "operatorOwnsExecution": True,
        },
    }


def create_session_record(
    session_name: str,
    worktree_path: str,
    *,
    channel_id: str | None = None,
    mention: str | None = None,
    state_dir: Path | None = None,
    orchestration_plan: bool = False,
    tmux_session: str | None = None,
    tmux_window: str = "gjc",
    tmux_pane: str = "0",
    gjc_command: str = "gjc",
) -> dict[str, Any]:
    issues = [*validate_session_name(session_name), *validate_worktree_path(worktree_path)]
    plan = None
    if orchestration_plan:
        plan = build_tmux_orchestration_plan(
            session_name,
            worktree_path,
            tmux_session=tmux_session,
            tmux_window=tmux_window,
            tmux_pane=tmux_pane,
            gjc_command=gjc_command,
        )
        issues.extend(plan["issues"])
    if issues:
        return {
            "ok": False,
            "schemaVersion": SCHEMA_VERSION,
            "helper": "create-gjc-session",
            "issues": issues,
            "orchestrationPlan": plan,
        }

    record_path = session_record_path(session_name, state_dir)
    record = {
        "ok": True,
        "schemaVersion": SCHEMA_VERSION,
        "helper": "create-gjc-session",
        "sessionName": session_name,
        "status": "orchestration-plan-recorded" if plan else "metadata-recorded",
        "recordPath": _jsonable_path(record_path),
        "createdAt": utc_now(),
        "updatedAt": utc_now(),
        "worktreePath": _jsonable_path(Path(worktree_path).expanduser()),
        "channelId": channel_id,
        "mention": mention,
        "executionAllowedHere": False,
        "hiddenExecutionStarted": False,
        "productWorkStarted": False,
        "tuiReady": False,
        "promptPrepared": False,
        "promptInjectedByHelper": False,
        "scrollbackIsCompletion": False,
        "durableEvidenceRequired": True,
        "supportedHelperModes": SUPPORTED_HELPER_MODES,
        "orchestrationPlan": plan,
        "evidence": [],
        "operatorActionRequired": "start or attach the visible GJC TUI in the recorded worktree, then run prompt-gjc-session after readiness",
        "nextHelper": "prompt-gjc-session",
    }
    _atomic_write_json(record_path, record)
    return record


def _validate_task_ref(task_ref: str) -> tuple[list[str], str | None]:
    issues: list[str] = []
    if not task_ref.startswith("@"):
        issues.append("task reference must use @/absolute/path/to/task.md")
        return issues, None
    task_path = Path(task_ref[1:]).expanduser()
    if not task_path.is_absolute():
        issues.append("task file path must be absolute")
    resolved = task_path.resolve()
    if not resolved.exists():
        issues.append("task file must exist before prompt handoff metadata is recorded")
    elif not resolved.is_file():
        issues.append("task file must be a regular file")
    return issues, str(resolved)


def prepare_prompt_record(
    session_name: str,
    task_ref: str,
    *,
    tui_ready: bool = False,
    state_dir: Path | None = None,
    orchestration_plan: bool = False,
    tmux_session: str | None = None,
    tmux_window: str = "gjc",
    tmux_pane: str = "0",
    gjc_command: str = "gjc",
) -> dict[str, Any]:
    issues = validate_session_name(session_name)
    task_issues, task_path = _validate_task_ref(task_ref)
    issues.extend(task_issues)
    record_path = session_record_path(session_name, state_dir)
    if not record_path.exists():
        issues.append("session metadata record does not exist; run create-gjc-session first")
    if issues:
        return {
            "ok": False,
            "schemaVersion": SCHEMA_VERSION,
            "helper": "prompt-gjc-session",
            "issues": issues,
            "orchestrationPlan": None,
        }

    record = load_session_record(session_name, state_dir)
    plan = record.get("orchestrationPlan")
    if orchestration_plan:
        plan = build_tmux_orchestration_plan(
            session_name,
            str(record["worktreePath"]),
            tmux_session=tmux_session,
            tmux_window=tmux_window,
            tmux_pane=tmux_pane,
            gjc_command=gjc_command,
            task_path=task_path,
        )
        if plan["issues"]:
            return {
                "ok": False,
                "schemaVersion": SCHEMA_VERSION,
                "helper": "prompt-gjc-session",
                "issues": plan["issues"],
                "orchestrationPlan": plan,
            }
    record.update(
        {
            "updatedAt": utc_now(),
            "helper": "prompt-gjc-session",
            "tuiReady": bool(tui_ready),
            "promptPrepared": True,
            "promptInjectedByHelper": False,
            "taskFile": task_path,
            "promptDelivery": {
                "status": "prepared-for-visible-operator-injection",
                "taskFile": task_path,
                "tuiReadyConfirmed": bool(tui_ready),
                "helperExecutedPrompt": False,
                "operatorActionRequired": "inject the task into the visible GJC pane only after TUI readiness is confirmed",
            },
            "orchestrationPlan": plan,
        }
    )
    _atomic_write_json(record_path, record)
    return {"ok": True, "schemaVersion": SCHEMA_VERSION, "helper": "prompt-gjc-session", "recordPath": _jsonable_path(record_path), "session": record}


def _evidence_signals(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if "kind" in payload:
        return [payload]
    signals = payload.get("signals")
    if isinstance(signals, list):
        return [signal for signal in signals if isinstance(signal, dict)]
    evidence = payload.get("evidence")
    if isinstance(evidence, list):
        return [signal for signal in evidence if isinstance(signal, dict)]
    return []


VAGUE_DESCRIPTION_VALUES = {"done", "ok", "complete", "completed", "passed", "success"}


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_command_evidence(value: Any) -> bool:
    if isinstance(value, list):
        return bool(value) and all(isinstance(part, str) and bool(part.strip()) for part in value)
    return False


def _has_concrete_evidence_reference(signal: dict[str, Any]) -> bool:
    if any(_non_empty_string(signal.get(key)) for key in ["source", "path", "artifact", "turn_id"]):
        return True
    description = signal.get("description")
    if _non_empty_string(description) and len(description.strip()) >= 12 and description.strip().lower() not in VAGUE_DESCRIPTION_VALUES:
        return True
    return _valid_command_evidence(signal.get("command"))


def _evidence_reference_issue(kind: str, signal: dict[str, Any]) -> str | None:
    if _has_concrete_evidence_reference(signal):
        return None
    if "command" in signal and not _valid_command_evidence(signal.get("command")):
        return f"{kind} evidence command must be a non-empty argv array"
    if "description" in signal:
        return f"{kind} evidence description must be concrete, not a vague completion word"
    return f"{kind} evidence requires source, path, artifact, turn_id, concrete description, or argv command"



def validate_visible_evidence_payload(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    signals = _evidence_signals(payload)
    if not signals:
        return ["at least one durable evidence signal is required"]

    accepted_seen = False
    rejected_seen = False
    for signal in signals:
        kind = str(signal.get("kind", "")).lower().replace(" ", "_")
        if kind in REJECTED_EVIDENCE_KINDS:
            rejected_seen = True
            issues.append(f"{kind} is debug-only and cannot prove completion")
            continue
        if kind in ACCEPTED_EVIDENCE_KINDS:
            accepted_seen = True
            reference_issue = _evidence_reference_issue(kind, signal)
            if reference_issue:
                issues.append(reference_issue)
        else:
            issues.append(f"unsupported evidence kind {kind!r}")

    if not accepted_seen:
        issues.append("at least one non-scrollback durable evidence signal is required")
    if rejected_seen and accepted_seen:
        issues.append("scrollback evidence may be kept only as debug context, not as a completion source")
    return issues


def build_tail_report(
    session_name: str,
    *,
    lines: int = 200,
    evidence: dict[str, Any] | None = None,
    state_dir: Path | None = None,
    orchestration_plan: bool = False,
    tmux_session: str | None = None,
    tmux_window: str = "gjc",
    tmux_pane: str = "0",
    gjc_command: str = "gjc",
) -> dict[str, Any]:
    issues = validate_session_name(session_name)
    record_path = session_record_path(session_name, state_dir)
    if not record_path.exists():
        issues.append("session metadata record does not exist; run create-gjc-session first")
    if lines < 1 or lines > 1000:
        issues.append("lines must be between 1 and 1000")
    if issues:
        return {
            "ok": False,
            "schemaVersion": SCHEMA_VERSION,
            "helper": "tail-gjc-session",
            "issues": issues,
            "orchestrationPlan": None,
        }

    record = load_session_record(session_name, state_dir)
    plan = record.get("orchestrationPlan")
    if orchestration_plan:
        plan = build_tmux_orchestration_plan(
            session_name,
            str(record["worktreePath"]),
            tmux_session=tmux_session,
            tmux_window=tmux_window,
            tmux_pane=tmux_pane,
            gjc_command=gjc_command,
            task_path=record.get("taskFile"),
            lines=lines,
        )
        if plan["issues"]:
            return {
                "ok": False,
                "schemaVersion": SCHEMA_VERSION,
                "helper": "tail-gjc-session",
                "issues": plan["issues"],
                "orchestrationPlan": plan,
            }
    evidence_issues = validate_visible_evidence_payload(evidence) if evidence is not None else ["no durable evidence payload supplied"]
    return {
        "ok": True,
        "schemaVersion": SCHEMA_VERSION,
        "helper": "tail-gjc-session",
        "sessionName": session_name,
        "recordPath": _jsonable_path(record_path),
        "requestedLines": lines,
        "scrollbackCaptured": False,
        "scrollbackIsCompletion": False,
        "debugOnly": True,
        "session": record,
        "evidenceValidation": {
            "accepted": evidence is not None and not evidence_issues,
            "issues": evidence_issues,
        },
        "orchestrationPlan": plan,
    }


def _emit(payload: dict[str, Any], *, pretty: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None, sort_keys=True))


def _state_dir_arg(value: str | None) -> Path | None:
    return Path(value).expanduser().resolve() if value else None


def main_create(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record a host-owned visible GJC session handoff.")
    parser.add_argument("session_name", nargs="?")
    parser.add_argument("worktree_path", nargs="?")
    parser.add_argument("channel_id", nargs="?")
    parser.add_argument("mention", nargs="?")
    parser.add_argument("--state-dir")
    parser.add_argument("--contract", action="store_true")
    parser.add_argument("--json", action="store_true", help="Accepted for helper-contract compatibility; output is always JSON.")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--tmux-plan", action="store_true", help="Emit a dry-run tmux/GJC orchestration argv plan without executing it.")
    parser.add_argument("--tmux-session")
    parser.add_argument("--tmux-window", default="gjc")
    parser.add_argument("--tmux-pane", default="0")
    parser.add_argument("--gjc-command", default="gjc")
    args = parser.parse_args(argv)
    if args.contract:
        _emit({"ok": True, "contract": helper_contract("create-gjc-session")}, pretty=args.pretty)
        return 0
    if not args.session_name or not args.worktree_path:
        _emit({"ok": False, "schemaVersion": SCHEMA_VERSION, "helper": "create-gjc-session", "issues": ["session_name and worktree_path are required"]}, pretty=args.pretty)
        return 2
    payload = create_session_record(
        args.session_name,
        args.worktree_path,
        channel_id=args.channel_id,
        mention=args.mention,
        state_dir=_state_dir_arg(args.state_dir),
        orchestration_plan=args.tmux_plan,
        tmux_session=args.tmux_session,
        tmux_window=args.tmux_window,
        tmux_pane=args.tmux_pane,
        gjc_command=args.gjc_command,
    )
    _emit(payload, pretty=args.pretty)
    return 0 if payload.get("ok") else 2


def main_prompt(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare a visible GJC prompt handoff without hidden execution.")
    parser.add_argument("session_name", nargs="?")
    parser.add_argument("task_ref", nargs="?")
    parser.add_argument("--state-dir")
    parser.add_argument("--tui-ready", action="store_true")
    parser.add_argument("--contract", action="store_true")
    parser.add_argument("--json", action="store_true", help="Accepted for helper-contract compatibility; output is always JSON.")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--tmux-plan", action="store_true", help="Emit a dry-run tmux/GJC orchestration argv plan without executing it.")
    parser.add_argument("--tmux-session")
    parser.add_argument("--tmux-window", default="gjc")
    parser.add_argument("--tmux-pane", default="0")
    parser.add_argument("--gjc-command", default="gjc")
    args = parser.parse_args(argv)
    if args.contract:
        _emit({"ok": True, "contract": helper_contract("prompt-gjc-session")}, pretty=args.pretty)
        return 0
    if not args.session_name or not args.task_ref:
        _emit({"ok": False, "schemaVersion": SCHEMA_VERSION, "helper": "prompt-gjc-session", "issues": ["session_name and task_ref are required"]}, pretty=args.pretty)
        return 2
    payload = prepare_prompt_record(
        args.session_name,
        args.task_ref,
        tui_ready=args.tui_ready,
        state_dir=_state_dir_arg(args.state_dir),
        orchestration_plan=args.tmux_plan,
        tmux_session=args.tmux_session,
        tmux_window=args.tmux_window,
        tmux_pane=args.tmux_pane,
        gjc_command=args.gjc_command,
    )
    _emit(payload, pretty=args.pretty)
    return 0 if payload.get("ok") else 2


def main_tail(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read visible-session metadata and validate durable evidence.")
    parser.add_argument("session_name", nargs="?")
    parser.add_argument("lines", nargs="?", type=int, default=200)
    parser.add_argument("--state-dir")
    parser.add_argument("--evidence-json")
    parser.add_argument("--contract", action="store_true")
    parser.add_argument("--json", action="store_true", help="Accepted for helper-contract compatibility; output is always JSON.")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--tmux-plan", action="store_true", help="Emit a dry-run tmux/GJC orchestration argv plan without executing it.")
    parser.add_argument("--tmux-session")
    parser.add_argument("--tmux-window", default="gjc")
    parser.add_argument("--tmux-pane", default="0")
    parser.add_argument("--gjc-command", default="gjc")
    args = parser.parse_args(argv)
    if args.contract:
        _emit({"ok": True, "contract": helper_contract("tail-gjc-session")}, pretty=args.pretty)
        return 0
    if not args.session_name:
        _emit({"ok": False, "schemaVersion": SCHEMA_VERSION, "helper": "tail-gjc-session", "issues": ["session_name is required"]}, pretty=args.pretty)
        return 2
    evidence = json.loads(args.evidence_json) if args.evidence_json else None
    payload = build_tail_report(
        args.session_name,
        lines=args.lines,
        evidence=evidence,
        state_dir=_state_dir_arg(args.state_dir),
        orchestration_plan=args.tmux_plan,
        tmux_session=args.tmux_session,
        tmux_window=args.tmux_window,
        tmux_pane=args.tmux_pane,
        gjc_command=args.gjc_command,
    )
    _emit(payload, pretty=args.pretty)
    return 0 if payload.get("ok") else 2
