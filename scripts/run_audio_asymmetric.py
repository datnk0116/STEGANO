#!/usr/bin/env python3
"""Measure reference-assisted Sleepy Alarm under one-sided audio changes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from stegano.audio import decode_sleepy_alarm  # noqa: E402

GROUND_TRUTH = "ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}"
TARGET_PATH = ROOT / "data" / "sleepy_alarm" / "morning_n_breakfast.mp3"
REFERENCE_PATH = ROOT / "data" / "sleepy_alarm" / "morning_n_breakfast_original.mp3"
OUTPUT_DIR = ROOT / "results" / "asymmetric"
OUTPUT_JSON = "asymmetric_robustness.json"
OUTPUT_CSV = "asymmetric_robustness.csv"

VARIANTS: tuple[dict[str, Any], ...] = (
    {"variant": "target_only_gain_0.5", "side": "target", "operation": "gain", "gain": 0.5},
    {"variant": "target_only_gain_1.5", "side": "target", "operation": "gain", "gain": 1.5},
    {
        "variant": "target_only_resample_44k1_48k_44k1",
        "side": "target",
        "operation": "resample_roundtrip",
        "intermediate_sample_rate": 48000,
    },
    {"variant": "reference_only_gain_0.5", "side": "reference", "operation": "gain", "gain": 0.5},
    {"variant": "reference_only_gain_1.5", "side": "reference", "operation": "gain", "gain": 1.5},
    {
        "variant": "reference_only_resample_44k1_48k_44k1",
        "side": "reference",
        "operation": "resample_roundtrip",
        "intermediate_sample_rate": 48000,
    },
)

CSV_FIELDS = (
    "variant",
    "changed_side",
    "transformation",
    "status",
    "success",
    "format_valid",
    "ground_truth_match",
    "decoded_length",
    "symbol_count",
    "separator_count",
    "errors",
    "decode_error",
    "alignment_lag_samples",
    "alignment_correlation",
    "target_clipped_fraction",
    "reference_clipped_fraction",
    "elapsed_seconds",
    "decoded_text_json",
)


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


def _clip_and_measure(samples: np.ndarray) -> tuple[np.ndarray, float]:
    outside_range = (samples < -1.0) | (samples > 1.0)
    clipped_fraction = float(np.count_nonzero(outside_range) / outside_range.size)
    return np.clip(samples, -1.0, 1.0), clipped_fraction


def _transform(samples: np.ndarray, sample_rate: int, spec: dict[str, Any]) -> tuple[np.ndarray, float]:
    samples = np.asarray(samples, dtype=np.float64)
    if spec["operation"] == "gain":
        transformed = samples * float(spec["gain"])
    elif spec["operation"] == "resample_roundtrip":
        intermediate_rate = int(spec["intermediate_sample_rate"])
        if sample_rate != 44100 or intermediate_rate != 48000:
            raise ValueError("the reference experiment requires a 44,100→48,000→44,100 Hz round trip")
        transformed = resample_poly(samples, 160, 147, axis=0)
        transformed = resample_poly(transformed, 147, 160, axis=0)
        if len(transformed) < len(samples):
            transformed = np.pad(transformed, ((0, len(samples) - len(transformed)), (0, 0)))
        transformed = transformed[: len(samples)]
    else:
        raise ValueError(f"unsupported transformation: {spec['operation']}")
    return _clip_and_measure(transformed)


def _case_row(
    name: str,
    side: str | None,
    transformation: str,
    decoded: dict[str, Any] | None,
    elapsed_seconds: float,
    target_clipped_fraction: float = 0.0,
    reference_clipped_fraction: float = 0.0,
    decode_error: str | None = None,
) -> dict[str, Any]:
    decoded = decoded or {}
    text = str(decoded.get("decoded_text") or "")
    errors = decoded.get("errors") or []
    format_valid = decoded.get("format_valid") is True
    ground_truth_match = text == GROUND_TRUTH
    success = format_valid and ground_truth_match and not errors and decode_error is None
    alignment = decoded.get("alignment") or {}
    return {
        "variant": name,
        "changed_side": side,
        "transformation": transformation,
        "status": "PASS" if success else "FAIL",
        "success": success,
        "format_valid": format_valid,
        "ground_truth_match": ground_truth_match,
        "decoded_length": len(text),
        "symbol_count": decoded.get("symbol_count"),
        "separator_count": decoded.get("separator_count"),
        "errors": errors,
        "decode_error": decode_error,
        "alignment_lag_samples": alignment.get("lag_samples"),
        "alignment_correlation": alignment.get("correlation"),
        "target_clipped_fraction": target_clipped_fraction,
        "reference_clipped_fraction": reference_clipped_fraction,
        "elapsed_seconds": round(elapsed_seconds, 6),
        "decoded_text": text,
    }


def _run_case(
    name: str,
    target_path: Path,
    reference_path: Path,
    side: str | None,
    transformation: str,
    target_clipped_fraction: float = 0.0,
    reference_clipped_fraction: float = 0.0,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        decoded = decode_sleepy_alarm(target_path, reference_path)
        return _case_row(
            name,
            side,
            transformation,
            decoded,
            time.perf_counter() - started,
            target_clipped_fraction,
            reference_clipped_fraction,
        )
    except Exception as exc:  # retain per-variant failures in the matrix
        return _case_row(
            name,
            side,
            transformation,
            None,
            time.perf_counter() - started,
            target_clipped_fraction,
            reference_clipped_fraction,
            f"{type(exc).__name__}: {exc}",
        )


def _write_outputs(output_dir: Path, payload: dict[str, Any]) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / OUTPUT_JSON
    csv_path = output_dir / OUTPUT_CSV
    payload["csv"] = _relative(csv_path)
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in payload["results"]:
            csv_row = {field: row.get(field) for field in CSV_FIELDS}
            csv_row["errors"] = json.dumps(row["errors"], ensure_ascii=False, separators=(",", ":"))
            csv_row["decoded_text_json"] = json.dumps(row["decoded_text"], ensure_ascii=True)
            writer.writerow(csv_row)
    return json_path, csv_path


def run_experiment(target_path: Path, reference_path: Path, output_dir: Path) -> dict[str, Any]:
    target_path = target_path.resolve()
    reference_path = reference_path.resolve()
    target, target_rate = sf.read(target_path, always_2d=True, dtype="float64")
    reference, reference_rate = sf.read(reference_path, always_2d=True, dtype="float64")
    if target_rate != 44100 or reference_rate != 44100:
        raise ValueError("the recorded asymmetric variants require both input files at 44,100 Hz")

    results: list[dict[str, Any]] = [
        _run_case("baseline", target_path, reference_path, None, "original pair")
    ]
    with tempfile.TemporaryDirectory(prefix="stegano-audio-asymmetric-") as temporary_dir:
        temp_root = Path(temporary_dir)
        for spec in VARIANTS:
            side = str(spec["side"])
            original = target if side == "target" else reference
            sample_rate = target_rate if side == "target" else reference_rate
            transformed, clipped_fraction = _transform(original, sample_rate, spec)
            changed_path = temp_root / f"{spec['variant']}.wav"
            sf.write(changed_path, transformed, sample_rate, subtype="FLOAT")
            changed_target = changed_path if side == "target" else target_path
            changed_reference = changed_path if side == "reference" else reference_path
            transformation = (
                f"gain ×{spec['gain']:g}"
                if spec["operation"] == "gain"
                else "resample 44,100→48,000→44,100 Hz"
            )
            results.append(
                _run_case(
                    str(spec["variant"]),
                    changed_target,
                    changed_reference,
                    side,
                    transformation,
                    target_clipped_fraction=clipped_fraction if side == "target" else 0.0,
                    reference_clipped_fraction=clipped_fraction if side == "reference" else 0.0,
                )
            )

    baseline = results[0]
    variants = results[1:]
    variant_success_count = sum(row["success"] for row in variants)
    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "challenge": "Sleepy Alarm",
        "mode": "reference-assisted asymmetric robustness",
        "inputs": [
            {"role": "target", "path": _relative(target_path), "sha256": _sha256(target_path)},
            {"role": "reference", "path": _relative(reference_path), "sha256": _sha256(reference_path)},
        ],
        "configuration": {
            "carrier_hz": 8000.0,
            "baud": 50.0,
            "duration_seconds": 7.0,
            "ground_truth": GROUND_TRUTH,
            "pass_criteria": "format_valid and exact ground-truth match and no byte errors",
            "gain_factors": [0.5, 1.5],
            "resample_roundtrip_hz": [44100, 48000, 44100],
        },
        "baseline_success": baseline["success"],
        "variant_success_count": variant_success_count,
        "variant_count": len(variants),
        "variant_pass_fraction": f"{variant_success_count}/{len(variants)}",
        "all_variants_success": variant_success_count == len(variants),
        "results": results,
        "interpretation": (
            "Results characterize this challenge artifact and these exact transformations only. "
            "The baseline is reported separately from the six one-sided variants."
        ),
    }
    _write_outputs(output_dir, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=TARGET_PATH)
    parser.add_argument("--reference", type=Path, default=REFERENCE_PATH)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    payload = run_experiment(args.target, args.reference, args.output_dir)
    print("Variant                                      Status  Symbols  Separators  Characters  Errors")
    for row in payload["results"]:
        print(
            f"{row['variant']:<44} {row['status']:<7} "
            f"{str(row['symbol_count'] if row['symbol_count'] is not None else '-'):>7}  "
            f"{str(row['separator_count'] if row['separator_count'] is not None else '-'):>10}  "
            f"{row['decoded_length']:>10}  {len(row['errors']):>6}"
        )
    print(
        f"One-sided variants: {payload['variant_success_count']}/{payload['variant_count']} PASS; "
        f"baseline: {'PASS' if payload['baseline_success'] else 'FAIL'}"
    )
    print(f"JSON: {_relative(args.output_dir.resolve() / OUTPUT_JSON)}")
    print(f"CSV:  {_relative(args.output_dir.resolve() / OUTPUT_CSV)}")
    return 0 if payload["baseline_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
