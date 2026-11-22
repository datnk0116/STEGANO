#!/usr/bin/env python3
"""Run the local artifact, unittest, and provenance checks and write a quality gate."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "results" / "verification" / "quality-gate.json"
PROVENANCE_PATH = ROOT / "results" / "verification" / "provenance.json"
LOG_PATH = ROOT / "results" / "verification" / "reproducibility.log"


def run_command(command: list[str], env: dict[str, str] | None = None) -> dict[str, Any]:
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "command": command,
        "exit_code": result.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "output": result.stdout,
    }


def parse_unittest(output: str, exit_code: int) -> dict[str, Any]:
    match = re.search(r"Ran\s+(\d+)\s+tests?", output)
    total = int(match.group(1)) if match else None
    failures_match = re.search(r"failures=(\d+)", output)
    errors_match = re.search(r"errors=(\d+)", output)
    skipped_match = re.search(r"skipped=(\d+)", output)
    failures = int(failures_match.group(1)) if failures_match else 0
    errors = int(errors_match.group(1)) if errors_match else 0
    skipped = int(skipped_match.group(1)) if skipped_match else 0
    passed = max(0, total - failures - errors - skipped) if total is not None else None
    return {
        "status": "passed" if exit_code == 0 and total is not None else "failed",
        "total": total,
        "passed": passed,
        "failed": failures,
        "errors": errors,
        "skipped": skipped,
        "exit_code": exit_code,
    }


def parse_artifacts(output: str, exit_code: int) -> dict[str, Any]:
    match = re.search(r"Summary:\s*(\d+)/(\d+) artifacts verified", output)
    passed, total = (int(match.group(1)), int(match.group(2))) if match else (None, None)
    return {
        "status": "passed" if exit_code == 0 and match else "failed",
        "passed": passed,
        "total": total,
        "exit_code": exit_code,
    }


def write_log(runs: list[tuple[str, dict[str, Any]]]) -> None:
    sections = []
    for label, run in runs:
        sections.append(
            f"[{label}]\n$ {' '.join(run['command'])}\n"
            f"exit_code={run['exit_code']}\n{run['output'].rstrip()}"
        )
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("\n\n".join(sections) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="JSON output path (default: results/verification/quality-gate.json)",
    )
    args = parser.parse_args()
    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    started_at = datetime.now(timezone.utc).isoformat()

    artifact_run = run_command([sys.executable, "scripts/verify_artifacts.py"])
    test_env = os.environ.copy()
    current_pythonpath = test_env.get("PYTHONPATH")
    test_env["PYTHONPATH"] = str(ROOT / "src") + (
        os.pathsep + current_pythonpath if current_pythonpath else ""
    )
    unittest_run = run_command(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        env=test_env,
    )
    provenance_run = run_command([sys.executable, "scripts/check_provenance.py"])
    runs = [
        ("artifact_verification", artifact_run),
        ("unittest", unittest_run),
        ("provenance", provenance_run),
    ]
    write_log(runs)

    provenance: dict[str, Any] = {}
    if PROVENANCE_PATH.is_file():
        try:
            provenance = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            provenance = {}

    artifact_summary = parse_artifacts(artifact_run["output"], artifact_run["exit_code"])
    test_summary = parse_unittest(unittest_run["output"], unittest_run["exit_code"])
    provenance_status = provenance.get("status", "failed")
    submission = provenance.get("submission_package", {})
    reported_submission = re.search(
        r"submission_package\s+(verified|not_verified|failed)", provenance_run["output"]
    )
    submission_status = (
        reported_submission.group(1)
        if reported_submission
        else submission.get("status", "failed")
    )
    quality_pass = (
        artifact_summary["status"] == "passed"
        and test_summary["status"] == "passed"
        and provenance_run["exit_code"] == 0
        and provenance_status == "verified"
        and submission_status == "not_verified"
    )

    gate = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": "STEGANO",
        "verification_run": {
            "tests": test_summary,
            "artifact_integrity": artifact_summary,
            "provenance": {"status": provenance_status, "exit_code": provenance_run["exit_code"]},
        },
        "submission_package": {
            "status": submission_status,
            "reported_by": "scripts/check_provenance.py",
            "script_exit_code": provenance_run["exit_code"],
            "reason": submission.get("reason"),
        },
        "quality_gate": {
            "status": "passed" if quality_pass else "failed",
            "passed": quality_pass,
            "scope": "Artifact integrity, the discovered unittest suite, and source provenance.",
            "submission_ready": False,
        },
        "runs": [
            {
                "name": label,
                "command": run["command"],
                "exit_code": run["exit_code"],
                "duration_seconds": run["duration_seconds"],
            }
            for label, run in runs
        ],
        "log": "results/verification/reproducibility.log",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(gate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        f"STEGANO quality gate: {gate['quality_gate']['status']} — tests "
        f"{test_summary['passed']}/{test_summary['total']} — artifacts "
        f"{artifact_summary['passed']}/{artifact_summary['total']} — "
        f"provenance {provenance_status} — submission_package {submission_status}"
    )
    print(f"Wrote {output_path.relative_to(ROOT) if output_path.is_relative_to(ROOT) else output_path}")
    if not quality_pass:
        for label, run in runs:
            if run["exit_code"] != 0:
                print(f"\n[{label}]\n{run['output']}", file=sys.stderr)
    return 0 if quality_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
