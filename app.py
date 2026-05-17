"""FastAPI app for ShieldAgent.

Run:
    python train.py --sample-size 100000
    uvicorn app:app --reload
Open:
    http://127.0.0.1:8000
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent import ShieldAgent, MODEL_PATH

ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
METRICS_PATH = ROOT / "models" / "metrics.json"
REFERENCE_PATH = ROOT / "data" / "reference_transactions.csv"

app = FastAPI(title="ShieldAgent API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

_agent: ShieldAgent | None = None
_reference_df: pd.DataFrame | None = None


class TransactionPayload(BaseModel):
    transaction_id: str = Field(default_factory=lambda: f"TXN-{random.randint(100000, 999999)}")
    duration: float = 0
    protocol_type: str = "tcp"
    service: str = "http"
    flag: str = "SF"
    src_bytes: float = 181
    dst_bytes: float = 5450
    land: int = 0
    wrong_fragment: int = 0
    urgent: int = 0
    hot: int = 0
    num_failed_logins: int = 0
    logged_in: int = 1
    num_compromised: int = 0
    root_shell: int = 0
    su_attempted: int = 0
    num_root: int = 0
    num_file_creations: int = 0
    num_shells: int = 0
    num_access_files: int = 0
    num_outbound_cmds: int = 0
    is_host_login: int = 0
    is_guest_login: int = 0
    count: int = 8
    srv_count: int = 8
    serror_rate: float = 0.0
    srv_serror_rate: float = 0.0
    rerror_rate: float = 0.0
    srv_rerror_rate: float = 0.0
    same_srv_rate: float = 1.0
    diff_srv_rate: float = 0.0
    srv_diff_host_rate: float = 0.0
    dst_host_count: int = 9
    dst_host_srv_count: int = 9
    dst_host_same_srv_rate: float = 1.0
    dst_host_diff_srv_rate: float = 0.0
    dst_host_same_src_port_rate: float = 0.11
    dst_host_srv_diff_host_rate: float = 0.0
    dst_host_serror_rate: float = 0.0
    dst_host_srv_serror_rate: float = 0.0
    dst_host_rerror_rate: float = 0.0
    dst_host_srv_rerror_rate: float = 0.0


def get_agent() -> ShieldAgent:
    global _agent
    if _agent is None:
        if not MODEL_PATH.exists():
            raise HTTPException(status_code=503, detail="Model not trained. Run `python train.py` first.")
        _agent = ShieldAgent(MODEL_PATH)
    return _agent


def get_reference_df() -> pd.DataFrame:
    global _reference_df
    if _reference_df is None:
        if not REFERENCE_PATH.exists():
            raise HTTPException(status_code=503, detail="Reference data not found. Run `python train.py` first.")
        _reference_df = pd.read_csv(REFERENCE_PATH)
    return _reference_df


@app.get("/")
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "model_ready": MODEL_PATH.exists(), "metrics_ready": METRICS_PATH.exists()}


@app.get("/api/metrics")
def metrics() -> dict[str, Any]:
    if not METRICS_PATH.exists():
        raise HTTPException(status_code=503, detail="Metrics not found. Run `python train.py` first.")
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


@app.post("/api/predict")
def predict(payload: TransactionPayload) -> dict[str, Any]:
    decision = get_agent().run_once(payload.model_dump())
    return decision.to_dict()


@app.get("/api/stream")
def stream_one() -> dict[str, Any]:
    """Return one real KDD-shaped reference row scored by the trained model.

    The row comes from the public dataset sample saved during training.
    The displayed business fields are presentation aliases only; the model score is real.
    """
    df = get_reference_df()
    row = df.sample(n=1).iloc[0].to_dict()
    tx_id = f"TXN-{random.randint(100000, 999999)}"
    row["transaction_id"] = tx_id

    decision = get_agent().run_once(row).to_dict()
    return {
        "transaction_id": tx_id,
        "region": random.choice(["SG", "MY", "TH", "PH", "ID", "VN"]),
        "amount": round(float(abs(row.get("src_bytes", 0))) / 100 + random.uniform(5, 80), 2),
        "service": row.get("service", "unknown"),
        "protocol_type": row.get("protocol_type", "unknown"),
        "actual_label": int(row.get("actual_label", 0)),
        "decision": decision,
    }
