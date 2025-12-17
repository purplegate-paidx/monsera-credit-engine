import pandas as pd
from datetime import timedelta

from src.credit_engine.scoring import v0_decision

# --------------------------------------------------
# Scenario definitions
# --------------------------------------------------

SCENARIOS = {
    "Scenario_Conservative": {
        "max_failed_ratio": 50,
        "max_dormancy_days": 60,
        "exposure_multiplier": 0.6,
    },
    "Scenario_Balanced": {
        "max_failed_ratio": 70,
        "max_dormancy_days": 90,
        "exposure_multiplier": 1.0,
    },
    "Scenario_Learning_Heavy": {
        "max_failed_ratio": 85,
        "max_dormancy_days": 120,
        "exposure_multiplier": 1.3,
    },
}

SUCCESS_STATUSES = {"SUCCESS", "COMPLETED", "SUCCESSFUL"}

# --------------------------------------------------
# Load data
# --------------------------------------------------

df = pd.read_csv("demo/data/consolidated_transactions.csv")
df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"])

today = df["Transaction_Date"].max()

# --------------------------------------------------
# Prepare Excel writer
# --------------------------------------------------

writer = pd.ExcelWriter(
    "Monsera_V0_Scenario_Results.xlsx",
    engine="xlsxwriter"
)

# --------------------------------------------------
# Generate one sheet per scenario
# --------------------------------------------------

for scenario_name, rules in SCENARIOS.items():
    rows = []

    for user_id, user_df in df.groupby("User_ID"):
        user_df = user_df.sort_values("Transaction_Date")

        window_start = today - timedelta(days=60)
        recent = user_df[user_df["Transaction_Date"] >= window_start]
        successful = recent[recent["Status"].isin(SUCCESS_STATUSES)]

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

        # Apply scenario soft caps
        adjusted_failed_ratio = min(
            failed_ratio,
            rules["max_failed_ratio"],
        )

        adjusted_days_since_last = min(
            days_since_last,
            rules["max_dormancy_days"],
        )

        features = {
            "vend_count_last_60_days": vend_count,
            "days_since_last_vend": adjusted_days_since_last,
            "vend_frequency": vend_count / 2,
            "median_vend_amount": median_vend,
            "vend_amount_volatility": volatility,
            "inter_vend_variance": 0,
            "failed_vend_ratio": adjusted_failed_ratio,
            "has_active_obligation": False,
        }

        decision = v0_decision(features)

        rows.append({
            "User_ID": user_id,
            "Service_Provider": user_df["Service_Provider"].iloc[0],
            "eligible": decision.get("eligible"),
            "approved_amount": decision.get("approved_amount"),
            "reason": decision.get("reason", "APPROVED"),
            "vend_count_last_60_days": vend_count,
            "failed_vend_ratio": failed_ratio,
            "median_vend_amount": median_vend,
            "days_since_last_vend": days_since_last,
        })

    scenario_df = pd.DataFrame(rows)
    scenario_df.to_excel(writer, sheet_name=scenario_name, index=False)

writer.close()

print("Excel output generated: Monsera_V0_Scenario_Results.xlsx")
