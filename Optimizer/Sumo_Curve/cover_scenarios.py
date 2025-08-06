from __future__ import annotations

"""trading.risk

High-level risk utilities including the `R_survival` function that the live
engine will query every time it receives fresh market data.

The code is a cleaned-up, script-ready extraction of the logic you developed
in the Jupyter notebook.
"""
from typing import Dict, List, Tuple, Union
import logging
import numpy as np
import sys
import os
import pandas as pd
import time
import csv
import math

# Add the workspace root to Python path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, workspace_root)

from config import TRADE_STATE_EVENTS_CSV, NET_POSITION_STREAMING_CSV, TECHNICAL_DICT_CSV

from Optimizer.risk_utils import (
    zn_to_decimal,
    decimal_to_zn,  # noqa: F401 – exposed for convenience
    levels_crossed,
    TECH_LEVELS_DEC,
)

from .breakeven_curve import breakeven
from .risk_update import R_survival

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Basic helpers (kept identical to the NB for traceability)
# ---------------------------------------------------------------------------

def get_last_trade_state_event(file_path: str) -> dict:
    """Get the last row of the trade state events CSV as a dictionary."""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Get the last row
        last_row = df.iloc[-1]
        
        # Convert the last row to a dictionary
        trade_dict = last_row.to_dict()
        
        return trade_dict
    except Exception as e:
        print(f"Error reading trade state events: {e}")
        return {}


def get_technical_dict(file_path: str) -> dict:
    """Get the last row of the technical dict CSV as a dictionary."""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Get the last row
        last_row = df.iloc[-1]
        
        # Convert the last row to a dictionary
        technical_dict = last_row.to_dict()
        
        return technical_dict
    except Exception as e:
        print(f"Error reading technical dict: {e}")
        return {}


def get_last_net_position(file_path: str) -> dict:
    """Get the last row of the net position streaming CSV as a dictionary."""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Get the last row
        last_row = df.iloc[-1]
        
        # Convert the last row to a dictionary
        net_position_dict = last_row.to_dict()
        
        return net_position_dict
    except Exception as e:
        print(f"Error reading net position streaming: {e}")
        return {}


def get_current_price(file_path: str) -> float:
    """Get the current price from the price streaming CSV."""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Get the last row
        last_row = df.iloc[-1]
        
        # Convert the last row to a dictionary
        last_row_dict = last_row.to_dict()
        
        current_price = 0.5*(last_row_dict["Bid Price"] + last_row_dict["Ask Price"])
        
        return current_price
    except Exception as e:
        print(f"Error reading price streaming: {e}")
        return 0



def risk():
    """Calculate the risk for the current price."""
    trade_dict = get_last_trade_state_event(TRADE_STATE_EVENTS_CSV)
    technical_dict = get_technical_dict(TECHNICAL_DICT_CSV)
    net_position_dict = get_last_net_position(NET_POSITION_STREAMING_CSV)
    current_price = get_current_price("Z:/Archive/ZN_future_price_2025-07-20_2025-07-21.csv")
    SL = -5000
    net_position = net_position_dict["NetPosition"]
    starting_price = trade_dict["Price"]
    #delta_risk_dict, risk_dict, pnl_dict, be_dict, extreme_level_above, ticks_to_extreme_above = R_survival(breakeven, current_price, net_position_dict["NetPosition"]*1000, technical_dict, starting_price, tech_levels_dec=TECH_LEVELS_DEC, stop_loss = SL, NBM=25, pnl_0=-46.8)
    delta_risk_dict, risk_dict, pnl_dict, be_dict, extreme_level_above, ticks_to_extreme_above = R_survival(breakeven, current_price, -1000, technical_dict, starting_price, tech_levels_dec=TECH_LEVELS_DEC, stop_loss = SL, NBM=25, pnl_0=-15.5)

    combined_dict = {decimal_to_zn(key): (delta_risk_dict[key]/1000, risk_dict[key]/1000, risk_dict[key]/16, pnl_dict[key], be_dict[key]) for key in sorted(risk_dict.keys(), reverse=True)}

    return combined_dict

if __name__ == "__main__":
    # Run the streaming monitor
    print("Hi")