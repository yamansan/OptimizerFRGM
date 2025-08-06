# Live ZN Trading Display

This is a simple HTML-based display system for monitoring live ZN trading data.

## How to Use

### Method 1: Using the Batch File (Recommended)
1. Double-click `start_live_display.bat`
2. Open `live_display.html` in your web browser
3. The page will auto-refresh every 5 seconds showing the latest data

### Method 2: Using Python Directly
1. Run: `python live_display.py`
2. Open `live_display.html` in your web browser
3. The page will auto-refresh every 5 seconds showing the latest data

## What It Shows

The display shows:
- **Current Price**: Latest ZN price
- **NBM (New Breakout Move)**: Dip analysis for 3, 4, and 5 bps breakeven levels
- **NAM (New Advance Move)**: Rise analysis for 3, 4, and 5 bps breakeven levels

For each breakeven level, you can see:
- Current dip/rise in basis points
- Percentile (how this compares to historical data)
- Remaining points until target (25 bps)
- Anchor point price

## Important Notes

- This system reads from `Live_NBM_NAM.csv` and does NOT interfere with the live data collection
- The HTML file auto-refreshes every 5 seconds
- Keep the Python script running to update the HTML file
- You can have multiple browsers open to the same HTML file
- Press Ctrl+C to stop the display updater

## Troubleshooting

- If you see "Live_NBM_NAM.csv not found", make sure your live monitor is running
- If the HTML file doesn't exist, run the Python script first
- If data looks stale, check that the Python script is still running 