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
The system approves an **amount**, not a forced vend.
Customers can accept **full or partial power**, just like normal prepaid vending.
"""
)
# Demo scenarios (behavioural profiles)

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

if st.button("Simulate Vend"):
    if wallet_balance >= vend_price:
        st.success("✅ Vend completed without credit.")
        st.markdown("💰 DisCo paid in full.")
    else:
        st.warning("⚠️ Insufficient balance. Aggregator requests Monsera decision…")

        response = requests.post(API_URL, json=SCENARIOS[scenario])
        decision = response.json()

        if not decision["eligible"]:
            st.error("❌ Credit declined")
            st.markdown(f"**Reason:** {decision['reason']}")
        else:
            approved = decision["approved_amount"]

            st.success("✅ Credit approved")
            st.markdown(f"**Approved advance:** ₦{approved:,}")

            total_available = wallet_balance + approved

            st.markdown(
                f"""
**Total available for vend:** ₦{total_available:,}

The customer can:
- Proceed with a **partial vend**
- Top up wallet and vend more
- Decline the offer
"""
            )

            if total_available > 0:
                vend_amount = min(total_available, vend_price)

                st.info(f"⚡ **Vend completed for ₦{vend_amount:,}**")
                st.markdown("💰 **DisCo paid in full for this vend**")
                st.markdown("📅 **Repayment scheduled on next vend**")
            else:
                st.warning("Approved amount is zero. No vend possible.")
