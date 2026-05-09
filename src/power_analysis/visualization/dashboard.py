"""Streamlit dashboard for interactive match power analysis.

Launch with:
    streamlit run src/power_analysis/visualization/dashboard.py
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from power_analysis import config

# ---------------------------------------------------------------------------
# Page config — must be the first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="FRC 4065 Power Analysis",
    page_icon="⚡",
    layout="wide",
)


def main() -> None:
    st.title("FRC Team 4065 — Match Power Analysis")

    # -----------------------------------------------------------------------
    # Sidebar: file selection
    # -----------------------------------------------------------------------
    st.sidebar.header("Load Telemetry")

    # TODO: Use st.sidebar.file_uploader to accept a CSV file OR
    #       let the user pick from a dropdown of files in config.SAMPLE_DIR
    # TODO: Parse the uploaded/selected file with TelemetryParser

    # -----------------------------------------------------------------------
    # Main area: metrics and plots
    # -----------------------------------------------------------------------
    st.subheader("Match Summary")

    col1, col2, col3, col4 = st.columns(4)
    # TODO: Display peak_power, average_power, energy (Wh), and brownout_count
    #       using st.metric() in each column

    st.subheader("Voltage Over Time")
    # TODO: Call plots.plot_voltage(df) and display with st.pyplot()

    st.subheader("Current Draw Over Time")
    # TODO: Call plots.plot_current(df) and display with st.pyplot()

    st.subheader("Instantaneous Power")
    # TODO: Call plots.plot_power(df, power) and display with st.pyplot()

    st.subheader("Per-Channel Current Breakdown")
    # TODO: Call plots.plot_channel_breakdown(df) and display with st.pyplot()


if __name__ == "__main__":
    main()
