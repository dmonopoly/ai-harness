#!/usr/bin/env python3
"""End-to-end smoke test for the harness task flow."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
HARNESS_ROOT = HOME / ".harness"
SCRIPT = HARNESS_ROOT / "scripts" / "tasklog.py"
TICKET_ID = "SMOKE-001"
TICKET_DIR = HARNESS_ROOT / TICKET_ID


def run(*args: str, expect_ok: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if expect_ok and result.returncode != 0:
        raise AssertionError(f"command failed: {args}\nstdout={result.stdout}\nstderr={result.stderr}")
    if not expect_ok and result.returncode == 0:
        raise AssertionError(f"command unexpectedly succeeded: {args}\nstdout={result.stdout}")
    return result


def load_tasks() -> dict:
    return json.loads((TICKET_DIR / "tasks.json").read_text())


def write_dummy_tasks() -> None:
    payload = {
        "ticket_id": TICKET_ID,
        "tasks": [
            {
                "id": "T1",
                "title": "Create initial task output",
                "requirement_ids": ["R1"],
                "acceptance_criteria_ids": ["AC1"],
                "depends_on": [],
                "status": "AVAILABLE",
                "files_or_symbols": ["app.py"],
                "validation_notes": "Run a focused smoke validation.",
                "needs_work_reason": "",
            },
            {
                "id": "T2",
                "title": "Follow-up task with dependency",
                "requirement_ids": ["R2"],
                "acceptance_criteria_ids": ["AC2"],
                "depends_on": ["T1"],
                "status": "AVAILABLE",
                "files_or_symbols": ["worker.py"],
                "validation_notes": "Confirm dependency-aware readiness.",
                "needs_work_reason": "",
            },
        ],
    }
    (TICKET_DIR / "tasks.json").write_text(json.dumps(payload, indent=2) + "\n")


def main() -> int:
    print("[smoke] starting")
    shutil.rmtree(TICKET_DIR, ignore_errors=True)

    try:
        init_result = run("init", TICKET_ID)
        assert "created" in init_result.stdout, init_result.stdout
        assert (TICKET_DIR / "spec.md").exists(), "spec.md was not created"
        assert (TICKET_DIR / "tasks.json").exists(), "tasks.json was not created"
        assert (TICKET_DIR / "progress.log").exists(), "progress.log was not created"

        write_dummy_tasks()

        next_result = run("next", TICKET_ID)
        assert next_result.stdout.strip().startswith("T1\tAVAILABLE"), next_result.stdout

        claim_result = run("claim", TICKET_ID, "T1")
        assert "claimed\tT1\tWIP" in claim_result.stdout, claim_result.stdout
        assert load_tasks()["tasks"][0]["status"] == "WIP"

        implemented_result = run("update", TICKET_ID, "T1", "IMPLEMENTED")
        assert "WIP->IMPLEMENTED" in implemented_result.stdout, implemented_result.stdout
        assert load_tasks()["tasks"][0]["status"] == "IMPLEMENTED"

        validated_result = run("update", TICKET_ID, "T1", "VALIDATED")
        assert "IMPLEMENTED->VALIDATED" in validated_result.stdout, validated_result.stdout
        assert load_tasks()["tasks"][0]["status"] == "VALIDATED"

        summary_result = run("summary", TICKET_ID)
        assert "ID\tSTATUS\tREADY\tDEPENDS_ON\tTITLE" in summary_result.stdout, summary_result.stdout
        assert "T2\tAVAILABLE\tyes\tT1\tFollow-up task with dependency" in summary_result.stdout

        invalid_result = run("update", TICKET_ID, "T2", "VALIDATED", expect_ok=False)
        assert "invalid transition" in invalid_result.stderr, invalid_result.stderr

        dependency_payload = load_tasks()
        dependency_payload["tasks"][0]["status"] = "AVAILABLE"
        dependency_payload["tasks"][1]["status"] = "AVAILABLE"
        (TICKET_DIR / "tasks.json").write_text(json.dumps(dependency_payload, indent=2) + "\n")

        dependency_result = run("next", TICKET_ID)
        assert dependency_result.stdout.strip().startswith("T1\tAVAILABLE"), dependency_result.stdout

        blocked_claim = run("claim", TICKET_ID, "T2", expect_ok=False)
        assert "not ready" in blocked_claim.stderr, blocked_claim.stderr

        print("[smoke] PASS")
        return 0
    except AssertionError as exc:
        print(f"[smoke] FAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(TICKET_DIR, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
