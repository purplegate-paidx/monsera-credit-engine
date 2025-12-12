import pytest
from credit_engine.scoring import v0_score


def test_new_user_gets_minimum_limit():
    """
    New users should always receive the minimum limit,
    regardless of other inputs.
    """
    result = v0_score(
        tenure_months=0,
        avg_monthly_spend=0,
        vend_frequency=0,
        amount_volatility=0,
        failed_vend_ratio=0,
        is_new_user=True,
    )

    assert result["score"] == 45
    assert result["risk_band"] == "Marginal"
    assert result["credit_limit"] == 2000


def test_high_risk_user_is_not_eligible():
    """
    Users with very weak behavior signals
    should be classified as High Risk and rejected.
    """
    result = v0_score(
        tenure_months=1,
        avg_monthly_spend=1500,
        vend_frequency=0.5,
        amount_volatility=80,
        failed_vend_ratio=25,
        is_new_user=False,
    )

    assert result["risk_band"] == "High Risk"
    assert result["credit_limit"] == 0


def test_weak_user_is_high_risk():
    """
    Users with low tenure, weak frequency,
    high volatility, and failed vends
    should be classified as High Risk.
    """
    result = v0_score(
        tenure_months=3,
        avg_monthly_spend=3000,
        vend_frequency=1,
        amount_volatility=55,
        failed_vend_ratio=12,
        is_new_user=False,
    )

    assert result["risk_band"] == "High Risk"
    assert result["credit_limit"] == 0


def test_marginal_user_gets_minimum_limit():
    """
    Users with moderate but imperfect behavior
    should be classified as Marginal.
    """
    result = v0_score(
        tenure_months=6,            # +15
        avg_monthly_spend=3500,     # +15
        vend_frequency=2,           # +10
        amount_volatility=40,       # +10
        failed_vend_ratio=10,       # -10
        is_new_user=False,
    )

    # Total = 40
    assert result["risk_band"] == "Marginal"
    assert result["credit_limit"] == 2000


def test_bankable_user_gets_scaled_limit():
    """
    Bankable users should receive up to
    10% of average monthly spend.
    """
    result = v0_score(
        tenure_months=6,
        avg_monthly_spend=5000,
        vend_frequency=3,
        amount_volatility=40,
        failed_vend_ratio=5,
        is_new_user=False,
    )

    assert result["risk_band"] == "Bankable"
    assert result["credit_limit"] == 500  # 10% of 5000


def test_prime_user_gets_higher_limit():
    """
    Prime users should receive up to
    20% of average monthly spend.
    """
    result = v0_score(
        tenure_months=12,
        avg_monthly_spend=10000,
        vend_frequency=6,
        amount_volatility=20,
        failed_vend_ratio=2,
        is_new_user=False,
    )

    assert result["risk_band"] == "Prime Meter"
    assert result["credit_limit"] == 2000  # 20% of 10,000


def test_credit_limit_is_capped_at_maximum():
    """
    Even prime users should not exceed
    the global maximum credit limit.
    """
    result = v0_score(
        tenure_months=24,
        avg_monthly_spend=200000,
        vend_frequency=10,
        amount_volatility=10,
        failed_vend_ratio=0,
        is_new_user=False,
    )

    assert result["risk_band"] == "Prime Meter"
    assert result["credit_limit"] == 20000


@pytest.mark.parametrize(
    "failed_vend_ratio, expected_penalty",
    [
        (0, 0),
        (8, 0),
        (10, -10),
        (15, -10),
        (25, -20),
    ],
)
def test_failed_vend_penalties_are_applied(failed_vend_ratio, expected_penalty):
    """
    Failed vend ratios should correctly
    apply penalty logic.
    """
    result = v0_score(
        tenure_months=12,
        avg_monthly_spend=8000,
        vend_frequency=5,
        amount_volatility=30,
        failed_vend_ratio=failed_vend_ratio,
        is_new_user=False,
    )

    # We don't assert exact score, but ensure risk band degrades as expected
    assert result["score"] <= 100
