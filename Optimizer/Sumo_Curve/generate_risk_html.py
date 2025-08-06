import pickle
import sys
import os
import math
import time
from datetime import datetime
import argparse
# Add the workspace root to Python path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, workspace_root)

from Optimizer.risk_utils import zn_to_decimal
from config import RISK_VS_PRICE_HTML, RISK_TABLE_DATA_HTML

def generate_html_once():
    """Generate HTML file once from current pickle data."""
    try:
        # Read the risk_streaming.pkl file
        with open('data/output/risk_streaming.pkl', 'rb') as f:
            history = pickle.load(f)

        # Get the last row of the list
        latest_entry = history[-1]
        combined_dict = latest_entry['combined_dict']

        # Generate HTML content with JavaScript for instant updates
        html_content = f'''
<html>
<head>
    <title>Predicted Risk vs Price</title>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <style>
        table {{
            font-family: Arial, sans-serif;
            border-collapse: collapse;
            width: 70%;
            margin: 20px auto;
        }}
        th, td {{
            border: 1px solid #dddddd;
            text-align: left;
            padding: 8px;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        .timestamp {{
            text-align: center;
            font-size: 12px;
            color: #666;
            margin-top: 10px;
        }}
        .loading {{
            text-align: center;
            color: #666;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <h2 style="text-align: center;">Risk vs Price</h2>
    <div id="table-container">
        <div class="loading">Loading data...</div>
    </div>
    <div class="timestamp">Last updated: <span id="timestamp">Loading...</span></div>
    
    <script>
        function updateTable() {{
            const timestamp = Date.now();
            fetch('./risk_table_data.html?t=' + timestamp, {{
                cache: 'no-cache',
                headers: {{
                    'Cache-Control': 'no-cache'
                }}
            }})
            .then(response => {{
                if (!response.ok) {{
                    throw new Error('Network response was not ok');
                }}
                return response.text();
            }})
            .then(html => {{
                // Update table content directly
                document.getElementById('table-container').innerHTML = html;
                
                // Update timestamp
                const currentTime = new Date().toLocaleString();
                document.getElementById('timestamp').textContent = currentTime;
            }})
            .catch(error => {{
                console.error('Error updating table:', error);
                document.getElementById('table-container').innerHTML = '<div class="loading">Error loading data. Retrying...</div>';
            }});
        }}
        
        // Update every second
        setInterval(updateTable, 1000);
        
        // Initial load
        updateTable();
    </script>
</body>
</html>
'''

        # Sort prices in descending order using decimal conversion
        price_data_pairs = []
        for price, (delta_units, total_units, dv01, pnl_trade, pnl_breakeven) in combined_dict.items():
            decimal_price = zn_to_decimal(price)
            price_data_pairs.append((decimal_price, price, delta_units, total_units, dv01, pnl_trade, pnl_breakeven))

        # Sort by decimal price in descending order
        price_data_pairs.sort(key=lambda x: x[0], reverse=True)

        # Generate the complete table HTML for JavaScript to fetch
        table_html = '''
        <table>
            <thead>
                <tr>
                    <th>Price</th>
                    <th>Delta Units</th>
                    <th>Total Units</th>
                    <th>DV01</th>
                    <th>PnL_Trade</th>
                    <th>PnL Breakeven</th>
                </tr>
            </thead>
            <tbody>
'''
        
        # Add rows to the table HTML
        for decimal_price, price, delta_units, total_units, dv01, pnl_trade, pnl_breakeven in price_data_pairs:
            # Round units to integers
            delta_units_rounded = int(round(delta_units))
            total_units_rounded = int(round(total_units))
            table_html += f'            <tr><td>{price}</td><td>{delta_units_rounded}</td><td>{total_units_rounded}</td><td>{dv01:.1f}</td><td>{pnl_trade:.1f}</td><td>{pnl_breakeven:.1f}</td></tr>\n'

        # Close the table HTML
        table_html += '''
            </tbody>
        </table>
'''
        
        # Close the main HTML content
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        html_content += f'''
    </div>
    <div class="timestamp">Last updated: {current_time}</div>
</body>
</html>
'''

        # Write the main HTML file (with JavaScript)
        with open(RISK_VS_PRICE_HTML, 'w') as file:
            file.write(html_content)
            file.flush()  # Force write to disk
            os.fsync(file.fileno())  # Force sync to disk

        # Write the table data file (for JavaScript to fetch) - use relative path
        with open(RISK_TABLE_DATA_HTML, 'w') as file:
            file.write(table_html)
            file.flush()  # Force write to disk
            os.fsync(file.fileno())  # Force sync to disk

        print(f"HTML files updated successfully at {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"Error generating HTML: {e}")

def run_continuous_html_generation(interval_seconds: int = 5):
    """Run HTML generation continuously every interval_seconds."""
    print("Starting continuous HTML generation...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            generate_html_once()
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\nStopping HTML generation...")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Risk HTML generation')
    parser.add_argument('--run-once', action='store_true', 
                       help='Run once and exit (for watchdog integration)')
    parser.add_argument('--interval', type=int, default=5,
                       help='Interval in seconds for continuous mode (default: 5)')
    
    args = parser.parse_args()
    
    if args.run_once:
        generate_html_once()
    else:
        run_continuous_html_generation(args.interval)