from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_score_endpoint_bankable_user():
    """
    Test that the /score endpoint returns a valid response
    for a typical bankable user.
    """

    payload = {
        "tenure_months": 6,
        "avg_monthly_spend": 4500,
        "vend_frequency": 3,
        "amount_volatility": 40,
        "failed_vend_ratio": 8,
        "is_new_user": False
    }

    response = client.post("/score", json=payload)

    assert response.status_code == 200

    data = response.json()

    # Validate response structure
    assert "score" in data
    assert "risk_band" in data
    assert "credit_limit" in data

    # Validate expected logic
    assert data["risk_band"] in ["Marginal", "Bankable", "Prime Meter"]
    assert data["credit_limit"] >= 0


def test_score_endpoint_new_user():
    """
    Test that new users always receive the minimum limit.
    """

    payload = {
        "tenure_months": 0,
        "avg_monthly_spend": 0,
        "vend_frequency": 0,
        "amount_volatility": 0,
        "failed_vend_ratio": 0,
        "is_new_user": True
    }

    response = client.post("/score", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["risk_band"] == "Marginal"
    assert data["credit_limit"] == 2000
