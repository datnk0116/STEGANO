#!/usr/bin/env python3
"""Verify pinned challenge-artifact sizes and SHA-256 checksums."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "results" / "artifact_manifest.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_artifacts(
    root: Path = ROOT, manifest_path: Path | None = None
) -> dict[str, Any]:
    """Return per-artifact checks and an aggregate result.

    Paths in the manifest are repository-relative and may not escape ``root``.
    The manifest is read at runtime so the CLI and dashboard share one source
    of truth.
    """
    root = Path(root).resolve()
    manifest_path = Path(manifest_path) if manifest_path else root / DEFAULT_MANIFEST.relative_to(ROOT)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("manifest must contain a non-empty 'artifacts' list")

    checks: list[dict[str, Any]] = []
    for artifact in artifacts:
        relative_path = Path(artifact["path"])
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"artifact path must stay inside repository: {relative_path}")

        path = (root / relative_path).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"artifact path must stay inside repository: {relative_path}")

        expected_bytes = int(artifact["bytes"])
        expected_sha256 = str(artifact["sha256"]).lower()
        check: dict[str, Any] = {
            "path": relative_path.as_posix(),
            "expected_bytes": expected_bytes,
            "expected_sha256": expected_sha256,
            "exists": path.is_file(),
            "actual_bytes": None,
            "actual_sha256": None,
            "passed": False,
        }
        if path.is_file():
            check["actual_bytes"] = path.stat().st_size
            check["actual_sha256"] = _sha256(path)
            check["passed"] = (
                check["actual_bytes"] == expected_bytes
                and check["actual_sha256"] == expected_sha256
            )
        checks.append(check)

    passed = sum(check["passed"] for check in checks)
    return {
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "all_passed": passed == len(checks),
    }


def main() -> int:
    try:
        report = verify_artifacts()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"FAIL manifest/artifact verification: {type(exc).__name__}: {exc}")
        return 1

    for check in report["checks"]:
        status = "PASS" if check["passed"] else "FAIL"
        if check["passed"]:
            print(
                f"PASS {check['path']} — {check['actual_bytes']} bytes — "
                f"sha256 {check['actual_sha256']}"
            )
        elif not check["exists"]:
            print(f"{status} {check['path']} — file is missing")
        else:
            print(
                f"FAIL {check['path']} — expected {check['expected_bytes']} bytes / "
                f"sha256 {check['expected_sha256']}; got {check['actual_bytes']} bytes / "
                f"sha256 {check['actual_sha256']}"
            )

    print(f"Summary: {report['passed']}/{report['total']} artifacts verified")
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
