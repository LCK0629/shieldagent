"""Train ShieldAgent fraud/intrusion-risk model on the public KDD Cup 99 dataset.

Why KDD Cup 99?
- It is a real public dataset available through scikit-learn.
- It is not synthetic or fake data.
- Labels are converted into binary risk classes: normal vs attack.

Run:
    python train.py --sample-size 100000
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.datasets import fetch_kddcup99
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from xgboost import XGBClassifier
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "xgboost is required. Install dependencies with: pip install -r requirements.txt"
    ) from exc

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "models"
DATA_DIR = ROOT / "data"
MODEL_PATH = MODEL_DIR / "fraud_model.pkl"
METRICS_PATH = MODEL_DIR / "metrics.json"
REFERENCE_PATH = DATA_DIR / "reference_transactions.csv"

FEATURE_COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes", "land",
    "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in", "num_compromised",
    "root_shell", "su_attempted", "num_root", "num_file_creations", "num_shells",
    "num_access_files", "num_outbound_cmds", "is_host_login", "is_guest_login", "count",
    "srv_count", "serror_rate", "srv_serror_rate", "rerror_rate", "srv_rerror_rate",
    "same_srv_rate", "diff_srv_rate", "srv_diff_host_rate", "dst_host_count",
    "dst_host_srv_count", "dst_host_same_srv_rate", "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate", "dst_host_serror_rate",
    "dst_host_srv_serror_rate", "dst_host_rerror_rate", "dst_host_srv_rerror_rate",
]

CATEGORICAL_COLUMNS = ["protocol_type", "service", "flag"]
NUMERIC_COLUMNS = [c for c in FEATURE_COLUMNS if c not in CATEGORICAL_COLUMNS]


def _decode_bytes(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return value


def load_kddcup99(sample_size: int | None, random_state: int) -> tuple[pd.DataFrame, pd.Series]:
    print("Loading public KDD Cup 99 dataset via scikit-learn...")
    data = fetch_kddcup99(subset="SA", percent10=True, shuffle=True, random_state=random_state)

    X = pd.DataFrame(data.data, columns=FEATURE_COLUMNS).map(_decode_bytes)
    labels = pd.Series(data.target).map(_decode_bytes)
    y = (labels != "normal.").astype(int)

    for col in NUMERIC_COLUMNS:
        X[col] = pd.to_numeric(X[col], errors="coerce")

    if sample_size and sample_size < len(X):
        sampled = X.sample(n=sample_size, random_state=random_state)
        y = y.loc[sampled.index]
        X = sampled

    return X.reset_index(drop=True), y.reset_index(drop=True)


def build_pipeline(random_state: int) -> Pipeline:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_COLUMNS),
            ("cat", categorical_pipeline, CATEGORICAL_COLUMNS),
        ]
    )

    classifier = XGBClassifier(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=random_state,
        n_jobs=-1,
        tree_method="hist",
    )

    return Pipeline(steps=[("preprocessor", preprocessor), ("model", classifier)])


def train(sample_size: int | None, test_size: float, random_state: int) -> dict[str, Any]:
    MODEL_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)

    X, y = load_kddcup99(sample_size=sample_size, random_state=random_state)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    pipeline = build_pipeline(random_state=random_state)
    print(f"Training on {len(X_train):,} rows; testing on {len(X_test):,} rows...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "dataset": "KDD Cup 99 SA subset via sklearn.datasets.fetch_kddcup99",
        "rows_total": int(len(X)),
        "rows_train": int(len(X_train)),
        "rows_test": int(len(X_test)),
        "positive_attack_rate": float(y.mean()),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_prob)),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "classification_report": classification_report(y_test, y_pred, target_names=["normal", "attack"], output_dict=True),
    }

    bundle = {
        "pipeline": pipeline,
        "feature_columns": FEATURE_COLUMNS,
        "categorical_columns": CATEGORICAL_COLUMNS,
        "numeric_columns": NUMERIC_COLUMNS,
        "label_mapping": {"0": "normal", "1": "attack"},
        "thresholds": {"pass": 0.35, "flag": 0.70, "block": 0.90},
    }
    joblib.dump(bundle, MODEL_PATH)

    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    # Save realistic reference rows for the dashboard stream. These are real KDD rows, not fake labels.
    reference = X_test.copy()
    reference["actual_label"] = y_test.values
    reference["risk_score"] = y_prob
    reference.sample(n=min(300, len(reference)), random_state=random_state).to_csv(REFERENCE_PATH, index=False)

    print(f"Saved model: {MODEL_PATH}")
    print(f"Saved metrics: {METRICS_PATH}")
    print(f"Saved dashboard reference data: {REFERENCE_PATH}")
    print(json.dumps({k: metrics[k] for k in ["accuracy", "precision", "recall", "f1", "roc_auc"]}, indent=2))
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train ShieldAgent on KDD Cup 99.")
    parser.add_argument("--sample-size", type=int, default=100000, help="Rows to sample for faster training. Use 0 for all rows.")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    size = None if args.sample_size == 0 else args.sample_size
    train(sample_size=size, test_size=args.test_size, random_state=args.random_state)
