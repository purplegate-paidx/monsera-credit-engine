import pandas as pd
from datetime import timedelta

from src.credit_engine.scoring import v0_decision

# ---------------------------------------------
# Configuration
# ---------------------------------------------

SUCCESS_STATUSES = {"SUCCESS", "COMPLETED"}

SCENARIOS = {
    "Conservative": {
        "max_failed_ratio": 50,
        "max_dormancy_days": 60,
    },
    "Balanced": {
        "max_failed_ratio": 70,
        "max_dormancy_days": 90,
    },
    "Learning_Heavy": {
        "max_failed_ratio": 85,
        "max_dormancy_days": 120,
    },
}

INPUT_PATH = "demo/data/consolidated_transactions.csv"
OUTPUT_PATH = "Monsera_V0_Scenario_Results.xlsx"

# ---------------------------------------------
# Load data
# ---------------------------------------------

df = pd.read_csv(INPUT_PATH)
df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"])

today = df["Transaction_Date"].max()
scenario_results = {name: [] for name in SCENARIOS}

# ---------------------------------------------
# Feature engineering per user
# ---------------------------------------------

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

    vend_amount_volatility = (
        successful["Amount"].std() / median_vend * 100
        if vend_count > 1 and median_vend > 0
        else 0
    )

    inter_vend_variance = (
        successful["Transaction_Date"]
        .diff()
        .dt.days
        .var()
        if vend_count > 2
        else 0
    )

    days_since_last = (
        (today - successful["Transaction_Date"].max()).days
        if vend_count
        else 999
    )

    base_features = {
        "vend_count_last_60_days": int(vend_count),
        "days_since_last_vend": int(days_since_last),
        "vend_frequency": float(vend_count / 2),  # informational only
        "median_vend_amount": float(median_vend),
        "vend_amount_volatility": float(vend_amount_volatility),
        "inter_vend_variance": float(inter_vend_variance),
        "failed_vend_ratio": float(failed_ratio),
        "has_active_obligation": False,
    }

    service_provider = user_df["Service_Provider"].iloc[0]

    # ---------------------------------------------
    # Scenario evaluation
    # ---------------------------------------------

    for scenario, rules in SCENARIOS.items():
        features = base_features.copy()

        # Scenario tolerance (policy overlay, not model rewrite)
        features["failed_vend_ratio"] = min(
            features["failed_vend_ratio"],
            rules["max_failed_ratio"],
        )
        features["days_since_last_vend"] = min(
            features["days_since_last_vend"],
            rules["max_dormancy_days"],
        )

        decision = v0_decision(features)

        scenario_results[scenario].append({
            "User_ID": user_id,
            "Service_Provider": service_provider,

            # Decision outputs (authoritative)
            "eligible": decision["eligible"],
            "band": decision["band"],
            "score": decision["score"],
            "approved_amount": decision["approved_amount"],
            "reason": decision["reason"],

            # Core behavioural inputs
            "vend_count_last_60_days": vend_count,
            "median_vend_amount": median_vend,
            "vend_amount_volatility": vend_amount_volatility,
            "inter_vend_variance": inter_vend_variance,
            "failed_vend_ratio_observed": failed_ratio,
            "days_since_last_vend_observed": days_since_last,

            # Scenario-adjusted inputs (explicit)
            "scenario_failed_ratio_used": features["failed_vend_ratio"],
            "scenario_days_since_last_vend_used": features["days_since_last_vend"],
        })

# ---------------------------------------------
# Write Excel output
# ---------------------------------------------

with pd.ExcelWriter(
    OUTPUT_PATH,
    engine="xlsxwriter"
) as writer:
    for scenario, rows in scenario_results.items():
        pd.DataFrame(rows).to_excel(
            writer,
            sheet_name=scenario,
            index=False,
        )

print(f"✅ Excel output generated: {OUTPUT_PATH}")
