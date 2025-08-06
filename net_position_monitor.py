import pandas as pd
import numpy as np
import os
import sys
import time
import pickle
import argparse
from datetime import datetime
from typing import Tuple
import json

workspace_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, workspace_root)

from config import CONTINUOUS_FILLS_CSV, NET_POSITION_STREAMING_CSV, NET_POSITION_MONITOR_STATE_PKL

def load_state(state_file: str) -> Tuple[int, float]:
    """Load the last processed row index and current net position from state file."""
    if os.path.exists(state_file):
        try:
            with open(state_file, 'rb') as f:
                state = pickle.load(f)
                last_processed_row = state.get('last_processed_row', 0)
                current_net_position = state.get('current_net_position', 0)
                print(f"Loaded state: last_row={last_processed_row}, net_position={current_net_position}")
                return last_processed_row, current_net_position
        except Exception as e:
            print(f"Error loading state: {e}")
    
    return 0, 0


def save_state(state_file: str, last_processed_row: int, current_net_position: float) -> None:
    """Save the current state to file."""
    try:
        state = {
            'last_processed_row': last_processed_row,
            'current_net_position': current_net_position
        }
        with open(state_file, 'wb') as f:
            pickle.dump(state, f)
        print(f"Saved state: last_row={last_processed_row}, net_position={current_net_position}")
    except Exception as e:
        print(f"Error saving state: {e}")


def load_config(config_file='config.json'):
    """Load configuration from a JSON file."""
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config

# Load configuration
config = load_config()

def stream_net_position_monitor(
    input_file: str = CONTINUOUS_FILLS_CSV,
    output_file: str = NET_POSITION_STREAMING_CSV,
    state_file: str = NET_POSITION_MONITOR_STATE_PKL,
    interval: float = 10.0,
    reset: bool = False
) -> None:
    """
    Stream net position monitoring with state persistence.
    """
    
    # Reset state if requested
    if reset:
        if os.path.exists(state_file):
            os.remove(state_file)
            print("State file reset")
        if os.path.exists(output_file):
            os.remove(output_file)
            print("Output file reset")
    
    last_processed_row, current_net_position = load_state(state_file)
    
    # Initialize output CSV with headers if it doesn't exist
    if not os.path.exists(output_file):
        header_columns = [
            'Date', 'Time', 'InstrumentId', 'InstrumentName', 'Side', 'SideName', 
            'Quantity', 'Price', 'OrderId', 'AccountId', 'MarketId', 'TransactTime', 
            'TimeStamp', 'ExecId', 'OrderStatus', 'Exchange', 'Contract', 'Originator', 
            'CurrentUser', 'SignedQuantity', 'NetPosition'
        ]
        
        with open(output_file, 'w', newline='') as f:
            import csv
            writer = csv.writer(f)
            writer.writerow(header_columns)
        print(f"Created output file: {output_file}")
    
    print(f"Starting net position monitor...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"Polling every {interval} seconds")
    print(f"Starting from row: {last_processed_row}, Net position: {current_net_position}")
    
    save_counter = 0
    
    while True:
        try:
            if not os.path.exists(input_file):
                print(f"Waiting for {input_file}...")
                time.sleep(interval)
                continue
            
            # Read the full CSV
            df = pd.read_csv(input_file)
            
            # Filter for trades based on config
            mask = (df['Exchange'] == config['exchange']) & \
                   (df['Contract'] == config['contract'])
            filtered_df = df[mask].copy()
            
            # Check if we have new rows to process
            if len(filtered_df) > last_processed_row:
                print(f"Processing {len(filtered_df) - last_processed_row} new rows...")
                
                # Process only new rows
                new_rows = filtered_df.iloc[last_processed_row:].copy()
                
                if not new_rows.empty:
                    # Calculate signed quantity for new rows
                    new_rows['SignedQuantity'] = np.where(new_rows['Side'] == 1, new_rows['Quantity'], -new_rows['Quantity'])
                    
                    # Calculate cumulative net position starting from current position
                    new_rows['NetPosition'] = current_net_position + new_rows['SignedQuantity'].cumsum()
                    
                    # Append new rows to output CSV
                    new_rows.to_csv(output_file, mode='a', header=False, index=False)
                    
                    # Update state
                    last_processed_row = len(filtered_df)
                    current_net_position = new_rows['NetPosition'].iloc[-1]
                    
                    print(f"Processed {len(new_rows)} new trades")
                    print(f"Latest net position: {current_net_position}")
                    print(f"Total processed rows: {last_processed_row}")
                else:
                    print("No new matching trades found")
            else:
                print("No new rows to process")
            
            # Save state periodically
            save_counter += 1
            if save_counter >= 5:  # Save every 5 iterations
                save_state(state_file, last_processed_row, current_net_position)
                save_counter = 0
            
            time.sleep(interval)
            
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            time.sleep(interval)


def run_net_position_once(
    input_file: str = CONTINUOUS_FILLS_CSV,
    output_file: str = NET_POSITION_STREAMING_CSV,
    state_file: str = NET_POSITION_MONITOR_STATE_PKL
) -> bool:
    """
    Run one cycle of net position monitoring and return immediately.
    Returns True on success, False on error.
    """
    try:
        # Load state from previous runs
        last_processed_row, current_net_position = load_state(state_file)
        print(f"📂 Loaded state: row={last_processed_row}, position={current_net_position}")
        
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"⏳ Input file {input_file} not found, skipping...")
            return True  # Not an error, just no data yet
        
        if not os.path.exists(output_file):
            header_columns = [
                'Date', 'Time', 'InstrumentId', 'InstrumentName', 'Side', 'SideName', 
                'Quantity', 'Price', 'OrderId', 'AccountId', 'MarketId', 'TransactTime', 
                'TimeStamp', 'ExecId', 'OrderStatus', 'Exchange', 'Contract', 'Originator', 
                'CurrentUser', 'SignedQuantity', 'NetPosition'
            ]
            with open(output_file, 'w', newline='') as f:
                import csv
                writer = csv.writer(f)
                writer.writerow(header_columns)
            print(f"Created output file: {output_file}")

        # Read and filter data (same logic as continuous monitor)
        df = pd.read_csv(input_file)
        mask = (df['Exchange'] == config['exchange']) & \
               (df['Contract'] == config['contract'])
        filtered_df = df[mask].copy()
        
        # Check for new rows to process
        if len(filtered_df) <= last_processed_row:
            print(f"✅ No new rows to process (have {last_processed_row}, total {len(filtered_df)})")
            return True  # Success, just no new data
        
        print(f"🔄 Processing {len(filtered_df) - last_processed_row} new rows...")
        
        # Process only new rows
        new_rows = filtered_df.iloc[last_processed_row:].copy()
        
        if not new_rows.empty:
            # Calculate signed quantity for new rows
            new_rows['SignedQuantity'] = np.where(new_rows['Side'] == 1, new_rows['Quantity'], -new_rows['Quantity'])
            
            # Calculate cumulative net position starting from current position
            new_rows['NetPosition'] = current_net_position + new_rows['SignedQuantity'].cumsum()
            
            # Append new rows to output CSV
            new_rows.to_csv(output_file, mode='a', header=False, index=False)
            
            # Update state variables
            last_processed_row = len(filtered_df)
            current_net_position = new_rows['NetPosition'].iloc[-1]
            
            print(f"✅ Processed {len(new_rows)} new trades")
            print(f"📊 Latest net position: {current_net_position}")
            print(f"📈 Total processed rows: {last_processed_row}")
        
        # Always save state after processing (critical for watchdog approach)
        save_state(state_file, last_processed_row, current_net_position)
        print(f"💾 State saved: row={last_processed_row}, position={current_net_position}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in net position monitor: {e}")
        return False


def main():
    """Main function with command line arguments."""
    parser = argparse.ArgumentParser(description='Stream net position monitoring')
    parser.add_argument('--input', default=CONTINUOUS_FILLS_CSV, 
                       help='Input CSV file path')
    parser.add_argument('--output', default=NET_POSITION_STREAMING_CSV, 
                       help='Output CSV file path')
    parser.add_argument('--state', default=NET_POSITION_MONITOR_STATE_PKL, 
                       help='State file path')
    parser.add_argument('--interval', type=float, default=10.0, 
                       help='Polling interval in seconds')
    parser.add_argument('--reset', action='store_true', 
                       help='Reset state and start fresh')
    parser.add_argument('--run-once', action='store_true',
                       help='Run once and exit (for event-driven mode)')
    
    args = parser.parse_args()
    
    print("=== Net Position Stream Monitor ===")
    print(f"Input file: {args.input}")
    print(f"Output file: {args.output}")
    print(f"State file: {args.state}")
    if not args.run_once:
        print(f"Interval: {args.interval}s")
    print(f"Reset: {args.reset}")
    print(f"Run once: {args.run_once}")
    print("=" * 40)
    
    try:
        if args.run_once:
            # Run once and exit (for watchdog approach)
            success = run_net_position_once(
                input_file=args.input,
                output_file=args.output,
                state_file=args.state
            )
            print(f"🏁 Run completed with {'success' if success else 'errors'}")
            sys.exit(0 if success else 1)
        else:
            # Original continuous monitoring mode
            stream_net_position_monitor(
                input_file=args.input,
                output_file=args.output,
                state_file=args.state,
                interval=args.interval,
                reset=args.reset
            )
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Error: {e}")



if __name__ == "__main__":
    main()





