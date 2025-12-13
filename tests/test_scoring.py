import pytest
from credit_engine.scoring import v0_decision


def base_features(**overrides):
    """
    Helper to build a valid base feature set
    and override only what matters per test.
    """
    features = {
        "vend_count_last_60_days": 12,
        "days_since_last_vend": 2,
        "vend_frequency": 3,
        "median_vend_amount": 4000,
        "vend_amount_volatility": 30,
        "inter_vend_variance": 25,
        "failed_vend_ratio": 5,
        "has_active_obligation": False,
    }
    features.update(overrides)
    return features


# Hard gate tests

def test_user_with_active_obligation_is_ineligible():
    result = v0_decision(
        base_features(has_active_obligation=True)
    )

    assert result["eligible"] is False
    assert result["reason"] == "ACTIVE_OUTSTANDING_OBLIGATION"
    assert result["approved_amount"] == 0


def test_insufficient_history_is_rejected():
    result = v0_decision(
        base_features(vend_count_last_60_days=3)
    )

    assert result["eligible"] is False
    assert result["reason"] == "INSUFFICIENT_HISTORY"
    assert result["approved_amount"] == 0


def test_dormant_meter_is_rejected():
    result = v0_decision(
        base_features(days_since_last_vend=45)
    )

    assert result["eligible"] is False
    assert result["reason"] == "DORMANT_METER"
    assert result["approved_amount"] == 0


def test_high_failed_vend_ratio_triggers_gate():
    result = v0_decision(
        base_features(failed_vend_ratio=30)
    )

    assert result["eligible"] is False
    assert result["reason"] == "HIGH_FAILED_ATTEMPTS"
    assert result["approved_amount"] == 0


# Behaviour score & band tests

def test_strong_behaviour_gets_band_a():
    result = v0_decision(
        base_features(
            vend_frequency=6,
            median_vend_amount=7000,
            vend_amount_volatility=20,
            inter_vend_variance=15,
            failed_vend_ratio=2,
        )
    )

    assert result["eligible"] is True
    assert result["score"] >= 80
    assert result["band"] == "A"
    assert result["approved_amount"] >= 2000


def test_good_behaviour_gets_band_b():
    result = v0_decision(
        base_features(
            vend_frequency=4,
            median_vend_amount=5000,
            vend_amount_volatility=35,
            inter_vend_variance=35,
            failed_vend_ratio=5,
        )
    )

    assert result["eligible"] is True
    assert 65 <= result["score"] < 80
    assert result["band"] == "B"


def test_marginal_behaviour_gets_band_c():
    result = v0_decision(
        base_features(
            vend_frequency=2,
            median_vend_amount=3000,
            vend_amount_volatility=50,
            inter_vend_variance=50,
            failed_vend_ratio=8,
        )
    )

    assert result["eligible"] is True
    assert 50 <= result["score"] < 65
    assert result["band"] == "C"
    assert result["approved_amount"] == 2000


def test_weak_behaviour_is_declined():
    result = v0_decision(
        base_features(
            vend_frequency=1,
            median_vend_amount=1500,
            vend_amount_volatility=80,
            inter_vend_variance=70,
            failed_vend_ratio=15,
        )
    )

    assert result["eligible"] is True
    assert result["score"] < 50
    assert result["band"] == "D"
    assert result["approved_amount"] == 0


# Limit sizing & risk adjustments

def test_limit_scales_with_median_vend_amount():
    low = v0_decision(
        base_features(median_vend_amount=3000)
    )
    high = v0_decision(
        base_features(median_vend_amount=6000)
    )

    assert high["approved_amount"] > low["approved_amount"]


def test_high_volatility_does_not_increase_limit():
    normal = v0_decision(
        base_features(vend_amount_volatility=30)
    )
    volatile = v0_decision(
        base_features(vend_amount_volatility=80)
    )

    assert volatile["approved_amount"] <= normal["approved_amount"]


def test_low_frequency_does_not_increase_limit():
    normal = v0_decision(
        base_features(vend_frequency=3)
    )
    low_freq = v0_decision(
        base_features(vend_frequency=1)
    )

    assert low_freq["approved_amount"] <= normal["approved_amount"]
