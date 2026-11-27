#!/usr/bin/env python3
"""Reproduce post-hoc signal discovery metrics and render the residual spectrum SVG."""

from __future__ import annotations

import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image
from scipy.signal import periodogram

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stegano.audio import _align  # noqa: E402


BLUE3_PATH = ROOT / "data/blue3/blue.png"
TARGET_AUDIO_PATH = ROOT / "data/sleepy_alarm/morning_n_breakfast.mp3"
REF_AUDIO_PATH = ROOT / "data/sleepy_alarm/morning_n_breakfast_original.mp3"
DEFAULT_JSON = ROOT / "results/final-2026-11-27/discovery-signals.json"
DEFAULT_SVG = ROOT / "report/figures/sleepy-residual-spectrum.svg"


def inspect_blue3(path: Path = BLUE3_PATH) -> dict:
    """Measure pixel uniqueness and diagonal localization on the Blue 3 image."""
    with Image.open(path) as im:
        pixels = np.asarray(im.convert("RGB"), dtype=np.uint8)
    h, w, _ = pixels.shape
    colors, counts = np.unique(pixels.reshape(-1, 3), axis=0, return_counts=True)
    modal_idx = int(np.argmax(counts))
    base = colors[modal_idx]
    diff_mask = np.any(pixels != base, axis=2)
    ys, xs = np.where(diff_mask)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "width": int(w),
        "height": int(h),
        "total_pixels": int(w * h),
        "unique_rgb_count": int(len(colors)),
        "modal_rgb": [int(v) for v in base],
        "modal_pixel_count": int(counts[modal_idx]),
        "modal_rgb_fraction": float(counts[modal_idx] / (w * h)),
        "non_base_pixel_count": int(diff_mask.sum()),
        "non_base_fraction": float(diff_mask.sum() / (w * h)),
        "max_abs_x_minus_y_px": int(np.max(np.abs(xs - ys))) if len(xs) else 0,
    }


def _band_ratio(freqs: np.ndarray, power: np.ndarray, sr: int, carrier: float = 8000.0) -> tuple[float, float]:
    total_band = (freqs >= 100.0) & (freqs < sr / 2.0)
    carrier_band = (freqs >= carrier - 100.0) & (freqs <= carrier + 100.0)
    total_power = float(power[total_band].sum())
    ratio = float(power[carrier_band].sum() / max(total_power, 1e-30))
    peak_hz = float(freqs[int(np.argmax(power))])
    return peak_hz, ratio


def inspect_sleepy_alarm(
    target_path: Path = TARGET_AUDIO_PATH,
    ref_path: Path = REF_AUDIO_PATH,
    duration_seconds: float = 7.0,
) -> tuple[dict, np.ndarray, np.ndarray, np.ndarray]:
    """Compare 0-7s power spectra before and after reference alignment subtraction."""
    target, sr = sf.read(target_path, always_2d=True, dtype="float64")
    ref, ref_sr = sf.read(ref_path, always_2d=True, dtype="float64")
    x, y, alignment = _align(target, sr, ref, ref_sr)

    win = int(round(duration_seconds * sr))
    t_ch0 = target[:win, 0]
    r_ch0 = (x - y)[:win, 0]

    freqs, psd_target = periodogram(t_ch0, fs=sr, scaling="spectrum")
    _, psd_residual = periodogram(r_ch0, fs=sr, scaling="spectrum")
    t_peak_hz, t_ratio = _band_ratio(freqs, psd_target, sr)
    r_peak_hz, r_ratio = _band_ratio(freqs, psd_residual, sr)

    metrics = {
        "target_path": target_path.relative_to(ROOT).as_posix(),
        "reference_path": ref_path.relative_to(ROOT).as_posix(),
        "sample_rate_hz": int(sr),
        "analysis_window_seconds": duration_seconds,
        "alignment": alignment,
        "target_peak_hz": t_peak_hz,
        "target_8khz_band_energy_ratio": t_ratio,
        "residual_peak_hz": r_peak_hz,
        "residual_8khz_band_energy_ratio": r_ratio,
    }
    return metrics, freqs, psd_target, psd_residual


def _downsample_bins(freqs: np.ndarray, power: np.ndarray, max_hz: float = 16000.0, bins: int = 320) -> tuple[np.ndarray, np.ndarray]:
    edges = np.linspace(0.0, max_hz, bins + 1)
    centers = 0.5 * (edges[:-1] + edges[1:])
    vals = np.zeros(bins, dtype=np.float64)
    for i in range(bins):
        mask = (freqs >= edges[i]) & (freqs < edges[i + 1])
        vals[i] = float(power[mask].max()) if np.any(mask) else 0.0
    vals /= max(float(vals.max()), 1e-30)
    return centers, vals


def render_spectrum_svg(
    freqs: np.ndarray,
    psd_target: np.ndarray,
    psd_residual: np.ndarray,
    metrics: dict,
    out_path: Path = DEFAULT_SVG,
) -> None:
    """Render a side-by-side 0-16 kHz spectrum comparison SVG."""
    f_t, v_t = _downsample_bins(freqs, psd_target)
    f_r, v_r = _downsample_bins(freqs, psd_residual)

    w, h = 1100, 420
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">',
        '<rect width="100%" height="100%" fill="#f6f8fb"/>',
        '<text x="32" y="42" font-family="Arial,Helvetica,sans-serif" font-size="22px" font-weight="700" fill="#17243a">Sleepy Alarm: 0–16 kHz spectrum before vs. after reference subtraction</text>',
        f'<text x="32" y="66" font-family="Arial,Helvetica,sans-serif" font-size="13px" fill="#53647c">Post-hoc inspection (first 7.0 s, lag={metrics["alignment"]["lag_samples"]} samples, corr={metrics["alignment"]["correlation"]:.4f})</text>',
    ]

    panels = [
        (32, "Target audio (before subtraction)", f_t, v_t, "#bd3b37", f'8 kHz band ratio: {metrics["target_8khz_band_energy_ratio"]*100:.2f}% (masked by music)'),
        (566, "Aligned residual (target − reference)", f_r, v_r, "#17804b", f'Peak: {metrics["residual_peak_hz"]:.0f} Hz · 8 kHz band ratio: {metrics["residual_8khz_band_energy_ratio"]*100:.2f}%'),
    ]
    pw, ph = 502, 286
    px_pad, py_top, plot_w, plot_h = 46, 56, 434, 180

    for ox, title, fc, val, color, note in panels:
        oy = 88
        parts.append(f'<rect x="{ox}" y="{oy}" width="{pw}" height="{ph}" rx="12" fill="#ffffff" stroke="#d9e0ea"/>')
        parts.append(f'<text x="{ox + 20}" y="{oy + 30}" font-family="Arial,Helvetica,sans-serif" font-size="16px" font-weight="700" fill="#17243a">{html.escape(title)}</text>')
        gx, gy = ox + px_pad, oy + py_top
        parts.append(f'<rect x="{gx}" y="{gy}" width="{plot_w}" height="{plot_h}" fill="#fbfcfe" stroke="#e2e8f0"/>')

        # 8 kHz marker line
        x8 = gx + (8000.0 / 16000.0) * plot_w
        parts.append(f'<line x1="{x8:.1f}" y1="{gy}" x2="{x8:.1f}" y2="{gy + plot_h}" stroke="#1f4e79" stroke-width="1.5" stroke-dasharray="4,4"/>')
        parts.append(f'<text x="{x8 + 5:.1f}" y="{gy + 16}" font-family="Arial,Helvetica,sans-serif" font-size="11px" font-weight="700" fill="#1f4e79">8 kHz</text>')

        # Spectrum polyline
        pts = " ".join(f"{gx + (f / 16000.0) * plot_w:.1f},{gy + plot_h - v * (plot_h - 14):.1f}" for f, v in zip(fc, val))
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="1.8" points="{pts}"/>')

        # X-axis ticks (0, 4, 8, 12, 16 kHz)
        for khz in (0, 4, 8, 12, 16):
            tx = gx + (khz / 16.0) * plot_w
            parts.append(f'<text x="{tx:.1f}" y="{gy + plot_h + 16}" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="11px" fill="#53647c">{khz} kHz</text>')
        parts.append(f'<text x="{ox + 20}" y="{oy + ph - 16}" font-family="Arial,Helvetica,sans-serif" font-size="12px" font-weight="700" fill="{color}">{html.escape(note)}</text>')

    parts.append(
        f'<text x="32" y="402" font-family="Arial,Helvetica,sans-serif" font-size="12px" fill="#53647c">'
        f'Normalized periodogram (0.1–16 kHz, bin-max pooled). Reference subtraction lifts the 8 kHz ASK carrier '
        f'from {metrics["target_8khz_band_energy_ratio"]*100:.2f}% to {metrics["residual_8khz_band_energy_ratio"]*100:.2f}% of signal energy.'
        f'</text>'
    )
    parts.append("</svg>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main() -> int:
    blue3 = inspect_blue3()
    sleepy, freqs, psd_t, psd_r = inspect_sleepy_alarm()
    render_spectrum_svg(freqs, psd_t, psd_r, sleepy, DEFAULT_SVG)

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "post_hoc_note": "Reproducible post-hoc signal inspection of the pinned challenge artifacts; not a contemporaneous pre-solve log.",
        "blue3": blue3,
        "sleepy_alarm": sleepy,
        "figure": DEFAULT_SVG.relative_to(ROOT).as_posix(),
    }
    DEFAULT_JSON.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        f"Blue 3: base={tuple(blue3['modal_rgb'])} "
        f"non_base={blue3['non_base_pixel_count']}/{blue3['total_pixels']} "
        f"max_|x-y|={blue3['max_abs_x_minus_y_px']}px"
    )
    print(
        f"Sleepy Alarm: target_8khz_ratio={sleepy['target_8khz_band_energy_ratio']:.6f} "
        f"residual_peak={sleepy['residual_peak_hz']:.2f}Hz "
        f"residual_8khz_ratio={sleepy['residual_8khz_band_energy_ratio']:.4f}"
    )
    print(f"Wrote {DEFAULT_JSON.relative_to(ROOT)} and {DEFAULT_SVG.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
