import pandas as pd
import numpy as np
from datetime import datetime
import time
import os
from pathlib import Path

def read_trading_view_data(file_path=None):
    if file_path is None:
        import glob
        folder_path = os.path.join(os.path.dirname(__file__), "Price_Tradingview")
        files = glob.glob(f"{folder_path}/*")
        if not files:
            raise FileNotFoundError(f"No files found in {folder_path} folder")
        if len(files) > 1:
            print(f"Warning: Multiple files found in {folder_path}, using: {files[0]}")
        file_path = files[0]
    """Read Trading View data and convert timezone to EST"""
    df = pd.read_csv(file_path)
    
    # Convert time column to datetime with timezone info
    df['time'] = pd.to_datetime(df['time'])
    
    # Convert from original timezone to EST (Eastern Standard Time)
    # The original data has -04:00 which is EDT, convert to EST
    df['timestamp'] = df['time'].dt.tz_convert('US/Eastern').dt.tz_localize(None)
    df['price'] = df['close']
    # Keep only necessary columns and rename close to Close
    df = df[['timestamp', 'price']].copy()    
    return df

def read_archive_data(file_path="Z:/Archive/price_log.csv"):
    try:
        df = pd.read_csv(file_path)
        df = df[df['price'] != df['price'].shift()]
        df['price'] = pd.to_numeric(df['price'], errors='coerce')

        # Drop rows where conversion failed (i.e., was non-numeric)
        df = df.dropna(subset=['price'])

        # Optional: convert column to float explicitly (ensures dtype)
        df['price'] = df['price'].astype(float)
        # Convert timestamp from CDT to datetime
        # First convert to datetime without timezone info
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Check if timestamp is already timezone-aware
        if df['timestamp'].dt.tz is None:
            # Timezone-naive: localize to CDT and convert to Eastern time
            df['timestamp'] = df['timestamp'].dt.tz_localize('US/Central').dt.tz_convert('US/Eastern').dt.tz_localize(None)
        else:
            # Already timezone-aware: just convert to Eastern time and remove timezone info
            df['timestamp'] = df['timestamp'].dt.tz_convert('US/Eastern').dt.tz_localize(None)
                
        # Keep only necessary columns
        df = df[['timestamp', 'price']].copy()
        df['price'] = df['price'].astype(float)
        
        return df
    except FileNotFoundError:
        print(f"Archive file not found: {file_path}")
        return pd.DataFrame({'timestamp': [], 'price': []})
    except Exception as e:
        print(f"Error reading archive file: {e}")
        return pd.DataFrame({'timestamp': [], 'price': []})

def merge_price_data(trading_view_df, archive_df):
    """Merge trading view and archive data, prioritizing more recent data"""
    
    # Work with a copy to avoid modifying the original DataFrame
    trading_view_copy = trading_view_df.copy()
    
    # If no archive data, just return trading view data
    if archive_df.empty:
        # Check if timestamp is already string format
        if trading_view_copy['timestamp'].dtype == 'object':
            return trading_view_copy
        else:
            trading_view_copy['timestamp'] = trading_view_copy['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            return trading_view_copy
    
    # Find the latest timestamp in trading view data
    latest_trading_view_time = trading_view_copy['timestamp'].max()
    
    # Filter archive data to only include timestamps after the latest trading view timestamp
    filtered_archive_df = archive_df[archive_df['timestamp'] > latest_trading_view_time].copy()
    
    # Combine both dataframes
    combined_df = pd.concat([trading_view_copy, filtered_archive_df], ignore_index=True)
    
    # Sort by timestamp
    combined_df = combined_df.sort_values('timestamp')
    
    # Convert timestamp to the desired format (YYYY-MM-DD HH:MM:SS) only if it's not already string
    if combined_df['timestamp'].dtype != 'object':
        combined_df['timestamp'] = combined_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    combined_df = combined_df.rename(columns={'price': 'Close'})
    return combined_df

def create_live_csv(output_file="Live_ZN_Prices.csv", update_interval=10):
    """Create and continuously update a live CSV with merged price data"""
    
    # Make output file path relative to script location
    if not os.path.isabs(output_file):
        output_file = os.path.join(os.path.dirname(__file__), output_file)
    
    print(f"Starting live price processing...")
    print(f"Output file: {os.path.abspath(output_file)}")
    print(f"Update interval: {update_interval} seconds")
    
    # Read initial trading view data
    trading_view_df = read_trading_view_data()
    print(f"Loaded {len(trading_view_df)} rows from Trading View data")
    
    iteration = 0
    while True:
        try:
            iteration += 1
            print(f"\nIteration {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Read current archive data
            archive_df = read_archive_data()
            print(f"Loaded {len(archive_df)} rows from archive data")
            
            # Merge the data
            merged_df = merge_price_data(trading_view_df, archive_df)
            print(f"Merged data contains {len(merged_df)} rows")
            
            # Save to CSV
            merged_df.to_csv(output_file, index=False)
            print(f"Updated {output_file} with latest data")
            print(f"File exists: {os.path.exists(output_file)}")
            print(f"File size: {os.path.getsize(output_file) if os.path.exists(output_file) else 0} bytes")
            
            # Show latest prices
            if not merged_df.empty:
                latest_rows = merged_df.tail(5)
                print("Latest 5 prices:")
                print(latest_rows.to_string(index=False))
            
            # Wait before next update
            time.sleep(update_interval)
            
        except KeyboardInterrupt:
            print("\nStopping live price processing...")
            break
        except Exception as e:
            print(f"Error in iteration {iteration}: {e}")
            time.sleep(update_interval)

def run_once():
    """Run the merge once without continuous updating"""
    print("Running one-time merge...")
    
    # Read both datasets
    trading_view_df = read_trading_view_data()
    archive_df = read_archive_data()
    
    # Merge the data
    merged_df = merge_price_data(trading_view_df, archive_df)
    
    # Save to CSV with path relative to script location
    output_file = os.path.join(os.path.dirname(__file__), "Live_ZN_Prices.csv")
    merged_df.to_csv(output_file, index=False)
    
    print(f"Merged data saved to {os.path.abspath(output_file)}")
    print(f"Total rows: {len(merged_df)}")
    
    if not merged_df.empty:
        print("\nFirst 5 rows:")
        print(merged_df.head().to_string(index=False))
        print("\nLast 5 rows:")
        print(merged_df.tail().to_string(index=False))
    
    return merged_df

if __name__ == "__main__":
    # Choose mode
    mode = input("Enter 'live' for continuous updates or 'once' for one-time merge: ").strip().lower()
    
    if mode == 'live':
        create_live_csv()
    else:
        run_once()

