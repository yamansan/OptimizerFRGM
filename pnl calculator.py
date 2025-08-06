import pandas as pd
import sys
import os
from datetime import datetime, timedelta
import time
import math
import pickle
import requests
from utils import *

# Add the workspace root to Python path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, workspace_root)


from Optimizer.risk_utils import (
    zn_to_decimal,
    decimal_to_zn,  # noqa: F401 – exposed for convenience
    levels_crossed,
    TECH_LEVELS_DEC,
)

# Import risk functions
from Optimizer.Sumo_Curve.risk_curve import R_dict
from Optimizer.Sumo_Curve.risk_update import R_survival
from Optimizer.Sumo_Curve.breakeven_curve import breakeven

def intraday_pnl():
    df = pd.read_csv("data/output/net_position_streaming.csv")

    current_datetime = pd.Timestamp.now()

    if (current_datetime.time() > pd.Timestamp('15:00:00').time()) and (current_datetime.time() < pd.Timestamp('18:00:00').time()):
        px_settle = float(pd.read_csv("data/output/px_settle.csv")["Px_Settle"].iloc[-2])
    else:
        px_settle = float(pd.read_csv("data/output/px_settle.csv")["Px_Settle"].iloc[-1])

    print("px_settle: ", px_settle)
    current_price = get_current_price("Z:/Archive/Live_TT_ZN_Prices.csv")


    # Merge Date and Time columns to create a datetime column
    df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    
    # Dynamic cutoff time logic
    current_datetime = pd.Timestamp.now()
    if current_datetime.time() < pd.Timestamp('18:00:00').time():
        cutoff_time = current_datetime.normalize() - pd.Timedelta(days=1) + pd.Timedelta(hours=18)
    else:
        cutoff_time = current_datetime.normalize() + pd.Timedelta(hours=18)

    roll_over_df = df[df['DateTime'] <= cutoff_time]

    if roll_over_df.empty:
        roll_over_quantity = 0
    else:
        roll_over_quantity = roll_over_df['NetPosition'].iloc[-1]

    intraday_roll_over_pnl = roll_over_quantity * (current_price - px_settle) * 1000

    df_new_trades = df[df['DateTime'] > cutoff_time]

    if df_new_trades.empty:
        intraday_new_pnl = 0
    else:
        intraday_new_pnl = ((current_price-df_new_trades['Price'])*df_new_trades['SignedQuantity']*1000).sum()

    intraday_pnl = intraday_roll_over_pnl + intraday_new_pnl

    return intraday_pnl


def get_3pm_pnl(path: str):
    df = pd.read_csv(path)
    df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])

    px_settle = float(pd.read_csv("data/output/px_settle.csv")["Px_Settle"].iloc[-1])

    previous_px_settle = float(pd.read_csv("data/output/px_settle.csv")["Px_Settle"].iloc[-2])

    current_datetime = pd.Timestamp.now()
    three_pm_today = current_datetime.normalize() + pd.Timedelta(hours=15)
    six_pm_yesterday = current_datetime.normalize() - pd.Timedelta(days=1) + pd.Timedelta(hours=18)

    df_filtered = df[(df["DateTime"] <= three_pm_today) & (df["DateTime"] >= six_pm_yesterday)]
    roll_over_position = (df[df["DateTime"] < six_pm_yesterday]["NetPosition"].iloc[-1])

    roll_over_pnl_upto_3pm = (px_settle-previous_px_settle) * roll_over_position * 1000

    new_pnl_upto_three_pm = ((px_settle - df_filtered["Price"]) * df_filtered["SignedQuantity"] * 1000).sum()

    pnl_upto_3pm = roll_over_pnl_upto_3pm + new_pnl_upto_three_pm
    print("roll over pnl_upto_3pm:", roll_over_pnl_upto_3pm)
    print("new pnl_upto_3pm:", new_pnl_upto_three_pm)
    print("pnl_upto_3pm:", pnl_upto_3pm)
    return pnl_upto_3pm


def ladder_settlement_pnl(path: str):

    pnl_upto_3pm = get_3pm_pnl(path)

    df = pd.read_csv(path)
    df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    current_datetime = pd.Timestamp.now()
    three_pm_today = current_datetime.normalize() + pd.Timedelta(hours=15)

    px_settle = float(pd.read_csv("data/output/px_settle.csv")["Px_Settle"].iloc[-1])
    #px_settle = 115 + (22/32)
    settle_pnl_after_3pm = ((px_settle-df[df["DateTime"] >= three_pm_today]['Price']) * df[df["DateTime"] >= three_pm_today]['SignedQuantity'] * 1000).sum()

    pnl_at_settlement = pnl_upto_3pm + settle_pnl_after_3pm
    #pnl_at_settlement = settle_pnl_after_3pm

    return pnl_at_settlement

if __name__ == "__main__":
    ZN_PATH = "data/output/net_position_streaming.csv"
    ZB_PATH = "data/output/net_position_streaming_ZB.csv"

    print("ladder_settlement_pnl(ZN_PATH): ", ladder_settlement_pnl(ZN_PATH))
    #print("ladder_settlement_pnl(ZB_PATH): ", ladder_settlement_pnl(ZB_PATH))

    """
    #print(pd.read_csv(ZN_PATH))
    #print(pd.read_csv(ZB_PATH))
    """