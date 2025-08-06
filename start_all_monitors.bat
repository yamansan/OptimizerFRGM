@echo off
echo ============================================================
echo Starting All Trading Monitors (Normal Start)
echo ============================================================
echo.

cd /d "C:\Users\YamanSanghavi\Desktop\scenario_ladder_standalone"

echo [1/4] Starting Continuous Fill Monitor (Background)...
start /B python continuous_fill_monitor.py --interval 10 --quiet

echo [2/4] Starting LIFO PnL Monitor (Background)...
timeout /t 3 /nobreak >nul
start /B python lifo_pnl_monitor.py --start-time "2025-05-06 14:00:00" --output data/output/lifo_streaming.csv --interval 2

echo [3/4] Starting Net Position Monitor (Background)...
timeout /t 3 /nobreak >nul
start /B python net_position_monitor.py --interval 10

echo [4/4] Starting Trade State Monitor (Background)...
timeout /t 3 /nobreak >nul
start /B python Optimizer/Sumo_Curve/trade_state_monitor.py --interval 10

echo.
echo ============================================================
echo All monitors started successfully in background!
echo ============================================================
echo.
echo Running processes:
echo   - Continuous Fill Monitor (polling TT API every 10s)
echo   - LIFO PnL Monitor (processing fills every 2s)
echo   - Net Position Monitor (updating positions every 10s)
echo   - Trade State Monitor (tracking trade start/end events every 10s)
echo.
echo Output files:
echo   - data\output\ladder\continuous_fills.csv
echo   - data\output\lifo_streaming.csv
echo   - data\output\net_position_streaming.csv
echo   - data\output\trade_state_events.csv
echo.
echo All monitors are running in background.
echo Press Ctrl+C to stop all monitors, or close this window.
echo ============================================================

REM Keep the window open and show status
:loop
timeout /t 30 /nobreak >nul
echo [%date% %time%] Monitors still running... (Press Ctrl+C to stop)
goto loop 