"""Shared data access for the Streamlit pages.

Decoder results are returned unchanged. Display-only audio sampling is kept
separate so plot size never changes the input passed to the decoder.
"""

from __future__ import annotations

from math import ceil
from pathlib import Path
import sys
from typing import Any, Callable

import numpy as np
import soundfile as sf
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from audio_alignment import align_audio, alignment_diagnostics  # noqa: E402
from stegano.audio import decode_sleepy_alarm  # noqa: E402
from stegano.image import decode_blue3  # noqa: E402

BLUE3_PATH = ROOT / "data" / "blue3" / "blue.png"
SLEEPY_TARGET_PATH = ROOT / "data" / "sleepy_alarm" / "morning_n_breakfast.mp3"
SLEEPY_REFERENCE_PATH = ROOT / "data" / "sleepy_alarm" / "morning_n_breakfast_original.mp3"


def _execute(decoder: Callable[..., dict[str, Any]], *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Run a decoder and preserve its result, including format-invalid output."""
    try:
        result = decoder(*args, **kwargs)
    except Exception as exc:
        return {
            "status": "Failed",
            "result": None,
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "status": "Success" if result.get("format_valid") is True else "Failed",
        "result": result,
        "error": None,
    }


def run_blue3(path: str | Path = BLUE3_PATH) -> dict[str, Any]:
    """Call the existing Blue 3 decoder without altering its returned data."""
    return _execute(decode_blue3, path)


def run_sleepy_alarm(
    target_path: str | Path = SLEEPY_TARGET_PATH,
    reference_path: str | Path | None = None,
) -> dict[str, Any]:
    """Call the existing audio decoder in the selected reference mode."""
    return _execute(decode_sleepy_alarm, target_path, reference_path)


def image_summary(path: str | Path) -> tuple[np.ndarray, tuple[int, int, int], int]:
    """Load the displayed RGB pixels and compute the decoder's RGB baseline."""
    with Image.open(path) as image:
        pixels = np.asarray(image.convert("RGB"), dtype=np.uint8)

    # Match image.py: RGB tuples are uniquely sorted, then the first maximum
    # count is selected. This is only a display statistic; decoding still uses
    # decode_blue3() above.
    colors, counts = np.unique(pixels.reshape(-1, 3), axis=0, return_counts=True)
    index = int(np.argmax(counts))
    baseline = tuple(int(channel) for channel in colors[index])
    return pixels, baseline, int(counts[index])


def audio_metadata(path: str | Path) -> dict[str, int | float]:
    """Return file metadata without loading the full audio signal."""
    info = sf.info(path)
    return {
        "sample_rate": int(info.samplerate),
        "channels": int(info.channels),
        "frames": int(info.frames),
        "samples_per_channel": int(info.frames),
        "total_samples": int(info.frames * info.channels),
        "duration_seconds": float(info.duration),
    }


def read_waveform(path: str | Path, max_points: int = 12_000) -> tuple[np.ndarray, np.ndarray]:
    """Read a bounded waveform for display, sampling the original audio stream.

    The decoder receives its original full-resolution file separately. Audio is
    read in bounded blocks here so a long recording does not become one huge
    Plotly payload.
    """
    if max_points < 1:
        raise ValueError("max_points must be at least 1")

    indices: list[np.ndarray] = []
    samples: list[np.ndarray] = []
    with sf.SoundFile(path) as audio:
        frame_count = len(audio)
        sample_rate = int(audio.samplerate)
        channels = int(audio.channels)
        if frame_count == 0:
            return np.empty(0, dtype=np.float64), np.empty((0, channels), dtype=np.float32)

        stride = max(1, ceil(frame_count / max_points))
        offset = 0
        for block in audio.blocks(blocksize=65_536, dtype="float32", always_2d=True):
            frame_indices = np.arange(offset, offset + len(block), dtype=np.int64)
            keep = frame_indices % stride == 0
            if np.any(keep):
                indices.append(frame_indices[keep])
                samples.append(block[keep])
            offset += len(block)

    selected_indices = np.concatenate(indices) if indices else np.empty(0, dtype=np.int64)
    waveform = np.concatenate(samples, axis=0) if samples else np.empty((0, channels), dtype=np.float32)
    return selected_indices / sample_rate, waveform


def align_sleepy_audio(
    target_path: str | Path = SLEEPY_TARGET_PATH,
    reference_path: str | Path = SLEEPY_REFERENCE_PATH,
) -> tuple[np.ndarray, np.ndarray, dict[str, float | int]]:
    """Load both challenge audios and run the committed alignment helper."""
    target, target_sr = sf.read(target_path, always_2d=True, dtype="float64")
    reference, reference_sr = sf.read(reference_path, always_2d=True, dtype="float64")
    return align_audio(target, target_sr, reference, reference_sr)


def sleepy_alignment_diagnostics(
    target_path: str | Path = SLEEPY_TARGET_PATH,
    reference_path: str | Path = SLEEPY_REFERENCE_PATH,
) -> dict[str, Any]:
    """Load challenge audio and return resampling/alignment plot data."""
    target, target_sr = sf.read(target_path, always_2d=True, dtype="float64")
    reference, reference_sr = sf.read(reference_path, always_2d=True, dtype="float64")
    diagnostics = alignment_diagnostics(target, target_sr, reference, reference_sr)
    diagnostics.update(
        {
            "target_sample_rate": int(target_sr),
            "reference_sample_rate": int(reference_sr),
            "target_frames": int(len(target)),
            "reference_frames": int(len(reference)),
        }
    )
    return diagnostics


def bounded_signal(signal: np.ndarray, max_points: int = 12_000) -> tuple[np.ndarray, np.ndarray]:
    """Return sample indices and values bounded for interactive plotting."""
    signal = np.asarray(signal)
    if signal.ndim != 1:
        raise ValueError("signal must be one-dimensional")
    if max_points < 1:
        raise ValueError("max_points must be at least 1")
    stride = max(1, ceil(len(signal) / max_points))
    indices = np.arange(0, len(signal), stride, dtype=np.int64)
    return indices, signal[indices]
