"""
Intraday PnL Calculator - Continuous Streaming Version
Calculates intraday PnL for filled orders from 3pm to 3pm periods.
Filters for Exchange="CME", CurrentUser="Eric", Contract="ZN Sep25"
Uses file tail monitoring for continuous processing.
"""

import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
import os
import sys
import time as time_module
import pickle

# Add workspace root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def load_fills_data(file_path):
    """Load and filter the continuous fills data"""
    df = pd.read_csv(file_path)
    
    # Filter for CME, Eric, ZN Sep25
    filtered_df = df[
        (df['Exchange'] == 'CME') & 
        (df['CurrentUser'] == 'Eric') & 
        (df['Contract'] == 'ZN Sep25')
    ].copy()
    
    # Convert Date and Time to datetime
    if not filtered_df.empty:
        filtered_df['DateTime'] = pd.to_datetime(filtered_df['Date'] + ' ' + filtered_df['Time'])
    
    return filtered_df

def create_signed_quantity(df):
    """Create signed quantity: positive for BUY, negative for SELL"""
    df = df.copy()
    df['SignedQuantity'] = np.where(df['Side'] == 1, df['Quantity'], -df['Quantity'])
    return df

def get_intraday_period_start(current_datetime):
    """Get the 3pm start time for the intraday period containing the current datetime"""
    current_date = current_datetime.date()
    cutoff_time = time(15, 0)  # 3:00 PM
    
    if current_datetime.time() >= cutoff_time:
        # Trade is after 3pm, period starts today at 3pm
        period_start = datetime.combine(current_date, cutoff_time)
    else:
        # Trade is before 3pm, period started yesterday at 3pm
        yesterday = current_date - timedelta(days=1)
        period_start = datetime.combine(yesterday, cutoff_time)
    
    return period_start

def calculate_intraday_pnl(df):
    """Calculate intraday PnL for each trade"""
    if df.empty:
        return df
        
    df = df.copy()
    df = df.sort_values('DateTime').reset_index(drop=True)
    
    intraday_pnls = []
    df = create_signed_quantity(df)
    net_position = df['SignedQuantity'].sum()
    
    for idx, row in df.iterrows():
        current_datetime = row['DateTime']
        current_price = row['Price']
        current_signed_qty = row['SignedQuantity']
        
        # Get the start of the intraday period
        period_start = get_intraday_period_start(current_datetime)
        
        # Get all trades in the same intraday period up to current trade
        period_trades = df[
            (df['DateTime'] >= period_start) & 
            (df['DateTime'] <= current_datetime)
        ].copy()
        
        # Calculate cumulative position and weighted average price
        cumulative_position = 0
        total_cost = 0
        
        for _, trade in period_trades.iterrows():
            trade_signed_qty = trade['SignedQuantity']
            trade_price = trade['Price']
            
            if cumulative_position * trade_signed_qty >= 0:
                # Same direction or starting from flat
                total_cost += trade_signed_qty * trade_price
                cumulative_position += trade_signed_qty
            else:
                # Opposite direction - partial or full close
                if abs(trade_signed_qty) <= abs(cumulative_position):
                    # Partial close
                    cumulative_position += trade_signed_qty
                else:
                    # Full close and reverse
                    remaining_qty = trade_signed_qty + cumulative_position
                    total_cost = remaining_qty * trade_price
                    cumulative_position = remaining_qty
        
        # Calculate weighted average price
        if cumulative_position != 0:
            avg_price = total_cost / cumulative_position
            # PnL = Position * (Current Price - Average Price)
            pnl = cumulative_position * (current_price - avg_price)
        else:
            pnl = 0
        
        intraday_pnls.append(pnl)
    
    df['intraday_pnl'] = intraday_pnls
    return df

def save_results(df, output_path):
    """Save the results to CSV with duplicate prevention"""
    # Remove any duplicates before saving
    df_clean = df.drop_duplicates()
    
    df_clean.to_csv(output_path, index=False)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Results updated: {len(df_clean)} trades, Latest PnL: {df_clean['intraday_pnl'].iloc[-1]:.2f}")

def load_state(state_file):
    """Load the last processed row count"""
    if os.path.exists(state_file):
        try:
            with open(state_file, 'rb') as f:
                return pickle.load(f)
        except:
            return 0
    return 0

def save_state(state_file, last_row):
    """Save the last processed row count"""
    try:
        with open(state_file, 'wb') as f:
            pickle.dump(last_row, f)
    except Exception as e:
        print(f"Warning: Could not save state: {e}")

def continuous_monitor(input_file, output_file, state_file, poll_interval=2):
    """Continuously monitor for new data and process incrementally"""
    print(f"Starting continuous intraday PnL monitoring...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"Poll interval: {poll_interval} seconds")
    print("Press Ctrl+C to stop")
    
    # Load last processed state
    last_processed_row = load_state(state_file)
    
    try:
        while True:
            try:
                # Check if input file exists
                if not os.path.exists(input_file):
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for input file: {input_file}")
                    time_module.sleep(poll_interval)
                    continue
                
                # Read the full CSV file
                df_full = pd.read_csv(input_file)
                
                # Check for new rows
                if len(df_full) > last_processed_row:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing {len(df_full) - last_processed_row} new rows...")
                    
                    # Get ALL filtered data (to maintain proper context for PnL calculations)
                    all_filtered_df = df_full[
                        (df_full['Exchange'] == 'CME') & 
                        (df_full['CurrentUser'] == 'Eric') & 
                        (df_full['Contract'] == 'ZN Sep25')
                    ].copy()
                    
                    if not all_filtered_df.empty:
                        # Convert datetime and create signed quantities
                        all_filtered_df['DateTime'] = pd.to_datetime(all_filtered_df['Date'] + ' ' + all_filtered_df['Time'])
                        all_filtered_df = create_signed_quantity(all_filtered_df)
                        
                        # Calculate PnL for all matching trades
                        result_df = calculate_intraday_pnl(all_filtered_df)
                        
                        # Save results with duplicate prevention
                        save_results(result_df, output_file)
                        
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Processed {len(all_filtered_df)} total matching trades")
                    else:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] No matching trades found")
                    
                    # Update state regardless of whether we found matching trades
                    last_processed_row = len(df_full)
                    save_state(state_file, last_processed_row)
                
                # Wait before next check
                time_module.sleep(poll_interval)
                
            except KeyboardInterrupt:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Stopping monitor...")
                break
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
                time_module.sleep(poll_interval * 2)  # Wait longer on error
                
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Monitor stopped by user")

def main():
    """Main function to run the intraday PnL calculator"""
    # File paths
    input_file = "data/output/ladder/continuous_fills.csv"
    output_file = "Optimizer/Sumo_Curve/intraday_pnl_results.csv"
    state_file = "Optimizer/Sumo_Curve/intraday_pnl_state.pkl"
    
    # Start continuous monitoring
    continuous_monitor(input_file, output_file, state_file, poll_interval=2)

if __name__ == "__main__":
    main()
