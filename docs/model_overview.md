# Model Overview – Monsera V0 Behavioural Credit Engine

## 1. Overview

The Monsera V0 Credit Decision Engine is the foundational underwriting engine for prepaid electricity advances.

It is a deterministic, rule-based model designed for early-stage deployment where:

* Historical Monsera repayment data is still limited
* Traditional credit bureau data may be unavailable
* Meter vending behaviour provides useful alternative signals
* Decisions must be explainable
* Credit exposure must remain controlled
* The business needs to generate reliable repayment data for future models

The V0 engine is not a machine-learning model.

Instead, it uses predefined business rules and behavioural thresholds to determine whether a meter is eligible for an electricity advance and, if eligible, how much Monsera is willing to expose.

The same inputs will always produce the same decision under the same configuration.

---

## 2. Primary Objective

The V0 engine answers two main questions:

1. **Should Monsera provide an electricity advance to this meter?**
2. **If yes, what is the maximum amount Monsera should expose?**

The engine uses observed meter behaviour rather than relying primarily on traditional borrower attributes.

The decision flow is:

```text
Historical Meter Transactions
            ↓
Behavioural Feature Engineering
            ↓
Hard Eligibility Gates
            ↓
Behaviour Score
            ↓
Credit Band
            ↓
Capacity-Based Limit Calculation
            ↓
Behavioural Dampeners
            ↓
Band and Global Caps
            ↓
Final Credit Decision
```

---

# 3. Design Principles

The V0 model follows six core principles.

## 3.1 Behaviour Over Identity

The engine primarily evaluates how the electricity meter behaves.

Current behavioural signals include:

* Recent vending activity
* Recency of the most recent successful vend
* Typical vend amount
* Vend amount volatility
* Consistency of vending intervals
* Failed transaction behaviour
* Existing Monsera obligations

The objective is to make a credit decision using observable utility behaviour.

---

## 3.2 Eligibility Before Scoring

Hard eligibility gates are evaluated before behavioural scoring.

These gates are reserved for extreme cases.

The current hard gates are:

```text
Active Monsera obligation
→ Reject

Failed vend ratio >= 85%
→ Reject

More than 120 days since last successful vend
→ Reject
```

If none of these conditions are present, the meter continues to behavioural scoring.

---

## 3.3 Uncertainty Reduces Exposure Before Access

The current V0 model deliberately avoids rejecting meters simply because their purchasing patterns are irregular.

Instead:

```text
Higher uncertainty
        ↓
Lower approved exposure
```

For example:

* High vend amount volatility reduces the advance amount
* High inter-vend variance reduces the advance amount

These factors do not directly create a hard rejection.

This allows Monsera to continue learning while controlling financial exposure.

---

## 3.4 Capacity Comes From Observed Vend Behaviour

The primary capacity signal is:

```text
median_vend_amount
```

The median vend amount represents the customer's typical electricity purchase size.

The engine uses this as the starting point for advance sizing.

The final amount is then adjusted according to behavioural confidence and stability.

---

## 3.5 Thin-History Users Remain Learnable

Limited transaction history is not automatically treated as a reason to reject a meter.

If:

```text
vend_count_last_60_days < 3
```

and the meter passes all hard gates, the current engine approves the minimum starter exposure:

```text
₦2,000
```

This allows Monsera to collect repayment outcomes for users with limited history while keeping initial exposure low.

---

## 3.6 Portfolio Safety Through Exposure Control

The model controls risk primarily through:

* Hard eligibility rules
* Behaviour score
* Credit bands
* Band-specific maximums
* Volatility reductions
* Inter-vend variance reductions
* Global minimum and maximum limits

The current global exposure range is:

```text
Minimum advance: ₦2,000
Maximum advance: ₦20,000
```

---

# 4. Input Features

The current API accepts eight input features.

```json
{
  "vend_count_last_60_days": 8,
  "days_since_last_vend": 5,
  "vend_frequency": 4,
  "median_vend_amount": 4000,
  "vend_amount_volatility": 30,
  "inter_vend_variance": 20,
  "failed_vend_ratio": 10,
  "has_active_obligation": false
}
```

---

## 4.1 `vend_count_last_60_days`

Number of successful electricity vends during the most recent 60-day period.

This feature is used for:

* Activity scoring
* Starter-user identification

Higher recent successful vend activity contributes positively to the behavioural score.

---

## 4.2 `days_since_last_vend`

Number of days since the most recent successful vend.

This feature is used for:

* Recency scoring
* Dormancy hard-gate detection

Recent activity increases the behavioural score.

More than 120 days since the most recent successful vend causes rejection.

---

## 4.3 `vend_frequency`

Estimated average vending frequency.

The current API accepts and validates this feature.

However:

```text
vend_frequency
```

is **not currently used directly** by:

* Hard gates
* Behaviour scoring
* Limit calculation

It remains in the request schema for future model development.

---

## 4.4 `median_vend_amount`

The median amount of successful electricity vending transactions.

This is the main capacity signal used when calculating the approved advance.

The median is preferred over total spend because it better represents the customer's typical vend size and is less sensitive to unusual transactions.

---

## 4.5 `vend_amount_volatility`

Measures how much successful vend amounts vary.

Lower values indicate relatively stable purchasing amounts.

Higher values indicate less predictable purchase sizes.

This feature does not directly affect eligibility or score.

It reduces the approved amount through a volatility dampener.

---

## 4.6 `inter_vend_variance`

Measures variability in the intervals between successful vends.

Lower values indicate more predictable purchasing timing.

Higher values indicate irregular intervals.

This feature does not directly affect eligibility or score.

It reduces the approved amount through a variance dampener.

---

## 4.7 `failed_vend_ratio`

Percentage of transaction attempts that failed.

This feature affects:

* Behaviour score
* Hard eligibility gates

Moderate failed-vend ratios reduce the behavioural score.

An extreme failed-vend ratio of 85% or more causes rejection.

---

## 4.8 `has_active_obligation`

Boolean indicator showing whether the meter currently has an outstanding Monsera obligation.

If:

```text
has_active_obligation = true
```

the current engine rejects the new credit request.

In production, this value should come from Monsera's obligation-management system.

---

# 5. Outputs

For each request, the engine returns:

* Eligibility status
* Approved amount
* Decision reason
* Behaviour score
* Behaviour band

Example:

```json
{
  "eligible": true,
  "approved_amount": 4500,
  "reason": "APPROVED",
  "score": 75,
  "band": "B"
}
```

Rejected example:

```json
{
  "eligible": false,
  "approved_amount": 0,
  "reason": "ACTIVE_OBLIGATION",
  "score": 0,
  "band": "REJECTED"
}
```

---

# 6. Hard Eligibility Gates

The current hard-gate logic is intentionally limited to extreme conditions.

A meter is rejected if any of the following is true.

## Active Obligation

```text
has_active_obligation = true
```

Reason:

```text
ACTIVE_OBLIGATION
```

---

## Extreme Failed Transactions

```text
failed_vend_ratio >= 85
```

Reason:

```text
EXTREME_FAILED_ATTEMPTS
```

---

## Long Dormancy

```text
days_since_last_vend > 120
```

Reason:

```text
LONG_DORMANCY
```

---

# 7. Behaviour Score

Meters that pass the hard gates begin with a neutral score of:

```text
50
```

The score is adjusted using:

* Recent activity
* Recency
* Failed-vend behaviour

The score is always constrained between:

```text
0 and 100
```

---

## Activity

```text
10+ recent successful vends → +20

5–9 recent successful vends → +10

0–4 recent successful vends → +0
```

---

## Recency

```text
0–7 days since last vend → +15

8–30 days → +5

31+ days → +0
```

---

## Failed-Vend Penalty

```text
Below 30% → 0

30%–49.99% → -10

50%–84.99% → -20

85%+ → Hard rejection
```

---

# 8. Behaviour Bands

The current score bands are:

|  Score | Band |
| -----: | :--: |
| 80–100 |   A  |
|  60–79 |   B  |
|  40–59 |   C  |
|   0–39 |   D  |

Band D is not automatically rejected.

A meter that passes the hard gates remains eligible.

The band primarily controls maximum credit exposure.

---

# 9. Band Caps

Current maximum advance per band:

| Band | Maximum Advance |
| :--: | --------------: |
|   A  |         ₦20,000 |
|   B  |         ₦10,000 |
|   C  |          ₦5,000 |
|   D  |          ₦2,000 |

These are ceilings rather than automatic approved amounts.

---

# 10. Starter User Handling

The current starter rule is:

```text
vend_count_last_60_days < 3
```

If this condition is true and the meter passes all hard gates:

```text
approved_amount = ₦2,000
```

Limited history alone does not create a rejection.

---

# 11. Credit Limit Calculation

For meters with at least three successful vends during the 60-day window, limit sizing begins with:

```text
median_vend_amount
```

A score-based confidence multiplier is applied:

```text
confidence_multiplier
=
0.6 + (score / 100 × 0.6)
```

The preliminary limit is:

```text
median_vend_amount
×
confidence_multiplier
```

The engine then applies:

```text
vend_amount_volatility dampener
×
inter_vend_variance dampener
```

The result is rounded to the nearest:

```text
₦500
```

The applicable band cap is then applied.

Finally, the global bounds are enforced:

```text
Minimum = ₦2,000
Maximum = ₦20,000
```

---

# 12. Volatility Dampener

Current values:

| Vend Amount Volatility | Multiplier |
| ---------------------: | ---------: |
|                   ≤ 30 |       1.00 |
|                  31–60 |       0.90 |
|                 61–100 |       0.75 |
|                  > 100 |       0.60 |

Higher volatility reduces exposure.

---

# 13. Inter-Vend Variance Dampener

Current values:

| Inter-Vend Variance | Multiplier |
| ------------------: | ---------: |
|                ≤ 20 |       1.00 |
|               21–50 |       0.90 |
|              51–100 |       0.80 |
|               > 100 |       0.70 |

Higher variance reduces exposure.

---

# 14. Role in the Credit Lifecycle

The V0 model serves three main purposes.

## Initial Credit Decisioning

It provides a deterministic and explainable method for launching utility credit before Monsera has a large repayment dataset.

---

## Controlled Learning

The model allows Monsera to approve controlled amounts and observe:

* Acceptance behaviour
* Actual credit utilisation
* Repayment timing
* Repayment success
* Delinquency
* Default behaviour

---

## Foundation for Future Models

The outcomes generated by V0 can later support:

* Statistical scorecards
* Probability-of-default models
* Machine-learning models
* Fraud models
* Limit optimisation models

V0 is therefore both an underwriting engine and a data-generation mechanism for future model development.

---

# 15. Current Source of Truth

The current implemented V0 decision logic is defined primarily in:

```text
src/credit_engine/config.py

src/credit_engine/hard_gates.py

src/credit_engine/behaviour_score.py

src/credit_engine/limit_engine.py

src/credit_engine/scoring.py

api/main.py
```

