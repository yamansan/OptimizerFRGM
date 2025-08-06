import pandas as pd
import time
import os
import sys
from datetime import datetime
from Optimizer.risk_utils import *
# Add path for TT API imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
from config import NET_POSITION_STREAMING_CSV, LIVE_PRICE_PATH

# Import TT API functionality from position_monitor
try:
    from trading.tt_api import (
        TTTokenManager, 
        TT_API_KEY, TT_API_SECRET, TT_SIM_API_KEY, TT_SIM_API_SECRET,
        APP_NAME, COMPANY_NAME, ENVIRONMENT, TOKEN_FILE
    )
    from position_monitor import get_positions, get_instrument_info, get_market_name
    TT_API_AVAILABLE = True
except ImportError as e:
    print(f"TT API not available: {e}")
    TT_API_AVAILABLE = False

def read_net_position_data():
    """Read the required columns from net_position_streaming.csv"""
    try:
        df = pd.read_csv(NET_POSITION_STREAMING_CSV)
        return df[['Date', 'Time', 'Price', 'SignedQuantity', 'NetPosition']]
    except Exception as e:
        print(f"Error reading net position data: {e}")
        return pd.DataFrame()

def get_current_price():
    """Get the last price from Z:/Archive/price_log.csv"""
    try:
        df = pd.read_csv(LIVE_PRICE_PATH)
        # Get the last row
        last_row = df.iloc[-1]
        
        # Convert the last row to a dictionary
        last_row_dict = last_row.to_dict()
        
        current_price = last_row_dict["price"]

        if isinstance(current_price, str):
            current_price = decimal_to_zn(float(current_price))

        return current_price

    except Exception as e:
        print(f"Error reading archive price data: {e}")
    return "N/A"

def get_live_pnl_from_tt():
    """Get live P&L from TT API for ZN Sep25 position."""
    if not TT_API_AVAILABLE:
        return 0.0
    
    try:
        # Initialize token manager
        token_manager = TTTokenManager(
            api_key=TT_SIM_API_KEY if ENVIRONMENT == "SIM" else TT_API_KEY,
            api_secret=TT_SIM_API_SECRET if ENVIRONMENT == "SIM" else TT_API_SECRET,
            app_name=APP_NAME,
            company_name=COMPANY_NAME,
            environment=ENVIRONMENT,
            token_file_base=TOKEN_FILE
        )
        
        # Get positions
        positions_data = get_positions(token_manager)
        if not positions_data or positions_data.get('status') != 'Ok':
            return 0.0
        
        positions = positions_data.get('positions', [])
        
        # Find ZN Sep25 position
        for position in positions:
            instrument_id = position.get('instrumentId', '')
            if instrument_id:
                instrument_info = get_instrument_info(instrument_id, token_manager)
                market_id = instrument_info.get('marketId')
                if market_id:
                    market_name = get_market_name(market_id, token_manager)
                    contract_name = instrument_info.get('alias', 'Unknown')
                    
                    # Check if this is ZN Sep25 and CME market
                    if market_name == 'CME' and ('ZN Sep25' in contract_name or 'ZN Sep 25' in contract_name):
                        pnl = position.get('pnl', 0)
                        print(f"Found ZN Sep25 P&L: {pnl}")
                        return pnl
        
        print("ZN Sep25 position not found")
        return 0.0
        
    except Exception as e:
        print(f"Error getting live P&L: {e}")
        return 0.0

def generate_html(position_data, current_price, live_pnl):
    """Generate HTML content with the position table, current price, and P&L"""
    
    # Create table rows
    table_rows = ""
    for _, row in position_data.iterrows():
        table_rows += f"""
        <tr>
            <td>{row['Date']}</td>
            <td>{row['Time']}</td>
            <td>{decimal_to_zn(row['Price'])}</td>
            <td>{row['SignedQuantity']}</td>
            <td>{row['NetPosition']}</td>
        </tr>"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live Position Monitor</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header-container {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
            .price-header, .pnl-header {{ background-color: #f0f8ff; padding: 15px; text-align: center; border-radius: 5px; width: 48%; }}
            .pnl-header {{ background-color: {('#e8f5e8' if live_pnl >= 0 else '#ffe8e8')}; }}
            .price-value, .pnl-value {{ font-size: 24px; font-weight: bold; color: #2c5aa0; }}
            .pnl-value {{ color: {('#2e8b57' if live_pnl >= 0 else '#dc143c')}; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .update-time {{ text-align: right; font-style: italic; color: #666; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="header-container">
            <div class="price-header">
                <div>Current Price</div>
                <div class="price-value">{current_price}</div>
            </div>
            <div class="pnl-header">
                <div>Live P&L (ZN Sep25)</div>
                <div class="pnl-value">${live_pnl:.2f}</div>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Price</th>
                    <th>Quantity Bought/Sold</th>
                    <th>Net Position</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        
        <div class="update-time">
            Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </body>
    </html>
    """
    return html_content

def save_html(html_content, output_path):
    """Save HTML content to file, creating directory if needed"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        print(f"HTML updated successfully at {datetime.now().strftime('%H:%M:%S')}")
    except Exception as e:
        print(f"Error saving HTML: {e}")

def main():
    output_path = r"Z:\LIVE NBM NAM\live_positions.html"
    
    print("Starting Live Position HTML Generator...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            # Read data
            position_data = read_net_position_data()
            current_price = get_current_price()
            live_pnl = get_live_pnl_from_tt() # Get live P&L
            
            # Generate and save HTML
            if not position_data.empty:
                html_content = generate_html(position_data, current_price, live_pnl)
                save_html(html_content, output_path)
            else:
                print("No position data available")
            
            # Wait 5 seconds
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nStopping HTML generator...")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main() 