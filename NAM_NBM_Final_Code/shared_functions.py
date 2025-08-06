import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def preprocess_data(df1_path, df2_path):
    """
    Complete data preprocessing from your notebook
    Returns: df, nan_ranges, cols_to_null
    """
    # Load data
    df1 = pd.read_csv(df1_path)
    df2 = pd.read_csv(df2_path)
    
    # Make values NaN for times not in df1
    tz_in_df1 = set(df1['US/Eastern Timezone'])
    df = df2.copy()
    mask_common = df['US/Eastern Timezone'].isin(tz_in_df1)
    
    cols_to_null = [col for col in df.columns 
                    if col not in ['Datetime', 'US/Eastern Timezone']]
    
    df.loc[~mask_common, cols_to_null] = np.nan
    df = df.drop(columns=['Datetime'])
    
    reordered_cols = ['US/Eastern Timezone'] + [c for c in df.columns 
                                               if c != 'US/Eastern Timezone']
    df = df[reordered_cols]
    df = df.rename(columns={'US/Eastern Timezone': 'timestamp'})
    
    # Convert timestamps
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df['timestamp'] = (
        df['timestamp']
          .dt.tz_convert('US/Eastern')
          .dt.tz_localize(None)
    )
    
    # Compute nan_ranges
    mask_allna = df[cols_to_null].isna().all(axis=1).to_numpy()
    N = len(df)
    nan_ranges = {}
    in_run = False
    
    for idx in range(N):
        if mask_allna[idx] and not in_run:
            run_start = idx
            in_run = True
        elif in_run and (idx == N-1 or not mask_allna[idx]):
            run_end = idx-1 if not mask_allna[idx] else idx
            nan_ranges[run_start] = run_end
            in_run = False
    
    return df, nan_ranges, cols_to_null

def find_minimal_intervals(df, breakeven_decimal, nan_ranges, max_length=300):
    """
    Your exact function from notebook with nan_ranges parameter
    """
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)

    N = len(df)
    delta_close = df['Close'].values - df['Close'].shift(1).values
    df = df.iloc[1:]
    lower = breakeven_decimal
    
    results = []
    i = 0
    while i < N:
        if i in nan_ranges:
            i = nan_ranges[i]+1
            continue
        
        t_start = df['timestamp'].iloc[i]
        found = False

        if delta_close[i]<0:
            i+=1
            continue    

        for L in range(0, max_length):
            j = i + L
            if j >= N:
                break
            
            # Condition 1: Check for NaN
            if df.iloc[j].isna().any():
                break
            
            # Condition 2: Check window sum
            window_sum = delta_close[i:j+1].sum()
            if window_sum<=0:
                break
            
            # Condition 3: Check if threshold reached
            if lower <= window_sum:
                results.append(t_start)
                i = i + L +1
                found = True
                break
            
        if not found:
            i += 1

    return results

def dip_distribution_data_only(df, breakeven_decimal, max_rise, nan_ranges, threshold_for_NBM=6):
    """
    Modified version of your dip_distribution that returns data instead of plotting
    """
    delta_close = df["Close"].values - df["Close"].shift(1).values
    df = df.iloc[1:]
    max_drops_decimal = []

    results = find_minimal_intervals(df, breakeven_decimal, nan_ranges)

    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    df = df.set_index('timestamp')  
    index_list = df.index

    for t in results:
        try:
            i_curr = index_list.get_loc(t)
        except KeyError:
            max_drops_decimal.append(np.nan)
            continue

        if i_curr == 0:
            max_drops_decimal.append(0.0)
            continue

        i_prev = i_curr - 1
        max_drop_for_t = -float('inf')
        aborted_due_to_nan = False

        for j in range(i_prev, -1, -1):
            row_j = df.iloc[j]

            if row_j[["Open", "High", "Low", "Close", "Volume"]].isna().any():
                aborted_due_to_nan = True
                break

            drop_j = -1*float(delta_close[j:i_prev+1].sum())
            if drop_j > max_drop_for_t:
                max_drop_for_t = drop_j

            if max_drop_for_t-drop_j >= max_rise:
                break
            
        if aborted_due_to_nan:
            continue
        else:
            max_drops_decimal.append(max_drop_for_t)

    max_drops_decimal = np.array(max_drops_decimal, dtype=float)
    max_drops_bps = max_drops_decimal * 16
    valid_drops_bps = max_drops_bps[~np.isnan(max_drops_bps)]
    filtered_drops_bps = valid_drops_bps[valid_drops_bps >= threshold_for_NBM]

    return filtered_drops_bps

def find_minimal_intervals_NAM(df, breakeven_decimal, nan_ranges, max_length=300):
    """
    Your exact function from notebook with nan_ranges parameter
    """
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)

    N = len(df)
    delta_close = df['Close'].values - df['Close'].shift(1).values
    df = df.iloc[1:]
    lower = -1*breakeven_decimal
    
    results = []
    i = 0
    while i < N:
        if i in nan_ranges:
            i = nan_ranges[i]+1
            continue
        
        t_start = df['timestamp'].iloc[i]
        found = False

        if delta_close[i]>0:
            i+=1
            continue    

        for L in range(0, max_length):
            j = i + L
            if j >= N:
                break
            
            # Condition 1: Check for NaN
            if df.iloc[j].isna().any():
                break
            
            # Condition 2: Check window sum
            window_sum = delta_close[i:j+1].sum()
            if window_sum>=0:
                break
            
            # Condition 3: Check if threshold reached
            if window_sum <= lower:
                results.append(t_start)
                i = i + L +1
                found = True
                break
            
        if not found:
            i += 1

    return results

def rise_distribution_data_only(df, breakeven_decimal, max_dip, nan_ranges, threshold_for_NBM=6):
    """
    Modified version of your dip_distribution that returns data instead of plotting
    """
    delta_close = df["Close"].values - df["Close"].shift(1).values
    df = df.iloc[1:]
    max_rise_decimal = []

    results = find_minimal_intervals_NAM(df, breakeven_decimal, nan_ranges)

    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    df = df.set_index('timestamp')  
    index_list = df.index

    for t in results:
        try:
            i_curr = index_list.get_loc(t)
        except KeyError:
            max_rise_decimal.append(np.nan)
            continue

        if i_curr == 0:
            max_rise_decimal.append(0.0)
            continue

        i_prev = i_curr - 1
        max_rise_for_t = -float('inf')
        aborted_due_to_nan = False

        # Loop backwards to find max rise
        for j in range(i_prev, -1, -1):
            row_j = df.iloc[j]

            # Check for NaN
            if row_j[["Open", "High", "Low", "Close", "Volume"]].isna().any():
                aborted_due_to_nan = True
                break

            # Compute rise
            rise_j = float(delta_close[j:i_prev+1].sum())
            if rise_j > max_rise_for_t:
                max_rise_for_t = rise_j

            # Check if threshold reached
            if max_rise_for_t-rise_j >= max_dip:
                break
            
        if aborted_due_to_nan:
            continue
        else:
            max_rise_decimal.append(max_rise_for_t)

    # Filter out NaNs and convert to bps
    max_rise_decimal = np.array(max_rise_decimal, dtype=float)
    max_rise_bps = max_rise_decimal * 16
    valid_rise_bps = max_rise_bps[~np.isnan(max_rise_bps)]
    filtered_rise_bps = valid_rise_bps[valid_rise_bps >= threshold_for_NBM]

    return filtered_rise_bps