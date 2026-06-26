#!/usr/bin/env python3
"""Deterministic first-slice router for the just-chill vNext design.

The script does not execute tools. It turns one user request into a small
handoff packet that a Hermes/just-chill layer can use before delegating to GJC
or a non-development tool lane.

It is intentionally stdlib-only so the JARVIS control-plane repository remains
checkable without project dependencies.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from typing import Iterable

SCHEMA_VERSION = 1
ROUTER_NAME = "just-chill-vnext-router"
BRIDGE_REFERENCE = "https://gajae-code.com/docs/hermes-mcp-bridge.html"

DEV_KEYWORDS = {
    "api", "auth", "bug", "build", "ci", "cli", "code", "config", "debug",
    "deploy", "diff", "docker", "error", "feature", "fix", "git", "github",
    "implement", "issue", "lint", "migration", "package", "pr", "refactor",
    "repo", "review", "schema", "sdk", "server", "typecheck",
    "gjc", "gajae", "gajae-code",
    "ui", "개발", "구현", "코드", "레포", "저장소", "테스트", "배포", "설정",
    "버그", "오류", "리팩터", "리팩토링", "리뷰", "깃", "브랜치", "기능",
}

NONDEV_TOOL_KEYWORDS = {
    "calendar": {"calendar", "schedule", "meeting", "invite", "book", "reschedule", "캘린더", "일정", "미팅", "회의", "초대", "예약"},
    "mail": {"email", "mail", "inbox", "메일", "이메일"},
    "research": {"research", "search", "investigate", "조사", "검색", "리서치"},
    "writing": {"write", "draft", "summarize", "summary", "문서", "작성", "요약", "정리", "초안"},
    "memory": {"remember", "memory", "recall", "save", "store", "기억", "장기기억", "저장", "회상"},
    "data-analysis": {"csv", "spreadsheet", "excel", "analysis", "데이터", "분석", "엑셀"},
}

SENSITIVE_KEYWORDS = {
    "api key", "oauth", "password", "token", "private key", "ssh", "ssh key",
    "secret", "secrets", "credential", "credentials", "auth.json", ".env",
    "비밀번호", "토큰", "시크릿", "자격증명", "인증파일",
}

APPROVAL_KEYWORDS = {
    "send", "publish", "delete", "remove", "overwrite", "payment", "purchase",
    "pay", "buy", "wire", "transfer", "subscribe", "order", "invite", "schedule",
    "deploy", "push", "release",
    "보내", "발송", "게시", "삭제", "결제", "구매", "송금", "이체", "구독", "주문", "초대", "예약", "배포", "푸시", "릴리즈",
    *SENSITIVE_KEYWORDS,
}

HIGH_RISK_DEV_KEYWORDS = {
    "auth", "migration", "database", "db", "deploy",
    "release", "production", "prod", "push", "delete", "payment", "security",
    "인증", "시크릿", "마이그레이션", "데이터베이스", "배포", "운영", "보안",
}

TEAM_KEYWORDS = {"team", "parallel", "tmux", "multi-agent", "workers", "팀", "병렬"}
DEEP_INTERVIEW_KEYWORDS = {
    "vague", "requirements", "interview", "deep-interview", "구상", "아이디어",
    "모호", "요구사항", "인터뷰", "명세",
}
RALPLAN_KEYWORDS = {"ralplan", "architecture", "architectural", "consensus", "설계", "아키텍처"}
ULTRAGOAL_KEYWORDS = {"ultragoal", "approved", "pending-approval", "끝까지", "완성"}
EXPLICIT_GJC_KEYWORDS = {
    "gjc", "gajae", "gajae-code", "deep-interview", "ralplan", "ultragoal",
    "gjc_delegate", "/skill:deep-interview", "/skill:ralplan", "/skill:ultragoal", "/skill:team",
}
MACHINE_CONTROL_KEYWORDS = {"mcp", "coordinator", "turn_id", "poll", "artifact", "machine control", "durable turn"}
DELEGATE_KEYWORDS = {"gjc_delegate", "delegate", "whole workflow", "plan workflow", "execute workflow"}
RPC_KEYWORDS = {"rpc", "customtools", "host tools", "host_tool_call", "hermes tool", "reverse direction"}
DEV_ACTION_KEYWORDS = {"fix", "add", "update", "implement", "debug", "refactor", "run", "수정", "추가", "구현", "실행"}

PATH_RE = re.compile(r"(?:^|\s)(?:[\w.-]+/)+[\w.-]+(?:\.[A-Za-z0-9_]+)?")
ISSUE_RE = re.compile(r"(?:#\d+|\b(?:issue|pr)\s*\d+\b)", re.IGNORECASE)
SYMBOL_RE = re.compile(r"\b(?:[a-z]+[A-Z][A-Za-z0-9]*|[A-Z][A-Za-z0-9]+|[a-z]+_[a-z0-9_]+)\b")
ERROR_RE = re.compile(r"\b(?:TypeError|ReferenceError|SyntaxError|Traceback|Exception|Error:)\b")
TEST_RE = re.compile(r"\b(?:npm|pnpm|bun|pytest|cargo|go test|tests?|lint|typecheck)\b", re.IGNORECASE)
DEV_TEST_INTENT_RE = re.compile(
    r"\b(?:unit|integration|e2e|end-to-end|regression)\s+tests?\b"
    r"|\b(?:write|create|add)\s+(?:unit\s+|integration\s+|e2e\s+|end-to-end\s+|regression\s+)?tests?\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Signals:
    development: list[str]
    anchors: list[str]
    risk: list[str]
    nondev: list[str]
    bridge: list[str]


def _matches_keyword(lower_text: str, keyword: str) -> bool:
    keyword_lower = keyword.lower()
    if any(ord(ch) > 127 for ch in keyword_lower):
        return keyword_lower in lower_text
    if re.fullmatch(r"[a-z0-9_]+", keyword_lower):
        return re.search(rf"\b{re.escape(keyword_lower)}\b", lower_text) is not None
    return keyword_lower in lower_text


def _contains_any(text: str, words: Iterable[str]) -> list[str]:
    lower = text.lower()
    return sorted({word for word in words if _matches_keyword(lower, word)})


def collect_signals(request: str) -> Signals:
    anchors: list[str] = []
    if PATH_RE.search(request):
        anchors.append("path")
    if ISSUE_RE.search(request):
        anchors.append("issue_or_pr")
    if SYMBOL_RE.search(request):
        anchors.append("symbol")
    if ERROR_RE.search(request):
        anchors.append("error")
    if TEST_RE.search(request):
        anchors.append("test_or_command")

    nondev = []
    lower = request.lower()
    for category, words in NONDEV_TOOL_KEYWORDS.items():
        if any(_matches_keyword(lower, word) for word in words):
            nondev.append(category)

    bridge = []
    if _contains_any(request, RPC_KEYWORDS):
        bridge.append("rpc-host-tools")
    if _contains_any(request, MACHINE_CONTROL_KEYWORDS):
        bridge.append("coordinator-mcp")
    if _contains_any(request, DELEGATE_KEYWORDS):
        bridge.append("gjc-delegation")

    risk = sorted(
        set(_contains_any(request, HIGH_RISK_DEV_KEYWORDS))
        | set(_contains_any(request, SENSITIVE_KEYWORDS))
        | set(_contains_any(request, APPROVAL_KEYWORDS))
    )

    return Signals(
        development=_contains_any(request, DEV_KEYWORDS),
        anchors=anchors,
        risk=risk,
        nondev=nondev,
        bridge=bridge,
    )


def is_development_request(request: str, signals: Signals) -> bool:
    explicit_gjc = bool(_contains_any(request, EXPLICIT_GJC_KEYWORDS))
    sensitive = bool(_contains_any(request, SENSITIVE_KEYWORDS))
    concrete_anchors = [anchor for anchor in signals.anchors if anchor != "symbol"]
    dev_action = bool(_contains_any(request, DEV_ACTION_KEYWORDS))
    dev_test_intent = bool(DEV_TEST_INTENT_RE.search(request))
    memory_intent = "memory" in signals.nondev

    if memory_intent and sensitive and not dev_action:
        return False
    if memory_intent and not concrete_anchors and not dev_action:
        return False
    if sensitive and signals.nondev and not concrete_anchors:
        return False
    if explicit_gjc:
        return True
    if signals.development:
        return True
    if dev_test_intent:
        return True
    if signals.anchors and dev_action:
        return True
    return False


def choose_gjc_route(request: str, signals: Signals) -> str:
    lower = request.lower()
    has_team = bool(_contains_any(request, TEAM_KEYWORDS))
    has_deep_interview = bool(_contains_any(request, DEEP_INTERVIEW_KEYWORDS))
    has_ralplan = bool(_contains_any(request, RALPLAN_KEYWORDS))
    has_ultragoal = bool(_contains_any(request, ULTRAGOAL_KEYWORDS))

    if has_team:
        return "gjc-team"
    if has_ultragoal or "approved plan" in lower or "pending-approval" in lower:
        return "gjc-ultragoal"
    if has_deep_interview and not signals.anchors:
        return "gjc-deep-interview"
    if signals.risk or has_ralplan:
        return "gjc-ralplan"
    if signals.anchors:
        return "gjc-direct"
    return "gjc-deep-interview"


def choose_bridge_path(request: str, gjc_route: str, signals: Signals) -> str:
    if "rpc-host-tools" in signals.bridge:
        return "rpc-host-tools"
    if "coordinator-mcp" in signals.bridge:
        return "coordinator-mcp"
    if "gjc-delegation" in signals.bridge or gjc_route in {"gjc-ralplan", "gjc-ultragoal", "gjc-team"}:
        return "gjc-delegation"
    return "visible-routed-session"


def choose_nondev_category(signals: Signals) -> str:
    if not signals.nondev:
        return "direct-general"
    priority = ["memory", "mail", "calendar", "data-analysis", "research", "writing"]
    for category in priority:
        if category in signals.nondev:
            return category
    return signals.nondev[0]


def risk_level(request: str, is_dev: bool, signals: Signals) -> str:
    if signals.risk or _contains_any(request, APPROVAL_KEYWORDS):
        return "high"
    if is_dev and not signals.anchors:
        return "medium"
    return "low"


def approval_required(request: str, risk: str) -> bool:
    if risk == "high":
        return True
    return bool(_contains_any(request, APPROVAL_KEYWORDS))


def skill_for_route(route: str) -> str | None:
    return {
        "gjc-direct": None,
        "gjc-deep-interview": "/skill:deep-interview",
        "gjc-ralplan": "/skill:ralplan",
        "gjc-ultragoal": "/skill:ultragoal",
        "gjc-team": "/skill:team",
    }.get(route)


def classify_request(request: str) -> dict:
    request = request.strip()
    signals = collect_signals(request)
    is_dev = is_development_request(request, signals)
    risk = risk_level(request, is_dev, signals)
    needs_approval = approval_required(request, risk)

    if is_dev:
        route = choose_gjc_route(request, signals)
        bridge = choose_bridge_path(request, route, signals)
        lane = "development-to-gjc"
        target = "GJC"
        category = None
    else:
        route = "non-development-tool-or-direct"
        if "rpc-host-tools" in signals.bridge:
            bridge = "rpc-host-tools"
        elif "coordinator-mcp" in signals.bridge:
            bridge = "coordinator-mcp"
        else:
            bridge = "host-tool-or-direct"
        lane = "non-development"
        target = "just-chill-or-external-tool"
        category = choose_nondev_category(signals)

    completion_evidence = [
        "durable turn/report/artifact reference",
        "diff/test/PR evidence when code changes",
        "source links or artifact ids for research/memory work",
    ]
    if is_dev and bridge == "visible-routed-session":
        completion_evidence.append("real GJC work signal; tmux scrollback alone is insufficient")
    if is_dev and bridge in {"coordinator-mcp", "gjc-delegation"}:
        completion_evidence.append("terminal GJC turn_id state")

    return {
        "schemaVersion": SCHEMA_VERSION,
        "router": ROUTER_NAME,
        "bridgeReference": BRIDGE_REFERENCE,
        "request": request,
        "classification": {
            "isDevelopment": is_dev,
            "lane": lane,
            "category": category,
            "risk": risk,
            "approvalRequired": needs_approval,
        },
        "routing": {
            "target": target,
            "routeHint": route,
            "skillEntrypoint": skill_for_route(route),
            "bridgePath": bridge,
        },
        "signals": {
            "development": signals.development,
            "anchors": signals.anchors,
            "risk": signals.risk,
            "nonDevelopmentCategories": signals.nondev,
            "bridge": signals.bridge,
        },
        "handoff": {
            "forbiddenActions": [
                "do not push/deploy/delete/modify secrets without explicit approval",
                "do not perform a second development interview outside GJC",
                "do not treat terminal scrollback as completion evidence",
            ],
            "completionEvidenceRequired": completion_evidence,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify a request using the just-chill vNext routing contract.")
    parser.add_argument("request", nargs="*", help="User request text. If omitted, stdin is read.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args(argv)

    if args.request:
        request = " ".join(args.request)
    else:
        import sys
        request = sys.stdin.read()

    packet = classify_request(request)
    print(json.dumps(packet, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
