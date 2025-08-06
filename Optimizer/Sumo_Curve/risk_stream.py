import pandas as pd
import sys
import os
from datetime import datetime, timedelta
import time
import math
import pickle
import requests
import argparse
# Add the workspace root to Python path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, workspace_root)
from utils import *
# Add lib directory for TT API imports
sys.path.insert(0, os.path.join(workspace_root, 'lib'))

from Optimizer.risk_utils import (
    zn_to_decimal,
    decimal_to_zn,  # noqa: F401 – exposed for convenience
    levels_crossed,
    TECH_LEVELS_DEC,
)
from config import TRADE_STATE_EVENTS_CSV, NET_POSITION_STREAMING_CSV, TECHNICAL_DICT_CSV, LIVE_PRICE_PATH, RISK_STREAMING_PKL

# Import risk functions
from Optimizer.Sumo_Curve.risk_curve import R_dict
from Optimizer.Sumo_Curve.risk_update import R_survival
from Optimizer.Sumo_Curve.breakeven_curve import breakeven

# TT API imports for live P&L
try:
    from trading.tt_api import (
        TTTokenManager, 
        TT_API_KEY, TT_API_SECRET, TT_SIM_API_KEY, TT_SIM_API_SECRET,
        APP_NAME, COMPANY_NAME, ENVIRONMENT, TOKEN_FILE
    )
    TT_API_AVAILABLE = True
except ImportError as e:
    print(f"TT API not available: {e}")
    TT_API_AVAILABLE = False

"""
First we need to get the last row of the trade state events CSV as a dictionary.
This will tell us if we have an active trade or not.
If we don't have an active trade, we will use the R_dict function to calculate the risk.
If we have an active trade, we will use the R_survival function to calculate the risk.
"""


def risk():
    """Calculate the risk for the current price."""
    trade_dict = get_last_trade_state_event(TRADE_STATE_EVENTS_CSV)
    technical_dict = get_technical_dict(TECHNICAL_DICT_CSV)
    net_position_dict = get_last_net_position(NET_POSITION_STREAMING_CSV)
    
    # Get live P&L from TT API
    #live_pnl = get_live_pnl_from_tt()

    # Get the current price from the Live_ZN_Prices.csv (using relative path)
    #live_prices_path = os.path.join(workspace_root, "NAM_NBM_Final_Code", "Live_ZN_Prices.csv")
    live_prices_path = LIVE_PRICE_PATH
    current_price = get_current_price(live_prices_path)
    #current_price = "111'01"
    #print("current_price: ", current_price)

    SL = -5000

    if trade_dict["TradeState"] == 0: # No Active Trade

        if pd.isna(technical_dict["Size Up Long Price"]):
            technical_dict["Size Up Long Price"] = current_price
        if pd.isna(technical_dict["Size Up Short Price"]):
            technical_dict["Size Up Short Price"] = current_price
            
        risk_data = R_dict(breakeven, current_price, technical_dict, TECH_LEVELS_DEC, stop_loss = SL, NBM=25, pnl_0=0)
        #risk_dict = risk_data[0]
        R0_above = risk_data[1]
        R0_below = risk_data[2]
        level_above_0 = risk_data[3]
        level_below_0 = risk_data[4]
        #print("R0_above: ", R0_above)
        #print("R0_below: ", R0_below)

        """
        # Get the minimum long quantity and the maximum short quantity to see if we need to start with 1 lot or -1 lot
        min_long_quantity = min([value for key, value in risk_dict.items() if value > 0])
        max_short_quantity = max([value for key, value in risk_dict.items() if value < 0])
        """

        R0_below = max(R0_below, 1000)
        R0_below = math.floor(R0_below/1000)*1000
        R0_above = min(R0_above, -1000)
        R0_above = math.ceil(R0_above/1000)*1000
    
        delta_risk_long, risk_curve_long, pnl_curve_long, be_curve_long, extreme_level_below, ticks_to_extreme_below = R_survival(breakeven, level_below_0, R0_below, technical_dict, current_price, tech_levels_dec=TECH_LEVELS_DEC, stop_loss = SL, NBM=25, pnl_0=0)
        delta_risk_short, risk_curve_short, pnl_curve_short, be_curve_short, extreme_level_above, ticks_to_extreme_above = R_survival(breakeven, level_above_0, R0_above, technical_dict, current_price, tech_levels_dec=TECH_LEVELS_DEC, stop_loss = SL, NBM=25, pnl_0=0)
        #print("risk_curve_long: ", risk_curve_long)

        #print("risk_curve_short: ", risk_curve_short)
        delta_risk_dict = {**delta_risk_long, **delta_risk_short}
        risk_dict = {**risk_curve_long, **risk_curve_short}
        pnl_dict = {**pnl_curve_long, **pnl_curve_short}
        be_dict = {**be_curve_long, **be_curve_short}
        #print("delta_risk_dict: ", delta_risk_dict)
        #print("risk_dict: ", risk_dict)
        #print("pnl_dict: ", pnl_dict)
        #print("be_dict: ", be_dict)
        combined_dict = {decimal_to_zn(key): (delta_risk_dict[key]/1000, risk_dict[key]/1000, risk_dict[key]/16, pnl_dict[key], be_dict[key]) for key in sorted(risk_dict.keys(), reverse=True)}
        #print("combined_dict: ", combined_dict)
        return combined_dict

    elif trade_dict["TradeState"] == 1: # Active Trade
        #print("trade_dict: ", trade_dict)
        #print("net_position_dict: ", net_position_dict)
        #print("technical_dict: ", technical_dict)
        #print("current_price: ", current_price)
        starting_price = trade_dict["Price"]
        #print("starting_price: ", starting_price)
        #delta_risk_dict, risk_dict, pnl_dict, be_dict, extreme_level_above, ticks_to_extreme_above = R_survival(breakeven, current_price, net_position_dict["NetPosition"]*1000, technical_dict, starting_price, tech_levels_dec=TECH_LEVELS_DEC, stop_loss = SL, NBM=25, pnl_0=-46.8)
        delta_risk_dict, risk_dict, pnl_dict, be_dict, extreme_level_above, ticks_to_extreme_above = R_survival(breakeven, current_price, net_position_dict["NetPosition"]*1000, technical_dict, starting_price, tech_levels_dec=TECH_LEVELS_DEC, stop_loss = SL, NBM=19.5, pnl_0=0)
        #print("delta_risk_dict: ", delta_risk_dict)
        #print("risk_dict: ", risk_dict)
        #print("pnl_dict: ", pnl_dict)
        #print("be_dict: ", be_dict)
        combined_dict = {decimal_to_zn(key): (delta_risk_dict[key]/1000, risk_dict[key]/1000, risk_dict[key]/16, pnl_dict[key], be_dict[key]) for key in sorted(risk_dict.keys(), reverse=True)}
        #print("combined_dict: ", combined_dict)
        return combined_dict

    else:
        print("Error: TradeState is not 1 or 0")
        return {}, {}, {}


def stream_risk_to_pickle(file_path: str = RISK_STREAMING_PKL):
    """Stream risk() dictionary to pickle with timestamp."""
    try:
        #print("Good till 0")
        # Get risk data
        combined_dict = risk()
        #print("Good till 1")
        #print("combined_dict: ", combined_dict)
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #print("Good till 2")
        
        # Read existing data if file exists
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                history = pickle.load(f)
        else:
            history = []
        
        # Check if data changed (compare dictionaries directly)
        if history and history[-1]['combined_dict'] == combined_dict:
            # Update timestamp only
            history[-1]['timestamp'] = current_timestamp
        else:
            # Add new entry
            history.append({
                'timestamp': current_timestamp,
                'combined_dict': combined_dict
            })
        
        # Write back to file
        with open(file_path, 'wb') as f:
            pickle.dump(history, f)
            
        #print("Good till 3")
    except Exception as e:
        print(f"Error streaming risk to pickle: {e}")


def run_risk_once():
    """Run risk streaming once and return immediately."""
    try:
        print("🔄 Running risk stream once...")
        stream_risk_to_pickle()
        print("✅ Risk stream completed")
        return True
    except Exception as e:
        print(f"❌ Error in risk stream: {e}")
        return False


def run_continuous_risk_streaming(interval_seconds: int = 1):
    """Run risk streaming continuously."""
    while True:
        stream_risk_to_pickle()
        print("--------------------------------")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Risk streaming monitor')
    parser.add_argument('--run-once', action='store_true', 
                       help='Run once and exit (for watchdog integration)')
    parser.add_argument('--interval', type=int, default=1,
                       help='Interval in seconds for continuous mode (default: 1)')
    
    args = parser.parse_args()
    
    if args.run_once:
        run_risk_once()
    else:
        print("Running risk streaming...")
        run_continuous_risk_streaming(args.interval)
    """
    print("risk_dict: ", risk()[0])
    print("--------------------------------")
    print("pnl_dict: ", risk()[1])
    print("--------------------------------")
    print("be_dict: ", risk()[2])
    """
