"""Build and validate a clean project submission archive."""

from __future__ import annotations

import argparse
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
INCLUDE = (
    "README.md",
    "LOGBOOK.md",
    "requirements.txt",
    "requirements-lock.txt",
    "data",
    "src",
    "scripts",
    "tests",
    "visualization",
    "report",
    "evidence",
    "results",
)
REQUIRED_ARCHIVE_FILES = {
    "README.md",
    "LOGBOOK.md",
    "requirements.txt",
    "src/stegano/cli.py",
    "report/REPORT.md",
    "report/24021404_UETCN3124_CTF_Report.pdf",
}
EXCLUDED_PARTS = {".git", ".venv", "__pycache__"}
PACKAGE_BUILD_LOGS = {
    "results/recheck/package-build.log",
    "results/final/package-build.log",
}
SELF_CHECK_OUTPUTS = {
    "results/recheck/quality-gate.json",
    "results/recheck/quality-gate-console.log",
    "results/recheck/provenance.json",
    "results/recheck/reproducibility.log",
    "results/final/quality-gate.json",
    "results/final/quality-gate-console.log",
    "results/final/provenance.json",
    "results/final/reproducibility.log",
}


def should_skip(path: Path, output: Path) -> bool:
    if path.is_symlink() or path.resolve() == output:
        return True
    try:
        if path.relative_to(ROOT).as_posix() in PACKAGE_BUILD_LOGS:
            return True
    except ValueError:
        pass
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return True
    if path.name == "AGENTS.md" or path.name == ".DS_Store":
        return True
    if path.suffix.lower() in {".pyc", ".pyo", ".zip"}:
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("submission_package_current.zip"),
        help="archive path (relative paths are resolved from the project root)",
    )
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output = output.resolve()
    temporary = output.with_name(output.name + ".tmp")

    missing = [name for name in INCLUDE if not (ROOT / name).exists()]
    if missing:
        parser.error("missing project paths: " + ", ".join(missing))

    output.parent.mkdir(parents=True, exist_ok=True)
    entries: list[tuple[Path, str]] = []
    for name in INCLUDE:
        source = ROOT / name
        candidates = [source] if source.is_file() else sorted(source.rglob("*"))
        for path in candidates:
            if not path.is_file() or should_skip(path, output):
                continue
            entries.append((path, path.relative_to(ROOT).as_posix()))

    try:
        with zipfile.ZipFile(
            temporary, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for path, archive_name in entries:
                archive.write(path, archive_name)

        with zipfile.ZipFile(temporary, mode="r") as archive:
            damaged = archive.testzip()
            names = set(archive.namelist())
            missing_required = REQUIRED_ARCHIVE_FILES - names
            if damaged:
                raise RuntimeError(f"archive integrity check failed at {damaged}")
            if missing_required:
                raise RuntimeError(
                    "required files missing from archive: "
                    + ", ".join(sorted(missing_required))
                )

        temporary.replace(output)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    print(f"Created and verified: {output}")
    print(f"Files: {len(entries)} | Size: {output.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
