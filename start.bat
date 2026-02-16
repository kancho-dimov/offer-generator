@echo off
title Romstal - Offer ^& Order Generator
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
echo ==========================================
echo   Romstal Offer ^& Order Generator
echo ==========================================
echo.
echo Local: http://localhost:8501
echo.
venv\Scripts\streamlit.exe run app.py
pause
