import streamlit as st
import pandas as pd
import requests
from datetime import timedelta

API_URL = "https://monsera-credit-engine.onrender.com/decision"
SUCCESS_STATUSES = {"SUCCESS", "COMPLETED", "SUCCESSFUL"}

st.set_page_config(
    page_title="Monsera Aggregator Console",
    layout="wide",
)

# --------------------------------------------------
# Header
# --------------------------------------------------

st.markdown("## ⚡ Monsera Aggregator Console")
st.caption(
    "Behavioural credit for prepaid electricity • "
    "Learning-first • Meter-enforced • DisCo-safe"
)

st.divider()

# --------------------------------------------------
# Load data
# --------------------------------------------------

@st.cache_data
def load_data():
    df = pd.read_csv("demo/data/consolidated_transactions.csv")
    df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"])
    return df

df = load_data()

# --------------------------------------------------
# Meter selection (reset state on change)
# --------------------------------------------------

meters = (
    df[["User_ID", "Service_Provider"]]
    .drop_duplicates()
    .sort_values("User_ID")
)

selected_meter = st.selectbox(
    "Select Meter (User ID)",
    meters["User_ID"].tolist(),
)

if st.session_state.get("current_meter") != selected_meter:
    st.session_state.current_meter = selected_meter
    st.session_state.offer = None
    st.session_state.decision_made = None
    st.session_state.vend_amount = None

meter_df = df[df["User_ID"] == selected_meter].sort_values("Transaction_Date")
service_provider = meter_df["Service_Provider"].iloc[0]

st.markdown(f"**Service Provider:** `{service_provider}`")
st.divider()

# --------------------------------------------------
# Recent transactions
# --------------------------------------------------

st.markdown("### Recent Activity (Last 5 Transactions)")
st.dataframe(
    meter_df.tail(5)[
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
# Feature engineering (last 60 days)
# --------------------------------------------------

today = meter_df["Transaction_Date"].max()
recent = meter_df[meter_df["Transaction_Date"] >= today - timedelta(days=60)]
successful = recent[recent["Status"].isin(SUCCESS_STATUSES)]

# Calculate inter-vend gaps (in days)
if len(successful) >= 3:
    inter_vend_gaps = (
        successful
        .sort_values("Transaction_Date")["Transaction_Date"]
        .diff()
        .dt.days
        .dropna()
    )
    inter_vend_variance = inter_vend_gaps.var()
else:
    inter_vend_variance = 0


vend_count = len(successful)
total_attempts = len(recent)

failed_ratio = (
    100 * (total_attempts - vend_count) / total_attempts
    if total_attempts > 0
    else 100
)

median_vend = successful["Amount"].median() if vend_count else 0

volatility = (
    successful["Amount"].std() / median_vend * 100
    if vend_count > 1 and median_vend > 0
    else 0
)

days_since_last = (
    (today - successful["Transaction_Date"].max()).days
    if vend_count > 0
    else 999
)

features = {
    "vend_count_last_60_days": int(vend_count),
    "days_since_last_vend": int(days_since_last),
    "vend_frequency": float(vend_count / 2),
    "median_vend_amount": float(median_vend),
    "vend_amount_volatility": float(volatility),
    "inter_vend_variance": float(inter_vend_variance),
    "failed_vend_ratio": float(failed_ratio),
    "has_active_obligation": False,
}

# --------------------------------------------------
# Behaviour summary
# --------------------------------------------------

st.markdown("### Behaviour Summary")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Vends (60d)", vend_count)
c2.metric("Median Vend (₦)", f"{int(median_vend):,}")
c3.metric("Failed Attempts (%)", f"{failed_ratio:.1f}%")
c4.metric("Days Since Last Vend", days_since_last)

st.divider()

# --------------------------------------------------
# Vend simulation inputs
# --------------------------------------------------

st.markdown("### Vend Simulation")

left, right = st.columns(2)

with left:
    wallet_balance = st.number_input(
        "Wallet Balance (₦)",
        min_value=0,
        value=0,
        step=500,
    )

with right:
    vend_request = st.number_input(
        "Electricity Requested (₦)",
        min_value=1000,
        value=4000,
        step=500,
    )

st.session_state.setdefault("offer", None)
st.session_state.setdefault("decision_made", None)

# --------------------------------------------------
# Request decision
# --------------------------------------------------

if st.button("Simulate Vend", use_container_width=True):
    with st.spinner("Contacting Monsera decision engine..."):
        try:
            response = requests.post(API_URL, json=features, timeout=30)
            response.raise_for_status()
            decision = response.json()
        except requests.exceptions.RequestException:
            st.error("Decision engine unavailable. Please try again.")
            st.stop()

    if not decision["eligible"]:
        st.session_state.offer = None
        st.session_state.decision_made = "DECLINED"
        st.error("❌ Credit declined (extreme risk detected)")
    else:
        st.session_state.offer = decision
        st.session_state.decision_made = None

# --------------------------------------------------
# Offer + repayment preview
# --------------------------------------------------

if st.session_state.offer and st.session_state.decision_made is None:
    approved = st.session_state.offer["approved_amount"]
    total_available = wallet_balance + approved

    st.success("✅ Credit Offer Available")
    st.markdown(f"**Approved Advance:** ₦{approved:,}")
    st.markdown(f"**Total Available for Vend:** ₦{total_available:,}")

    if approved == 2000:
        st.info(
            "Starter / safety-limit advance applied "
            "while the system continues to learn."
        )

    st.caption("Advance amounts vary continuously based on meter behaviour.")

    # --------------------------------------------------
    # Choose final vend amount
    # --------------------------------------------------

    # Default: cap requested amount to what is actually possible
    final_vend_amount = min(vend_request, total_available)

    if approved > vend_request:
        st.markdown("### Confirm Vend Amount")

        choice = st.radio(
            f"You requested ₦{vend_request:,}, but you are eligible for up to ₦{approved:,}.",
            ["Proceed with requested amount", "Increase vend amount"],
        )

        if choice == "Increase vend amount":
            final_vend_amount = st.slider(
                "Select vend amount (₦)",
                min_value=vend_request,
                max_value=min(approved, total_available),
                step=500,
                value=final_vend_amount,
            )


    # --------------------------------------------------
    # Repayment preview (NEW)
    # --------------------------------------------------

    credit_used = max(final_vend_amount - wallet_balance, 0)

    st.markdown("### Repayment Preview")
    st.info(
        f"You will use **₦{credit_used:,}** in credit.\n\n"
        f"This amount will be **automatically recovered on your next successful vend** "
        f"before new electricity is credited."
    )

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        if st.button("✅ Confirm & Vend", use_container_width=True):
            st.session_state.decision_made = "ACCEPTED"
            st.session_state.vend_amount = final_vend_amount
            st.session_state.offer = None

    with c2:
        if st.button("❌ Decline Offer", use_container_width=True):
            st.session_state.decision_made = "DECLINED"
            st.session_state.offer = None

# --------------------------------------------------
# Final outcome
# --------------------------------------------------

if st.session_state.decision_made == "ACCEPTED":
    st.success(f"⚡ Vend completed for ₦{st.session_state.vend_amount:,}")
    st.markdown("💰 **DisCo paid in full**")
    st.markdown("📅 **Credit recovered on next vend**")

elif st.session_state.decision_made == "DECLINED":
    st.warning("Customer declined the credit offer.")
    st.caption("No vend occurred. No risk taken.")
