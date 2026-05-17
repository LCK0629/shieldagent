# 🚀 ShieldAgent Quick Start Guide

Get the project running in **5 minutes**.

---

## Step 1: Clone & Setup (1 minute)

```bash
cd shieldagent
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate
```

---

## Step 2: Install Dependencies (2 minutes)

```bash
pip install -r requirements.txt
```

---

## Step 3: Train the Model (2 minutes)

```bash
python train.py --sample-size 100000
```

**Output:**
```
✓ models/fraud_model.pkl (trained XGBoost pipeline)
✓ models/metrics.json (performance metrics)
✓ data/reference_transactions.csv (300 sample transactions)
```

---

## Step 4: Run Streamlit Dashboard

```bash
streamlit run streamlit_app.py
```

**Open browser:**
```
http://localhost:8501
```

---

## 🎯 What You'll See

### 1. Dashboard Tab 🏠
- Model accuracy, precision, recall
- Real transaction analyzer
- Performance summary

### 2. Live Stream Tab 📡
- Real-time transactions from dataset
- PASS / FLAG / ESCALATE / BLOCK actions
- Live statistics

### 3. Model Explorer Tab ⚙️
- Test custom transactions with JSON
- View feature configuration
- Decision thresholds

### 4. Performance Tab 📈
- Detailed classification metrics
- Confusion matrix
- Per-class reports

### 5. Transaction Log Tab 💾
- Audit trail
- Transaction filtering
- Summary statistics

---

## 📊 Example Metrics

After training on 100k samples:

```
Accuracy:   ~92%
Precision:  ~89%
Recall:     ~95%
F1 Score:   ~92%
ROC AUC:    ~98%
```

---

## 🔧 Common Tasks

### Change Training Sample Size
```bash
python train.py --sample-size 50000   # Faster
python train.py --sample-size 0       # All rows (slower)
```

### Run FastAPI Backend (Optional)
```bash
uvicorn app:app --reload
# Open: http://localhost:8000
```

### Stop Streamlit
```
Press Ctrl+C
```

---

## ❓ Troubleshooting

**Q: "Model not found" error**  
A: Run `python train.py --sample-size 100000` first

**Q: Streamlit won't start**  
A: Check port 8501 is free, or use:
```bash
streamlit run streamlit_app.py --server.port 8502
```

**Q: Training is very slow**  
A: Use smaller sample: `python train.py --sample-size 50000`

**Q: Want to retrain?**  
A: Just run `python train.py` again—it overwrites the model

---

## 📁 Project Structure

```
├── train.py              ← Run this to train model
├── agent.py              ← Core agent logic
├── streamlit_app.py      ← Run this for dashboard
├── app.py                ← (Optional) FastAPI backend
├── requirements.txt
├── README.md
└── models/               ← Created by train.py
    ├── fraud_model.pkl
    └── metrics.json
```

---

## 🎓 Learning Path

1. **Understand the data**: Read `train.py` to see KDD Cup 99 loading
2. **Understand the model**: See XGBoost pipeline and feature processing
3. **Understand the agent**: Read `agent.py` Observe→Score→Act logic
4. **Explore the UI**: Play with dashboard, test transactions
5. **Deploy ideas**: Modify thresholds, experiment with parameters

---

## ✅ Success Checklist

- [ ] Environment activated
- [ ] Dependencies installed
- [ ] Model trained (fraud_model.pkl exists)
- [ ] Streamlit dashboard running
- [ ] Can generate transactions
- [ ] Can see metrics on dashboard
- [ ] Can test custom transactions in Model Explorer

**You're done!** 🎉

---

**Next**: Check out full README.md for advanced usage and API documentation.
