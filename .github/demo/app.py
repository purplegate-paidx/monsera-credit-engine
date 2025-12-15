import streamlit as st
import requests

API_URL = "https://monsera-credit-engine.onrender.com/decision"

st.set_page_config(
    page_title="Monsera Credit Demo",
    layout="centered"
)

st.title("⚡ Monsera Pay-Later Demo")
st.subheader("Simulating a prepaid electricity vend")

st.markdown(
    """
This demo simulates how Monsera enables **safe electricity advances**
without exposing DisCos to credit risk.
"""
)

# User scenarios

SCENARIOS = {
    "Consistent Household": {
        "vend_count_last_60_days": 15,
        "days_since_last_vend": 2,
        "vend_frequency": 4,
        "median_vend_amount": 4500,
        "vend_amount_volatility": 25,
        "inter_vend_variance": 20,
        "failed_vend_ratio": 3,
        "has_active_obligation": False,
    },
    "Marginal Household": {
        "vend_count_last_60_days": 8,
        "days_since_last_vend": 3,
        "vend_frequency": 2,
        "median_vend_amount": 3000,
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
    value=500,
    step=500
)

vend_price = st.number_input(
    "Electricity needed (₦)",
    min_value=1000,
    value=4000,
    step=500
)

if st.button("Simulate Vend"):
    st.markdown("---")

    if wallet_balance >= vend_price:
        st.success("Vend completed without credit.")
    else:
        st.warning("Insufficient balance. Aggregator requests Monsera decision…")

        response = requests.post(API_URL, json=SCENARIOS[scenario])
        decision = response.json()

        if not decision["eligible"]:
            st.error("Credit declined")
            st.markdown(f"**Reason:** {decision['reason']}")
        else:
            approved = decision["approved_amount"]

            st.success("Credit approved")
            st.markdown(f"**Approved advance:** ₦{approved:,}")

            if wallet_balance + approved >= vend_price:
                st.markdown("⚡ **Vend completed successfully**")
                st.markdown("💰 **DisCo paid in full immediately**")
                st.markdown("📅 **Repayment occurs on next vend**")
            else:
                st.warning("Approved amount not sufficient to complete vend.")
