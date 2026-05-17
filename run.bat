@echo off
REM ShieldAgent quick launcher (Windows)

setlocal enabledelayedexpansion

echo.
echo 🛡️  ShieldAgent Launcher
echo =======================
echo.

if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

echo ✓ Activating environment...
call venv\Scripts\activate.bat

echo ✓ Installing dependencies...
pip install -q -r requirements.txt >nul 2>&1
if !errorlevel! neq 0 (
    pip install -r requirements.txt
)

if not exist "models\fraud_model.pkl" (
    echo.
    echo ⏳ Training model (first time only, ~2-3 min)...
    python train.py --sample-size 100000
)

echo.
echo ✓ Starting Streamlit dashboard...
echo 📊 Opening http://localhost:8501
echo.

streamlit run streamlit_app.py

pause
