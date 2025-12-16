import streamlit as st
import pandas as pd
import requests
from datetime import timedelta

API_URL = "https://monsera-credit-engine.onrender.com/decision"
SUCCESS_STATUSES = {"SUCCESS", "COMPLETED"}

st.set_page_config(page_title="Monsera Aggregator Demo", layout="wide")

st.title("⚡ Monsera Aggregator Console (Demo)")
st.caption("Real transaction data • Behavioural credit • DisCo-safe")

# --------------------------------------------------
# Load data (cached for speed)
# --------------------------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv("demo/data/consolidated_transactions.csv")
    df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"])
    return df

df = load_data()

# --------------------------------------------------
# Meter (User_ID) selection
# --------------------------------------------------

users = (
    df[["User_ID", "Service_Provider"]]
    .drop_duplicates()
    .sort_values("User_ID")
)

selected_user = st.selectbox(
    "Select Meter (User ID)",
    users["User_ID"].tolist()
)

user_df = df[df["User_ID"] == selected_user].sort_values("Transaction_Date")

service_provider = user_df["Service_Provider"].iloc[0]

st.markdown(f"**Service Provider:** `{service_provider}`")

# --------------------------------------------------
# Show last 5 transactions only
# --------------------------------------------------

st.markdown("### Last 5 Transactions")
st.dataframe(
    user_df.tail(5)[
        [
            "Transaction_Date",
            "Amount",
            "Status",
            "Is_Retry",
            "Retry_Count",
        ]
    ],
    use_container_width=True,
)

# --------------------------------------------------
# Feature engineering (V0 – last 60 days)
# --------------------------------------------------

today = user_df["Transaction_Date"].max()
window_start = today - timedelta(days=60)

recent = user_df[user_df["Transaction_Date"] >= window_start]
successful = recent[recent["Status"].isin(SUCCESS_STATUSES)]

vend_count = len(successful)
total_attempts = len(recent)

failed_vend_ratio = (
    100 * (total_attempts - vend_count) / total_attempts
    if total_attempts > 0
    else 100
)

median_vend = successful["Amount"].median() if vend_count > 0 else 0

vend_amount_volatility = (
    successful["Amount"].std() / median_vend * 100
    if vend_count > 1 and median_vend > 0
    else 0
)

inter_vend_variance = (
    successful["Transaction_Date"]
    .sort_values()
    .diff()
    .dt.days
    .var()
    if vend_count > 2
    else 0
)

days_since_last_vend = (
    (today - successful["Transaction_Date"].max()).days
    if vend_count > 0
    else 999
)

features = {
    "vend_count_last_60_days": int(vend_count),
    "days_since_last_vend": int(days_since_last_vend),
    "vend_frequency": float(vend_count / 2),
    "median_vend_amount": float(median_vend),
    "vend_amount_volatility": float(vend_amount_volatility),
    "inter_vend_variance": float(inter_vend_variance),
    "failed_vend_ratio": float(failed_vend_ratio),
    "has_active_obligation": False,
}

# --------------------------------------------------
# Behaviour summary
# --------------------------------------------------

st.markdown("### Behaviour Summary (Derived)")
st.json(features)

# --------------------------------------------------
# Vend simulation (stateful, realistic)
# --------------------------------------------------

st.markdown("### Vend Simulation")

wallet_balance = st.number_input(
    "Wallet balance (₦)", min_value=0, value=0, step=500
)

vend_request = st.number_input(
    "Electricity requested (₦)", min_value=1000, value=4000, step=500
)

# Initialize state
if "offer" not in st.session_state:
    st.session_state.offer = None

if "decision_made" not in st.session_state:
    st.session_state.decision_made = None


# Step 1: Request decision
if st.button("Simulate Vend"):
    response = requests.post(API_URL, json=features, timeout=5)
    decision = response.json()

    if not decision["eligible"]:
        st.session_state.offer = None
        st.session_state.decision_made = "DECLINED"

        st.error("❌ Credit declined")
        st.markdown(f"**Reason:** {decision['reason']}")

    else:
        st.session_state.offer = decision
        st.session_state.decision_made = None


# Step 2: Show offer if available
if st.session_state.offer and st.session_state.decision_made is None:
    approved = st.session_state.offer["approved_amount"]
    total_available = wallet_balance + approved

    st.success("✅ Credit offer available")
    st.markdown(f"**Approved advance:** ₦{approved:,}")
    st.markdown(f"**Total available for vend:** ₦{total_available:,}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Accept Offer"):
            vend_amount = min(vend_request, total_available)

            st.session_state.decision_made = "ACCEPTED"
            st.session_state.vend_amount = vend_amount

            st.session_state.offer = None

    with col2:
        if st.button("❌ Decline Offer"):
            st.session_state.decision_made = "DECLINED"
            st.session_state.offer = None


# Step 3: Final outcome (very important)
if st.session_state.decision_made == "ACCEPTED":
    st.info(f"⚡ Vend completed for ₦{st.session_state.vend_amount:,}")
    st.markdown("💰 **DisCo paid in full**")
    st.markdown("📅 **Repayment scheduled on next vend**")

elif st.session_state.decision_made == "DECLINED":
    st.warning("Customer declined the credit offer.")
    st.markdown("No vend occurred. No risk taken.")

