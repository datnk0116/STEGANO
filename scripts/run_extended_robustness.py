#!/usr/bin/env python3
"""Run extended Blue 3 and Sleepy Alarm robustness matrices."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image, ImageEnhance, ImageFilter
from scipy.signal import butter, resample_poly, sosfiltfilt

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from stegano.audio import diagnose_sleepy_alarm  # noqa: E402
from stegano.image import decode_blue3  # noqa: E402


BLUE3_DEFAULT = ROOT / "data" / "blue3" / "blue.png"
SLEEPY_DEFAULT = ROOT / "data" / "sleepy_alarm" / "morning_n_breakfast.mp3"
REFERENCE_DEFAULT = ROOT / "data" / "sleepy_alarm" / "morning_n_breakfast_original.mp3"
BLUE3_GROUND_TRUTH = "byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}"
SLEEPY_GROUND_TRUTH = "ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}"
DEFAULT_SEED = 20261114


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def _levenshtein_distance(expected: str, observed: str) -> int:
    if len(expected) < len(observed):
        expected, observed = observed, expected
    previous = list(range(len(observed) + 1))
    for i, left in enumerate(expected, start=1):
        current = [i]
        for j, right in enumerate(observed, start=1):
            current.append(min(
                current[-1] + 1,
                previous[j] + 1,
                previous[j - 1] + (left != right),
            ))
        previous = current
    return previous[-1]


def _blue_character_metrics(expected: str, observed: str | None) -> dict:
    if observed is None:
        return {
            "candidate_available": False,
            "candidate_length": 0,
            "position_matches": 0,
            "position_accuracy": 0.0,
            "edit_distance": None,
            "normalized_edit_similarity": 0.0,
        }
    distance = _levenshtein_distance(expected, observed)
    denominator = max(len(expected), len(observed), 1)
    matches = sum(left == right for left, right in zip(expected, observed))
    return {
        "candidate_available": True,
        "candidate_length": len(observed),
        "position_matches": matches,
        "position_accuracy": matches / denominator,
        "edit_distance": distance,
        "normalized_edit_similarity": 1.0 - distance / denominator,
    }


def _expected_ask_symbols(expected_text: str) -> str:
    if not expected_text:
        raise ValueError("expected_text must not be empty")
    if any(ord(character) > 0x7F for character in expected_text):
        raise ValueError("Sleepy Alarm expected payload must be ASCII")
    return " ".join(f"{ord(character):08b}" for character in expected_text)


def _sleepy_symbol_metrics(expected_text: str, observed_symbols: list[str]) -> dict:
    expected = _expected_ask_symbols(expected_text)
    observed = "".join(observed_symbols)
    if len(observed) != len(expected):
        raise ValueError(f"expected {len(expected)} measured symbols, received {len(observed)}")
    if any(symbol not in {"0", "1", " "} for symbol in observed):
        raise ValueError("observed symbols must contain only '0', '1' or spaces")

    bit_positions = [index for index, symbol in enumerate(expected) if symbol in "01"]
    separator_positions = [index for index, symbol in enumerate(expected) if symbol == " "]
    bit_errors = sum(observed[index] != expected[index] for index in bit_positions)
    separator_tp = sum(observed[index] == " " for index in separator_positions)
    separator_fn = len(separator_positions) - separator_tp
    separator_fp = sum(observed[index] == " " for index in bit_positions)
    symbol_errors = sum(left != right for left, right in zip(expected, observed))
    predicted_separators = separator_tp + separator_fp
    return {
        "expected_symbol_count": len(expected),
        "symbol_errors": symbol_errors,
        "symbol_error_rate": symbol_errors / len(expected),
        "bit_count": len(bit_positions),
        "bit_errors": bit_errors,
        "bit_error_rate": bit_errors / len(bit_positions),
        "expected_separators": len(separator_positions),
        "true_positive_separators": separator_tp,
        "false_positive_separators": separator_fp,
        "false_negative_separators": separator_fn,
        "separator_precision": separator_tp / predicted_separators if predicted_separators else None,
        "separator_recall": separator_tp / len(separator_positions) if separator_positions else None,
    }


def _write_json_csv(output_dir: Path, stem: str, payload: dict, rows: list[dict]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{stem}.json"
    csv_path = output_dir / f"{stem}.csv"
    payload["csv"] = _relative(csv_path)
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if rows:
        fields = list(dict.fromkeys(key for row in rows for key in row))
        with csv_path.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({
                    key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
                    for key, value in row.items()
                })


def _image_variants(original: Image.Image, seed: int) -> dict[str, tuple[Image.Image, str]]:
    variants: dict[str, tuple[Image.Image, str]] = {
        "brightness_0.9": (ImageEnhance.Brightness(original).enhance(0.9), "brightness ×0.9"),
        "brightness_1.1": (ImageEnhance.Brightness(original).enhance(1.1), "brightness ×1.1"),
        "contrast_0.9": (ImageEnhance.Contrast(original).enhance(0.9), "contrast ×0.9"),
        "contrast_1.1": (ImageEnhance.Contrast(original).enhance(1.1), "contrast ×1.1"),
        "gaussian_blur_radius_0.3": (
            original.filter(ImageFilter.GaussianBlur(0.3)), "Gaussian blur radius 0.3"
        ),
    }
    if original.width <= 32 or original.height <= 32:
        raise ValueError("image must be larger than 32×32 pixels for the 16-pixel crop case")
    variants["crop_16px"] = (
        original.crop((16, 16, original.width - 16, original.height - 16)),
        "crop 16 pixels from each edge",
    )

    rng = np.random.default_rng(seed)
    pixels = np.asarray(original, dtype=np.int16)
    for sigma in (0.5, 1.0, 2.0):
        noised = np.clip(pixels + rng.normal(0, sigma, pixels.shape), 0, 255).astype(np.uint8)
        variants[f"gaussian_noise_sigma_{sigma}"] = (
            Image.fromarray(noised), f"Gaussian noise σ={sigma}",
        )
    return variants


def run_blue3_matrix(image_path: Path, output_dir: Path, seed: int) -> dict:
    if not image_path.is_file():
        raise FileNotFoundError(f"missing Blue 3 image: {image_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline_started = time.perf_counter()
    baseline_error = None
    try:
        baseline = decode_blue3(image_path)
        baseline_candidate = baseline.get("flag")
        baseline_valid = baseline.get("format_valid") is True
    except Exception as exc:
        baseline_candidate = None
        baseline_valid = False
        baseline_error = f"{type(exc).__name__}: {exc}"
    baseline_row = {
        "status": "PASS" if baseline_valid and baseline_candidate == BLUE3_GROUND_TRUTH else "FAIL",
        "format_valid": baseline_valid,
        "ground_truth_match": baseline_candidate == BLUE3_GROUND_TRUTH,
        "success": baseline_valid and baseline_candidate == BLUE3_GROUND_TRUTH,
        "decoded_length": len(baseline_candidate) if baseline_candidate else 0,
        "elapsed_seconds": time.perf_counter() - baseline_started,
        "candidate": baseline_candidate,
        "error": baseline_error,
    }

    with Image.open(image_path) as image:
        original = image.convert("RGB")
    variants = _image_variants(original, seed)
    rows: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="stegano-blue3-robustness-") as temporary:
        temp_root = Path(temporary)
        expected_length = len(BLUE3_GROUND_TRUTH)
        for name, (variant_image, transformation) in variants.items():
            started = time.perf_counter()
            row = {
                "variant": name,
                "transformation": transformation,
                "status": "FAIL",
                "success": False,
                "format_valid": False,
                "ground_truth_match": False,
                "decoded_length": 0,
                "candidate": None,
                "candidate_at_expected_length": None,
                "attempt_count": None,
                "elapsed_seconds": None,
                "error": None,
            }
            try:
                path = temp_root / f"{name}.png"
                variant_image.save(path, format="PNG")
                decoded = decode_blue3(path)
                candidate = decoded.get("flag")
                attempts = decoded.get("attempts") or []
                candidate_at_length = next(
                    (item["candidate"] for item in attempts if item.get("length") == expected_length),
                    candidate if candidate and len(candidate) == expected_length else None,
                )
                success = decoded.get("format_valid") is True and candidate == BLUE3_GROUND_TRUTH
                row.update(
                    status="PASS" if success else "FAIL",
                    success=success,
                    format_valid=decoded.get("format_valid") is True,
                    ground_truth_match=candidate == BLUE3_GROUND_TRUTH,
                    decoded_length=len(candidate) if candidate else 0,
                    candidate=candidate,
                    candidate_at_expected_length=candidate_at_length,
                    attempt_count=len(attempts),
                    **_blue_character_metrics(BLUE3_GROUND_TRUTH, candidate_at_length),
                )
            except Exception as exc:  # keep every requested transformation in the matrix
                row["error"] = f"{type(exc).__name__}: {exc}"
                row.update(_blue_character_metrics(BLUE3_GROUND_TRUTH, None))
            row["elapsed_seconds"] = round(time.perf_counter() - started, 6)
            rows.append(row)

    success_count = sum(bool(row["success"]) for row in rows)
    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "challenge": "Blue 3",
        "input": _relative(image_path),
        "ground_truth_used_only_for_validation": True,
        "baseline": baseline_row,
        "baseline_success": baseline_row["success"],
        "seed": seed,
        "variant_count": len(rows),
        "success_count": success_count,
        "pass_fraction": f"{success_count}/{len(rows)}",
        "partial_recovery_note": (
            "Character metrics use a candidate at the expected flag length. "
            "A missing candidate has no measured edit distance."
        ),
        "results": rows,
        "warning": "Results characterize this decoder and exact attack settings only.",
    }
    _write_json_csv(output_dir, "blue3_extended_robustness", payload, rows)
    return payload


def _decode_audio_trial(
    name: str,
    side: str,
    target_path: Path,
    reference_path: Path,
    expected: str,
) -> dict:
    started = time.perf_counter()
    row = {
        "variant": name,
        "transformed_side": side,
        "status": "FAIL",
        "success": False,
        "format_valid": False,
        "ground_truth_match": False,
        "decoded_length": 0,
        "symbols": None,
        "separators": None,
        "error_count": None,
        "errors": [],
        "alignment_correlation": None,
        "decoded_text": "",
        "decode_error": None,
    }
    try:
        diagnosed = diagnose_sleepy_alarm(target_path, reference_path)
        result = diagnosed["result"]
        diagnostics = diagnosed["diagnostics"]
        text = str(result.get("decoded_text") or "")
        errors = result.get("errors") or []
        success = result.get("format_valid") is True and text == expected and not errors
        row.update(
            status="PASS" if success else "FAIL",
            success=success,
            format_valid=result.get("format_valid") is True,
            ground_truth_match=text == expected,
            decoded_length=len(text),
            symbols=result.get("symbol_count"),
            separators=result.get("separator_count"),
            error_count=len(errors),
            errors=errors,
            alignment_correlation=(result.get("alignment") or {}).get("correlation"),
            decoded_text=text,
            **_sleepy_symbol_metrics(expected, diagnostics["symbol_labels"]),
        )
    except Exception as exc:  # retain failed runs rather than dropping the row
        row["decode_error"] = f"{type(exc).__name__}: {exc}"
    row["elapsed_seconds"] = round(time.perf_counter() - started, 6)
    return row


def _resample_roundtrip(samples: np.ndarray) -> np.ndarray:
    transformed = resample_poly(samples, 160, 147, axis=0)
    transformed = resample_poly(transformed, 147, 160, axis=0)
    if len(transformed) < len(samples):
        transformed = np.pad(transformed, ((0, len(samples) - len(transformed)), (0, 0)))
    return transformed[:len(samples)]


def _evaluate_audio_arrays(
    name: str,
    side: str,
    target: np.ndarray,
    reference: np.ndarray,
    sample_rate: int,
    expected: str,
) -> dict:
    with tempfile.TemporaryDirectory(prefix="stegano-audio-robustness-") as temporary:
        temp_root = Path(temporary)
        target_path = temp_root / "target.wav"
        reference_path = temp_root / "reference.wav"
        sf.write(target_path, target, sample_rate, subtype="PCM_24")
        sf.write(reference_path, reference, sample_rate, subtype="PCM_24")
        return _decode_audio_trial(name, side, target_path, reference_path, expected)


def run_sleepy_alarm_matrix(
    audio_path: Path,
    reference_path: Path,
    output_dir: Path,
    seed: int,
    expected: str,
) -> dict:
    for path in (audio_path, reference_path):
        if not path.is_file():
            raise FileNotFoundError(f"missing audio input: {path}")
    target, sample_rate = sf.read(audio_path, always_2d=True, dtype="float64")
    reference, reference_rate = sf.read(reference_path, always_2d=True, dtype="float64")
    if sample_rate != reference_rate:
        raise ValueError("target/reference sample rates must match for this robustness matrix")

    baseline = _decode_audio_trial("baseline", "none", audio_path, reference_path, expected)
    rows = [baseline]
    rng = np.random.default_rng(seed)

    def evaluate(name: str, changed_target: np.ndarray, changed_reference: np.ndarray, side: str) -> None:
        rows.append(_evaluate_audio_arrays(
            name, side, changed_target, changed_reference, sample_rate, expected
        ))

    for side in ("target", "reference"):
        base = target if side == "target" else reference
        for gain in (0.25, 0.5, 0.75, 1.25, 1.5, 1.75):
            changed = np.clip(base * gain, -1.0, 1.0)
            evaluate(
                f"{side}_gain_{gain}",
                changed if side == "target" else target,
                changed if side == "reference" else reference,
                side,
            )
        for snr_db in (30, 20, 10):
            power = float(np.mean(base ** 2))
            noise_power = power / (10 ** (snr_db / 10))
            changed = base + rng.normal(0, np.sqrt(noise_power), base.shape)
            evaluate(
                f"{side}_awgn_snr_{snr_db}db",
                changed if side == "target" else target,
                changed if side == "reference" else reference,
                side,
            )
        sos = butter(4, [7500, 8500], btype="bandpass", fs=sample_rate, output="sos")
        changed = sosfiltfilt(sos, base, axis=0)
        evaluate(
            f"{side}_bandpass_7p5_8p5khz",
            changed if side == "target" else target,
            changed if side == "reference" else reference,
            side,
        )
        changed = _resample_roundtrip(base)
        evaluate(
            f"{side}_resample_roundtrip_44k1_48k",
            changed if side == "target" else target,
            changed if side == "reference" else reference,
            side,
        )

    success_count = sum(bool(row["success"]) for row in rows)
    aggregate = {
        "mean_symbol_error_rate": float(np.mean([row["symbol_error_rate"] for row in rows if "symbol_error_rate" in row])),
        "mean_bit_error_rate": float(np.mean([row["bit_error_rate"] for row in rows if "bit_error_rate" in row])),
        "mean_separator_precision": float(np.mean([
            row["separator_precision"] for row in rows
            if row.get("separator_precision") is not None
        ])),
        "mean_separator_recall": float(np.mean([
            row["separator_recall"] for row in rows
            if row.get("separator_recall") is not None
        ])),
    }
    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "challenge": "Sleepy Alarm",
        "mode": "reference-assisted one-sided robustness",
        "inputs": {"target": _relative(audio_path), "reference": _relative(reference_path)},
        "ground_truth_used_only_for_validation": True,
        "seed": seed,
        "pass_criteria": "format_valid and exact ground-truth match and no byte errors",
        "trial_count": len(rows),
        "pass_count": success_count,
        "pass_fraction": f"{success_count}/{len(rows)}",
        "baseline_success": baseline["success"],
        "aggregate": aggregate,
        "partial_recovery_note": (
            "Symbol, bit, and separator metrics compare the measured decoder symbols to the "
            "expected ASK encoding after extraction; expected text is never passed to the decoder."
        ),
        "results": rows,
        "warning": "Single-artifact exploratory matrix; not a population-level robustness estimate.",
    }
    _write_json_csv(output_dir, "sleepy_alarm_robustness_matrix", payload, rows)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blue3", type=Path, default=BLUE3_DEFAULT)
    parser.add_argument("--sleepy", type=Path, default=SLEEPY_DEFAULT)
    parser.add_argument("--reference", type=Path, default=REFERENCE_DEFAULT)
    parser.add_argument("--expected", default=SLEEPY_GROUND_TRUTH)
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "robustness")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    try:
        blue = run_blue3_matrix(args.blue3, args.out, args.seed)
        sleepy = run_sleepy_alarm_matrix(args.sleepy, args.reference, args.out, args.seed, args.expected)
    except Exception as exc:
        parser.error(f"robustness experiment failed: {type(exc).__name__}: {exc}")

    print(json.dumps({
        "blue3": {
            "baseline_status": blue["baseline"]["status"],
            "variant_pass_fraction": blue["pass_fraction"],
            "json": _relative(args.out.resolve() / "blue3_extended_robustness.json"),
        },
        "sleepy_alarm": {
            "baseline_status": "PASS" if sleepy["baseline_success"] else "FAIL",
            "pass_fraction": sleepy["pass_fraction"],
            "trials": sleepy["trial_count"],
            "json": _relative(args.out.resolve() / "sleepy_alarm_robustness_matrix.json"),
        },
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
