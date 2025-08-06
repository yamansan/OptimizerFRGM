@echo off
echo ============================================================
echo FRESH RESTART - All Trading Monitors
echo ============================================================
echo.
echo WARNING: This will delete all existing state and start fresh!
echo.

set /p confirm="Are you sure you want to restart everything fresh? (y/N): "
if /i not "%confirm%"=="y" (
    echo Operation cancelled.
    pause
    exit /b
)

cd /d "C:\Users\YamanSanghavi\Desktop\scenario_ladder_standalone - Yaman"

echo.
echo [CLEANUP] Stopping all Python processes...
taskkill /F /IM python.exe 2>nul
if %errorlevel% == 0 (
    echo Python processes stopped.
) else (
    echo No Python processes were running.
)

echo.
echo [CLEANUP] Deleting state files and outputs...

REM Delete LIFO state and output
if exist data\output\lifo_streaming.csv (
    del data\output\lifo_streaming.csv
    echo Deleted lifo_streaming.csv
)
if exist data\output\lifo_streaming_state.pkl (
    del data\output\lifo_streaming_state.pkl
    echo Deleted lifo_streaming_state.pkl
)

REM Delete net position state and output
if exist data\output\net_position_streaming.csv (
    del data\output\net_position_streaming.csv
    echo Deleted net_position_streaming.csv
)
if exist data\output\net_position_state.pkl (
    del data\output\net_position_state.pkl
    echo Deleted net_position_state.pkl
)

REM Delete trade state monitor state and output
if exist data\output\trade_state_events.csv (
    del data\output\trade_state_events.csv
    echo Deleted trade_state_events.csv
)
if exist data\output\trade_state_monitor_state.pkl (
    del data\output\trade_state_monitor_state.pkl
    echo Deleted trade_state_monitor_state.pkl
)

REM Delete continuous fills (this will force fresh download from TT)
if exist data\output\ladder\continuous_fills.csv (
    del data\output\ladder\continuous_fills.csv
    echo Deleted continuous_fills.csv (will be recreated from TT API)
)

echo.
echo [RESTART] Starting all monitors fresh in background...
timeout /t 3 /nobreak >nul

echo [1/4] Starting Continuous Fill Monitor (fresh, background)...
start /B python continuous_fill_monitor.py --interval 10 --quiet

echo [2/4] Starting LIFO PnL Monitor (reset, background)...
timeout /t 5 /nobreak >nul
start /B python lifo_pnl_monitor.py --start-time "2025-05-06 00:00:00" --output data/output/lifo_streaming.csv --interval 2 --reset

echo [3/4] Starting Net Position Monitor (reset, background)...
timeout /t 3 /nobreak >nul
start /B python net_position_monitor.py --interval 10 --reset

echo [4/6] Starting Trade State Monitor (reset, background)...
timeout /t 3 /nobreak >nul
start /B python Optimizer/Sumo_Curve/trade_state_monitor.py --interval 10 --reset

echo [5/6] Starting Risk Stream Monitor (background)...
timeout /t 5 /nobreak >nul
start /B python Optimizer/Sumo_Curve/risk_stream.py

echo [6/6] Starting HTML Generator (background)...
timeout /t 3 /nobreak >nul
start /B python Optimizer/Sumo_Curve/generate_risk_html.py

echo.
echo ============================================================
echo Fresh restart completed!
echo ============================================================
echo.
echo All systems restarted with clean state:
echo   - Continuous fills downloading fresh from TT API
echo   - LIFO calculations starting from beginning
echo   - Net position starting from zero
echo   - Trade state tracking starting fresh
echo   - Risk calculations streaming
echo   - HTML risk table generating
echo.
echo Output files:
echo   - data\output\ladder\continuous_fills.csv
echo   - data\output\lifo_streaming.csv  
echo   - data\output\net_position_streaming.csv
echo   - data\output\trade_state_events.csv
echo   - data\output\risk_streaming.pkl
echo   - Z:\LIVE NBM NAM\risk_vs_price.html
echo.
echo All monitors running in background.
echo Press Ctrl+C to stop all monitors, or close this window.
echo ============================================================

REM Keep the window open and show status
:loop
timeout /t 30 /nobreak >nul
echo [%date% %time%] Monitors still running... (Press Ctrl+C to stop)
goto loop 