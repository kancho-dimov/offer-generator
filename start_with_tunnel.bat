@echo off
title Romstal - Offer Generator (with tunnel)
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo ==========================================
echo   Romstal Offer ^& Order Generator
echo   (with ngrok tunnel for iPhone)
echo ==========================================
echo.
echo Starting Streamlit + ngrok tunnel...
echo The tunnel URL will appear below - open it on your iPhone.
echo.
venv\Scripts\python.exe start_tunnel.py
pause
