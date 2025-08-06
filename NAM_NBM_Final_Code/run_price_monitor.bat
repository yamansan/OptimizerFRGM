@echo off
echo ========================================
echo    ZN Future Price Monitor
echo ========================================
echo.
echo Choose mode:
echo [1] Live monitoring (updates every 10 seconds)
echo [2] One-time merge
echo [3] Exit
echo.
set /p choice="Enter your choice (1-3): "

REM Change to the script directory
cd /d "C:\Users\YamanSanghavi\Desktop\NAM_NBM_Final_Code"

if "%choice%"=="1" (
    echo.
    echo Starting live price monitoring...
    echo Press Ctrl+C to stop the monitor
    echo.
    echo live | python Live_Price_Processing.py
) else if "%choice%"=="2" (
    echo.
    echo Running one-time merge...
    echo.
    echo once | python Live_Price_Processing.py
) else if "%choice%"=="3" (
    echo.
    echo Exiting...
    exit /b
) else (
    echo.
    echo Invalid choice. Please run the script again.
)

echo.
echo Script finished.
pause 