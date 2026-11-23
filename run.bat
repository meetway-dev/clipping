@echo off
title ClipForge AI Studio - 100%% Free Local Podcast Clipper
echo ========================================================
echo        ClipForge AI - Viral Video Studio
echo ========================================================
echo.
echo [*] Checking Python environment...
python --version
echo.
echo [*] Launching ClipForge Studio Web Application...
echo [*] Opening at http://localhost:8000
echo.
start http://localhost:8000
python app.py
pause
