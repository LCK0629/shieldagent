@echo off
REM ShieldAgent - Complete Setup & Run Script for Windows
REM This script installs everything and starts the dashboard

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ================================================================
echo.
echo           SHIELDAGENT - FRAUD DETECTION AI AGENT
echo.
echo ================================================================
echo.

REM Step 1: Create venv if needed
if not exist "venv" (
    echo [Step 1] Creating Python virtual environment...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo ERROR: Failed to create venv. Make sure Python 3.9+ is installed.
        pause
        exit /b 1
    )
)

REM Step 2: Activate venv
echo [Step 2] Activating virtual environment...
call venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo ERROR: Failed to activate venv.
    pause
    exit /b 1
)

REM Step 3: Install dependencies
echo [Step 3] Installing dependencies (this may take 2-3 minutes)...
pip install -q xgboost scikit-learn pandas numpy joblib streamlit streamlit-option-menu plotly matplotlib seaborn 2>nul

if !errorlevel! neq 0 (
    echo WARNING: Some packages may have failed to install
    echo Continuing anyway...
)

REM Step 4: Train model if not exists
if not exist "models\fraud_model.pkl" (
    echo.
    echo [Step 4] Training model on KDD Cup 99 dataset...
    echo          This is your FIRST run - training takes 1-2 minutes
    echo.
    python train.py --sample-size 50000

    if !errorlevel! neq 0 (
        echo ERROR: Model training failed
        pause
        exit /b 1
    )
) else (
    echo [Step 4] Model already trained - skipping (found fraud_model.pkl)
)

REM Step 5: Launch Streamlit
echo.
echo ================================================================
echo.
echo [Step 5] LAUNCHING DASHBOARD...
echo.
echo   Opening: http://localhost:8501
echo.
echo   Press Ctrl+C to stop
echo.
echo ================================================================
echo.

timeout /t 2

streamlit run streamlit_app.py

pause
