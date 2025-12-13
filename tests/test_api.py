from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def base_payload(**overrides):
    """
    Helper to build a valid base decision payload
    and override only what matters per test.
    """
    payload = {
        "vend_count_last_60_days": 12,
        "days_since_last_vend": 2,
        "vend_frequency": 3,
        "median_vend_amount": 4000,
        "vend_amount_volatility": 30,
        "inter_vend_variance": 25,
        "failed_vend_ratio": 5,
        "has_active_obligation": False,
    }
    payload.update(overrides)
    return payload


# Successful decision scenarios

def test_decision_endpoint_bankable_user():
    """
    Test that the /decision endpoint returns
    a valid approval for a good behavioural profile.
    """

    response = client.post(
        "/decision",
        json=base_payload(
            vend_frequency=4,
            median_vend_amount=5000,
            vend_amount_volatility=35,
            inter_vend_variance=30,
            failed_vend_ratio=5,
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["eligible"] is True
    assert "score" in data
    assert "band" in data
    assert "approved_amount" in data

    assert data["band"] in ["A", "B", "C"]
    assert data["approved_amount"] >= 2000


def test_decision_endpoint_prime_user():
    """
    Strong behavioural users should receive
    higher approved amounts.
    """

    response = client.post(
        "/decision",
        json=base_payload(
            vend_frequency=6,
            median_vend_amount=8000,
            vend_amount_volatility=20,
            inter_vend_variance=15,
            failed_vend_ratio=2,
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["eligible"] is True
    assert data["band"] == "A"
    assert data["approved_amount"] > 2000


# Decline scenarios (hard gates)

def test_decision_endpoint_rejects_active_obligation():
    """
    Meters with an active obligation
    should be declined immediately.
    """

    response = client.post(
        "/decision",
        json=base_payload(has_active_obligation=True),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["eligible"] is False
    assert data["reason"] == "ACTIVE_OUTSTANDING_OBLIGATION"
    assert data["approved_amount"] == 0


def test_decision_endpoint_rejects_insufficient_history():
    """
    Meters with insufficient recent activity
    should be rejected at the hard gate stage.
    """

    response = client.post(
        "/decision",
        json=base_payload(vend_count_last_60_days=3),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["eligible"] is False
    assert data["reason"] == "INSUFFICIENT_HISTORY"
    assert data["approved_amount"] == 0


def test_decision_endpoint_rejects_dormant_meter():
    """
    Dormant meters should not be scored.
    """

    response = client.post(
        "/decision",
        json=base_payload(days_since_last_vend=45),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["eligible"] is False
    assert data["reason"] == "DORMANT_METER"
    assert data["approved_amount"] == 0
