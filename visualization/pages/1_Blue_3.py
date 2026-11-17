from pathlib import Path
import sys

import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from visualization.utils import BLUE3_PATH, run_blue3_diagnostics  # noqa: E402
from visualization.plotting import plotly_chart  # noqa: E402

st.title("Blue 3 · Image extraction")
st.caption("Image measurements and candidate extraction use the project's decode_blue3() implementation.")

run = run_blue3_diagnostics(BLUE3_PATH)
if run["status"] == "Success":
    st.success("Success — format_valid = true")
else:
    st.error("Failed — no format-valid candidate was returned")
if run["error"]:
    st.error(run["error"])
    st.stop()

diagnostics = run["diagnostics"]
pixels = diagnostics["pixels"]
baseline = diagnostics["baseline"]
baseline_count = diagnostics["baseline_count"]
result = run["result"]
blocks = diagnostics["blocks"]
if not blocks:
    st.warning("The decoder did not select a valid diagonal candidate, so there are no selected blocks to annotate.")

height, width, _ = pixels.shape
left, right = st.columns([1, 1])
with left:
    st.image(pixels, caption="data/blue3/blue.png", width="stretch")
with right:
    st.metric("Image size", f"{width} × {height} px")
    st.metric("Most common RGB baseline", str(baseline))
    st.caption(f"This color appears in {baseline_count:,} pixels. The baseline uses the same most-frequent RGB calculation as decode_blue3().")

st.subheader("RGB channel distribution")
st.caption("Histogram of pixel values in each channel (0–255); counts are shown per channel.")
fig = go.Figure()
for channel, name, color in ((0, "Red", "#d1495b"), (1, "Green", "#2a9d8f"), (2, "Blue", "#457b9d")):
    fig.add_trace(go.Histogram(x=pixels[:, :, channel].ravel(), name=name, nbinsx=256, opacity=0.58, marker_color=color))
fig.update_layout(
    barmode="overlay",
    xaxis_title="Channel value",
    yaxis_title="Pixel count",
    legend_title="RGB channel",
    margin={"l": 20, "r": 20, "t": 20, "b": 20},
    height=360,
)
plotly_chart(fig)

st.subheader("Blue 3 diagonal extraction trace")
st.caption(
    "Highlighted squares are the same diagonal blocks used by decode_blue3(). Hover a block or inspect its RGB delta and character code below."
    if blocks else "No valid candidate was selected, so the image has no extraction blocks to annotate."
)
overlay = go.Figure(go.Image(z=pixels))
for block in blocks:
    overlay.add_shape(
        type="rect",
        x0=block["x0"], y0=block["y0"], x1=block["x1"], y1=block["y1"],
        line={"color": "#ffcc66", "width": 1},
        fillcolor="rgba(255, 204, 102, 0.10)",
    )
    overlay.add_trace(go.Scatter(
        x=[(block["x0"] + block["x1"]) / 2],
        y=[(block["y0"] + block["y1"]) / 2],
        mode="markers",
        marker={"size": 5, "color": "#ffcc66"},
        customdata=[[block["index"] + 1, block["character"], block["value"], block["rgb_delta"]]],
        hovertemplate="Block %{customdata[0]}<br>Character: %{customdata[1]}<br>Code point / RGB delta sum: %{customdata[2]}<br>Per-channel delta: %{customdata[3]}<extra></extra>",
        showlegend=False,
    ))
overlay.update_layout(
    height=650,
    margin={"l": 10, "r": 10, "t": 10, "b": 10},
    xaxis={"range": [0, width], "visible": False, "constrain": "domain"},
    yaxis={"range": [height, 0], "visible": False, "scaleanchor": "x", "scaleratio": 1},
)
plotly_chart(overlay)
st.markdown("**Selected candidate**")
st.code(result["flag"] or "No valid candidate")
st.caption(f"Baseline RGB: {baseline}; selected diagonal length: {len(blocks)} blocks.")
st.dataframe(
    [{
        "block": block["index"] + 1,
        "character": block["character"],
        "character code": block["value"],
        "RGB delta (R, G, B)": tuple(block["rgb_delta"]),
        "pixel bounds": f"x {block['x0']}–{block['x1']}, y {block['y0']}–{block['y1']}",
    } for block in blocks],
    width="stretch",
    hide_index=True,
)

st.subheader("Decoder candidates")
if result is not None:
    st.metric("format_valid", str(result["format_valid"]).lower())
    st.markdown("**Final candidate**")
    st.code(result["flag"] if result["flag"] is not None else "No valid candidate")
    st.caption("Candidate list returned directly by decode_blue3().")
    st.dataframe(result["attempts"], width="stretch", hide_index=True)
else:
    st.info("Candidate list is unavailable because the decoder could not complete.")
