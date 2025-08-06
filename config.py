# config.py
import os

# Base directories
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
DATA_DIR = os.path.join(WORKSPACE_ROOT, "data")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")
LADDER_DIR = os.path.join(OUTPUT_DIR, "ladder")

# Input files
CONTINUOUS_FILLS_CSV = os.path.join(LADDER_DIR, "continuous_fills.csv")
LIVE_ZN_PRICES_CSV = os.path.join(WORKSPACE_ROOT, "NAM_NBM_Final_Code", "Live_ZN_Prices.csv")

# Output files
LIFO_STREAMING_CSV = os.path.join(OUTPUT_DIR, "lifo_streaming.csv")
NET_POSITION_STREAMING_CSV = os.path.join(OUTPUT_DIR, "net_position_streaming.csv")
NET_POSITION_MONITOR_STATE_PKL = os.path.join(OUTPUT_DIR, "net_position_state.pkl")
RISK_STREAMING_PKL = os.path.join(OUTPUT_DIR, "risk_streaming.pkl")
TRADE_STATE_EVENTS_CSV = os.path.join(OUTPUT_DIR, "trade_state_events.csv")
TRADE_STATE_MONITOR_STATE_PKL = os.path.join(OUTPUT_DIR, "trade_state_monitor_state.pkl")
TECHNICAL_DICT_CSV = os.path.join(OUTPUT_DIR, "technical_dict.csv")
LIVE_PRICE_PATH = "Z:/Archive/Live_TT_ZN_Prices.csv"


# HTML files
HTML_SERVE_DIR = "Z:/Yaman"
RISK_VS_PRICE_HTML = os.path.join(HTML_SERVE_DIR, "risk_vs_price.html")
RISK_TABLE_DATA_HTML = os.path.join(HTML_SERVE_DIR, "risk_table_data.html")

# State files
LIFO_STATE_PKL = os.path.join(OUTPUT_DIR, "lifo_streaming_state.pkl")
WATCHDOG_STATE_JSON = os.path.join(OUTPUT_DIR, "watchdog_state.json")

# Script directories
OPTIMIZER_DIR = os.path.join(WORKSPACE_ROOT, "Optimizer")
SUMO_CURVE_DIR = os.path.join(OPTIMIZER_DIR, "Sumo_Curve")
NAM_NBM_DIR = os.path.join(WORKSPACE_ROOT, "NAM_NBM_Final_Code")

