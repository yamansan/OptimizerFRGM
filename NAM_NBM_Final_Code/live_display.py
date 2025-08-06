import pandas as pd
import time
import os
from datetime import datetime
from risk_utils import *

def create_html_display():
    """Create an HTML file that displays the latest values from Live_NBM_NAM.csv"""
    
    # Get the script directory to construct proper file paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "Live_NBM_NAM.csv")
    
    # Check if CSV file exists
    if not os.path.exists(csv_path):
        print("Live_NBM_NAM.csv not found. Make sure the live monitor is running.")
        return
    
    try:
        # Read the CSV and get the latest row
        df = pd.read_csv(csv_path)
        if len(df) == 0:
            print("No data found in CSV file.")
            return
        
        latest_row = df.iloc[-1]
        
        # Create HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Live ZN Trading Monitor</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        .timestamp {{
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        .price-info {{
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 30px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #007bff;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .positive {{
            color: #28a745;
        }}
        .negative {{
            color: #dc3545;
        }}
        .breakeven {{
            background-color: #fff3cd;
        }}
        .footer {{
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Live ZN Trading Monitor</h1>
        <div class="timestamp">Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data from: {latest_row['timestamp']}</div>
        <div class="price-info">Current Price: {decimal_to_zn(latest_row['current_price'])}</div>
        
        <div class="section">
            <h2>NBM - Dip Analysis</h2>
            <table>
                <tr>
                    <th>Breakeven (bps)</th>
                    <th>Dip (bps)</th>
                    <th>Percentile (%)</th>
                    <th>Remaining (bps)</th>
                    <th>Anchor Point</th>
                    <th>Price at 99% NBM</th>
                </tr>
                <tr class="breakeven">
                    <td>1</td>
                    <td>{latest_row['NBM_dip_bps_1']:.2f}</td>
                    <td>{latest_row['NBM_percentile_1']:.1f}</td>
                    <td>{latest_row['NBM_dips_remaining_1']:.2f}</td>
                    <td>{decimal_to_zn(latest_row['NBM_anchor_point_1'])}</td>
                    <td>{decimal_to_zn(latest_row['NBM_position_1'])}</td>
                </tr>
                <tr class="breakeven">
                    <td>1.5</td>
                    <td>{latest_row['NBM_dip_bps_1.5']:.2f}</td>
                    <td>{latest_row['NBM_percentile_1.5']:.1f}</td>
                    <td>{latest_row['NBM_dips_remaining_1.5']:.2f}</td>
                    <td>{decimal_to_zn(latest_row['NBM_anchor_point_1.5'])}</td>
                    <td>{decimal_to_zn(latest_row['NBM_position_1.5'])}</td>
                </tr>
                <tr class="breakeven">
                    <td>2</td>
                    <td>{latest_row['NBM_dip_bps_2']:.2f}</td>
                    <td>{latest_row['NBM_percentile_2']:.1f}</td>
                    <td>{latest_row['NBM_dips_remaining_2']:.2f}</td>
                    <td>{decimal_to_zn(latest_row['NBM_anchor_point_2'])}</td>
                    <td>{decimal_to_zn(latest_row['NBM_position_2'])}</td>
                </tr>
                <tr class="breakeven">
                    <td>2.5</td>
                    <td>{latest_row['NBM_dip_bps_2.5']:.2f}</td>
                    <td>{latest_row['NBM_percentile_2.5']:.1f}</td>
                    <td>{latest_row['NBM_dips_remaining_2.5']:.2f}</td>
                    <td>{decimal_to_zn(latest_row['NBM_anchor_point_2.5'])}</td>
                    <td>{decimal_to_zn(latest_row['NBM_position_2.5'])}</td>
                </tr>
                <tr class="breakeven">
                    <td>3</td>
                    <td>{latest_row['NBM_dip_bps_3']:.2f}</td>
                    <td>{latest_row['NBM_percentile_3']:.1f}</td>
                    <td>{latest_row['NBM_dips_remaining_3']:.2f}</td>
                    <td>{decimal_to_zn(latest_row['NBM_anchor_point_3'])}</td>
                    <td>{decimal_to_zn(latest_row['NBM_position_3'])}</td>
                </tr>
                <tr class="breakeven">
                    <td>4</td>
                    <td>{latest_row['NBM_dip_bps_4']:.2f}</td>
                    <td>{latest_row['NBM_percentile_4']:.1f}</td>
                    <td>{latest_row['NBM_dips_remaining_4']:.2f}</td>
                    <td>{decimal_to_zn(latest_row['NBM_anchor_point_4'])}</td>
                    <td>{decimal_to_zn(latest_row['NBM_position_4'])}</td>
                </tr>
                <tr class="breakeven">
                    <td>5</td>
                    <td>{latest_row['NBM_dip_bps_5']:.2f}</td>
                    <td>{latest_row['NBM_percentile_5']:.1f}</td>
                    <td>{latest_row['NBM_dips_remaining_5']:.2f}</td>
                    <td>{decimal_to_zn(latest_row['NBM_anchor_point_5'])}</td>
                    <td>{decimal_to_zn(latest_row['NBM_position_5'])}</td>
                </tr>
            </table>
        </div>
        
        <div class="section">
            <h2>NAM - Rise Analysis</h2>
            <table>
                <tr>
                    <th>Breakeven (bps)</th>
                    <th>Rise (bps)</th>
                    <th>Percentile (%)</th>
                    <th>Remaining (bps)</th>
                    <th>Anchor Point</th>
                    <th>Price at 99% NAM</th>
                </tr>
                                 <tr class="breakeven">
                     <td>1</td>
                     <td>{latest_row['NAM_rises_bps_1']:.2f}</td>
                     <td>{latest_row['NAM_percentile_1']:.1f}</td>
                     <td>{latest_row['NAM_rises_remaining_1']:.2f}</td>
                     <td>{decimal_to_zn(latest_row['NAM_anchor_point_1'])}</td>
                     <td>{decimal_to_zn(latest_row['NAM_position_1'])}</td>
                 </tr>
                                 <tr class="breakeven">
                     <td>1.5</td>
                     <td>{latest_row['NAM_rises_bps_1.5']:.2f}</td>
                     <td>{latest_row['NAM_percentile_1.5']:.1f}</td>
                     <td>{latest_row['NAM_rises_remaining_1.5']:.2f}</td>
                     <td>{decimal_to_zn(latest_row['NAM_anchor_point_1.5'])}</td>
                     <td>{decimal_to_zn(latest_row['NAM_position_1.5'])}</td>
                 </tr>
                                 <tr class="breakeven">
                     <td>2</td>
                     <td>{latest_row['NAM_rises_bps_2']:.2f}</td>
                     <td>{latest_row['NAM_percentile_2']:.1f}</td>
                     <td>{latest_row['NAM_rises_remaining_2']:.2f}</td>
                     <td>{decimal_to_zn(latest_row['NAM_anchor_point_2'])}</td>
                     <td>{decimal_to_zn(latest_row['NAM_position_2'])}</td>
                 </tr>
                                 <tr class="breakeven">
                     <td>2.5</td>
                     <td>{latest_row['NAM_rises_bps_2.5']:.2f}</td>
                     <td>{latest_row['NAM_percentile_2.5']:.1f}</td>
                     <td>{latest_row['NAM_rises_remaining_2.5']:.2f}</td>
                     <td>{decimal_to_zn(latest_row['NAM_anchor_point_2.5'])}</td>
                     <td>{decimal_to_zn(latest_row['NAM_position_2.5'])}</td>
                 </tr>
                                 <tr class="breakeven">
                     <td>3</td>
                     <td>{latest_row['NAM_rises_bps_3']:.2f}</td>
                     <td>{latest_row['NAM_percentile_3']:.1f}</td>
                     <td>{latest_row['NAM_rises_remaining_3']:.2f}</td>
                     <td>{decimal_to_zn(latest_row['NAM_anchor_point_3'])}</td>
                     <td>{decimal_to_zn(latest_row['NAM_position_3'])}</td>
                 </tr>
                 <tr class="breakeven">
                     <td>4</td>
                     <td>{latest_row['NAM_rises_bps_4']:.2f}</td>
                     <td>{latest_row['NAM_percentile_4']:.1f}</td>
                     <td>{latest_row['NAM_rises_remaining_4']:.2f}</td>
                     <td>{decimal_to_zn(latest_row['NAM_anchor_point_4'])}</td>
                     <td>{decimal_to_zn(latest_row['NAM_position_4'])}</td>
                 </tr>
                 <tr class="breakeven">
                     <td>5</td>
                     <td>{latest_row['NAM_rises_bps_5']:.2f}</td>
                     <td>{latest_row['NAM_percentile_5']:.1f}</td>
                     <td>{latest_row['NAM_rises_remaining_5']:.2f}</td>
                     <td>{decimal_to_zn(latest_row['NAM_anchor_point_5'])}</td>
                     <td>{decimal_to_zn(latest_row['NAM_position_5'])}</td>
                 </tr>
            </table>
        </div>
        
        <div class="footer">
            Auto-refreshes every 5 seconds | Data source: Live_NBM_NAM.csv
        </div>
    </div>
</body>
</html>
        """
        
        # Write HTML file to specified folder
        output_folder = r"Z:\LIVE NBM NAM"
        os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(output_folder, "live_display.html")
        with open(output_path, "w") as f:
            f.write(html_content)
        
        print(f"HTML display updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"Error creating HTML display: {e}")

def run_live_display():
    """Run the live display updater"""
    print("Starting live HTML display updater...")
    print(r"Open 'Z:\LIVE NBM NAM\live_display.html' in your browser to view live data.")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            create_html_display()
            time.sleep(5)  # Update every 5 seconds
    except KeyboardInterrupt:
        print("\nStopping live display updater.")

if __name__ == "__main__":
    run_live_display() 