#!/usr/bin/env python3
"""Host-owned GJC execution bridge contract for just-chill.

This bridge consumes a just-chill GJC handoff plan and prepares visible-session
operator artifacts. It deliberately does not start tmux, execute GJC, call
coordinator/delegate tools, or claim completion. Completion is accepted only
when a separate host/operator supplies durable non-scrollback evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from just_chill_harness import gjc_handoff_plan
from just_chill_visible_session_helpers import (
    build_tail_report,
    create_session_record,
    prepare_prompt_record,
    validate_session_name,
    validate_visible_evidence_payload,
)

SCHEMA_VERSION = 1
BRIDGE_NAME = "just-chill-gjc-execution-bridge-v1"
DEFAULT_BRIDGE_DIRNAME = "just-chill-gjc-execution-bridge"
VISIBLE_BRIDGE_PATH = "visible-routed-session"
SESSION_SAFE_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def json_text(data: Any, *, pretty: bool = False) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2 if pretty else None, sort_keys=True)


def default_bridge_root() -> Path:
    return Path(os.environ.get("JUST_CHILL_GJC_EXECUTION_BRIDGE_DIR", Path(tempfile.gettempdir(), DEFAULT_BRIDGE_DIRNAME))).expanduser().resolve()


def bridge_root(path: str | os.PathLike[str] | None = None) -> Path:
    return Path(path).expanduser().resolve() if path else default_bridge_root()


def authority_boundary() -> dict[str, bool]:
    return {
        "executionAllowedHere": False,
        "justChillExecutesGjc": False,
        "justChillCallsCoordinator": False,
        "justChillCallsDelegateTools": False,
        "justChillWritesHermes": False,
        "hostBridgeExecutesCommands": False,
        "hostBridgeStartsGjc": False,
        "hostBridgeInjectsPrompt": False,
        "scrollbackIsCompletion": False,
        "durableEvidenceRequired": True,
    }


def stable_session_name(request: str, cwd: str | None = None) -> str:
    seed = f"{cwd or ''}\0{request}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"jc-gjc-{digest}"


def _safe_filename(value: str) -> str:
    cleaned = SESSION_SAFE_PATTERN.sub("-", value.strip()).strip("-._")
    return cleaned[:96] or "gjc-task"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    os.replace(tmp_path, path)


def _load_handoff_plan(raw: str | dict[str, Any] | None, request: str, cwd: str | None, allow_mutation: bool) -> dict[str, Any]:
    if raw is None:
        return gjc_handoff_plan(request, cwd=cwd, allow_mutation=allow_mutation)
    if isinstance(raw, dict):
        return raw
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("handoff plan JSON must decode to an object")
    return parsed


def _bridge_path(plan: dict[str, Any]) -> str | None:
    return ((plan.get("bridgePlan") or {}).get("bridgePlan") or {}).get("bridgePath")


def _plan_request(plan: dict[str, Any], fallback: str) -> str:
    bridge = plan.get("bridgePlan") or {}
    dev = bridge.get("developmentHandoff") or plan.get("developmentHandoff") or {}
    return str(dev.get("request") or plan.get("request") or fallback)


def _task_markdown(*, request: str, cwd: str | None, handoff: dict[str, Any]) -> str:
    bridge = handoff.get("bridgePlan") or {}
    route_hint = (bridge.get("developmentHandoff") or {}).get("routeHint") or handoff.get("routeHint") or "gjc-direct"
    evidence = bridge.get("completionEvidenceRequired") or handoff.get("completionEvidenceRequired") or [
        "durable GJC turn/report/artifact/diff/test evidence",
    ]
    forbidden = bridge.get("forbiddenActions") or ["tmux scrollback as completion evidence"]
    return "\n".join([
        "# just-chill routed GJC task",
        "",
        f"- Bridge: `{BRIDGE_NAME}`",
        f"- Created: `{utc_now()}`",
        f"- Worktree: `{cwd or ''}`",
        f"- Route hint: `{route_hint}`",
        "- Execution boundary: host/operator-owned visible GJC only; just-chill does not execute this task.",
        "",
        "## User request",
        "",
        request.strip(),
        "",
        "## Required completion evidence",
        "",
        *[f"- {item}" for item in evidence],
        "",
        "## Forbidden completion evidence",
        "",
        *[f"- {item}" for item in forbidden],
        "- tmux pane capture / scrollback alone",
        "",
        "## Operator instruction",
        "",
        "Run this only in the visible GJC session prepared by the bridge. Return durable evidence such as turn_id, report, artifact, diff, test output, or PR reference.",
        "",
    ])


def prepare_visible_execution(
    request: str,
    *,
    cwd: str | None = None,
    handoff_plan: str | dict[str, Any] | None = None,
    session_name: str | None = None,
    bridge_dir: str | os.PathLike[str] | None = None,
    state_dir: str | os.PathLike[str] | None = None,
    allow_mutation: bool = False,
    tui_ready: bool = False,
    tmux_session: str | None = None,
    tmux_window: str = "gjc",
    tmux_pane: str = "0",
    gjc_command: str = "gjc",
) -> dict[str, Any]:
    root = bridge_root(bridge_dir)
    target_cwd = str(Path(cwd or os.getcwd()).expanduser().resolve())
    session = session_name or stable_session_name(request, target_cwd)
    issues = validate_session_name(session)
    try:
        handoff = _load_handoff_plan(handoff_plan, request, target_cwd, allow_mutation)
    except Exception as exc:
        handoff = None
        issues.append(f"handoff plan could not be loaded: {exc}")
    if handoff is not None and _bridge_path(handoff) != VISIBLE_BRIDGE_PATH:
        issues.append(f"execution bridge MVP supports only {VISIBLE_BRIDGE_PATH!r}; got {_bridge_path(handoff)!r}")

    output: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "bridge": BRIDGE_NAME,
        "operation": "prepare-visible-execution",
        "status": "blocked" if issues else "visible-execution-prepared",
        "executionAllowedHere": False,
        "authorityBoundary": authority_boundary(),
        "request": request,
        "cwd": target_cwd,
        "sessionName": session,
        "bridgeRoot": str(root),
        "blockedReasons": issues,
        "handoffPlan": handoff,
        "taskFile": None,
        "taskFileHash": None,
        "sessionRecord": None,
        "promptRecord": None,
        "hostOwnedNextSteps": [],
    }
    if issues:
        output["hostOwnedNextSteps"].append("fix blockedReasons before opening a visible GJC session")
        return output

    effective_request = _plan_request(handoff, request)
    task_path = root / "tasks" / f"{_safe_filename(session)}.md"
    task_text = _task_markdown(request=effective_request, cwd=target_cwd, handoff=handoff)
    _write_text(task_path, task_text)
    digest = hashlib.sha256(task_text.encode("utf-8")).hexdigest()
    state_root = Path(state_dir).expanduser().resolve() if state_dir else root / "sessions"
    session_record = create_session_record(
        session,
        target_cwd,
        state_dir=state_root,
        orchestration_plan=True,
        tmux_session=tmux_session,
        tmux_window=tmux_window,
        tmux_pane=tmux_pane,
        gjc_command=gjc_command,
    )
    prompt_record = None
    if session_record.get("ok"):
        prompt_record = prepare_prompt_record(
            session,
            "@" + str(task_path),
            state_dir=state_root,
            tui_ready=tui_ready,
            orchestration_plan=True,
            tmux_session=tmux_session,
            tmux_window=tmux_window,
            tmux_pane=tmux_pane,
            gjc_command=gjc_command,
        )
    if not session_record.get("ok") or (prompt_record and not prompt_record.get("ok")):
        output["status"] = "blocked"
        output["blockedReasons"].extend(session_record.get("issues", []))
        if prompt_record:
            output["blockedReasons"].extend(prompt_record.get("issues", []))
    output.update({
        "taskFile": str(task_path),
        "taskFileHash": "sha256:" + digest,
        "sessionStateDir": str(state_root),
        "sessionRecord": session_record,
        "promptRecord": prompt_record,
        "hostOwnedNextSteps": [
            "operator reviews taskFile",
            "operator runs only chosen argvPlan steps in a visible terminal",
            "GJC returns durable evidence: turn_id/report/artifact/diff/test/PR reference",
            "call verify-completion with durable evidence; never use scrollback as completion evidence",
        ],
    })
    return output


def verify_completion(
    session_name: str,
    *,
    evidence: dict[str, Any] | str | None,
    bridge_dir: str | os.PathLike[str] | None = None,
    state_dir: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    root = bridge_root(bridge_dir)
    state_root = Path(state_dir).expanduser().resolve() if state_dir else root / "sessions"
    issues = validate_session_name(session_name)
    parsed_evidence: dict[str, Any] | None = None
    if isinstance(evidence, str):
        try:
            parsed = json.loads(evidence)
            if not isinstance(parsed, dict):
                issues.append("evidence JSON must decode to an object")
            else:
                parsed_evidence = parsed
        except Exception as exc:
            issues.append(f"evidence JSON could not be loaded: {exc}")
    elif evidence is None:
        issues.append("evidence is required")
    elif isinstance(evidence, dict):
        parsed_evidence = evidence
    else:
        issues.append("evidence must be an object")

    evidence_issues = validate_visible_evidence_payload(parsed_evidence) if parsed_evidence is not None else []
    issues.extend(evidence_issues)
    tail_report = None
    if not validate_session_name(session_name):
        tail_report = build_tail_report(session_name, state_dir=state_root, evidence=parsed_evidence)
        for issue in tail_report.get("issues", []):
            if issue not in issues:
                issues.append(issue)
        if tail_report.get("evidenceValidation", {}).get("issues"):
            for issue in tail_report["evidenceValidation"]["issues"]:
                if issue not in issues:
                    issues.append(issue)
    return {
        "schemaVersion": SCHEMA_VERSION,
        "bridge": BRIDGE_NAME,
        "operation": "verify-completion",
        "status": "completion-evidence-accepted" if not issues else "completion-evidence-blocked",
        "executionAllowedHere": False,
        "authorityBoundary": authority_boundary(),
        "sessionName": session_name,
        "sessionStateDir": str(state_root),
        "evidence": parsed_evidence,
        "evidenceAccepted": not issues,
        "blockedReasons": issues,
        "tailReport": tail_report,
        "completionSource": "durable-evidence" if not issues else None,
        "scrollbackAccepted": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare/verify a host-owned visible GJC execution bridge without executing GJC.")
    parser.add_argument("--pretty", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="Prepare visible-session task and metadata artifacts.")
    prepare.add_argument("request", nargs="*", help="User request; ignored if handoff plan includes a request.")
    prepare.add_argument("--cwd")
    prepare.add_argument("--handoff-plan-json")
    prepare.add_argument("--session-name")
    prepare.add_argument("--bridge-dir")
    prepare.add_argument("--state-dir")
    prepare.add_argument("--allow-mutation", action="store_true")
    prepare.add_argument("--tui-ready", action="store_true")
    prepare.add_argument("--tmux-session")
    prepare.add_argument("--tmux-window", default="gjc")
    prepare.add_argument("--tmux-pane", default="0")
    prepare.add_argument("--gjc-command", default="gjc")

    verify = sub.add_parser("verify", help="Verify durable completion evidence for a prepared visible session.")
    verify.add_argument("--session-name", required=True)
    verify.add_argument("--evidence-json", required=True)
    verify.add_argument("--bridge-dir")
    verify.add_argument("--state-dir")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "prepare":
            request = " ".join(args.request).strip()
            output = prepare_visible_execution(
                request,
                cwd=args.cwd,
                handoff_plan=args.handoff_plan_json,
                session_name=args.session_name,
                bridge_dir=args.bridge_dir,
                state_dir=args.state_dir,
                allow_mutation=args.allow_mutation,
                tui_ready=args.tui_ready,
                tmux_session=args.tmux_session,
                tmux_window=args.tmux_window,
                tmux_pane=args.tmux_pane,
                gjc_command=args.gjc_command,
            )
        elif args.command == "verify":
            output = verify_completion(
                args.session_name,
                evidence=args.evidence_json,
                bridge_dir=args.bridge_dir,
                state_dir=args.state_dir,
            )
        else:  # pragma: no cover - argparse prevents this.
            raise ValueError(f"unknown command {args.command}")
    except Exception as exc:
        output = {
            "schemaVersion": SCHEMA_VERSION,
            "bridge": BRIDGE_NAME,
            "operation": args.command,
            "status": "blocked",
            "executionAllowedHere": False,
            "authorityBoundary": authority_boundary(),
            "blockedReasons": [str(exc)],
        }
    print(json_text(output, pretty=args.pretty))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
