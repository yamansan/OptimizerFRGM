@echo off
echo Starting Continuous Fill Monitor with 5-second interval...
echo Press Ctrl+C to stop
echo.

python continuous_fill_monitor.py --interval 1

echo.
echo Continuous Fill Monitor stopped.
pause