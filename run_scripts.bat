@echo off

REM Start risk_stream.py in background
start /B python Optimizer\Sumo_Curve\risk_stream.py

REM Wait a moment for risk_stream.py to generate some data
timeout /t 5 /nobreak

REM Run generate_risk_html.py once to create initial HTML
python generate_risk_html.py

REM Run generate_risk_html.py every 10 seconds to update the HTML
:loop
timeout /t 10 /nobreak
python generate_risk_html.py
goto loop 