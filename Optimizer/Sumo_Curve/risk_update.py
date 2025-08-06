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

from Optimizer.risk_utils import (
    zn_to_decimal,
    decimal_to_zn,  # noqa: F401 – exposed for convenience
    levels_crossed,
    TECH_LEVELS_DEC,
)
from config import TRADE_STATE_EVENTS_CSV, NET_POSITION_STREAMING_CSV, TECHNICAL_DICT_CSV, LIVE_PRICE_PATH

from Optimizer.Sumo_Curve.breakeven_curve import breakeven

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Basic helpers (kept identical to the NB for traceability)
# ---------------------------------------------------------------------------


def R_survival(breakeven_curve, current_price: Union[str, float],
    R0: float,
    technical_dict: dict,
    starting_price: float,
    *,
    tech_levels_dec: np.ndarray | List[float] = TECH_LEVELS_DEC,
    stop_loss: float = -10_0000.0,
    NBM: float = 25.0,
    pnl_0: float = 0.0,
) -> Tuple[Dict[float, float], float, float]:

    """
    breakeven_curve: function,
    current_price: spot_price,
    R0: current_risk,
    technical_dict: current_technical_dict,
    starting_price: starting_price for the breakeven_curve,
    tech_levels_dec: technical_levels,
    stop_loss: stop_loss,
    """
    # ------------------------------------------------------------------
    # Convert price to decimal early; keep the string for debug/logging only.
    # ------------------------------------------------------------------

    cp_dec = zn_to_decimal(current_price) if isinstance(current_price, str) else current_price

    # Update the technical_dict with the starting price if the trade has started already
    if R0 > 0:
        technical_dict["Size Up Long Price"] = starting_price

        if current_price > starting_price:
            lvls_below = levels_crossed(starting_price+0.001, tech_levels_dec[0],  tech_levels_dec)
        else:
            lvls_below = levels_crossed(cp_dec+0.001, tech_levels_dec[0],  tech_levels_dec)

        if not lvls_below or lvls_below[0] != cp_dec:
            lvls_below.insert(0, cp_dec)

        d_below = np.diff(lvls_below)
        d_below = d_below.tolist()

    elif R0 < 0:
        technical_dict["Size Up Short Price"] = starting_price

        if current_price < starting_price:
            lvls_above = levels_crossed(starting_price-0.001, tech_levels_dec[-1], tech_levels_dec)
        else:
            lvls_above = levels_crossed(cp_dec-0.001, tech_levels_dec[-1], tech_levels_dec)

        # Make sure *current price* is present at index 0 in both lists
        if not lvls_above or lvls_above[0] != cp_dec:
            lvls_above.insert(0, cp_dec)

        d_above = np.diff(lvls_above)
        d_above = d_above.tolist()

    else:
        print("No trade started yet")
        return None

    tech_levels_dec = sorted(tech_levels_dec)

    trade_pnl = pnl_0

    if R0 > 0:
        Risk_curve = {}
        PnL_curve = {}
        BE_curve = {}
        delta_risk = {}
        i=0
        R_current = R0
        Risk_curve[lvls_below[0]] = R0
        delta_risk[lvls_below[0]] = 0
        PnL_curve[lvls_below[0]] = trade_pnl
        BE_curve[lvls_below[0]] = 16*trade_pnl/R0
        while True:
            trade_pnl += R_current*d_below[i]
            if trade_pnl <= stop_loss:
                break
            R_prev = R_current
            R_current = max(trade_pnl/(breakeven_curve(lvls_below[i+1], technical_dict) / 16), R_current)
            R_current = math.ceil(R_current/1000)*1000  # This assumes that Risk is quantized and is in decimal format. So 1 lot is 1000 in decimal and 62.5 in 16th of a point.
            Risk_curve[lvls_below[i+1]] = R_current
            delta_risk[lvls_below[i+1]] = R_current - R_prev
            PnL_curve[lvls_below[i+1]] = trade_pnl
            BE_curve[lvls_below[i+1]] = 16*trade_pnl/R_current
            i+=1
        extreme_level_below = lvls_below[i]
        ticks_to_extreme = abs(extreme_level_below - cp_dec) * 16

        return delta_risk, Risk_curve, PnL_curve, BE_curve, extreme_level_below, ticks_to_extreme

    elif R0 < 0:
        Risk_curve = {}
        PnL_curve = {}
        BE_curve = {}
        delta_risk = {}
        i=0
        R_current = R0
        Risk_curve[lvls_above[0]] = R0
        delta_risk[lvls_above[0]] = 0
        PnL_curve[lvls_above[0]] = trade_pnl
        BE_curve[lvls_above[0]] = 16*trade_pnl/R0
        while True:
            trade_pnl += R_current*d_above[i]
            if trade_pnl <= stop_loss:
                break
            R_prev = R_current
            print("lvls_above[i+1]: ", lvls_above[i+1])
            R_current = min(trade_pnl/(breakeven_curve(lvls_above[i+1], technical_dict) / 16), R_current)
            print("breakeven_curve(lvls_above[i+1], technical_dict): ", breakeven_curve(lvls_above[i+1], technical_dict))
            R_current = math.floor(R_current/1000)*1000  # This assumes that Risk is in decimal format. So 1 lot is 1000 in decimal and 62.5 in 16th of a point.
            Risk_curve[lvls_above[i+1]] = R_current
            delta_risk[lvls_above[i+1]] = R_current - R_prev
            PnL_curve[lvls_above[i+1]] = trade_pnl
            BE_curve[lvls_above[i+1]] = 16*trade_pnl/R_current
            i+=1
        extreme_level_above = lvls_above[i]
        ticks_to_extreme = abs(extreme_level_above - cp_dec) * 16

        return delta_risk, Risk_curve, PnL_curve, BE_curve, extreme_level_above, ticks_to_extreme
    
    else:
        print("Error:Initial Risk is 0. No trade started yet")
        return None, None, None, None, None
    

def get_last_trade_state_event(file_path: str) -> dict:
    """Get the last row of the trade state events CSV as a dictionary."""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path).tail(1)
        
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
        df = pd.read_csv(file_path).tail(1)
        
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
        df = pd.read_csv(file_path).tail(1)
        
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
        df = pd.read_csv(file_path).tail(1)
        
        # Get the last row
        last_row = df.iloc[-1]
        
        # Convert the last row to a dictionary
        last_row_dict = last_row.to_dict()
        
        current_price = last_row_dict["price"]

        if isinstance(current_price, str):
            current_price = float(current_price)
        
        return current_price
    except Exception as e:
        print(f"Error reading price streaming: {e}")
        return 0


if __name__ == "__main__":
    """
    breakeven_curve, 
    current_price: Union[str, float],
    R0: float,
    technical_dict: dict,
    starting_price: float,
    """

    trade_dict = get_last_trade_state_event(TRADE_STATE_EVENTS_CSV)
    technical_dict = get_technical_dict(TECHNICAL_DICT_CSV)
    net_position_dict = get_last_net_position(NET_POSITION_STREAMING_CSV)
    live_prices_path = LIVE_PRICE_PATH
    current_price = get_current_price(live_prices_path)
    print("current_price: ", current_price)
    starting_price = trade_dict["Price"]
    print("starting_price: ", starting_price)
    SL = -5000
    delta_risk_dict, risk_dict, pnl_dict, be_dict, extreme_level_above, ticks_to_extreme_above = R_survival(breakeven, current_price, net_position_dict["NetPosition"]*1000, technical_dict, starting_price, tech_levels_dec=TECH_LEVELS_DEC, stop_loss = SL, NBM=19.5, pnl_0=0)