from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from visualization.utils import (  # noqa: E402
    SLEEPY_REFERENCE_PATH,
    SLEEPY_TARGET_PATH,
    audio_metadata,
    bounded_signal,
    read_waveform,
    run_sleepy_alarm,
    run_sleepy_alarm_diagnostics,
    sleepy_alignment_diagnostics,
)
from visualization.plotting import plotly_chart  # noqa: E402

st.title("Sleepy Alarm · Audio extraction")
st.caption("Waveforms are sampled only for display. Both decoder runs receive the original full-resolution audio files.")

with st.spinner("Running reference-assisted and reference-free decoders…"):
    assisted = run_sleepy_alarm_diagnostics(SLEEPY_TARGET_PATH, SLEEPY_REFERENCE_PATH)
    reference_free = run_sleepy_alarm(SLEEPY_TARGET_PATH)


def show_audio_info(label: str, path: Path) -> dict | None:
    st.markdown(f"**{label}**")
    try:
        info = audio_metadata(path)
    except Exception as exc:
        st.error(f"Unavailable: {type(exc).__name__}: {exc}")
        return None
    columns = st.columns(3)
    columns[0].metric("Sample rate", f"{info['sample_rate']:,} Hz")
    columns[1].metric("Channels", str(info["channels"]))
    columns[2].metric("Duration", f"{info['duration_seconds']:.3f} s")
    columns = st.columns(2)
    columns[0].metric("Samples per channel (frames)", f"{info['samples_per_channel']:,}")
    columns[1].metric("Total samples across channels", f"{info['total_samples']:,}")
    return info


st.subheader("Audio files")
target_info = show_audio_info("Target audio · morning_n_breakfast.mp3", SLEEPY_TARGET_PATH)
reference_info = show_audio_info("Reference audio · morning_n_breakfast_original.mp3", SLEEPY_REFERENCE_PATH)

waveforms: list[tuple[str, np.ndarray, np.ndarray]] = []
for label, path, info in (
    ("Target", SLEEPY_TARGET_PATH, target_info),
    ("Reference", SLEEPY_REFERENCE_PATH, reference_info),
):
    if info is None:
        continue
    try:
        seconds, samples = read_waveform(path)
        waveforms.append((label, seconds, samples))
    except Exception as exc:
        st.error(f"Could not read {label.lower()} waveform: {type(exc).__name__}: {exc}")

if waveforms:
    st.subheader("Waveforms")
    st.caption("Each trace is a bounded sample of the source waveform, plotted in seconds and amplitude.")
    fig = make_subplots(
        rows=len(waveforms),
        cols=1,
        shared_xaxes=False,
        vertical_spacing=0.12,
        subplot_titles=[label for label, _, _ in waveforms],
    )
    for row, (label, seconds, samples) in enumerate(waveforms, start=1):
        for channel in range(samples.shape[1]):
            fig.add_trace(
                go.Scattergl(
                    x=seconds,
                    y=samples[:, channel],
                    mode="lines",
                    name=f"{label} · channel {channel + 1}",
                    line={"width": 0.8},
                ),
                row=row,
                col=1,
            )
        fig.update_yaxes(title_text="Amplitude", row=row, col=1)
    fig.update_xaxes(title_text="Time (seconds)", row=len(waveforms), col=1)
    fig.update_layout(
        height=300 * len(waveforms),
        hovermode="x unified",
        margin={"l": 20, "r": 20, "t": 45, "b": 20},
        legend_title="Audio channel",
    )
    plotly_chart(fig)


st.subheader("Resampling and cross-correlation alignment")
st.caption("Input sample rates and frame counts are shown above. Diagnostics use the same resampling and correlation path as src/audio_alignment.py; plot point reduction affects display only.")
try:
    diagnostics = sleepy_alignment_diagnostics()
    alignment_view = diagnostics["metadata"]
    sample_rate = alignment_view["sample_rate"]
    st.markdown("**Resampling the reference**")
    st.caption(
        f"Reference: {diagnostics['reference_sample_rate']:,} Hz → "
        f"{sample_rate:,} Hz target rate; "
        f"{diagnostics['reference_frames']:,} input frames → "
        f"{len(diagnostics['reference_resampled']):,} resampled samples."
    )
    original_indices, original_values = bounded_signal(diagnostics["reference_original"])
    resampled_indices, resampled_values = bounded_signal(diagnostics["reference_resampled"])
    resample_fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=False,
        vertical_spacing=0.12,
        subplot_titles=("Reference before resampling", "Reference at target sample rate"),
    )
    resample_fig.add_trace(
        go.Scattergl(
            x=original_indices / diagnostics["reference_sample_rate"],
            y=original_values,
            mode="lines",
            name="Original reference",
            line={"width": 0.8},
        ),
        row=1,
        col=1,
    )
    resample_fig.add_trace(
        go.Scattergl(
            x=resampled_indices / sample_rate,
            y=resampled_values,
            mode="lines",
            name="Resampled reference",
            line={"width": 0.8},
        ),
        row=2,
        col=1,
    )
    resample_fig.update_yaxes(title_text="Amplitude", row=1, col=1)
    resample_fig.update_yaxes(title_text="Amplitude", row=2, col=1)
    resample_fig.update_xaxes(title_text="Time (seconds)", row=2, col=1)
    resample_fig.update_layout(
        height=520,
        hovermode="x unified",
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
    )
    plotly_chart(resample_fig)

    st.markdown("**Cross-correlation by lag**")
    correlation_indices, correlation_values = bounded_signal(
        diagnostics["correlation_profile"], max_points=12_000
    )
    correlation_lags = diagnostics["correlation_lags"][correlation_indices]
    selected_lag = alignment_view["lag_samples"]
    selected_index = int(np.argmin(np.abs(diagnostics["correlation_lags"] - selected_lag)))
    correlation_fig = go.Figure()
    correlation_fig.add_trace(
        go.Scattergl(
            x=correlation_lags / sample_rate * 1000,
            y=correlation_values,
            mode="lines",
            name="Normalized correlation",
            line={"width": 0.8},
        )
    )
    correlation_fig.add_trace(
        go.Scatter(
            x=[selected_lag / sample_rate * 1000],
            y=[diagnostics["correlation_profile"][selected_index]],
            mode="markers",
            name="Selected lag",
            marker={"size": 10, "color": "#ef553b"},
        )
    )
    correlation_fig.add_vline(
        x=selected_lag / sample_rate * 1000,
        line_dash="dash",
        line_color="#ef553b",
        annotation_text=f"{selected_lag:,} samples",
    )
    correlation_fig.update_layout(
        xaxis_title="Lag (milliseconds)",
        yaxis_title="Normalized cross-correlation",
        height=360,
        hovermode="x unified",
        margin={"l": 20, "r": 20, "t": 45, "b": 20},
    )
    plotly_chart(correlation_fig)

    st.markdown("**Aligned overlap and residual**")
    aligned_target = diagnostics["target_aligned"]
    aligned_reference = diagnostics["reference_aligned"]
    target_indices, target_values = bounded_signal(aligned_target)
    reference_indices, reference_values = bounded_signal(aligned_reference)
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=("Aligned overlap", "Target minus resampled reference"),
    )
    fig.add_trace(
        go.Scattergl(x=target_indices / sample_rate, y=target_values, mode="lines", name="Target", line={"width": 0.8}),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scattergl(x=reference_indices / sample_rate, y=reference_values, mode="lines", name="Resampled reference", line={"width": 0.8}),
        row=1,
        col=1,
    )
    count = min(len(target_indices), len(reference_indices))
    # Both traces are sampled with the same stride because they share overlap length.
    fig.add_trace(
        go.Scattergl(
            x=target_indices[:count] / sample_rate,
            y=target_values[:count] - reference_values[:count],
            mode="lines",
            name="Residual",
            line={"width": 0.8},
        ),
        row=2,
        col=1,
    )
    fig.update_yaxes(title_text="Amplitude", row=1, col=1)
    fig.update_yaxes(title_text="Difference", row=2, col=1)
    fig.update_xaxes(title_text="Time within aligned overlap (seconds)", row=2, col=1)
    fig.update_layout(height=620, hovermode="x unified", margin={"l": 20, "r": 20, "t": 50, "b": 20})
    plotly_chart(fig)
    metrics = st.columns(4)
    metrics[0].metric("Target sample rate", f"{sample_rate:,} Hz")
    metrics[1].metric("Lag", f"{alignment_view['lag_samples']:,} samples")
    metrics[2].metric("Correlation", f"{alignment_view['correlation']:.9f}")
    metrics[3].metric("Aligned overlap", f"{alignment_view['overlap_samples']:,} samples")
except Exception as exc:
    st.error(f"Could not calculate alignment visualization: {type(exc).__name__}: {exc}")


st.subheader("ASK decoder diagnosis")
st.caption("Per-symbol measurements and cluster labels below come from the same channel-0 measurements used by the reference-assisted decoder.")
if assisted["diagnostics"] is None:
    st.error(f"ASK diagnostics unavailable: {assisted['error']}")
else:
    diagnostic = assisted["diagnostics"]
    result = assisted["result"]
    nul_count = sum(group["codepoint"] == 0 for group in diagnostic["groups"] if group["codepoint"] is not None)
    summary_cols = st.columns(4)
    summary_cols[0].metric("Symbols decoded", f"{result['symbol_count']:,}")
    summary_cols[1].metric("Separators", f"{result['separator_count']:,}")
    summary_cols[2].metric("NUL characters", f"{nul_count:,}")
    summary_cols[3].metric("Analysis window", f"{diagnostic['duration_seconds']:.2f} s")

    labels = diagnostic["symbol_labels"]
    values = np.asarray(diagnostic["amplitude_levels"])
    times = np.asarray(diagnostic["symbol_times_seconds"])
    label_info = {" ": ("Separator", "#9ca3af"), "0": ("Bit 0", "#2a9d8f"), "1": ("Bit 1", "#4ea8de")}
    cluster_colors = {"separator": "#9ca3af", "0": "#2a9d8f", "1": "#4ea8de"}
    fig = go.Figure()
    for symbol, (name, color) in label_info.items():
        selected = np.asarray([label == symbol for label in labels])
        fig.add_trace(go.Scattergl(
            x=times[selected],
            y=values[selected],
            mode="markers",
            name=name,
            marker={"size": 7, "color": color},
            customdata=np.flatnonzero(selected),
            hovertemplate="Symbol %{customdata}<br>Time %{x:.3f} s<br>ASK level %{y:.8g}<extra>%{fullData.name}</extra>",
        ))
    for cluster in diagnostic["clusters"]:
        fig.add_hline(
            y=cluster["center"],
            line_dash="dash",
            line_color=cluster_colors[cluster["label"]],
            annotation_text=f"{cluster['label']}: {cluster['center']:.5g}",
            annotation_position="top right",
        )
    fig.update_layout(
        height=430,
        xaxis_title="Time (seconds)",
        yaxis_title="ASK amplitude per symbol",
        legend_title="Cluster",
        margin={"l": 20, "r": 20, "t": 35, "b": 20},
    )
    plotly_chart(fig)
    parameter_cols = st.columns(4)
    parameter_cols[0].metric("Channel", "0")
    parameter_cols[1].metric("Carrier", f"{diagnostic['carrier_hz']:,.0f} Hz")
    parameter_cols[2].metric("Symbol rate", f"{diagnostic['symbol_rate']:g} baud")
    parameter_cols[3].metric("Symbols analyzed", f"{len(values):,}")
    st.caption("Cluster centers are computed by the decoder. Points show the complete decoded 7-second symbol window; no plot-only resampling is applied.")

    st.markdown("**Decoded byte groups**")
    st.dataframe(
        [{
            "byte": group["byte_index"],
            "bits": group["bits"],
            "character": "NUL" if group["codepoint"] == 0 else (group["character"] or "(incomplete)"),
            "code point": group["codepoint"],
            "error": group["error"],
        } for group in diagnostic["groups"]],
        width="stretch",
        hide_index=True,
    )


def show_decoder_mode(title: str, run: dict) -> None:
    with st.container(border=True):
        st.subheader(title)
        if run["status"] == "Success":
            st.success("Success — format_valid = true")
        else:
            st.error("Failed — decoder did not return a format-valid result")
        if run["error"]:
            st.caption(run["error"])
            return

        result = run["result"]
        st.markdown("**Decoded text**")
        st.code(result["decoded_text"] or "(empty)")
        first = st.columns(3)
        first[0].metric("format_valid", str(result["format_valid"]).lower())
        first[1].metric("reference_assisted", str(result["reference_assisted"]).lower())
        first[2].metric("Symbol count", f"{result['symbol_count']:,}")
        second = st.columns(3)
        second[0].metric("Separator count", f"{result['separator_count']:,}")
        second[1].metric("Byte errors", f"{len(result['errors']):,}")
        centers = result["amplitude_centers"]
        second[2].metric("Amplitude centers", str(len(centers)))
        st.code(", ".join(f"{value:.8g}" for value in centers), language=None)

        alignment = result["alignment"]
        st.markdown("**Alignment**")
        if alignment is None:
            st.caption("Not performed in reference-free mode.")
        else:
            align_cols = st.columns(3)
            align_cols[0].metric("Lag", f"{alignment['lag_samples']:,} samples")
            align_cols[1].metric("Correlation", f"{alignment['correlation']:.9f}")
            align_cols[2].metric("Target start", f"{alignment['target_start_sample']:,} samples")

        if result["errors"]:
            with st.expander("Malformed byte groups returned by the decoder"):
                st.dataframe(result["errors"], width="stretch", hide_index=True)
        else:
            st.caption("Byte errors: none")


st.subheader("Decoder results")
assisted_col, free_col = st.columns(2)
with assisted_col:
    show_decoder_mode("Reference-assisted", assisted)
with free_col:
    show_decoder_mode("Reference-free", reference_free)
