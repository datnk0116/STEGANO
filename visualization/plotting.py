"""Compatibility wrappers for the Streamlit versions used by the project."""

from inspect import signature

import streamlit as st


def plotly_chart(figure) -> None:
    """Render a full-width Plotly chart across old and new Streamlit APIs."""
    parameters = signature(st.plotly_chart).parameters
    if "width" in parameters:
        st.plotly_chart(figure, width="stretch")
    else:
        st.plotly_chart(figure, use_container_width=True)
