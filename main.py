import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import time

# --- Configuration ---
DB_FILE = 'scan_data.db'
# ---------------------

st.set_page_config(layout="wide", page_title="ESP32 Scanner Dashboard")

st.title("ESP32 Servo Scanner Dashboard 🛰")

def load_data():
    """Loads all scan data from the SQLite database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        # Order by timestamp DESC to get the newest data first
        df = pd.read_sql_query("SELECT * FROM scans ORDER BY timestamp DESC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return pd.DataFrame(columns=["timestamp", "angle", "distance_m"])

# Load the data
all_data = load_data()

if all_data.empty:
    st.warning("No data found in database. Is data_logger.py running and connected?")
    st.stop()

# --- Display Data ---

st.header("Scan Visualization")

# Get the 4 most recent points for the "latest scan" plot
# (since your C++ loop has 4 steps)
latest_scan_data = all_data.head(4).copy()

# We need to filter out failed readings (-1) for the plot
plot_data = latest_scan_data[latest_scan_data['distance_m'] >= 0]

if not plot_data.empty:
    # A polar chart is perfect for this!
    # 'theta' is the angle, 'r' is the distance
    fig = px.line_polar(
        plot_data,
        r='distance_m',
        theta='angle',
        line_close=False,  # Don't connect the last point to the first
        markers=True,      # Show a dot for each measurement
        title="Latest Scan Cycle (4 points)",
        template="plotly_dark"
    )
    # Add a fill to make it look more like a radar sweep
    fig.update_traces(fill='toself')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Waiting for valid scan data (distance >= 0) to plot...")


# --- Raw Data Table ---
st.header("All Historical Data")
st.dataframe(all_data, use_container_width=True)


# --- Auto-Refresh ---
st.write("Page auto-refreshes every 5 seconds.")
time.sleep(5)
st.rerun()