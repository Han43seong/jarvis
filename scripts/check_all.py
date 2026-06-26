#!/usr/bin/env python3
"""Aggregate runner for the just-chill regression suite.

Runs every README-documented `scripts/check_*.py` acceptance check plus
`python3 -m compileall -q scripts`, prints a per-check PASS/FAIL summary, and
exits non-zero if any check fails or the on-disk check set drifts from this
canonical list.

Authority boundary: this aggregator is read-only orchestration. It only invokes
the existing deterministic check scripts and `compileall` as subprocesses (which
may write `__pycache__` bytecode caches). It never executes GJC, never writes
Hermes, and performs no other mutation. `executionAllowedHere` for GJC/Hermes
remains False.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

# Canonical, ordered list mirroring the README "Verification" section.
# Keep this in sync with README.md; drift is reported and fails the run.
CANONICAL_CHECKS: tuple[str, ...] = (
    "check_just_chill_router.py",
    "check_just_chill_bridge_contracts.py",
    "check_just_chill_live_bindings.py",
    "check_just_chill_visible_helpers.py",
    "check_just_chill_hermes_boundary.py",
    "check_just_chill_raw_artifact_store.py",
    "check_just_chill_hermes_raw_artifact_boundary.py",
    "check_just_chill_hermes_memory_mcp.py",
    "check_just_chill_hermes_mcp_receipts.py",
    "check_just_chill_summary_memory_receipts.py",
    "check_just_chill_ontology_contracts.py",
    "check_just_chill_rdf_persistence_receipts.py",
    "check_just_chill_vector_recall.py",
    "check_just_chill_memory_migration_fixture.py",
    "check_just_chill_cli.py",
    "check_just_chill_approval_registry.py",
    "check_just_chill_gjc_consent_policy.py",
    "check_just_chill_gjc_execution_bridge.py",
    "check_just_chill_dogfood_harness.py",
    "check_just_chill_harness.py",
    "check_just_chill_harness_mcp.py",
    "check_just_chill_hermes_harness.py",
    "check_executor_routing_policy.py",
)

# This aggregator is itself a `check_*.py` file; exclude it from discovery so it
# never recursively invokes itself.
SELF_NAME = Path(__file__).name


def discover_disk_checks() -> set[str]:
    return {
        path.name
        for path in SCRIPTS_DIR.glob("check_*.py")
        if path.name != SELF_NAME
    }


def check_drift() -> list[str]:
    """Return drift problems between the canonical list and on-disk checks."""
    problems: list[str] = []
    canonical = set(CANONICAL_CHECKS)
    if len(canonical) != len(CANONICAL_CHECKS):
        problems.append("CANONICAL_CHECKS contains duplicate entries")
    disk = discover_disk_checks()
    missing = sorted(canonical - disk)
    extra = sorted(disk - canonical)
    for name in missing:
        problems.append(f"listed check is missing on disk: {name}")
    for name in extra:
        problems.append(f"on-disk check is not registered here/README: {name}")
    return problems


def run_one(name: str) -> tuple[bool, str]:
    script = SCRIPTS_DIR / name
    if not script.is_file():
        return False, f"missing: {script}"
    proc = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return True, "ok"
    tail = (proc.stderr or proc.stdout or "").strip().splitlines()
    detail = tail[-1] if tail else f"exit {proc.returncode}"
    return False, detail


def run_compileall() -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", str(SCRIPTS_DIR)],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return True, "ok"
    tail = (proc.stderr or proc.stdout or "").strip().splitlines()
    detail = tail[-1] if tail else f"exit {proc.returncode}"
    return False, detail


def main(argv: list[str] | None = None) -> int:
    drift = check_drift()
    results: list[tuple[str, bool, str]] = []

    for name in CANONICAL_CHECKS:
        ok, detail = run_one(name)
        results.append((name, ok, detail))
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + ("" if ok else f" -> {detail}"))

    ca_ok, ca_detail = run_compileall()
    results.append(("compileall -q scripts", ca_ok, ca_detail))
    print(f"[{'PASS' if ca_ok else 'FAIL'}] compileall -q scripts" + ("" if ca_ok else f" -> {ca_detail}"))

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print("-" * 48)
    print(f"summary: {passed}/{total} passed")

    if drift:
        print("-" * 48)
        print("DRIFT: on-disk checks do not match the canonical list:")
        for problem in drift:
            print(f"  - {problem}")

    failed = total - passed
    if failed or drift:
        print(f"RESULT: FAIL ({failed} check failure(s), {len(drift)} drift problem(s))")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
