#!/usr/bin/env python3
"""Run a deterministic synthetic-control benchmark for the triage baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from steganalysis import analyze  # noqa: E402
from stegano.audio import decode_sleepy_alarm  # noqa: E402


SEED = 20261114
BLUE3_DEFAULT = ROOT / "data" / "blue3" / "blue.png"
SLEEPY_DEFAULT = ROOT / "data" / "sleepy_alarm" / "morning_n_breakfast.mp3"
REFERENCE_DEFAULT = ROOT / "data" / "sleepy_alarm" / "morning_n_breakfast_original.mp3"
BLUE3_GROUND_TRUTH = "byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}"
SLEEPY_GROUND_TRUTH = "ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}"


OPEN_SOURCE_COMPARISON = [
    {
        "name": "Aperi'Solve",
        "medium": "image",
        "scope": "Image triage, bit-plane visualization, and integrated forensic analyzers.",
        "comparison_limit": "Its common LSB and file-analysis methods do not directly model Blue 3's diagonal RGB-delta encoding.",
        "executed": False,
        "url": "https://github.com/Zeecka/AperiSolve",
    },
    {
        "name": "The-A-Files",
        "medium": "audio",
        "scope": "Research evaluation of audio steganography methods, attacks, and recovery metrics.",
        "comparison_limit": "It is an evaluation framework, not a drop-in detector for this reference-differenced ASK challenge.",
        "executed": False,
        "url": "https://github.com/pawel-kaczmarek/The-A-Files",
    },
    {
        "name": "WavSteg",
        "medium": "audio",
        "scope": "LSB payload embedding and recovery for WAV audio.",
        "comparison_limit": "The challenge artifact is MP3 with ASK modulation; WavSteg is not a general detector for that method.",
        "executed": False,
        "url": "https://github.com/ragibson/Steganography",
    },
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def _confusion(rows: list[dict]) -> dict:
    scored = [row for row in rows if isinstance(row.get("predicted"), bool)]
    tp = sum(row["label"] == "stego" and row["predicted"] for row in scored)
    tn = sum(row["label"] == "benign" and not row["predicted"] for row in scored)
    fp = sum(row["label"] == "benign" and row["predicted"] for row in scored)
    fn = sum(row["label"] == "stego" and not row["predicted"] for row in scored)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "false_positive_rate": fp / (fp + tn) if fp + tn else 0.0,
        "sample_count": len(rows),
        "scored_count": len(scored),
        "unscored_count": len(rows) - len(scored),
        "benign_count": sum(row["label"] == "benign" for row in rows),
        "stego_count": sum(row["label"] == "stego" for row in rows),
    }


def _analyze_sample(path: Path, kind: str, label: str, source: str) -> dict:
    row = {
        "sample": path.name,
        "kind": kind,
        "label": label,
        "source": source,
        "predicted": None,
        "reasons": [],
        "features": None,
        "error": None,
    }
    try:
        result = analyze(path, kind)
    except Exception as exc:  # retain analysis failures as unscored rows
        row["error"] = f"{type(exc).__name__}: {exc}"
        return row
    row.update(
        predicted=bool(result["flagged"]),
        reasons=result["reasons"],
        features=result["features"],
    )
    return row


def _decode_trial(target: Path, reference: Path | None, expected: str, name: str) -> dict:
    trial = {
        "name": name,
        "status": "FAIL",
        "reference_used": reference is not None,
        "format_valid": False,
        "ground_truth_match": False,
        "success": False,
        "decoded_length": 0,
        "symbol_count": None,
        "separator_count": None,
        "error_count": None,
        "errors": [],
        "decoded_text": "",
        "decode_error": None,
    }
    try:
        decoded = decode_sleepy_alarm(target, reference)
    except Exception as exc:  # report blind/assisted decoder failures as outcomes
        trial["decode_error"] = f"{type(exc).__name__}: {exc}"
        return trial

    text = str(decoded.get("decoded_text") or "")
    errors = decoded.get("errors") or []
    success = (
        decoded.get("format_valid") is True
        and text == expected
        and not errors
    )
    trial.update(
        status="PASS" if success else "FAIL",
        format_valid=decoded.get("format_valid") is True,
        ground_truth_match=text == expected,
        success=success,
        decoded_length=len(text),
        symbol_count=decoded.get("symbol_count"),
        separator_count=decoded.get("separator_count"),
        error_count=len(errors),
        errors=errors,
        decoded_text=text,
        alignment=decoded.get("alignment"),
    )
    return trial


def run_benchmark(
    blue3_path: Path,
    sleepy_path: Path,
    reference_path: Path,
    output_dir: Path,
    expected_sleepy: str = SLEEPY_GROUND_TRUTH,
) -> dict:
    for path in (blue3_path, sleepy_path, reference_path):
        if not path.is_file():
            raise FileNotFoundError(f"missing challenge artifact: {path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    rows: list[dict] = []

    def add(path: Path, kind: str, label: str, source: str) -> None:
        rows.append(_analyze_sample(path, kind, label, source))

    with tempfile.TemporaryDirectory(prefix="stegano-benchmark-") as temporary:
        temp_root = Path(temporary)

        # Deterministic benign image controls: eight textures and four graphics.
        for i in range(8):
            array = rng.integers(0, 256, size=(256, 256, 3), dtype=np.uint8)
            path = temp_root / f"benign_texture_{i}.png"
            Image.fromarray(array).save(path)
            add(path, "image", "benign", f"synthetic_seed={SEED}")
        for i in range(4):
            array = np.zeros((256, 256, 3), dtype=np.uint8)
            array[:] = ((i * 31) % 256, (i * 67) % 256, (i * 97) % 256)
            array[::8, :, :] = rng.integers(0, 256, size=array[::8, :, :].shape, dtype=np.uint8)
            path = temp_root / f"benign_graphic_{i}.png"
            Image.fromarray(array).save(path)
            add(path, "image", "benign", f"synthetic_seed={SEED}")

        add(blue3_path, "image", "stego", "official_ctf_artifact")
        with Image.open(blue3_path) as source_image:
            carrier = source_image.convert("RGB")
        for i, factor in enumerate((0.98, 1.02, 0.95, 1.05)):
            array = np.clip(np.asarray(carrier, dtype=np.float64) * factor, 0, 255).astype(np.uint8)
            path = temp_root / f"stego_blue3_brightness_{i}.png"
            Image.fromarray(array).save(path)
            add(path, "image", "stego", "derived_from_official_stego")

        # Eight seeded noise controls and five challenge-derived positives.
        sample_rate = 44100
        sample_count = int(sample_rate * 7.0)
        for i in range(8):
            noise = rng.normal(0, 0.04, sample_count)
            path = temp_root / f"benign_audio_{i}.wav"
            sf.write(path, np.column_stack([noise, noise * 0.9]), sample_rate)
            add(path, "audio", "benign", f"synthetic_seed={SEED}")

        add(sleepy_path, "audio", "stego", "official_ctf_artifact")
        source_audio, source_rate = sf.read(sleepy_path, always_2d=True, dtype="float64")
        for i, gain in enumerate((0.8, 0.9, 1.1, 1.2)):
            transformed = np.clip(source_audio * gain, -1.0, 1.0)
            path = temp_root / f"stego_sleepy_gain_{i}.wav"
            sf.write(path, transformed, source_rate)
            add(path, "audio", "stego", "derived_from_official_stego")

        reference_trials = [
            _decode_trial(sleepy_path, None, expected_sleepy, "reference_free"),
            _decode_trial(sleepy_path, reference_path, expected_sleepy, "reference_assisted"),
        ]

    summaries = {
        kind: _confusion([row for row in rows if row["kind"] == kind])
        for kind in ("image", "audio")
    }
    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "dataset_note": (
            "Positive examples are the official challenge artifact and deterministic transformed copies. "
            "Benign controls are deterministic synthetic samples, not a representative real-world corpus."
        ),
        "thresholds": {
            "image": {
                "modal_rgb_fraction_min": 0.90,
                "mean_channel_std_max": 8.0,
                "decision": "both conditions must be met",
            },
            "audio": {
                "carrier_band_energy_ratio_min": 0.02,
                "symbol_block_rms_cv_min": 0.15,
                "decision": "both conditions must be met",
            },
        },
        "inputs": {
            "blue3": {"path": _relative(blue3_path), "sha256": _sha256(blue3_path)},
            "sleepy_alarm": {"path": _relative(sleepy_path), "sha256": _sha256(sleepy_path)},
            "reference": {"path": _relative(reference_path), "sha256": _sha256(reference_path)},
        },
        "metrics": summaries,
        "samples": rows,
        "reference_comparison": {
            "expected_text_used_only_for_validation": True,
            "trials": reference_trials,
            "note": (
                "Reference-free and reference-assisted extraction are separate trials. "
                "Expected text is used only after decoding for exact-match validation."
            ),
        },
        "open_source_comparison": {
            "mode": "capability_scope_only_not_executed",
            "tools": OPEN_SOURCE_COMPARISON,
        },
        "warning": "Heuristic results are specific to this deterministic sample set and are not population estimates.",
    }
    json_path = output_dir / "benchmark.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blue3", type=Path, default=BLUE3_DEFAULT)
    parser.add_argument("--sleepy", type=Path, default=SLEEPY_DEFAULT)
    parser.add_argument("--reference", type=Path, default=REFERENCE_DEFAULT)
    parser.add_argument("--expected", default=SLEEPY_GROUND_TRUTH)
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "steganalysis")
    args = parser.parse_args()

    try:
        result = run_benchmark(args.blue3, args.sleepy, args.reference, args.out, args.expected)
    except Exception as exc:
        parser.error(f"benchmark failed: {type(exc).__name__}: {exc}")

    print(json.dumps({
        "metrics": result["metrics"],
        "reference_comparison": result["reference_comparison"]["trials"],
        "json": _relative(args.out.resolve() / "benchmark.json"),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
