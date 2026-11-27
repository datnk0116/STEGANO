#!/usr/bin/env python3
"""Build a provenance record from the current STEGANO source and artifacts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_artifacts import verify_artifacts  # noqa: E402


DEFAULT_OUTPUT = ROOT / "results" / "final-2026-11-27" / "provenance.json"
SOURCE_DIRECTORIES = (
    "src",
    "scripts",
    "tests",
    "visualization",
    "evidence",
    "report/figures",
)
SOURCE_FILES = (
    "README.md",
    "LOGBOOK.md",
    "requirements.txt",
    "requirements-lock.txt",
    "report/REPORT.md",
    "report/APPENDIX.md",
    "report/24021404_UETCN3124_CTF_Report.pdf",
    "results/artifact_manifest.json",
)
DEPENDENCIES = ("numpy", "Pillow", "scipy", "soundfile", "plotly", "streamlit")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_inventory(root: Path = ROOT) -> list[dict[str, Any]]:
    """Hash project source, script, test, evidence, figure, and report files."""
    paths: set[Path] = set()
    for directory in SOURCE_DIRECTORIES:
        base = root / directory
        if base.is_dir():
            paths.update(
                path
                for path in base.rglob("*")
                if path.is_file()
                and path.name != ".DS_Store"
                and "__pycache__" not in path.parts
            )
    paths.update(root / relative for relative in SOURCE_FILES if (root / relative).is_file())

    inventory = []
    for path in sorted(paths):
        resolved = path.resolve()
        if not resolved.is_relative_to(root.resolve()):
            raise ValueError(f"source path escapes project root: {path}")
        inventory.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    return inventory


def dependency_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for package in DEPENDENCIES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def build_provenance(root: Path = ROOT) -> dict[str, Any]:
    manifest_path = root / "results" / "artifact_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifact_result = verify_artifacts(root=root, manifest_path=manifest_path)
    artifacts = [
        {
            "path": check["path"],
            "expected_bytes": check["expected_bytes"],
            "actual_bytes": check["actual_bytes"],
            "expected_sha256": check["expected_sha256"],
            "actual_sha256": check["actual_sha256"],
            "status": "verified" if check["passed"] else "failed",
        }
        for check in artifact_result["checks"]
    ]
    inventory = source_inventory(root)
    package_result = {
        "status": "manual",
        "note": "Submission archive is packaged manually from tracked Git files.",
    }
    integrity_passed = artifact_result["all_passed"] and bool(inventory)

    artifact_sources = [
        {
            "path": str(item["path"]),
            "official_source": str(item.get("official_source", "not_listed")),
        }
        for item in manifest["artifacts"]
    ]

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": "STEGANO",
        "artifact_sources": artifact_sources,
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "dependencies": dependency_versions(),
        },
        "artifact_integrity": {
            "status": "verified" if artifact_result["all_passed"] else "failed",
            "passed": artifact_result["passed"],
            "total": artifact_result["total"],
            "artifacts": artifacts,
        },
        "source_inventory": {
            "status": "hashed" if inventory else "empty",
            "file_count": len(inventory),
            "files": inventory,
        },
        "submission_package": package_result,
        "status": "verified" if integrity_passed else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="JSON output path (default: results/final-2026-11-27/provenance.json)",
    )
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output

    try:
        provenance = build_provenance()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(provenance, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"FAIL provenance generation: {type(exc).__name__}: {exc}")
        return 1

    artifact = provenance["artifact_integrity"]
    print(
        f"Provenance: {provenance['status']} — artifacts "
        f"{artifact['passed']}/{artifact['total']} — "
        f"source_inventory {provenance['source_inventory']['file_count']} files"
    )
    print(f"Wrote {output.relative_to(ROOT) if output.is_relative_to(ROOT) else output}")
    return 0 if provenance["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
