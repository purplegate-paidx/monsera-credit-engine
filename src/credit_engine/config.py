"""
Configuration for the V0 credit scoring model.

All scoring weights, thresholds, and limits live here
so business logic can be adjusted without changing code.
"""

# --- Tenure scoring weights ---
TENURE_WEIGHTS = {
    ">=12": 20,
    "6-11": 15,
    "3-5": 10,
    "<3": 5,
}

# --- Monthly spend scoring weights ---
SPEND_WEIGHTS = {
    ">=8000": 25,
    "5000-7999": 20,
    "3000-4999": 15,
    "<3000": 10,
}

# --- Vend frequency scoring weights ---
FREQUENCY_WEIGHTS = {
    ">=5": 20,
    "3-4": 15,
    "1-2": 10,
    "<1": 5,
}

# --- Amount volatility scoring weights ---
VOLATILITY_WEIGHTS = {
    "<=30": 20,
    "31-60": 10,
    ">60": 5,
}

# --- Failed vend penalties ---
FAILED_VEND_PENALTIES = {
    ">=20": -20,
    "10-19": -10,
    "<10": 0,
}

# --- Credit limits ---
MIN_LIMIT = 2000
MAX_LIMIT = 20000
