@echo off
echo ============================================================
echo Starting Complete Streaming LIFO System
echo ============================================================
echo.

cd /d "C:\Users\YamanSanghavi\Desktop\scenario_ladder_standalone"

echo [1/2] Starting Continuous Fill Monitor (Background)...
start /B python continuous_fill_monitor.py --interval 10 --quiet

echo [2/2] Starting LIFO PnL Monitor (Background)...
timeout /t 3 /nobreak >nul
start /B python lifo_pnl_monitor.py --start-time "2025-05-06 14:00:00" --output lifo_streaming.csv --interval 2

echo.
echo ============================================================
echo System Started Successfully!
echo ============================================================
echo.
echo LIVE FILES:
echo   Input:  data\output\ladder\continuous_fills.csv
echo   Output: lifo_streaming.csv
echo.
echo Both monitors are running in background.
echo Press any key to exit this window (monitors will keep running)
echo ============================================================
pause >nul 