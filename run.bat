@echo off
setlocal
cd /d "%~dp0"

echo ===================================================================
echo   SIF Sentinel - Starting Automated Launch (Windows)
echo ===================================================================

:: Verify Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python was not found in your PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo and ensure "Add Python to PATH" is checked during installation.
    echo.
    pause
    exit /b 1
)

:: Run the universal orchestrator
python run.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] SIF Sentinel encountered an error.
    pause
    exit /b %errorlevel%
)

