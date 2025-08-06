import pandas as pd
import os
from datetime import datetime
from config import LIVE_PRICE_PATH, NET_POSITION_STREAMING_CSV
def get_current_price():
    """
    Get the current price from the last row of price_log.csv
    
    Returns:
        float: Current price as float
    """
    try:
        price_file = LIVE_PRICE_PATH
        
        # Check if file exists
        if not os.path.exists(price_file):
            print(f"Warning: Price file not found at {price_file}")
            print("Using default price of 111.0")
            return 111.0
        
        # Read the price log file
        price_df = pd.read_csv(price_file)
        
        # Get the last row's price (assuming price is in a column named 'Price' or similar)
        # You may need to adjust the column name based on actual file structure
        if 'Price' in price_df.columns:
            current_price = float(price_df.iloc[-1]['Price'])
        elif 'price' in price_df.columns:
            current_price = float(price_df.iloc[-1]['price'])
        else:
            # If column name is unknown, take the last column's last value
            current_price = float(price_df.iloc[-1, -1])
        
        print(f"Current price from {price_file}: {current_price}")
        return current_price
        
    except Exception as e:
        print(f"Error reading price file: {e}")
        print("Using default price of 111.0")
        return 111.0

def calculate_total_pnl():
    """
    Calculate total PnL using formula: sum(Q_i * (current_price - P_i))
    where Q_i is signed quantity and P_i is the transaction price
    
    Returns:
        float: Total PnL
    """
    try:
        # Read the net position streaming data
        net_position_file = NET_POSITION_STREAMING_CSV
        
        if not os.path.exists(net_position_file):
            print(f"Error: File not found: {net_position_file}")
            return 0.0
        
        df = pd.read_csv(net_position_file)
        
        # Get current price
        current_price = get_current_price()
        
        # Calculate PnL for each transaction
        total_pnl = 0.0
        pnl_details = []
        
        print("\n" + "="*80)
        print("PnL CALCULATION DETAILS")
        print("="*80)
        print(f"Current Price: {current_price}")
        print(f"Formula: PnL = Q_i * (Current_Price - P_i)")
        print("-"*80)
        print(f"{'Date':<12} {'Time':<12} {'Side':<4} {'Qty':<6} {'Price':<10} {'PnL':<10}")
        print("-"*80)
        
        for index, row in df.iterrows():
            # Extract values
            signed_qty = float(row['SignedQuantity'])  # Q_i
            transaction_price = float(row['Price'])     # P_i
            date = row['Date']
            time = row['Time']
            side = row['SideName']
            
            # Calculate PnL for this transaction: Q_i * (current_price - P_i)
            transaction_pnl = signed_qty * (current_price - transaction_price)*1000
            total_pnl += transaction_pnl
            
            # Store details for display
            pnl_details.append({
                'date': date,
                'time': time,
                'side': side,
                'signed_qty': signed_qty,
                'price': transaction_price,
                'pnl': transaction_pnl
            })
            
            # Print transaction details
            print(f"{date:<12} {time[:8]:<12} {side:<4} {signed_qty:>6.1f} {transaction_price:>10.6f} {transaction_pnl:>10.2f}")
        
        print("-"*80)
        print(f"TOTAL PnL: ${total_pnl:.2f}")
        print("="*80)
        
        return total_pnl
        
    except Exception as e:
        print(f"Error calculating PnL: {e}")
        return 0.0

def main():
    """
    Main function to calculate and display total PnL
    """
    print("PnL Calculator")
    print("Formula: Total PnL = Σ Q_i * (Current_Price - P_i)")
    print("Where:")
    print("  Q_i = Signed Quantity (positive for BUY, negative for SELL)")
    print("  P_i = Transaction Price")
    print("  Current_Price = Latest price from price_log.csv")
    
    total_pnl = calculate_total_pnl()
    
    print(f"\n📊 FINAL RESULT:")
    print(f"💰 Total PnL: ${total_pnl:.2f}")
    
    if total_pnl > 0:
        print("✅ Profitable position")
    elif total_pnl < 0:
        print("❌ Loss position")
    else:
        print("➖ Break-even position")

if __name__ == "__main__":
    main() 