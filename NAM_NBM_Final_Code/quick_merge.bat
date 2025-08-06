@echo off
echo ========================================
echo    Quick Price Merge
echo ========================================
echo.
echo Running one-time price merge...
echo.

REM Change to the script directory
cd /d "C:\Users\YamanSanghavi\Desktop\NAM_NBM_Final_Code"

REM Run one-time merge
echo once | python Live_Price_Processing.py

echo.
echo Merge complete! Check Live_ZN_Prices.csv for results.
pause 