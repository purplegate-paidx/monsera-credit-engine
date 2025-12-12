# Usage Guide – V0 Credit Engine

This guide explains how to use the V0 credit model both programmatically and via the API.

---

## 1. Direct Python Usage

The core scoring logic can be imported directly into your Python code.

### Example

```python
from credit_engine.scoring import v0_score

result = v0_score(
    tenure_months=6,
    avg_monthly_spend=4500,
    vend_frequency=3,
    amount_volatility=40,
    failed_vend_ratio=8,
    is_new_user=False
)

print(result)
```

### Sample Output

```json
{
  "score": 68,
  "risk_band": "Bankable",
  "credit_limit": 4500
}
```

---

## 2. API Usage

The model is also exposed as a FastAPI service.

### Start the API Server

```bash
uvicorn api.main:app --reload
```

---

## 3. API Endpoint Reference

### `POST /score`

#### Request Body

```json
{
  "tenure_months": 6,
  "avg_monthly_spend": 4500,
  "vend_frequency": 3,
  "amount_volatility": 40,
  "failed_vend_ratio": 8,
  "is_new_user": false
}
```

#### Response

```json
{
  "score": 68,
  "risk_band": "Bankable",
  "credit_limit": 4500
}
```

---

## 4. Example: New User

For users with no historical data, set `is_new_user` to `true` and provide zero values for other fields.

#### Request

```json
{
  "tenure_months": 0,
  "avg_monthly_spend": 0,
  "vend_frequency": 0,
  "amount_volatility": 0,
  "failed_vend_ratio": 0,
  "is_new_user": true
}
```

#### Response

```json
{
  "score": 45,
  "risk_band": "Marginal",
  "credit_limit": 2000
}
```

---

## 5. Common Use Cases

- Embed directly in backend services for real-time scoring
- Use as a decision engine behind utility or payment platforms
- Run in batch mode for portfolio risk analysis
- Serve as a baseline for comparison with machine learning models

---

## 6. Best Practices & Notes

- **Input Validation:** Always validate inputs before passing to the scoring function
- **Monitoring:** Regularly track approval rates and default rates
- **Baseline Role:** Treat V0 as a **conservative starting point**, not a final solution
- **Logging:** Record scores and outcomes to support future model training and validation