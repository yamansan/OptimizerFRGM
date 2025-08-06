import pandas as pd
import os
import sys
import time
import pickle
import argparse
from datetime import datetime
from typing import Tuple, Optional

workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, workspace_root)

from config import NET_POSITION_STREAMING_CSV, TRADE_STATE_EVENTS_CSV, TRADE_STATE_MONITOR_STATE_PKL

def load_state(state_file: str) -> int:
    """Load the last processed row index from state file."""
    if os.path.exists(state_file):
        try:
            with open(state_file, 'rb') as f:
                state = pickle.load(f)
                last_processed_row = state.get('last_processed_row', 0)
                print(f"Loaded state: last_processed_row={last_processed_row}")
                return last_processed_row
        except Exception as e:
            print(f"Error loading state: {e}")
    
    return 0


def save_state(state_file: str, last_processed_row: int) -> None:
    """Save the current state to file."""
    try:
        state = {'last_processed_row': last_processed_row}
        with open(state_file, 'wb') as f:
            pickle.dump(state, f)
        print(f"Saved state: last_processed_row={last_processed_row}")
    except Exception as e:
        print(f"Error saving state: {e}")


def detect_trade_events(previous_net_pos: float, current_net_pos: float) -> list:
    """
    Detect trade start/end events based on net position changes.
    Returns list of trade events: [(trade_state, description), ...]
    trade_state: 0 = trade start, 1 = trade end
    """
    events = []
    
    # Case 1: Trade starts (0 -> non-zero)
    if previous_net_pos == 0 and current_net_pos != 0:
        events.append((1, f"Trade started: 0 -> {current_net_pos}"))
    
    # Case 2: Trade ends (non-zero -> 0)
    elif previous_net_pos != 0 and current_net_pos == 0:
        events.append((0, f"Trade ended: {previous_net_pos} -> 0"))
    
    # Case 3: Direct sign change (positive -> negative or negative -> positive)
    elif (previous_net_pos > 0 and current_net_pos < 0) or (previous_net_pos < 0 and current_net_pos > 0):
        events.append((0, f"Previous trade ended: {previous_net_pos} -> {current_net_pos}"))
        events.append((1, f"New trade started: {previous_net_pos} -> {current_net_pos}"))
    
    return events


def stream_trade_state_monitor(
    input_file: str = NET_POSITION_STREAMING_CSV,
    output_file: str = TRADE_STATE_EVENTS_CSV,
    state_file: str = TRADE_STATE_MONITOR_STATE_PKL,
    interval: float = 10.0,
    reset: bool = False
) -> None:
    """
    Monitor net position changes and track trade state events.
    """
    
    # Reset state if requested
    if reset:
        if os.path.exists(state_file):
            os.remove(state_file)
            print("State file reset")
        if os.path.exists(output_file):
            os.remove(output_file)
            print("Output file reset")
    
    last_processed_row = load_state(state_file)
    
    # Initialize output CSV with headers if it doesn't exist
    if not os.path.exists(output_file):
        header_columns = ['Timestamp', 'Date', 'Time', 'Price', 'TradeState', 'NetPosition', 'PreviousNetPosition', 'Description']
        
        with open(output_file, 'w', newline='') as f:
            import csv
            writer = csv.writer(f)
            writer.writerow(header_columns)
        print(f"Created output file: {output_file}")
    
    print(f"Starting trade state monitor...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"Polling every {interval} seconds")
    print(f"Starting from row: {last_processed_row}")
    
    save_counter = 0
    previous_net_position = None
    
    while True:
        try:
            if not os.path.exists(input_file):
                print(f"Waiting for {input_file}...")
                time.sleep(interval)
                continue
            
            # Read the net position CSV
            df = pd.read_csv(input_file)
            
            # Check if we have new rows to process
            if len(df) > last_processed_row:
                print(f"Processing {len(df) - last_processed_row} new rows...")
                
                # Process only new rows
                new_rows = df.iloc[last_processed_row:].copy()
                
                if not new_rows.empty:
                    trade_events = []
                    
                    for idx, row in new_rows.iterrows():
                        current_net_pos = row['NetPosition']
                        
                        # Skip first row if we don't have previous position
                        if previous_net_position is not None:
                            events = detect_trade_events(previous_net_position, current_net_pos)
                            
                            for trade_state, description in events:
                                trade_events.append({
                                    'Timestamp': row['TimeStamp'],
                                    'Date': row['Date'],
                                    'Time': row['Time'],
                                    'Price': row['Price'],
                                    'TradeState': trade_state,
                                    'NetPosition': current_net_pos,
                                    'PreviousNetPosition': previous_net_position,
                                    'Description': description
                                })
                        
                        previous_net_position = current_net_pos
                    
                    # Write trade events to output CSV
                    if trade_events:
                        import csv
                        with open(output_file, 'a', newline='') as f:
                            writer = csv.DictWriter(f, fieldnames=['Timestamp', 'Date', 'Time', 'Price', 'TradeState', 'NetPosition', 'PreviousNetPosition', 'Description'])
                            writer.writerows(trade_events)
                        
                        print(f"Detected {len(trade_events)} trade events")
                        for event in trade_events:
                            print(f"  {event['Description']} at {event['Price']} on {event['Date']} {event['Time']}")
                    else:
                        print("No trade state changes detected")
                    
                    # Update state
                    last_processed_row = len(df)
                    
                    print(f"Total processed rows: {last_processed_row}")
                else:
                    print("No new rows found")
            else:
                print("No new rows to process")
            
            # Save state periodically
            save_counter += 1
            if save_counter >= 5:  # Save every 5 iterations
                save_state(state_file, last_processed_row)
                save_counter = 0
            
            time.sleep(interval)
            
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            time.sleep(interval)


def run_trade_state_once(
    input_file: str = NET_POSITION_STREAMING_CSV,
    output_file: str = TRADE_STATE_EVENTS_CSV,
    state_file: str = TRADE_STATE_MONITOR_STATE_PKL
) -> bool:
    """
    Run one cycle of trade state monitoring and return immediately.
    Returns True on success, False on error.
    """
    try:
        # Load state from previous runs
        last_processed_row = load_state(state_file)
        print(f"📂 Loaded state: row={last_processed_row}")
        
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"⏳ Input file {input_file} not found, skipping...")
            return True  # Not an error, just no data yet
        
        # Read the net position CSV
        df = pd.read_csv(input_file)
        
        if not os.path.exists(output_file):
            header_columns = ['Timestamp', 'Date', 'Time', 'Price', 'TradeState', 'NetPosition', 'PreviousNetPosition', 'Description']
            
            with open(output_file, 'w', newline='') as f:
                import csv
                writer = csv.writer(f)
                writer.writerow(header_columns)
            print(f"Created output file: {output_file}")

        # Check for new rows to process
        if len(df) <= last_processed_row:
            print(f"✅ No new rows to process (have {last_processed_row}, total {len(df)})")
            return True  # Success, just no new data
        
        print(f"🔄 Processing {len(df) - last_processed_row} new rows...")
        
        # Process only new rows
        new_rows = df.iloc[last_processed_row:].copy()
        previous_net_position = None
        
        # Get the last net position from existing data if we have processed rows before
        if last_processed_row > 0:
            existing_df = df.iloc[:last_processed_row]
            if not existing_df.empty:
                previous_net_position = existing_df['NetPosition'].iloc[-1]
        
        if not new_rows.empty:
            trade_events = []
            
            for idx, row in new_rows.iterrows():
                current_net_pos = row['NetPosition']
                
                # Skip first row if we don't have previous position
                if previous_net_position is not None:
                    events = detect_trade_events(previous_net_position, current_net_pos)
                    
                    for trade_state, description in events:
                        trade_events.append({
                            'Timestamp': row['TimeStamp'],
                            'Date': row['Date'],
                            'Time': row['Time'],
                            'Price': row['Price'],
                            'TradeState': trade_state,
                            'NetPosition': current_net_pos,
                            'PreviousNetPosition': previous_net_position,
                            'Description': description
                        })
                
                previous_net_position = current_net_pos
            
            # Write trade events to output CSV
            if trade_events:
                import csv
                with open(output_file, 'a', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['Timestamp', 'Date', 'Time', 'Price', 'TradeState', 'NetPosition', 'PreviousNetPosition', 'Description'])
                    writer.writerows(trade_events)
                
                print(f"✅ Detected {len(trade_events)} trade events")
                for event in trade_events:
                    print(f"  📊 {event['Description']} at {event['Price']} on {event['Date']} {event['Time']}")
            else:
                print("✅ No trade state changes detected")
            
            # Update state
            last_processed_row = len(df)
            print(f"📈 Total processed rows: {last_processed_row}")
        
        # Always save state after processing (critical for watchdog approach)
        save_state(state_file, last_processed_row)
        print(f"💾 State saved: row={last_processed_row}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in trade state monitor: {e}")
        return False


def main():
    """Main function with command line arguments."""
    parser = argparse.ArgumentParser(description='Monitor trade state changes based on net position')
    parser.add_argument('--input', default=NET_POSITION_STREAMING_CSV, 
                       help='Input net position CSV file path')
    parser.add_argument('--output', default=TRADE_STATE_EVENTS_CSV, 
                       help='Output trade events CSV file path')
    parser.add_argument('--state', default=TRADE_STATE_MONITOR_STATE_PKL, 
                       help='State file path')
    parser.add_argument('--interval', type=float, default=10.0, 
                       help='Polling interval in seconds')
    parser.add_argument('--reset', action='store_true', 
                       help='Reset state and start fresh')
    parser.add_argument('--run-once', action='store_true',
                       help='Run once and exit (for event-driven mode)')
    
    args = parser.parse_args()
    
    print("=== Trade State Monitor ===")
    print(f"Input file: {args.input}")
    print(f"Output file: {args.output}")
    print(f"State file: {args.state}")
    if not args.run_once:
        print(f"Interval: {args.interval}s")
    print(f"Reset: {args.reset}")
    print(f"Run once: {args.run_once}")
    print("=" * 30)
    
    try:
        if args.run_once:
            # Run once and exit (for watchdog approach)
            success = run_trade_state_once(
                input_file=args.input,
                output_file=args.output,
                state_file=args.state
            )
            print(f"🏁 Run completed with {'success' if success else 'errors'}")
            sys.exit(0 if success else 1)
        else:
            # Original continuous monitoring mode
            stream_trade_state_monitor(
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
    run_trade_state_once()