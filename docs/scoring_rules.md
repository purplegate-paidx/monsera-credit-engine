# Scoring Rules – V0 Model

This document details the exact rules and weights used to compute the V0 credit score.

The total score ranges from **0 to 100** and is derived by summing contributions from multiple factors.

---

## 1. Tenure (Meter Age)

Measures the stability and longevity of the meter.

| Tenure (Months) | Score |
|-----------------|-------|
| ≥ 12            | +20   |
| 6–11            | +15   |
| 3–5             | +10   |
| < 3             | +5    |

---

## 2. Average Monthly Spend

Serves as a proxy for consumption capacity and repayment ability.

| Monthly Spend (₦) | Score |
|-------------------|-------|
| ≥ 8,000           | +25   |
| 5,000–7,999       | +20   |
| 3,000–4,999       | +15   |
| < 3,000           | +10   |

---

## 3. Vend Frequency

Captures consistency and regularity of usage.

| Vends per Month | Score |
|-----------------|-------|
| ≥ 5             | +20   |
| 3–4             | +15   |
| 1–2             | +10   |
| < 1             | +5    |

---

## 4. Amount Volatility

Measures stability of vend amounts over time.

| Volatility (%) | Score |
|---------------|-------|
| ≤ 30%         | +20   |
| 31–60%        | +10   |
| > 60%         | +5    |

---

## 5. Failed Vend Penalties

Failed vending attempts indicate liquidity stress or operational issues.

| Failed Vend Ratio | Penalty |
|-------------------|---------|
| ≥ 20%             | −20     |
| 10–19%            | −10     |
| < 10%             | 0       |

---

## Score Bounding

After all components are summed, the final score is **clamped between 0 and 100** to prevent out-of-range values.

---

## Risk Band Mapping

| Score Range | Risk Band   |
|------------|-------------|
| 0–39       | High Risk   |
| 40–59      | Marginal    |
| 60–79      | Bankable    |
| 80–100     | Prime Meter |

---

## Credit Limit Rules

| Risk Band   | Credit Limit Rule |
|------------|-------------------|
| High Risk  | ₦0 (not eligible) |
| Marginal   | ₦2,000 (minimum) |
| Bankable   | Up to 10% of avg monthly spend (max ₦10,000) |
| Prime      | Up to 20% of avg monthly spend (max ₦20,000) |

---

These rules are intentionally conservative and designed for early-stage deployment.
