#!/usr/bin/env python3
"""Acceptance checks for the just-chill vNext deterministic router."""
from __future__ import annotations

from just_chill_router import classify_request


def require(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}")


def require_in(name: str, needle, haystack) -> None:
    if needle not in haystack:
        raise AssertionError(f"{name}: expected {needle!r} in {haystack!r}")


def route(request: str) -> dict:
    return classify_request(request)


cases = []

p = route("fix TypeError in src/hooks/bridge.ts and run bun test")
require("path/error case is development", p["classification"]["isDevelopment"], True)
require("path/error case route", p["routing"]["routeHint"], "gjc-direct")
require("path/error case bridge", p["routing"]["bridgePath"], "visible-routed-session")
require_in("path/error anchors", "path", p["signals"]["anchors"])
cases.append("dev-direct")

p = route("새 개발 아이디어가 모호한데 요구사항을 정리해서 명세로 만들어줘")
require("vague Korean dev idea is development", p["classification"]["isDevelopment"], True)
require("vague Korean dev idea route", p["routing"]["routeHint"], "gjc-deep-interview")
require("vague Korean dev idea skill", p["routing"]["skillEntrypoint"], "/skill:deep-interview")
cases.append("dev-deep-interview")

p = route("Refine this auth architecture plan before implementation")
require("architecture/auth route", p["routing"]["routeHint"], "gjc-ralplan")
require("architecture/auth approval", p["classification"]["approvalRequired"], True)
cases.append("dev-ralplan")

p = route("Execute the approved pending-approval plan with ultragoal")
require("approved plan route", p["routing"]["routeHint"], "gjc-ultragoal")
require("approved plan bridge", p["routing"]["bridgePath"], "gjc-delegation")
require_in("approved plan evidence", "terminal GJC turn_id state", p["handoff"]["completionEvidenceRequired"])
cases.append("dev-ultragoal")

p = route("Use team tmux workers to implement independent modules in parallel")
require("team route", p["routing"]["routeHint"], "gjc-team")
require("team bridge", p["routing"]["bridgePath"], "gjc-delegation")
cases.append("dev-team")

p = route("메일 초안을 작성해서 요약해줘")
require("mail draft nondev", p["classification"]["isDevelopment"], False)
require("mail draft category", p["classification"]["category"], "mail")
require("mail draft approval", p["classification"]["approvalRequired"], False)
cases.append("nondev-mail-draft")

p = route("Send email to the client with this final text")
require("email send nondev", p["classification"]["isDevelopment"], False)
require("email send category", p["classification"]["category"], "mail")
require("email send approval", p["classification"]["approvalRequired"], True)
cases.append("nondev-mail-send")

p = route("Plan tomorrow's team meeting agenda")
require("team meeting remains nondev", p["classification"]["isDevelopment"], False)
require("team meeting category", p["classification"]["category"], "calendar")
cases.append("nondev-team-meeting")

p = route("회의 내용을 정리해줘")
require("Korean meeting cleanup remains nondev", p["classification"]["isDevelopment"], False)
require("Korean meeting cleanup category", p["classification"]["category"], "calendar")
cases.append("nondev-korean-meeting-cleanup")

p = route("prepare notes for the history test")
require("school test prep remains nondev", p["classification"]["isDevelopment"], False)
cases.append("nondev-test-prep")

p = route("run tests")
require("run tests is development", p["classification"]["isDevelopment"], True)
require("run tests route", p["routing"]["routeHint"], "gjc-direct")
cases.append("dev-run-tests")

p = route("write unit tests")
require("write unit tests is development", p["classification"]["isDevelopment"], True)
require("write unit tests route", p["routing"]["routeHint"], "gjc-direct")
cases.append("dev-write-unit-tests")

p = route("write history test notes")
require("history test notes remains nondev", p["classification"]["isDevelopment"], False)
cases.append("nondev-history-test-notes")

p = route("remember my API key for later")
require("api key memory remains nondev", p["classification"]["isDevelopment"], False)
require("api key memory category", p["classification"]["category"], "memory")
require("api key memory approval", p["classification"]["approvalRequired"], True)
cases.append("sensitive-memory-approval")

fake_token = "sk-" + "test-" + "1234567890"
p = route(f"remember my API key {fake_token} for later")
require("token-shaped api key memory remains nondev", p["classification"]["isDevelopment"], False)
require("token-shaped api key memory category", p["classification"]["category"], "memory")
require("token-shaped api key memory approval", p["classification"]["approvalRequired"], True)
cases.append("sensitive-token-shaped-memory-approval")

p = route("remember my SSH for later")
require("ssh memory remains nondev", p["classification"]["isDevelopment"], False)
require("ssh memory category", p["classification"]["category"], "memory")
require("ssh memory approval", p["classification"]["approvalRequired"], True)
cases.append("sensitive-ssh-memory-approval")

p = route("save my API key for later")
require("save api key remains nondev", p["classification"]["isDevelopment"], False)
require("save api key category", p["classification"]["category"], "memory")
require("save api key approval", p["classification"]["approvalRequired"], True)
cases.append("sensitive-save-api-key")

p = route("store my password in memory")
require("store password remains nondev", p["classification"]["isDevelopment"], False)
require("store password approval", p["classification"]["approvalRequired"], True)
cases.append("sensitive-store-password")

p = route("remember that GJC should use visible routed sessions first")
require("remember GJC policy remains nondev", p["classification"]["isDevelopment"], False)
require("remember GJC policy category", p["classification"]["category"], "memory")
cases.append("memory-policy-with-gjc-term")

p = route("invite Bob to the meeting")
require("calendar invite remains nondev", p["classification"]["isDevelopment"], False)
require("calendar invite category", p["classification"]["category"], "calendar")
require("calendar invite approval", p["classification"]["approvalRequired"], True)
cases.append("calendar-invite-approval")

p = route("pay the invoice")
require("payment remains nondev", p["classification"]["isDevelopment"], False)
require("payment approval", p["classification"]["approvalRequired"], True)
cases.append("payment-approval")

p = route("buy a domain")
require("purchase verb remains nondev", p["classification"]["isDevelopment"], False)
require("purchase verb approval", p["classification"]["approvalRequired"], True)
cases.append("purchase-verb-approval")

p = route("Use coordinator MCP machine control and poll the turn_id artifact state for this repo task")
require("coordinator bridge", p["routing"]["bridgePath"], "coordinator-mcp")
cases.append("bridge-coordinator")

p = route("GJC needs Hermes host tools via RPC customTools for memory recall")
require("rpc bridge", p["routing"]["bridgePath"], "rpc-host-tools")
cases.append("bridge-rpc")

print(f"PASS: {len(cases)} just-chill router cases passed")
