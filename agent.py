"""ShieldAgent core loop: Observe -> Score -> Act.

This file intentionally keeps the agent deterministic and auditable.
No fake LLM reasoning is used. The action comes from the trained model score.

Real model outputs from KDD Cup 99 public dataset. No simulation.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "models" / "fraud_model.pkl"


@dataclass
class AgentDecision:
    transaction_id: str
    risk_score: float
    action: str
    severity: str
    reason: str
    timestamp_utc: str
    model_name: str = "xgboost-kddcup99"
    features_used: int = 41

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ShieldAgent:
    def __init__(self, model_path: str | Path = MODEL_PATH):
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found at {model_path}. Run `python train.py` first."
            )
        bundle = joblib.load(model_path)
        self.pipeline = bundle["pipeline"]
        self.feature_columns = bundle["feature_columns"]
        self.thresholds = bundle.get("thresholds", {"pass": 0.35, "flag": 0.70, "block": 0.90})

    def observe(self, transaction: dict[str, Any]) -> pd.DataFrame:
        missing = [c for c in self.feature_columns if c not in transaction]
        if missing:
            raise ValueError(f"Missing required feature(s): {missing}")
        return pd.DataFrame([{c: transaction[c] for c in self.feature_columns}])

    def score(self, observed: pd.DataFrame) -> float:
        return float(self.pipeline.predict_proba(observed)[:, 1][0])

    def act(self, transaction_id: str, risk_score: float) -> AgentDecision:
        if risk_score >= self.thresholds["block"]:
            action = "BLOCK"
            severity = "CRITICAL"
            reason = "Model predicts very high attack/fraud likelihood; automatically blocked."
        elif risk_score >= self.thresholds["flag"]:
            action = "ESCALATE"
            severity = "HIGH"
            reason = "Model predicts high risk; escalated for analyst review."
        elif risk_score >= self.thresholds["pass"]:
            action = "FLAG"
            severity = "MEDIUM"
            reason = "Model predicts moderate risk; transaction is flagged and monitored."
        else:
            action = "PASS"
            severity = "LOW"
            reason = "Model predicts low risk; transaction is allowed."

        return AgentDecision(
            transaction_id=transaction_id,
            risk_score=round(risk_score, 6),
            action=action,
            severity=severity,
            reason=reason,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )

    def run_once(self, transaction: dict[str, Any]) -> AgentDecision:
        transaction_id = str(transaction.get("transaction_id", "TXN-UNKNOWN"))
        observed = self.observe(transaction)
        risk_score = self.score(observed)
        return self.act(transaction_id, risk_score)


if __name__ == "__main__":
    # Example requires a trained model and a real KDD-shaped input row.
    print("ShieldAgent ready. Use app.py or import ShieldAgent in your own script.")
