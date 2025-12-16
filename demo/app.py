import streamlit as st
import requests

API_URL = "https://monsera-credit-engine.onrender.com/decision"

st.set_page_config(
    page_title="Monsera Pay-Later Demo",
    layout="centered"
)

st.title("⚡ Monsera Pay-Later Demo")
st.subheader("Simulating prepaid electricity vending with behavioural credit")

st.markdown(
    """
This demo shows how Monsera enables **safe electricity advances**.

• Monsera approves an **amount**, not a forced vend  
• Wallet balance does **not** affect eligibility  
• Customers may accept **full or partial power**  
• DisCos are always paid upfront
"""
)
# Behavioural scenarios

SCENARIOS = {
    "Consistent Household": {
        "vend_count_last_60_days": 15,
        "days_since_last_vend": 2,
        "vend_frequency": 4,
        "median_vend_amount": 12000,
        "vend_amount_volatility": 25,
        "inter_vend_variance": 20,
        "failed_vend_ratio": 3,
        "has_active_obligation": False,
    },
    "Marginal Household": {
        "vend_count_last_60_days": 8,
        "days_since_last_vend": 3,
        "vend_frequency": 2,
        "median_vend_amount": 6000,
        "vend_amount_volatility": 50,
        "inter_vend_variance": 45,
        "failed_vend_ratio": 8,
        "has_active_obligation": False,
    },
    "Dormant Meter": {
        "vend_count_last_60_days": 10,
        "days_since_last_vend": 45,
        "vend_frequency": 2,
        "median_vend_amount": 3500,
        "vend_amount_volatility": 40,
        "inter_vend_variance": 50,
        "failed_vend_ratio": 5,
        "has_active_obligation": False,
    },
}

scenario = st.selectbox("Select customer type", SCENARIOS.keys())

wallet_balance = st.number_input(
    "Customer wallet balance (₦)",
    min_value=0,
    value=0,
    step=1000
)

vend_price = st.number_input(
    "Electricity requested (₦)",
    min_value=2000,
    value=4000,
    step=1000
)

st.markdown("---")

# Vend simulation

if st.button("Simulate Vend"):
    st.session_state.clear()

    if wallet_balance >= vend_price:
        st.success("✅ Vend completed without credit.")
        st.markdown("💰 **DisCo paid in full**")
    else:
        st.warning("⚠️ Insufficient balance. Aggregator requests Monsera decision…")

        response = requests.post(API_URL, json=SCENARIOS[scenario])
        decision = response.json()

        if not decision["eligible"]:
            st.error("❌ Credit declined")
            st.markdown(f"**Reason:** {decision['reason']}")
        else:
            st.session_state["decision"] = decision
            st.session_state["show_offer"] = True

# Offer acceptance flow

if st.session_state.get("show_offer"):
    decision = st.session_state["decision"]
    approved = decision["approved_amount"]
    total_available = wallet_balance + approved

    st.success("✅ Credit offer available")
    st.markdown(f"**Approved advance:** ₦{approved:,}")
    st.markdown(f"**Total available for vend:** ₦{total_available:,}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Accept Offer"):
            vend_amount = min(total_available, vend_price)

            st.info(f"⚡ **Vend completed for ₦{vend_amount:,}**")
            st.markdown("💰 **DisCo paid in full for this vend**")
            st.markdown("📅 **Repayment scheduled on next vend**")

            st.session_state.clear()

    with col2:
        if st.button("❌ Decline Offer"):
            st.warning("Customer declined the credit offer.")
            st.markdown("No vend occurred. No risk taken.")
            st.session_state.clear()
