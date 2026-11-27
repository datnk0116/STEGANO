#!/usr/bin/env python3
"""Independently measure Sleepy Alarm ASK carrier, symbol timing, and active duration."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from scipy.signal import find_peaks, periodogram

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from stegano.audio import _align  # noqa: E402

DEFAULT_TARGET = ROOT / "data" / "sleepy_alarm" / "morning_n_breakfast.mp3"
DEFAULT_REFERENCE = ROOT / "data" / "sleepy_alarm" / "morning_n_breakfast_original.mp3"
DEFAULT_JSON = ROOT / "results" / "independent-measurement" / "ask_params.json"
DEFAULT_LOG = ROOT / "results" / "independent-measurement" / "ask_params.log"


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def measure_residual_arrays(
    target: np.ndarray,
    sr: int,
    reference: np.ndarray,
    ref_sr: int,
) -> dict[str, Any]:
    """Measure carrier frequency, ~5 ms envelope transitions, and drop-off independently."""
    x, y, alignment = _align(target, sr, reference, ref_sr)
    ov_start = int(alignment["target_start_sample"])
    res_overlap = (x - y)[:, 0]
    prefix = target[:ov_start, 0]
    if target.shape[1] != reference.shape[1] and target.shape[1] > 1:
        prefix = target[:ov_start].mean(axis=1)
    res_full = np.concatenate((prefix, res_overlap))

    # 1. Carrier peak via full aligned overlap periodogram (>=100 Hz to Nyquist).
    freqs, psd = periodogram(res_overlap, fs=sr, scaling="spectrum")
    valid = (freqs >= 100.0) & (freqs < sr / 2.0)
    masked_psd = np.where(valid, psd, -1.0)
    peak_idx = int(np.argmax(masked_psd))
    carrier_hz = float(freqs[peak_idx])
    total_power = float(psd[valid].sum())
    band = (freqs >= carrier_hz - 100.0) & (freqs <= carrier_hz + 100.0)
    band_ratio = float(psd[band].sum() / max(total_power, 1e-30))

    # 2. Sliding ~5 ms baseband envelope around the detected carrier peak.
    win = max(1, int(round(0.005 * sr)))
    kernel = np.ones(win, dtype=np.float64) / win
    t = np.arange(len(res_full), dtype=np.float64) / sr
    env = 2.0 * np.abs(
        np.convolve(res_full * np.exp(-2j * np.pi * carrier_hz * t), kernel, mode="same")
    )

    # 3. Carrier drop-off time using data-driven overlap percentiles.
    env_ov = env[ov_start:]
    p10 = float(np.percentile(env_ov, 10))
    p95 = float(np.percentile(env_ov, 95))
    drop_thresh = p10 + 0.20 * (p95 - p10)
    above = np.where(env_ov > drop_thresh)[0]
    if len(above) == 0:
        raise ValueError("carrier envelope never exceeded drop-off threshold")
    last_active_sample = ov_start + int(above[-1])
    dropoff_seconds = float(last_active_sample / sr)

    tail_start = min(len(env) - 1, last_active_sample + int(0.2 * sr))
    tail_env = env[tail_start:]
    tail_stats = {
        "tail_start_seconds": float(tail_start / sr),
        "mean": float(tail_env.mean()),
        "std": float(tail_env.std(ddof=1)) if len(tail_env) > 1 else 0.0,
        "max": float(tail_env.max()),
    }

    # 4. Amplitude transition detection inside the active aligned window.
    a0 = ov_start + win
    a1 = last_active_sample
    if a1 <= a0 + win:
        raise ValueError("active residual window too short for transition detection")
    seg = env[a0:a1]
    diff = np.abs(seg[win:] - seg[:-win])
    height_thresh = 0.25 * p95
    peaks, _ = find_peaks(
        diff,
        distance=max(1, int(round(0.010 * sr))),
        height=height_thresh,
        prominence=0.5 * height_thresh,
    )
    if len(peaks) < 2:
        raise ValueError(f"insufficient amplitude transitions detected: {len(peaks)}")

    times_ms = (peaks + a0 + win / 2.0) / sr * 1000.0
    dts_ms = np.diff(times_ms)

    # Identify single-symbol jumps from data (shortest cluster <= 1.5 * Q25),
    # then normalize all intervals by integer run length k = round(dt / median(single)).
    q25 = float(np.percentile(dts_ms, 25))
    single = dts_ms[dts_ms <= 1.5 * q25]
    if len(single) == 0:
        single = dts_ms
    single_median = float(np.median(single))
    run_lengths = np.maximum(1, np.round(dts_ms / single_median)).astype(int)
    normalized_ms = dts_ms / run_lengths

    single_mean = float(single.mean())
    single_std = float(single.std(ddof=1)) if len(single) > 1 else 0.0
    norm_mean = float(normalized_ms.mean())
    norm_std = float(normalized_ms.std(ddof=1)) if len(normalized_ms) > 1 else 0.0

    # Post-measurement error checks against nominal reference values (8000 Hz, 20 ms, 7.0 s).
    return {
        "sample_rate_hz": int(sr),
        "target_samples": int(len(target)),
        "reference_samples": int(len(reference)),
        "overlap_samples": int(len(res_overlap)),
        "overlap_duration_seconds": float(len(res_overlap) / sr),
        "alignment": alignment,
        "carrier": {
            "peak_hz": carrier_hz,
            "band_pm_100hz_energy_ratio": band_ratio,
            "error_vs_8000hz_hz": float(carrier_hz - 8000.0),
        },
        "envelope": {
            "window_samples": int(win),
            "window_ms": float(win / sr * 1000.0),
            "overlap_p10": p10,
            "overlap_p95": p95,
            "dropoff_threshold": float(drop_thresh),
            "transition_diff_height_threshold": float(height_thresh),
        },
        "transitions": {
            "transition_count": int(len(peaks)),
            "interval_count": int(len(dts_ms)),
            "raw_intervals_ms": {
                "mean": float(dts_ms.mean()),
                "std": float(dts_ms.std(ddof=1)) if len(dts_ms) > 1 else 0.0,
                "median": float(np.median(dts_ms)),
                "min": float(dts_ms.min()),
                "max": float(dts_ms.max()),
            },
            "single_symbol_intervals": {
                "count": int(len(single)),
                "mean_ms": single_mean,
                "std_ms": single_std,
                "error_vs_20ms_ms": float(single_mean - 20.0),
                "relative_error_vs_20ms_pct": float(abs(single_mean - 20.0) / 20.0 * 100.0),
                "implied_baud": float(1000.0 / single_mean),
            },
            "run_length_normalized": {
                "count": int(len(normalized_ms)),
                "max_run_length_k": int(run_lengths.max()),
                "mean_ms": norm_mean,
                "std_ms": norm_std,
                "error_vs_20ms_ms": float(norm_mean - 20.0),
                "relative_error_vs_20ms_pct": float(abs(norm_mean - 20.0) / 20.0 * 100.0),
                "implied_baud": float(1000.0 / norm_mean),
            },
        },
        "dropoff": {
            "last_active_sample": int(last_active_sample),
            "dropoff_seconds": dropoff_seconds,
            "error_vs_7s_seconds": float(dropoff_seconds - 7.0),
            "tail_noise_floor": tail_stats,
        },
    }


def format_report(payload: dict[str, Any]) -> str:
    """Format a concise human-readable log of the independent ASK measurements."""
    m = payload["measurements"]
    c = m["carrier"]
    tr = m["transitions"]
    raw = tr["raw_intervals_ms"]
    ss = tr["single_symbol_intervals"]
    rn = tr["run_length_normalized"]
    dr = m["dropoff"]
    al = m["alignment"]
    env = m["envelope"]
    lines = [
        f"Target: {payload['inputs']['target']}",
        f"Reference: {payload['inputs']['reference']}",
        (
            f"Alignment: lag={al['lag_samples']} samples, "
            f"target_start_sample={al['target_start_sample']}, "
            f"corr={al['correlation']:.6f}"
        ),
        (
            f"Carrier peak: {c['peak_hz']:.4f} Hz "
            f"(err vs 8000 Hz: {c['error_vs_8000hz_hz']:+.4f} Hz), "
            f"+-100 Hz energy ratio={c['band_pm_100hz_energy_ratio']:.6f} "
            f"({c['band_pm_100hz_energy_ratio']*100:.2f}%)"
        ),
        (
            f"Envelope window: {env['window_samples']} samples "
            f"({env['window_ms']:.4f} ms), p10={env['overlap_p10']:.6f}, "
            f"p95={env['overlap_p95']:.6f}"
        ),
        (
            f"Transitions detected: {tr['transition_count']} "
            f"({tr['interval_count']} intervals); raw interval mean={raw['mean']:.4f} ms, "
            f"std={raw['std']:.4f} ms, median={raw['median']:.4f} ms "
            f"[{raw['min']:.4f}, {raw['max']:.4f}] ms"
        ),
        (
            f"Single-step intervals (k=1, n={ss['count']}): "
            f"mean={ss['mean_ms']:.4f} ms, std={ss['std_ms']:.4f} ms, "
            f"err vs 20 ms={ss['error_vs_20ms_ms']:+.4f} ms "
            f"({ss['relative_error_vs_20ms_pct']:.2f}%), implied={ss['implied_baud']:.2f} baud"
        ),
        (
            f"Run-length normalized (n={rn['count']}, max_k={rn['max_run_length_k']}): "
            f"mean={rn['mean_ms']:.4f} ms, std={rn['std_ms']:.4f} ms, "
            f"err vs 20 ms={rn['error_vs_20ms_ms']:+.4f} ms "
            f"({rn['relative_error_vs_20ms_pct']:.2f}%), implied={rn['implied_baud']:.2f} baud"
        ),
        (
            f"Carrier drop-off: {dr['dropoff_seconds']:.4f} s "
            f"(sample {dr['last_active_sample']}, err vs 7.0 s: {dr['error_vs_7s_seconds']:+.4f} s), "
            f"tail noise mean={dr['tail_noise_floor']['mean']:.6f}, "
            f"max={dr['tail_noise_floor']['max']:.6f}"
        ),
    ]
    return "\n".join(lines) + "\n"


def run_self_check() -> None:
    """Assert independent recovery on a synthetic shifted 3-level ASK signal."""
    sr = 44100
    rng = np.random.default_rng(20261127)
    n_total = int(9.5 * sr)
    n_active = int(7.0 * sr)
    t = np.arange(n_total, dtype=np.float64) / sr

    # Cover broadband noise + known lag (1200 samples) + 8000 Hz 50-baud ASK payload.
    ref_mono = rng.normal(0.0, 0.05, n_total)
    lag = 1200
    target_mono = np.concatenate((rng.normal(0.0, 0.05, lag), ref_mono[:-lag]))
    sym_samples = round(sr / 50.0)
    levels = np.array([0.0001, 0.0020, 0.0050])
    # Alternate levels to guarantee many single-step transitions across 350 symbols.
    syms = np.array([((i * 7 + (i // 3)) % 3) for i in range(350)])
    env = np.zeros(n_total, dtype=np.float64)
    active_env = np.repeat(levels[syms], sym_samples)[:n_active]
    env[: len(active_env)] = active_env
    target_mono += env * np.cos(2.0 * np.pi * 8000.0 * t)

    res = measure_residual_arrays(
        np.column_stack([target_mono, target_mono]),
        sr,
        np.column_stack([ref_mono, ref_mono]),
        sr,
    )
    assert res["alignment"]["lag_samples"] == lag, res["alignment"]
    assert abs(res["carrier"]["peak_hz"] - 8000.0) < 5.0, res["carrier"]
    assert abs(res["transitions"]["run_length_normalized"]["mean_ms"] - 20.0) < 0.5, res["transitions"]
    assert abs(res["dropoff"]["dropoff_seconds"] - 7.0) < 0.05, res["dropoff"]
    print("Self-check PASS: synthetic ASK parameters recovered within tolerance.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--log-out", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    if args.self_check:
        run_self_check()
        return 0

    target_path = _resolve(args.target)
    ref_path = _resolve(args.reference)
    json_path = _resolve(args.json_out)
    log_path = _resolve(args.log_out)

    target, sr = sf.read(target_path, always_2d=True, dtype="float64")
    reference, ref_sr = sf.read(ref_path, always_2d=True, dtype="float64")
    measurements = measure_residual_arrays(target, sr, reference, ref_sr)

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "independent_residual_periodogram_and_5ms_envelope_transitions",
        "inputs": {
            "target": _relative(target_path),
            "reference": _relative(ref_path),
        },
        "measurements": measurements,
    }
    report_text = format_report(payload)

    json_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log_path.write_text(report_text, encoding="utf-8")

    print(report_text, end="")
    print(f"Wrote {_relative(json_path)} and {_relative(log_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
