@echo off
echo ============================================================
echo Clean Restart of Streaming System
echo ============================================================
echo.

echo [1] Stopping all Python processes...
taskkill /F /IM python.exe 2>nul
if %errorlevel% == 0 (
    echo Python processes stopped.
) else (
    echo No Python processes were running.
)
echo.

echo [2] Cleaning LIFO output file and state...
if exist lifo_streaming.csv (
    del lifo_streaming.csv
    echo Deleted old lifo_streaming.csv
) else (
    echo No existing lifo_streaming.csv found
)

if exist lifo_streaming_state.pkl (
    del lifo_streaming_state.pkl
    echo Deleted old lifo_streaming_state.pkl
) else (
    echo No existing lifo_streaming_state.pkl found
)
echo.

echo [3] Waiting 3 seconds for cleanup...
timeout /t 3 /nobreak >nul

cd /d "C:\Users\YamanSanghavi\Desktop\scenario_ladder_standalone"

echo [4] Starting Continuous Fill Monitor...
start /B python continuous_fill_monitor.py --interval 10 --quiet

echo [5] Waiting 5 seconds for fill monitor to initialize...
timeout /t 5 /nobreak >nul

echo [6] Starting LIFO PnL Monitor with reset...
start /B python lifo_pnl_monitor.py --start-time "2025-05-06 00:00:00" --output lifo_streaming.csv --interval 2 --reset

echo.
echo ============================================================
echo Clean restart completed!
echo ============================================================
echo.
echo System should be running cleanly now with fresh state.
echo Wait 30 seconds, then check lifo_streaming.csv for new data.
echo.
echo Press any key to exit...
pause >nul 