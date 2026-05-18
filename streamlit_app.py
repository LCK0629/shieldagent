"""Real-time Fraud Detection Agent Dashboard using Streamlit.

Run:
    streamlit run streamlit_app.py

Features:
- Real-time fraud detection from KDD Cup 99 dataset
- Live transaction stream with agent scoring
- Interactive model exploration
- Performance metrics and confusion matrix
- Transaction history and alerts
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu

from agent import ShieldAgent, AgentDecision

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "models" / "fraud_model.pkl"
METRICS_PATH = ROOT / "models" / "metrics.json"
REFERENCE_PATH = ROOT / "data" / "reference_transactions.csv"


st.set_page_config(
    page_title="🛡️ ShieldAgent - Fraud Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def load_agent() -> ShieldAgent:
    if not MODEL_PATH.exists():
        with st.spinner("Training model on KDD Cup 99 dataset — this takes about 1-2 minutes on first run..."):
            from train import train
            train(sample_size=30000, test_size=0.2, random_state=42)
    return ShieldAgent(MODEL_PATH)


@st.cache_data
def load_metrics() -> dict[str, Any]:
    if not METRICS_PATH.exists():
        return {}
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


@st.cache_data
def load_reference_data() -> pd.DataFrame:
    if not REFERENCE_PATH.exists():
        return pd.DataFrame()
    return pd.read_csv(REFERENCE_PATH)


def get_transaction_stream(reference_df: pd.DataFrame, num_transactions: int = 1) -> list[dict]:
    """Generate realistic transactions from reference data with model scoring."""
    if reference_df.empty:
        return []

    transactions = []
    agent = load_agent()

    for _ in range(num_transactions):
        row = reference_df.sample(n=1).iloc[0].to_dict()
        tx_id = f"TXN-{random.randint(1000000, 9999999)}"
        row["transaction_id"] = tx_id

        decision = agent.run_once(row)
        transactions.append(
            {
                "transaction_id": tx_id,
                "timestamp": datetime.now(),
                "region": random.choice(["SG", "MY", "TH", "PH", "ID", "VN"]),
                "amount_usd": round(float(abs(row.get("src_bytes", 0))) / 100 + random.uniform(10, 500), 2),
                "merchant": f"MER-{random.randint(1000, 9999)}",
                "service": row.get("service", "http"),
                "protocol_type": row.get("protocol_type", "tcp"),
                "decision": decision.to_dict(),
            }
        )
    return transactions


def main():
    with st.sidebar:
        selected = option_menu(
            "ShieldAgent Menu",
            ["🏠 Dashboard", "📊 Live Stream", "⚙️ Model Explorer", "📈 Performance", "💾 Transaction Log"],
            icons=["house", "play-circle", "sliders", "bar-chart", "file-earmark"],
            menu_icon="cast",
            default_index=0,
        )

    agent = load_agent()
    metrics = load_metrics()
    reference_df = load_reference_data()

    if selected == "🏠 Dashboard":
        dashboard_page(agent, metrics, reference_df)
    elif selected == "📊 Live Stream":
        live_stream_page(agent, reference_df)
    elif selected == "⚙️ Model Explorer":
        explorer_page(agent)
    elif selected == "📈 Performance":
        performance_page(metrics)
    elif selected == "💾 Transaction Log":
        transaction_log_page()


def dashboard_page(agent: ShieldAgent, metrics: dict, reference_df: pd.DataFrame):
    st.title("🛡️ ShieldAgent Fraud Detection Dashboard")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Transactions", metrics.get("rows_total", "N/A"), "KDD Cup 99")
    with col2:
        st.metric("✅ Accuracy", f"{metrics.get('accuracy', 0) * 100:.2f}%")
    with col3:
        st.metric("🎯 Precision", f"{metrics.get('precision', 0) * 100:.2f}%")
    with col4:
        st.metric("🚀 Recall", f"{metrics.get('recall', 0) * 100:.2f}%")

    st.markdown("### 🔍 Quick Scan: Real Transaction from Dataset")
    if not reference_df.empty:
        if st.button("🔄 Score Next Transaction", key="quick_scan"):
            with st.spinner("Analyzing transaction..."):
                tx = get_transaction_stream(reference_df, num_transactions=1)[0]

                col1, col2 = st.columns([2, 1])
                with col1:
                    st.subheader("Transaction Details")
                    st.write(f"**Transaction ID:** {tx['transaction_id']}")
                    st.write(f"**Timestamp:** {tx['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
                    st.write(f"**Region:** {tx['region']}")
                    st.write(f"**Amount:** ${tx['amount_usd']:.2f}")
                    st.write(f"**Merchant:** {tx['merchant']}")
                    st.write(f"**Service:** {tx['service']}")

                with col2:
                    decision = tx["decision"]
                    color = {
                        "PASS": "green",
                        "FLAG": "yellow",
                        "ESCALATE": "orange",
                        "BLOCK": "red",
                    }[decision["action"]]

                    st.markdown(f"### :{color}[{decision['action']}]")
                    st.metric("Risk Score", f"{decision['risk_score']:.4f}")
                    st.metric("Severity", decision["severity"])
                    st.write(f"*{decision['reason']}*")

    st.markdown("### 📈 Model Performance Summary")
    col1, col2 = st.columns(2)

    with col1:
        st.write("#### 🎯 Classification Metrics")
        st.text(
            f"""
Accuracy:  {metrics.get('accuracy', 0):.4f}
Precision: {metrics.get('precision', 0):.4f}
Recall:    {metrics.get('recall', 0):.4f}
F1 Score:  {metrics.get('f1', 0):.4f}
ROC AUC:   {metrics.get('roc_auc', 0):.4f}
        """
        )

    with col2:
        if "confusion_matrix" in metrics:
            st.write("#### 📊 Confusion Matrix")
            cm = np.array(metrics["confusion_matrix"])
            st.write(f"True Negatives:  {cm[0, 0]}")
            st.write(f"False Positives: {cm[0, 1]}")
            st.write(f"False Negatives: {cm[1, 0]}")
            st.write(f"True Positives:  {cm[1, 1]}")


def live_stream_page(agent: ShieldAgent, reference_df: pd.DataFrame):
    st.title("📊 Live Transaction Stream")
    st.markdown("Real-time fraud detection from public KDD Cup 99 dataset.")

    col1, col2, col3 = st.columns(3)
    with col1:
        num_tx = st.slider("Transactions to stream", 1, 20, 5)
    with col2:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=False)
    with col3:
        if auto_refresh:
            st.write("Updating every 3 seconds...")

    placeholder = st.empty()

    def render_transactions():
        transactions = get_transaction_stream(reference_df, num_tx)

        with placeholder.container():
            st.markdown("### Current Batch")

            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
            with stats_col1:
                passed = sum(1 for tx in transactions if tx["decision"]["action"] == "PASS")
                st.metric("✅ PASS", passed)
            with stats_col2:
                flagged = sum(1 for tx in transactions if tx["decision"]["action"] == "FLAG")
                st.metric("🚩 FLAG", flagged)
            with stats_col3:
                escalated = sum(1 for tx in transactions if tx["decision"]["action"] == "ESCALATE")
                st.metric("⚠️ ESCALATE", escalated)
            with stats_col4:
                blocked = sum(1 for tx in transactions if tx["decision"]["action"] == "BLOCK")
                st.metric("🛑 BLOCK", blocked)

            st.markdown("---")

            for i, tx in enumerate(transactions):
                decision = tx["decision"]
                action_icon = {
                    "PASS": "✅",
                    "FLAG": "🚩",
                    "ESCALATE": "⚠️",
                    "BLOCK": "🛑",
                }[decision["action"]]

                with st.expander(
                    f"{action_icon} {tx['transaction_id']} | ${tx['amount_usd']:.2f} | "
                    f"{decision['action']} ({decision['risk_score']:.4f})",
                    expanded=(i < 3),
                ):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Region:** {tx['region']}")
                        st.write(f"**Amount:** ${tx['amount_usd']:.2f}")
                        st.write(f"**Time:** {tx['timestamp'].strftime('%H:%M:%S')}")
                    with col2:
                        st.write(f"**Merchant:** {tx['merchant']}")
                        st.write(f"**Service:** {tx['service']}")
                        st.write(f"**Protocol:** {tx['protocol_type']}")
                    with col3:
                        st.write(f"**Risk Score:** {decision['risk_score']:.6f}")
                        st.write(f"**Severity:** {decision['severity']}")
                        st.write(f"**Timestamp:** {decision['timestamp_utc']}")

                    st.info(f"📝 {decision['reason']}")

    render_transactions()

    if auto_refresh:
        import time
        while auto_refresh:
            time.sleep(3)
            st.rerun()


def explorer_page(agent: ShieldAgent):
    st.title("⚙️ Model Explorer")
    st.markdown("Inspect and test the trained fraud detection model.")

    st.markdown("### 📋 Model Configuration")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Feature Columns:** {len(agent.feature_columns)}")
        st.write(f"**Numeric Features:** {len(agent.feature_columns) - 3}")
        st.write(f"**Categorical Features:** 3 (protocol_type, service, flag)")
    with col2:
        st.write("**Decision Thresholds:**")
        for key, val in agent.thresholds.items():
            st.write(f"- {key.upper()}: {val:.2f}")

    st.markdown("---")
    st.markdown("### 🧪 Manual Transaction Test")

    test_input = st.text_area(
        "Enter JSON transaction (or use defaults):",
        value="""{
  "transaction_id": "TXN-TEST-001",
  "duration": 0,
  "protocol_type": "tcp",
  "service": "http",
  "flag": "SF",
  "src_bytes": 181,
  "dst_bytes": 5450,
  "land": 0,
  "wrong_fragment": 0,
  "urgent": 0,
  "hot": 0,
  "num_failed_logins": 0,
  "logged_in": 1,
  "num_compromised": 0,
  "root_shell": 0,
  "su_attempted": 0,
  "num_root": 0,
  "num_file_creations": 0,
  "num_shells": 0,
  "num_access_files": 0,
  "num_outbound_cmds": 0,
  "is_host_login": 0,
  "is_guest_login": 0,
  "count": 8,
  "srv_count": 8,
  "serror_rate": 0.0,
  "srv_serror_rate": 0.0,
  "rerror_rate": 0.0,
  "srv_rerror_rate": 0.0,
  "same_srv_rate": 1.0,
  "diff_srv_rate": 0.0,
  "srv_diff_host_rate": 0.0,
  "dst_host_count": 9,
  "dst_host_srv_count": 9,
  "dst_host_same_srv_rate": 1.0,
  "dst_host_diff_srv_rate": 0.0,
  "dst_host_same_src_port_rate": 0.11,
  "dst_host_srv_diff_host_rate": 0.0,
  "dst_host_serror_rate": 0.0,
  "dst_host_srv_serror_rate": 0.0,
  "dst_host_rerror_rate": 0.0,
  "dst_host_srv_rerror_rate": 0.0
}""",
    )

    if st.button("🔍 Analyze Transaction"):
        try:
            payload = json.loads(test_input)
            decision = agent.run_once(payload)

            st.success("✅ Analysis Complete")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Risk Score", f"{decision.risk_score:.6f}")
            with col2:
                st.metric("Action", decision.action)
            with col3:
                st.metric("Severity", decision.severity)
            with col4:
                st.metric("Timestamp", decision.timestamp_utc[-8:])

            st.info(f"💡 {decision.reason}")
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON: {e}")
        except ValueError as e:
            st.error(f"❌ Missing features: {e}")


def performance_page(metrics: dict):
    st.title("📈 Model Performance Analysis")

    if not metrics:
        st.warning("⚠️ No metrics available. Run `python train.py` first.")
        return

    st.markdown("### 📊 Dataset Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Rows", f"{metrics.get('rows_total', 0):,}")
    with col2:
        st.metric("Training Rows", f"{metrics.get('rows_train', 0):,}")
    with col3:
        st.metric("Test Rows", f"{metrics.get('rows_test', 0):,}")
    with col4:
        st.metric("Attack Rate", f"{metrics.get('positive_attack_rate', 0) * 100:.2f}%")
    with col5:
        st.metric("Dataset", "KDD Cup 99")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎯 Classification Metrics")
        metrics_data = {
            "Metric": ["Accuracy", "Precision", "Recall", "F1 Score", "ROC AUC"],
            "Score": [
                f"{metrics.get('accuracy', 0):.4f}",
                f"{metrics.get('precision', 0):.4f}",
                f"{metrics.get('recall', 0):.4f}",
                f"{metrics.get('f1', 0):.4f}",
                f"{metrics.get('roc_auc', 0):.4f}",
            ],
        }
        st.dataframe(
            pd.DataFrame(metrics_data),
            use_container_width=True,
            hide_index=True,
        )

    with col2:
        st.markdown("### 📊 Confusion Matrix")
        if "confusion_matrix" in metrics:
            cm = np.array(metrics["confusion_matrix"])
            cm_df = pd.DataFrame(
                cm,
                index=["Predicted Normal", "Predicted Attack"],
                columns=["Actual Normal", "Actual Attack"],
            )
            st.dataframe(cm_df, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📋 Detailed Classification Report")
    if "classification_report" in metrics:
        report_data = metrics["classification_report"]
        report_df = pd.DataFrame(report_data).T
        st.dataframe(report_df, use_container_width=True)


def transaction_log_page():
    st.title("💾 Transaction Log")
    st.markdown("View and filter processed transactions.")

    if "transaction_history" not in st.session_state:
        st.session_state.transaction_history = []

    col1, col2 = st.columns(2)
    with col1:
        log_size = st.slider("Generate log entries", 5, 50, 10)
    with col2:
        if st.button("📥 Generate New Batch"):
            reference_df = load_reference_data()
            new_tx = get_transaction_stream(reference_df, log_size)
            st.session_state.transaction_history.extend(new_tx)

    if st.session_state.transaction_history:
        log_df = pd.DataFrame([
            {
                "Transaction ID": tx["transaction_id"],
                "Amount": f"${tx['amount_usd']:.2f}",
                "Region": tx["region"],
                "Action": tx["decision"]["action"],
                "Risk Score": f"{tx['decision']['risk_score']:.4f}",
                "Severity": tx["decision"]["severity"],
                "Timestamp": tx["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            }
            for tx in st.session_state.transaction_history[-50:]
        ])

        st.dataframe(log_df, use_container_width=True, hide_index=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total = len(st.session_state.transaction_history)
            st.metric("Total Transactions", total)
        with col2:
            passed = sum(1 for tx in st.session_state.transaction_history if tx["decision"]["action"] == "PASS")
            st.metric("Passed", passed)
        with col3:
            flagged = sum(1 for tx in st.session_state.transaction_history if tx["decision"]["action"] in ["FLAG", "ESCALATE"])
            st.metric("Flagged", flagged)
        with col4:
            blocked = sum(1 for tx in st.session_state.transaction_history if tx["decision"]["action"] == "BLOCK")
            st.metric("Blocked", blocked)
    else:
        st.info("📝 No transactions yet. Generate a batch above.")


if __name__ == "__main__":
    main()
