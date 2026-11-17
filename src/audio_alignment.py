"""Resample and align two audio signals using normalized cross-correlation."""

from fractions import Fraction

import numpy as np
from scipy.signal import correlate, correlation_lags, resample_poly


def _mono(signal):
    signal = np.asarray(signal, dtype=np.float64)
    if signal.ndim == 2:
        signal = signal.mean(axis=1)
    if signal.ndim != 1 or signal.size == 0:
        raise ValueError("audio signals must be non-empty one- or two-dimensional arrays")
    if not np.all(np.isfinite(signal)):
        raise ValueError("audio signals must contain only finite samples")
    return signal


def _prepare_audio(target, target_sr, reference, reference_sr):
    if not isinstance(target_sr, (int, np.integer)) or target_sr <= 0:
        raise ValueError("target_sr must be a positive integer")
    if not isinstance(reference_sr, (int, np.integer)) or reference_sr <= 0:
        raise ValueError("reference_sr must be a positive integer")

    target = _mono(target)
    reference = _mono(reference)
    original_reference = reference
    if reference_sr != target_sr:
        ratio = Fraction(int(target_sr), int(reference_sr)).limit_denominator(100000)
        reference = resample_poly(reference, ratio.numerator, ratio.denominator)
    if target.size < 2 or reference.size < 2:
        raise ValueError("audio signals must contain at least two samples")
    return target, original_reference, reference


def _align_prepared(target, reference, sample_rate):
    t = target - target.mean()
    r = reference - reference.mean()
    corr = correlate(t, r, mode="full", method="fft")
    lags = correlation_lags(t.size, r.size, mode="full")
    lag = int(lags[np.argmax(np.abs(corr))])
    denominator = np.linalg.norm(t) * np.linalg.norm(r)
    profile = corr / denominator if denominator else np.zeros_like(corr)

    target_start = max(lag, 0)
    reference_start = max(-lag, 0)
    length = min(target.size - target_start, reference.size - reference_start)
    if length <= 0:
        raise ValueError("signals have no overlap at the detected alignment")
    target_aligned = target[target_start:target_start + length]
    reference_aligned = reference[reference_start:reference_start + length]
    x = target_aligned - target_aligned.mean()
    y = reference_aligned - reference_aligned.mean()
    denominator = np.linalg.norm(x) * np.linalg.norm(y)
    score = abs(float(np.dot(x, y) / denominator)) if denominator else 0.0

    metadata = {
        "lag_samples": lag,
        "sample_rate": int(sample_rate),
        "target_start_sample": target_start,
        "reference_start_sample": reference_start,
        "overlap_samples": int(length),
        "correlation": score,
    }
    return target_aligned, reference_aligned, metadata, lags, profile


def align_audio(target, target_sr, reference, reference_sr):
    """Resample *reference* to target_sr and align it to *target*.

    Returns ``(target_overlap, reference_overlap, metadata)``. A positive
    ``lag_samples`` means the target begins after the reference.
    """
    target, _, reference = _prepare_audio(target, target_sr, reference, reference_sr)
    target_aligned, reference_aligned, metadata, _, _ = _align_prepared(
        target, reference, target_sr
    )
    return target_aligned, reference_aligned, metadata


def alignment_diagnostics(target, target_sr, reference, reference_sr):
    """Return alignment signals and the full correlation profile for plotting.

    The profile is normalized by the full demeaned signal norms. ``align_audio``
    uses the same profile to choose its lag, so the selected lag is its absolute
    maximum. Arrays use the target sample rate after resampling.
    """
    target, original_reference, reference = _prepare_audio(
        target, target_sr, reference, reference_sr
    )
    target_aligned, reference_aligned, metadata, lags, profile = _align_prepared(
        target, reference, target_sr
    )
    return {
        "target": target,
        "reference_original": original_reference,
        "reference_resampled": reference,
        "target_aligned": target_aligned,
        "reference_aligned": reference_aligned,
        "metadata": metadata,
        "correlation_lags": lags,
        "correlation_profile": profile,
    }
