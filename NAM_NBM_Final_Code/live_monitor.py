import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from shared_functions import preprocess_data, find_minimal_intervals
import matplotlib.pyplot as plt
import time
import os
# This is the live monitor that will be used to monitor the market dip in real-time.
# First we will load the price data till now.
# Then we will load the percentile tables.
# Then we define a function that will take the price data till now and give you the amoung of dip that has happened.
# Then we will use the percentile tables to give you the percentile of the dip that has happened.
# That's it.
# Let's make a function that will take the price data till now and give you the amount of dip that has happened.

def find_dip(df, breakeven_decimal, max_rise, threshold_for_NBM=6):

    # 1) Compute the "body" series and its cumulative sum (in decimal price units)
    delta_close = df["Close"].values - df["Close"].shift(1).values   
    df = df.iloc[1:]    
    if len(df) < 3:
        return np.nan
    #print(df.head())
    current_price = df["Close"].iloc[-1]

    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    df = df.set_index('timestamp')  
    index_list = df.index  # DatetimeIndex, sorted ascending

    i_prev = len(df) - 1

    max_drop_for_t = -float('inf')
    aborted_due_to_nan = False
    minima = float('inf')
    # Walk backward from row i_prev down to row 0 (inclusive)
    for j in range(i_prev, -1, -1):

        row_j = df.iloc[j]
        if df["Close"].iloc[j]<minima:
            minima = df["Close"].iloc[j]
        # If any of OHLCV is NaN at row j, abort and record NaN for this t
        # This means we encountered an event time.
        if row_j[["Close"]].isna().any():
            aborted_due_to_nan = True
            break
        
        # Compute drop_j = C_{t-1} - C_j  (sum of bodies from j+1 through i_prev)
        drop_j = -1*float(delta_close[j:i_prev+1].sum())
        
        if drop_j >= max_drop_for_t:
            max_drop_for_t = drop_j
            max_drop_j = j
            max_drop_price = df["Close"].iloc[j-1]
            minima_after_anchor = minima
            anchor_time = df.index[j-1]

        # Stop early if we've reached the threshold (≥ 0.1875 decimal)
        if max_drop_for_t - drop_j >= max_rise:
            break
        
    if aborted_due_to_nan:
        #print("Event time encountered.")
        return np.nan

    else:
        anchor_point = max_drop_price
        dip_length = anchor_point - current_price
        dip_bps = dip_length * 16
        #print(f"-----Anchor point: {anchor_point:.4f}")
        return dip_bps, anchor_point, minima_after_anchor, anchor_time


def find_rise(df, breakeven_decimal, max_dip, threshold_for_NBM=6):

    # 1) Compute the "body" series and its cumulative sum (in decimal price units)
    delta_close = df["Close"].values - df["Close"].shift(1).values   
    df = df.iloc[1:]    
    if len(df) < 3:
        return np.nan
    #print(df.head())
    current_price = df["Close"].iloc[-1]

    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    df = df.set_index('timestamp')  
    index_list = df.index  # DatetimeIndex, sorted ascending

    i_prev = len(df) - 1

    max_rise_for_t = -float('inf')
    aborted_due_to_nan = False
    maxima = -float('inf')
    # Walk backward from row i_prev down to row 0 (inclusive)
    for j in range(i_prev, -1, -1):

        row_j = df.iloc[j]

        if df["Close"].iloc[j]>maxima:
            maxima = df["Close"].iloc[j]

        # If any of OHLCV is NaN at row j, abort and record NaN for this t
        # This means we encountered an event time.
        if row_j[["Close"]].isna().any():
            aborted_due_to_nan = True
            break
        
        # Compute drop_j = C_{t-1} - C_j  (sum of bodies from j+1 through i_prev)
        rise_j = float(delta_close[j:i_prev+1].sum())
        
        if rise_j >= max_rise_for_t:
            max_rise_for_t = rise_j
            max_rise_j = j
            max_rise_price = df["Close"].iloc[j-1]
            maxima_after_anchor = maxima
            anchor_time = df.index[j-1]

        # Stop early if we've reached the threshold (≥ 0.1875 decimal)
        if max_rise_for_t - rise_j >= max_dip:
            break
        
    if aborted_due_to_nan:
        #print("Event time encountered.")
        return np.nan

    else:
        anchor_point = max_rise_price
        rise_length = current_price - anchor_point
        rise_bps = rise_length * 16
        #print(f"-----Anchor point: {anchor_point:.4f}")
        return rise_bps, anchor_point, maxima_after_anchor, anchor_time


def load_percentile_tables_NAM():
    """Load the percentile lookup tables created by historical_analysis.py"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'distributions', 'percentile_tables_NAM.pkl')
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def load_percentile_tables_NBM():
    """Load the percentile lookup tables created by historical_analysis.py"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'distributions', 'percentile_tables_NBM.pkl')
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def lookup_dip_percentile(dip_bps, percentile_tables, breakeven_decimal):
    """Look up what percentile the current dip represents"""
    
    # Historical tables are keyed by tick counts (e.g., 3, 4, 5) whereas here we receive
    # the decimal value (3/16 = 0.1875). Convert to ticks so we can locate the correct entry.
    breakeven_ticks = int(round(breakeven_decimal * 16))

    if breakeven_ticks not in percentile_tables:
        print(f"No historical data found for breakeven ticks = {breakeven_ticks}")
        return None

    table = percentile_tables[breakeven_ticks]
    sorted_dips = table['dips']
    percentiles = table['percentiles']
    
    # Find where current dip fits in historical distribution
    insert_idx = np.searchsorted(sorted_dips, dip_bps, side='right')
    
    if insert_idx == 0:
        return 0.0  # Smaller than any historical dip
    elif insert_idx >= len(percentiles):
        return 100.0  # Larger than any historical dip
    else:
        return percentiles[insert_idx]  # Interpolated percentile


def lookup_rise_percentile(rise_bps, percentile_tables, breakeven_decimal):
    """Look up what percentile the current dip represents"""
    
    # Historical tables are keyed by tick counts (e.g., 3, 4, 5) whereas here we receive
    # the decimal value (3/16 = 0.1875). Convert to ticks so we can locate the correct entry.
    breakeven_ticks = int(round(breakeven_decimal * 16))

    if breakeven_ticks not in percentile_tables:
        print(f"No historical data found for breakeven ticks = {breakeven_ticks}")
        return None

    table = percentile_tables[breakeven_ticks]
    sorted_rises = table['rises']
    percentiles = table['percentiles']
    
    # Find where current dip fits in historical distribution
    insert_idx = np.searchsorted(sorted_rises, rise_bps, side='right')
    
    if insert_idx == 0:
        return 0.0  # Smaller than any historical dip
    elif insert_idx >= len(percentiles):
        return 100.0  # Larger than any historical dip
    else:
        return percentiles[insert_idx]  # Interpolated percentile

# Example usage:
def main():
    # Load historical percentile tables
    percentile_tables_NAM = load_percentile_tables_NAM()
    percentile_tables_NBM = load_percentile_tables_NBM()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(script_dir, "Live_ZN_Prices.csv"))
    
    """
    df['time'] = pd.to_datetime(df['time'], utc=True).dt.tz_convert('US/Eastern').dt.tz_localize(None)
    df.rename(columns={'time': 'timestamp'}, inplace=True)
    df = df.rename(columns={'close': 'Close', 'open': 'Open', 'high': 'High', 'low': 'Low'})
    """

    # Define breakeven threshold
    breakeven_decimal = 5/16
    # Calculate current dip
    result_dip = find_dip(df, breakeven_decimal, breakeven_decimal)  # Use variable defined above
    result_rise = find_rise(df, breakeven_decimal, breakeven_decimal)  # Use variable defined above

    if isinstance(result_dip, tuple):  # Check if we got a valid result
        dip_bps, anchor_point, minima, anchor_time = result_dip
        # Find percentile of this dip
        percentile = lookup_dip_percentile(dip_bps, percentile_tables_NBM, breakeven_decimal)
        print(f"Current dip: {dip_bps:.2f} bps")
        print(f"Anchor point: {anchor_point:.4f}")  
        print(f"Minima: {minima:.4f}")
        print(f"Anchor time: {anchor_time}")
        if percentile is None:
            print("Percentile could not be determined (no matching historical data).")
        else:
            print(f"Percentile: {percentile:.1f}%")
            # Your trading logic based on percentile goes here
            if percentile >= 90:
                print("Large dip detected - consider significant position")
            elif percentile >= 70:
                print("Moderate dip - consider small position")
            else:
                print("Small dip - wait for better opportunity")
    else:
        print("Could not calculate dip (NaN result)")
    print("--------------------------------")
    if isinstance(result_rise, tuple):  # Check if we got a valid result
        rise_bps, anchor_point, maxima, anchor_time = result_rise
        # Find percentile of this rise
        percentile = lookup_rise_percentile(rise_bps, percentile_tables_NAM, breakeven_decimal)
        print(f"Current rise: {rise_bps:.2f} bps")
        print(f"Anchor point: {anchor_point:.4f}")  
        print(f"Anchor time: {anchor_time}")
        if percentile is None:
            print("Percentile could not be determined (no matching historical data).")
        else:
            print(f"Percentile: {percentile:.1f}%")
            # Your trading logic based on percentile goes here
            if percentile >= 90:
                print("Large rise detected - consider significant position")
            elif percentile >= 70:
                print("Moderate rise - consider small position")
            else:
                print("Small rise - wait for better opportunity")
    else:
        print("Could not calculate rise (NaN result)")



def live_NBM_NAM():
    
    NAM_99th = {
        1/16: 22.35,
        1.5/16: 22.48,
        2/16: 22.84,
        2.5/16: 23.43,
        3/16: 23.70,
        4/16: 24.29,
        5/16: 26.30,
    }

    NBM_99th = {
        1/16: 21.00,
        1.5/16: 21.00,
        2/16: 22.90,
        2.5/16: 23.98,
        3/16: 24.16,
        4/16: 24.82,
        5/16: 25.03,
    }

    percentile_tables_NAM = load_percentile_tables_NAM()
    percentile_tables_NBM = load_percentile_tables_NBM()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(script_dir, "Live_ZN_Prices.csv"))

    dip_bps = {}
    anchor_point_NBM = {}
    percentile = {}
    dip_remaining = {}

    rise_bps = {}
    anchor_point_NAM = {}
    percentile_NAM = {}
    rise_remaining = {}
    
    for breakeven_decimal in [1/16, 1.5/16, 2/16, 2.5/16, 3/16, 4/16, 5/16]:

        result_dip = find_dip(df, breakeven_decimal, breakeven_decimal)  # Use variable defined above
        result_rise = find_rise(df, breakeven_decimal, breakeven_decimal)  # Use variable defined above
        print(f"Breakeven = {int(breakeven_decimal*16)} bps")
        if isinstance(result_dip, tuple):  # Check if we got a valid result
            dip_bps[breakeven_decimal], anchor_point_NBM[breakeven_decimal], minima, anchor_time_NBM = result_dip
            dip_remaining[breakeven_decimal] = NBM_99th[breakeven_decimal] - dip_bps[breakeven_decimal]
            # Find percentile of this dip
            percentile[breakeven_decimal] = lookup_dip_percentile(dip_bps[breakeven_decimal], percentile_tables_NBM, breakeven_decimal)
            print(f"Current dip: {dip_bps[breakeven_decimal]:.2f} bps")
            print(f"Anchor point: {anchor_point_NBM[breakeven_decimal]:.4f}")  
            print(f"Anchor time: {anchor_time_NBM}")
            print(f"Minima: {minima:.4f}")
            print(f"Percentile: {percentile[breakeven_decimal]:.1f}%")
            print(f"Dip remaining: {dip_remaining[breakeven_decimal]:.2f} bps")
            print("--------------------------------")

        if isinstance(result_rise, tuple):  # Check if we got a valid result
            rise_bps[breakeven_decimal], anchor_point_NAM[breakeven_decimal], maxima, anchor_time_NAM = result_rise
            rise_remaining[breakeven_decimal] = NAM_99th[breakeven_decimal] - rise_bps[breakeven_decimal]
            # Find percentile of this rise
            percentile_NAM[breakeven_decimal] = lookup_rise_percentile(rise_bps[breakeven_decimal], percentile_tables_NAM, breakeven_decimal)
            print(f"Current rise: {rise_bps[breakeven_decimal]:.2f} bps")
            print(f"Anchor point: {anchor_point_NAM[breakeven_decimal]:.4f}")  
            print(f"Anchor time: {anchor_time_NAM}")
            print(f"Maxima: {maxima:.4f}")
            print(f"Percentile: {percentile_NAM[breakeven_decimal]:.1f}%")
            print(f"Rise remaining: {rise_remaining[breakeven_decimal]:.2f} bps")
            print("--------------------------------")

    while True:
        df = pd.read_csv(os.path.join(script_dir, "Live_ZN_Prices.csv"))
        current_price = df["Close"].iloc[-1]
        for breakeven_decimal in [1/16, 1.5/16, 2/16, 2.5/16, 3/16, 4/16, 5/16]:

            if current_price - minima > breakeven_decimal:
                if current_price > anchor_point_NBM[breakeven_decimal]:
                    anchor_point_NBM[breakeven_decimal] = current_price
                    anchor_time_NBM = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if current_price < minima:
                minima = current_price
            
            dip_bps[breakeven_decimal] = (anchor_point_NBM[breakeven_decimal] - current_price) * 16
            dip_remaining[breakeven_decimal] = NBM_99th[breakeven_decimal] - dip_bps[breakeven_decimal]
            percentile[breakeven_decimal] = lookup_dip_percentile(dip_bps[breakeven_decimal], percentile_tables_NBM, breakeven_decimal)
            print(f"Current dip: {dip_bps[breakeven_decimal]:.2f} bps")
            print(f"Anchor point NBM: {anchor_point_NBM[breakeven_decimal]:.4f}")  
            print(f"Minima: {minima:.4f}")
            print(f"Percentile NBM: {percentile[breakeven_decimal]:.1f}%")
            print(f"Dip remaining NBM: {dip_remaining[breakeven_decimal]:.2f} bps")
            print(f"Anchor time: {anchor_time_NBM}")
            print("--------------------------------")

        for breakeven_decimal in [1/16, 1.5/16, 2/16, 2.5/16, 3/16, 4/16, 5/16]:

            if maxima - current_price > breakeven_decimal:
                if current_price < anchor_point_NAM[breakeven_decimal]:
                    anchor_point_NAM[breakeven_decimal] = current_price
                    anchor_time_NAM = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if current_price > maxima:
                maxima = current_price
            
            rise_bps[breakeven_decimal] = (current_price - anchor_point_NAM[breakeven_decimal]) * 16
            rise_remaining[breakeven_decimal] = NAM_99th[breakeven_decimal] - rise_bps[breakeven_decimal]
            percentile_NAM[breakeven_decimal] = lookup_rise_percentile(rise_bps[breakeven_decimal], percentile_tables_NAM, breakeven_decimal)
            print(f"Current rise: {rise_bps[breakeven_decimal]:.2f} bps")
            print(f"Anchor point NAM: {anchor_point_NAM[breakeven_decimal]:.4f}")  
            print(f"Maxima: {maxima:.4f}")
            print(f"Percentile NAM: {percentile_NAM[breakeven_decimal]:.1f}%")
            print(f"Rise remaining NAM: {rise_remaining[breakeven_decimal]:.2f} bps")
            print(f"Anchor time: {anchor_time_NAM}")
            print("--------------------------------")

        levels = [1, 1.5, 2, 2.5, 3, 4, 5]

        # Create the row_data using loops
        row_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_price': current_price,
        }

        # Add NBM data
        for level in levels:
            level_key = str(level).replace('.', '_')  # Convert 1.5 to "1_5"
            row_data.update({
                f'NBM_dips_remaining_{level_key}': dip_remaining[level/16],
                f'NBM_position_{level_key}': -(dip_remaining[level/16])/16 + current_price,
                f'NBM_dip_bps_{level_key}': dip_bps[level/16],
                f'NBM_percentile_{level_key}': percentile[level/16],
                f'NBM_anchor_point_{level_key}': anchor_point_NBM[level/16],
            })

        # Add NAM data
        for level in levels:
            level_key = str(level).replace('.', '_')
            row_data.update({
                f'NAM_rises_remaining_{level_key}': rise_remaining[level/16],
                f'NAM_position_{level_key}': (rise_remaining[level/16])/16 + current_price,
                f'NAM_rises_bps_{level_key}': rise_bps[level/16],
                f'NAM_percentile_{level_key}': percentile_NAM[level/16],
                f'NAM_anchor_point_{level_key}': anchor_point_NAM[level/16],
            })
        csv_path = os.path.join(script_dir, "Live_NBM_NAM.csv")
        file_exists = os.path.exists(csv_path)
        pd.DataFrame([row_data]).to_csv(csv_path, mode='a', header=not file_exists, index=False)

        time.sleep(5)
        
if __name__ == "__main__":
    #main()
    live_NBM_NAM()

   