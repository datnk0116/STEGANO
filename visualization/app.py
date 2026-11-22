from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from visualization.utils import (  # noqa: E402
    BLUE3_PATH,
    SLEEPY_REFERENCE_PATH,
    SLEEPY_TARGET_PATH,
    run_blue3,
    run_sleepy_alarm,
)
from scripts.verify_artifacts import verify_artifacts  # noqa: E402


BLUE3_FLAG = "byuctf{more_blue_steganography_da_ba_dee_nkiY9CyP}"
SLEEPY_ALARM_FLAG = "ictf{1_sl33py_NaYuKi_alarm_2a634dc1bb2}"

st.set_page_config(page_title="STEGANO Challenge Visualizations", page_icon="🔎", layout="wide")
st.title("STEGANO Challenge Visualizations")
st.caption("Decoder-backed views for Blue 3 and Sleepy Alarm. Status below comes from decoder runs against the repository's challenge files.")

with st.spinner("Running the challenge decoders…"):
    blue3_run = run_blue3(BLUE3_PATH)
    assisted_run = run_sleepy_alarm(SLEEPY_TARGET_PATH, SLEEPY_REFERENCE_PATH)
    blind_run = run_sleepy_alarm(SLEEPY_TARGET_PATH)

try:
    artifact_report = verify_artifacts()
    artifact_checks = artifact_report["checks"]
except Exception as exc:
    artifact_report = {"passed": 0, "total": 0, "all_passed": False}
    artifact_checks = []
    artifact_error = f"{type(exc).__name__}: {exc}"
else:
    artifact_error = None

blue3_result = blue3_run["result"]
assisted_result = assisted_run["result"]
blue3_output = blue3_result.get("flag") if blue3_result else None
assisted_output = assisted_result.get("decoded_text") if assisted_result else None
blue3_exact = bool(
    blue3_result
    and blue3_result.get("format_valid") is True
    and blue3_output == BLUE3_FLAG
)
assisted_exact = bool(
    assisted_result
    and assisted_result.get("reference_assisted") is True
    and assisted_result.get("format_valid") is True
    and assisted_output == SLEEPY_ALARM_FLAG
)

st.subheader("Artifact integrity and exact-match verification")
if artifact_report["all_passed"]:
    st.success(f"Artifact SHA-256 check passed: {artifact_report['passed']}/{artifact_report['total']}")
else:
    st.error(f"Artifact SHA-256 check failed: {artifact_report['passed']}/{artifact_report['total']}")
if artifact_error:
    st.caption(artifact_error)

gate_cols = st.columns(3)
gate_cols[0].metric("Official artifacts verified", f"{artifact_report['passed']}/{artifact_report['total']}")
gate_cols[1].metric(
    "Blue 3 exact match",
    "PASS" if blue3_exact else "FAIL",
    f"{len(blue3_output) if blue3_output is not None else 0}/50 characters",
)
gate_cols[2].metric(
    "Sleepy Alarm exact match",
    "PASS" if assisted_exact else "FAIL",
    f"{len(assisted_output) if assisted_output is not None else 0}/39 characters · reference-assisted",
)

if assisted_result and assisted_result.get("alignment"):
    lag_samples = assisted_result["alignment"]["lag_samples"]
    st.caption(
        f"Sleepy Alarm alignment lag: {lag_samples:,} samples, measured by cross-correlation at run time. "
        "This is reported as an observed alignment offset, not attributed solely to MP3 encoder delay."
    )

if artifact_report["all_passed"] and blue3_exact and assisted_exact:
    st.success(
        "Artifact integrity, Blue 3 exact match, and Sleepy Alarm reference-assisted exact match passed. "
        "Reference-free output is shown separately."
    )
else:
    st.error("Artifact integrity or a required exact-match check failed; inspect the individual status cards.")

if artifact_checks:
    st.dataframe(
        [{
            "Artifact": check["path"],
            "Status": "PASS" if check["passed"] else "FAIL",
            "Bytes": check["actual_bytes"],
            "SHA-256": check["actual_sha256"] or "missing",
        } for check in artifact_checks],
        width="stretch",
        hide_index=True,
    )


def show_run(title: str, run: dict) -> None:
    with st.container(border=True):
        st.subheader(title)
        if run["status"] == "Success":
            st.success("Success — decoder returned format_valid = true")
        else:
            st.error("Failed — decoder did not return a format-valid result")
        if run["error"]:
            st.caption(run["error"])
        elif run["result"] is not None:
            result = run["result"]
            output = result.get("flag", result.get("decoded_text"))
            if output is not None:
                st.code(output)
            st.caption(f"format_valid: {result.get('format_valid')}")


st.markdown("Two challenge decoders are available from the page navigation: image-domain extraction for **Blue 3** and audio-domain extraction for **Sleepy Alarm**.")
col1, col2, col3 = st.columns(3)
with col1:
    show_run("Blue 3", blue3_run)
with col2:
    show_run("Sleepy Alarm · reference-assisted", assisted_run)
with col3:
    show_run("Sleepy Alarm · reference-free", blind_run)

st.info("Reference-assisted Sleepy Alarm uses the original recording for alignment and subtraction. Reference-free mode omits it; the two outcomes are shown independently.")
