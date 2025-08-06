import sys
import os
# Add the workspace root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
from datetime import datetime, time, timedelta

def calculate_intraday_pnl():
    """
    Calculate intraday PnL for Eric's CME ZN Sep25 trades.
    Intraday period: 3 PM day n-1 to 3 PM day n
    """
    
    # Read the CSV file
    df = pd.read_csv('data/output/ladder/continuous_fills.csv')
    
    # Filter for CME, Eric, ZN Sep25
    filtered_df = df[
        (df['Exchange'] == 'CME') &
        (df['CurrentUser'] == 'Eric') &
        (df['Contract'] == 'ZN Sep25')
    ].copy()
    
    if filtered_df.empty:
        print('No matching trades found for CME, Eric, ZN Sep25')
        return
    
    print(f'Found {len(filtered_df)} matching trades')
    
    # Convert Date and Time to datetime
    filtered_df['DateTime'] = pd.to_datetime(filtered_df['Date'] + ' ' + filtered_df['Time'])
    
    # Sort by datetime
    filtered_df = filtered_df.sort_values('DateTime')
    
    # Define signed quantity: BUY = +, SELL = -
    filtered_df['SignedQuantity'] = filtered_df.apply(
        lambda row: row['Quantity'] if row['SideName'] == 'BUY' else -row['Quantity'], 
        axis=1
    )
    
    # Group trades by intraday periods (3 PM to 3 PM next day)
    results = []
    
    for _, trade in filtered_df.iterrows():
        trade_date = trade['DateTime'].date()
        trade_time = trade['DateTime'].time()
        
        # Determine intraday period
        if trade_time >= time(15, 0):  # 3 PM or later
            period_start = datetime.combine(trade_date, time(15, 0))
            period_end = datetime.combine(trade_date + timedelta(days=1), time(15, 0))
        else:  # Before 3 PM
            period_start = datetime.combine(trade_date - timedelta(days=1), time(15, 0))
            period_end = datetime.combine(trade_date, time(15, 0))
        
        period_name = f'{period_start.strftime("%Y-%m-%d")} 3PM to {period_end.strftime("%Y-%m-%d")} 3PM'
        
        results.append({
            'Period': period_name,
            'DateTime': trade['DateTime'],
            'Side': trade['SideName'],
            'Quantity': trade['Quantity'],
            'SignedQuantity': trade['SignedQuantity'],
            'Price': trade['Price'],
            'OrderId': trade['OrderId']
        })
    
    # Convert to DataFrame for analysis
    results_df = pd.DataFrame(results)
    
    # Calculate PnL by period
    pnl_by_period = {}
    
    for period in results_df['Period'].unique():
        period_trades = results_df[results_df['Period'] == period]
        
        # Calculate cumulative position and PnL
        cumulative_position = 0
        cumulative_cost = 0
        period_pnl = 0
        
        for _, trade in period_trades.iterrows():
            signed_qty = trade['SignedQuantity']
            price = trade['Price']
            
            if cumulative_position == 0:
                # Opening position
                cumulative_position = signed_qty
                cumulative_cost = signed_qty * price
            elif (cumulative_position > 0 and signed_qty > 0) or (cumulative_position < 0 and signed_qty < 0):
                # Adding to position
                cumulative_cost += signed_qty * price
                cumulative_position += signed_qty
            else:
                # Reducing or reversing position
                if abs(signed_qty) <= abs(cumulative_position):
                    # Partial close
                    avg_cost = cumulative_cost / cumulative_position
                    realized_pnl = -signed_qty * (price - avg_cost)
                    period_pnl += realized_pnl
                    
                    cumulative_position += signed_qty
                    cumulative_cost = cumulative_position * avg_cost if cumulative_position != 0 else 0
                else:
                    # Full close and reverse
                    avg_cost = cumulative_cost / cumulative_position
                    realized_pnl = -cumulative_position * (price - avg_cost)
                    period_pnl += realized_pnl
                    
                    # New position in opposite direction
                    remaining_qty = signed_qty + cumulative_position
                    cumulative_position = remaining_qty
                    cumulative_cost = remaining_qty * price
        
        pnl_by_period[period] = {
            'total_pnl': period_pnl,
            'final_position': cumulative_position,
            'trades_count': len(period_trades),
            'trades': period_trades.to_dict('records')
        }
    
    # Print results
    print('\n=== INTRADAY PnL CALCULATION ===')
    print('Filter: Exchange=CME, User=Eric, Contract=ZN Sep25')
    print()
    
    total_pnl = 0
    for period, data in pnl_by_period.items():
        print(f'Period: {period}')
        print(f'  Trades: {data["trades_count"]}')
        print(f'  Final Position: {data["final_position"]}')
        print(f'  Period PnL: {data["total_pnl"]:.4f}')
        print()
        
        total_pnl += data['total_pnl']
        
        # Show trade details
        for trade in data['trades']:
            print(f'    {trade["DateTime"]} | {trade["Side"]} {trade["Quantity"]} @ {trade["Price"]}')
        print()
    
    print(f'TOTAL PnL ACROSS ALL PERIODS: {total_pnl:.4f}')

if __name__ == '__main__':
    calculate_intraday_pnl()
