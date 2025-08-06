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

# Add the workspace root to Python path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, workspace_root)

from Optimizer.risk_utils import (
    zn_to_decimal,
    decimal_to_zn, 
    levels_crossed,
    TECH_LEVELS_DEC,
)
from config import TECHNICAL_DICT_CSV

from Optimizer.Sumo_Curve.breakeven_curve import breakeven

logger = logging.getLogger(__name__)

def R_dict(breakeven_curve, current_price, technical_dict, tech_levels_dec=TECH_LEVELS_DEC, stop_loss = -100_000, NBM=25, pnl_0=0):
    """
    This function calculates the risk dictionary i.e. the risk for each NBM level above and below the current price.
    """

    # Convert the current price to a decimal if it is a string.
    if isinstance(current_price, str):
        current_price_dec = zn_to_decimal(current_price)
    else:
        current_price_dec = current_price
    
    # If the size up long price is not in the technical dict, we use the current price.
    if not pd.isna(technical_dict["Size Up Long Price"]):
        size_up_long_price = technical_dict["Size Up Long Price"] if isinstance(technical_dict["Size Up Long Price"], float) else zn_to_decimal(technical_dict["Size Up Long Price"])
    else:
        size_up_long_price = current_price_dec
        technical_dict["Size Up Long Price"] = size_up_long_price

    # If the size up short price is not in the technical dict, we use the current price.
    if not pd.isna(technical_dict["Size Up Short Price"]):
        size_up_short_price = technical_dict["Size Up Short Price"] if isinstance(technical_dict["Size Up Short Price"], float) else zn_to_decimal(technical_dict["Size Up Short Price"])
    else:
        size_up_short_price = current_price_dec
        technical_dict["Size Up Short Price"] = size_up_short_price
    
    # Calculate the NBM levels above and below the current price.
    NBM_levels_above_dec = levels_crossed(size_up_short_price-0.01, current_price_dec + NBM/16, tech_levels_dec)  # 0.01 is a small buffer to include the size_up_short_price price in the levels_above.
    NBM_levels_below_dec = levels_crossed(size_up_long_price+0.01, current_price_dec - NBM/16, tech_levels_dec)  # 0.01 is a small buffer to include the size_up_long_price price in the levels_below.

    levels_above = NBM_levels_above_dec
    levels_below = NBM_levels_below_dec
    #print("levels_above: ", levels_above)
    #print("levels_below: ", levels_below)

    # Calculate the deltaL for the levels_above and levels_below.
    deltaL_above = np.array(levels_above[1:]) - np.array(levels_above[:-1])
    deltaL_below = np.array(levels_below[1:]) - np.array(levels_below[:-1])
    deltaL_above = deltaL_above.tolist()
    deltaL_below = deltaL_below.tolist()

    # Calculate the product coefficient for the levels_above and levels_below.
    # coeff_above looks like the following: deltaL_above[0] * (1 + (deltaL_above[1] / breakeven(levels_above[0])) ) * (1 + (deltaL_above[2] / breakeven(levels_above[1])) ) * ...

    R_dict_result = {}

    r_below = [1.0]
    pnl_below = [0]
    for i in range(1, len(levels_below)):
        pnl_below.append(pnl_below[i-1] + deltaL_below[i-1] * r_below[i-1])
        r_below.append(pnl_below[i]/(breakeven_curve(levels_below[i], technical_dict)/16)) 
        r_below[i] = max(r_below[i], r_below[i-1])
    #print("r_below: ", r_below)

    R0_below = stop_loss/(r_below[-1]*(-3/16) + pnl_below[-1])
    for i in range(len(levels_below)):
        R_dict_result[levels_below[i]] = R0_below * r_below[i]
    
    r_above = [-1.0]
    pnl_above = [0]
    for i in range(1, len(levels_above)):
        pnl_above.append(pnl_above[i-1] + deltaL_above[i-1] * r_above[i-1])
        r_above.append(pnl_above[i]/(breakeven_curve(levels_above[i], technical_dict)/16))
        r_above[i] = min(r_above[i], r_above[i-1])
    #print("r_above: ", r_above)

    R0_above = -stop_loss/(r_above[-1]*(3/16) + pnl_above[-1]) # Stoploss is at least 3/16 ticks away from the last level.
    for i in range(len(levels_above)):
        R_dict_result[levels_above[i]] = R0_above * r_above[i]

    return R_dict_result, R0_above, R0_below, levels_above[0], levels_below[0]

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

if __name__ == "__main__":
    # R_dict2(breakeven_curve, current_price, technical_dict, tech_levels_dec=TECH_LEVELS_DEC, stop_loss = -100_000, NBM=25, pnl_0=0):
    TECH_DICT = get_technical_dict(TECHNICAL_DICT_CSV)
    print(R_dict(breakeven, "110'28", TECH_DICT, stop_loss = -500000, NBM=25, pnl_0=0))
