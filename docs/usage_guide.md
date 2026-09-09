# Usage Guide – V0 Credit Engine

This guide explains how to use the V0 credit model both programmatically and via the API.

---

## 1. Feature Preparation

Aggregators or Monsera compute behavioural features per meter:

- Vend count (last 60–90 days)
- Median vend amount
- Vend frequency
- Volatility metrics
- Failed vend ratio
- Days since last vend
- Outstanding obligation flag

---

## 2. Decision Flow

Call the decision engine with prepared features.

Example (Python):

```python
from credit_engine.scoring import v0_decision

decision = v0_decision(features)
```

---

## Api Usage

### `POST /decision`

```json
{
  "vend_count_last_60_days": 12,
  "days_since_last_vend": 3,
  "vend_frequency": 3,
  "median_vend_amount": 4000,
  "vend_amount_volatility": 35,
  "inter_vend_variance": 30,
  "failed_vend_ratio": 6,
  "has_active_obligation": false
}
```
## Response

```json
{
  "eligible": true,
  "score": 72,
  "band": "B",
  "approved_amount": 3200
}
```

## 4. Decline Example

```json
{
  "eligible": false,
  "reason": "INSUFFICIENT_HISTORY",
  "approved_amount": 0
}
```

## 5. Operational Notes

- Approved amount may be less than requested
- Portfolio-level caps may override approvals
- All decisions are logged for monitoring and model evolution

---

## 6. Common Use Cases

- Embed directly in backend services for real-time scoring
- Use as a decision engine behind utility or payment platforms
- Run in batch mode for portfolio risk analysis
- Serve as a baseline for comparison with machine learning models

---

## 7. Best Practices & Notes

- **Input Validation:** Always validate inputs before passing to the scoring function
- **Monitoring:** Regularly track approval rates and default rates
- **Baseline Role:** Treat V0 as a **conservative starting point**, not a final solution
- **Logging:** Record scores and outcomes to support future model training and validation