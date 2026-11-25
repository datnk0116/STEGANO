#!/usr/bin/env python3
"""Build a provenance record from the current STEGANO source and artifacts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_artifacts import verify_artifacts  # noqa: E402
from create_submission_zip import (  # noqa: E402
    INCLUDE as PACKAGE_INCLUDE,
    REQUIRED_ARCHIVE_FILES,
    SELF_CHECK_OUTPUTS,
    should_skip as should_skip_package_file,
)


DEFAULT_OUTPUT = ROOT / "results" / "verification" / "provenance.json"
SOURCE_DIRECTORIES = (
    "src",
    "scripts",
    "tests",
    "visualization",
    "evidence",
    "report/figures",
    "results/recheck/screenshots",
)
SOURCE_FILES = (
    "README.md",
    "LOGBOOK.md",
    "requirements.txt",
    "report/REPORT.md",
    "report/APPENDIX.md",
    "results/artifact_manifest.json",
)
SUBMISSION_PACKAGE = ROOT / "submission_package_current.zip"
DEPENDENCIES = ("numpy", "Pillow", "scipy", "soundfile", "plotly", "streamlit")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_inventory(root: Path = ROOT) -> list[dict[str, Any]]:
    """Hash project files, documented evidence, and the latest screenshot captures."""
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


def expected_package_files(root: Path = ROOT) -> dict[str, Path]:
    """Return the project files that the package builder is expected to archive."""
    expected: dict[str, Path] = {}
    for name in PACKAGE_INCLUDE:
        source = root / name
        candidates = [source] if source.is_file() else sorted(source.rglob("*"))
        for path in candidates:
            if path.is_file() and not should_skip_package_file(path, SUBMISSION_PACKAGE):
                expected[path.relative_to(root).as_posix()] = path
    return expected


def verify_submission_package(root: Path = ROOT) -> dict[str, Any]:
    """Verify archive readability, required members, and current project contents."""
    archive_path = root / SUBMISSION_PACKAGE.name
    if not archive_path.is_file():
        return {
            "status": "not_verified",
            "reason": f"Submission archive is missing: {archive_path.name}.",
        }

    expected = expected_package_files(root)
    errors: list[str] = []
    try:
        with zipfile.ZipFile(archive_path) as archive:
            names_list = archive.namelist()
            names = set(names_list)
            if len(names_list) != len(names):
                errors.append("Archive contains duplicate member names.")
            damaged = archive.testzip()
            if damaged:
                errors.append(f"Archive CRC check failed at {damaged}.")
            missing_required = REQUIRED_ARCHIVE_FILES - names
            if missing_required:
                errors.append(
                    "Required archive files are missing: "
                    + ", ".join(sorted(missing_required))
                    + "."
                )

            missing = set(expected) - names
            extra = names - set(expected)
            if missing:
                errors.append("Project files missing from archive: " + ", ".join(sorted(missing)))
            if extra:
                errors.append("Unexpected archive members: " + ", ".join(sorted(extra)))

            # Run records contain the result of this archive check, so their bytes are self-referential.
            # They remain required archive members and are covered by testzip() CRC validation.
            mismatched = [
                name
                for name, path in expected.items()
                if name in names and name not in SELF_CHECK_OUTPUTS and archive.read(name) != path.read_bytes()
            ]
            if mismatched:
                errors.append(
                    "Archive contents differ from the current project: "
                    + ", ".join(mismatched)
                    + "."
                )
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        errors.append(f"Archive could not be read: {type(exc).__name__}: {exc}")
        names = set()

    return {
        "status": "verified" if not errors else "failed",
        "path": archive_path.relative_to(root).as_posix(),
        "file_count": len(names),
        "required_files": sorted(REQUIRED_ARCHIVE_FILES),
        "validation": "zip CRC, required members, full file-set, project-file byte comparison; self-check records checked for presence and CRC",
        "self_check_outputs_exempt_from_byte_comparison": sorted(SELF_CHECK_OUTPUTS),
        "errors": errors,
    }


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
    package_result = verify_submission_package(root)
    integrity_passed = (
        artifact_result["all_passed"]
        and bool(inventory)
        and package_result["status"] == "verified"
    )

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
        help="JSON output path (default: results/verification/provenance.json)",
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
        f"submission_package {provenance['submission_package']['status']}"
    )
    print(f"Wrote {output.relative_to(ROOT) if output.is_relative_to(ROOT) else output}")
    return 0 if provenance["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
