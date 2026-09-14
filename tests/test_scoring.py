import pytest
from credit_engine.scoring import v0_decision


def base_features(**overrides):
    features = {
        "vend_count_last_60_days": 8,
        "days_since_last_vend": 5,
        "vend_frequency": 3,
        "median_vend_amount": 4000,
        "vend_amount_volatility": 30,
        "inter_vend_variance": 20,
        "failed_vend_ratio": 10,
        "has_active_obligation": False,
    }
    features.update(overrides)
    return features


# ==================================================
# HARD DECLINES (EXTREME ONLY)
# ==================================================

def test_active_obligation_is_declined():
    result = v0_decision(base_features(has_active_obligation=True))
    assert result["eligible"] is False
    assert result["approved_amount"] == 0


def test_extreme_failed_attempts_are_declined():
    result = v0_decision(base_features(failed_vend_ratio=90))
    assert result["eligible"] is False
    assert result["approved_amount"] == 0


def test_long_term_dormant_meter_is_declined():
    result = v0_decision(base_features(days_since_last_vend=150))
    assert result["eligible"] is False
    assert result["approved_amount"] == 0


# ==================================================
# STARTER / LEARNING USERS
# ==================================================

def test_low_history_user_gets_minimum():
    result = v0_decision(base_features(vend_count_last_60_days=1))
    assert result["eligible"] is True
    assert result["approved_amount"] == 2000


# ==================================================
# VOLATILITY & VARIANCE (SOFT ONLY)
# ==================================================

def test_high_volatility_does_not_decline():
    result = v0_decision(base_features(vend_amount_volatility=95))
    assert result["eligible"] is True
    assert result["approved_amount"] >= 2000


def test_high_variance_reduces_amount_not_band():
    low_var = v0_decision(base_features(inter_vend_variance=10))
    high_var = v0_decision(base_features(inter_vend_variance=150))

    assert low_var["band"] == high_var["band"]
    assert high_var["approved_amount"] < low_var["approved_amount"]


# ==================================================
# CAPACITY DRIVES AMOUNT
# ==================================================

def test_higher_median_vend_gets_higher_amount():
    low = v0_decision(base_features(median_vend_amount=2500))
    high = v0_decision(base_features(median_vend_amount=10000))

    assert high["approved_amount"] > low["approved_amount"]


def test_band_b_not_collapsed_to_minimum():
    result = v0_decision(
        base_features(
            median_vend_amount=5000,
            vend_count_last_60_days=8,
        )
    )
    assert result["band"] in ["A", "B"]
    assert result["approved_amount"] > 2000


# ==================================================
# ABSOLUTE INVARIANT
# ==================================================

def test_eligible_user_never_gets_zero():
    result = v0_decision(base_features(vend_amount_volatility=99))
    assert result["eligible"] is True
    assert result["approved_amount"] >= 2000


def test_band_c_or_b_cap_enforced():
    result = v0_decision(
        base_features(
            failed_vend_ratio=35,
            median_vend_amount=30000,
        )
    )

    if result["band"] == "C":
        assert result["approved_amount"] <= 5000
    elif result["band"] == "B":
        assert result["approved_amount"] <= 10000


def test_band_b_cap_enforced():
    result = v0_decision(
        base_features(
            median_vend_amount=30000,
            vend_count_last_60_days=6,
        )
    )

    assert result["band"] == "B"
    assert result["approved_amount"] <= 10000


def test_band_a_can_reach_global_max():
    result = v0_decision(
        base_features(
            vend_count_last_60_days=12,
            median_vend_amount=50000,
            failed_vend_ratio=5,
        )
    )

    assert result["band"] == "A"
    assert result["approved_amount"] <= 20000

