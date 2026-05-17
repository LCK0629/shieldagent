#!/bin/bash
# ShieldAgent quick launcher (macOS/Linux)

set -e

echo "🛡️  ShieldAgent Launcher"
echo "======================="
echo ""

if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "✓ Activating environment..."
source venv/bin/activate

echo "✓ Installing dependencies..."
pip install -q -r requirements.txt 2>/dev/null || pip install -r requirements.txt

if [ ! -f "models/fraud_model.pkl" ]; then
    echo ""
    echo "⏳ Training model (first time only, ~2-3 min)..."
    python train.py --sample-size 100000
fi

echo ""
echo "✓ Starting Streamlit dashboard..."
echo "📊 Opening http://localhost:8501"
echo ""

streamlit run streamlit_app.py
