@echo off
echo ========================================
echo    Starting All Live ZN Systems
echo ========================================
echo.

REM Change to the script directory
cd /d "C:\Users\YamanSanghavi\Desktop\scenario_ladder_standalone - Yaman\NAM_NBM_Final_Code"

echo [1/3] Starting Live Price Updates...
start /B cmd /c "echo live | python Live_Price_Processing.py"

REM Wait 3 seconds for Live_Price_Processing.py to create the CSV file
timeout /t 3 /nobreak >nul

echo [2/3] Starting Live NBM NAM Monitor...
start /B python live_monitor.py

echo [3/3] Starting Live HTML Display...
start /B python live_display.py

echo.
echo ========================================
echo    All Systems Started Successfully!
echo ========================================
echo.
echo Live systems are now running in background:
echo - Live Price Updates (Live_ZN_Prices.csv)
echo - NBM NAM Monitor (Live_NBM_NAM.csv)
echo - HTML Display (Z:\LIVE NBM NAM\live_display.html)
echo.
echo Open the HTML file in your browser to view live data.
echo.
echo Press any key to stop all systems...
pause >nul

echo.
echo Stopping all live systems...
taskkill /F /IM python.exe >nul 2>&1
echo All systems stopped.
pause 