"""Explainable first-pass steganalysis features for the project artifacts.

These fixed heuristics are challenge-oriented triage only. They are not a
calibrated or general-purpose steganography detector.
"""

from __future__ import annotations

from os import PathLike
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image
from scipy.signal import periodogram


def image_features(path: str | PathLike[str]) -> dict[str, int | float]:
    """Measure dominant-colour and channel-variation features for an image."""
    with Image.open(path) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)

    flat = rgb.reshape(-1, 3)
    _, counts = np.unique(flat, axis=0, return_counts=True)
    channel_std = np.std(rgb.astype(np.float64), axis=(0, 1))
    return {
        "width": int(rgb.shape[1]),
        "height": int(rgb.shape[0]),
        "modal_rgb_fraction": float(counts.max() / flat.shape[0]),
        "mean_channel_std": float(channel_std.mean()),
        "unique_rgb_count": int(len(counts)),
    }


def audio_features(
    path: str | PathLike[str],
    carrier_hz: float = 8000.0,
    baud: float = 50.0,
) -> dict[str, int | float]:
    """Measure carrier-band energy and symbol-sized RMS variation."""
    audio, sample_rate = sf.read(path, always_2d=True, dtype="float64")
    if audio.size == 0 or not np.isfinite(audio).all():
        raise ValueError("audio must contain finite samples")
    if baud <= 0:
        raise ValueError("baud must be positive")
    if not 0 < carrier_hz < sample_rate / 2:
        raise ValueError("carrier must be below Nyquist")

    signal = audio[:, 0]
    frequencies, power = periodogram(signal, fs=sample_rate, scaling="spectrum")
    total_band = (frequencies >= 100) & (frequencies < sample_rate / 2)
    carrier_band = (frequencies >= carrier_hz - 100) & (frequencies <= carrier_hz + 100)
    total_power = float(power[total_band].sum())
    carrier_ratio = float(power[carrier_band].sum() / max(total_power, 1e-30))

    samples_per_symbol = max(1, int(round(sample_rate / baud)))
    usable_count = len(signal) // samples_per_symbol * samples_per_symbol
    usable = signal[:usable_count]
    if usable.size:
        blocks = usable.reshape(-1, samples_per_symbol)
        levels = np.sqrt(np.mean(blocks * blocks, axis=1))
        level_cv = float(np.std(levels) / max(float(np.mean(levels)), 1e-12))
    else:
        level_cv = 0.0

    return {
        "sample_rate_hz": int(sample_rate),
        "channels": int(audio.shape[1]),
        "duration_seconds": float(len(audio) / sample_rate),
        "carrier_band_energy_ratio": carrier_ratio,
        "symbol_block_rms_cv": level_cv,
    }


def classify_image(features: dict) -> tuple[bool, list[str]]:
    """Apply the fixed image baseline thresholds and return their reasons."""
    reasons = []
    if features["modal_rgb_fraction"] >= 0.90:
        reasons.append("dominant_rgb_colour_fraction>=0.90")
    if features["mean_channel_std"] <= 8.0:
        reasons.append("low_mean_channel_std<=8")
    return len(reasons) == 2, reasons


def classify_audio(features: dict) -> tuple[bool, list[str]]:
    """Apply the fixed audio baseline thresholds and return their reasons."""
    reasons = []
    if features["carrier_band_energy_ratio"] >= 0.02:
        reasons.append("8khz_band_energy_ratio>=0.02")
    if features["symbol_block_rms_cv"] >= 0.15:
        reasons.append("50_baud_block_rms_cv>=0.15")
    return len(reasons) == 2, reasons


def analyze(path: str | PathLike[str], kind: str) -> dict:
    """Analyze one image or audio file with the corresponding baseline."""
    if kind == "image":
        features = image_features(path)
        flagged, reasons = classify_image(features)
    elif kind == "audio":
        features = audio_features(path)
        flagged, reasons = classify_audio(features)
    else:
        raise ValueError("kind must be 'image' or 'audio'")

    return {
        "file": str(Path(path)),
        "kind": kind,
        "flagged": flagged,
        "reasons": reasons,
        "features": features,
        "warning": "Heuristic triage only; not a calibrated or universal detector.",
    }
