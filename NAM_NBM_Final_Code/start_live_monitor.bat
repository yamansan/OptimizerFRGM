@echo off
echo ========================================
echo    ZN Future Live Price Monitor
echo ========================================
echo.
echo Starting live price monitoring...
echo Press Ctrl+C to stop the monitor
echo.

REM Change to the script directory
cd /d "C:\Users\YamanSanghavi\Desktop\NAM_NBM_Final_Code"

REM Run the live monitor automatically
echo live | python Live_Price_Processing.py

REM Pause if there's an error or the script stops
echo.
echo Live monitor stopped.
pause 