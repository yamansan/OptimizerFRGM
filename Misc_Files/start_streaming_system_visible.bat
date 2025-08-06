@echo off
echo ============================================================
echo Starting Complete Streaming LIFO System (Visible Windows)
echo ============================================================
echo.

cd /d "C:\Users\YamanSanghavi\Desktop\scenario_ladder_standalone"

echo [1/2] Opening Continuous Fill Monitor in new window...
start "Fill Monitor" cmd /k "python continuous_fill_monitor.py --interval 10"

echo [2/2] Opening LIFO PnL Monitor in new window...
timeout /t 3 /nobreak >nul
start "LIFO PnL Monitor" cmd /k "python lifo_pnl_monitor.py --start-time ""2025-05-06 14:00:00"" --output lifo_streaming.csv --interval 2"

echo.
echo ============================================================
echo System Started Successfully!
echo ============================================================
echo.
echo Two windows opened:
echo   1. "Fill Monitor" - Live trade collection
echo   2. "LIFO PnL Monitor" - Real-time PnL calculation
echo.
echo LIVE FILES:
echo   Input:  data\output\ladder\continuous_fills.csv
echo   Output: lifo_streaming.csv
echo.
echo Close each window individually to stop the monitors.
echo Press any key to exit this launcher window.
echo ============================================================
pause >nul 