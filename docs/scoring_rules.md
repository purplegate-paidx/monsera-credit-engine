# Scoring Rules – Monsera V0 Behavioural Credit Engine

## 1. Overview

This document defines the current scoring, eligibility, banding, and credit-limit rules used by the Monsera V0 Credit Decision Engine.

The V0 model is deterministic.

Given the same inputs and configuration, the engine returns the same decision.

The decision process has four stages:

```text
1. Hard Eligibility Gates
        ↓
2. Behaviour Score
        ↓
3. Behaviour Band
        ↓
4. Advance Limit Calculation
```

---

# 2. Hard Eligibility Gates

Hard gates are checked before the behaviour score is calculated.

These gates are intentionally reserved for extreme cases.

A meter is rejected if any of the following conditions applies.

---

## 2.1 Active Obligation

Rule:

```text
has_active_obligation = true
```

Decision:

```text
REJECT
```

Reason:

```text
ACTIVE_OBLIGATION
```

Approved amount:

```text
₦0
```

The purpose of this rule is to prevent multiple simultaneous Monsera obligations on the same meter.

---

## 2.2 Extreme Failed Vend Ratio

Rule:

```text
failed_vend_ratio >= 85
```

Decision:

```text
REJECT
```

Reason:

```text
EXTREME_FAILED_ATTEMPTS
```

Approved amount:

```text
₦0
```

Examples:

```text
20% → Pass hard gate

40% → Pass hard gate

60% → Pass hard gate

80% → Pass hard gate

85% → Reject

90% → Reject
```

Moderate failure rates affect the behaviour score instead of automatically removing access.

---

## 2.3 Long Dormancy

Rule:

```text
days_since_last_vend > 120
```

Decision:

```text
REJECT
```

Reason:

```text
LONG_DORMANCY
```

Approved amount:

```text
₦0
```

Examples:

```text
30 days → Pass

60 days → Pass

90 days → Pass

120 days → Pass

121 days → Reject
```

---

# 3. Behaviour Score

A meter that passes all hard gates receives a behaviour score.

The score starts from:

```text
50
```

This is the neutral baseline.

The score is then adjusted using three behavioural dimensions:

1. Recent activity
2. Recency
3. Failed-vend behaviour

The final score is constrained between:

```text
0 and 100
```

---

# 4. Activity Score

Activity is measured using:

```text
vend_count_last_60_days
```

Current rules:

| Successful Vends in Last 60 Days | Adjustment |
| -------------------------------: | ---------: |
|                              10+ |        +20 |
|                              5–9 |        +10 |
|                              0–4 |         +0 |

Example:

```text
Base score = 50

vend_count_last_60_days = 12

Activity adjustment = +20

Current score = 70
```

---

# 5. Recency Score

Recency is measured using:

```text
days_since_last_vend
```

Current rules:

| Days Since Last Successful Vend | Adjustment |
| ------------------------------: | ---------: |
|                             0–7 |        +15 |
|                            8–30 |         +5 |
|                             31+ |         +0 |

Example:

```text
Current score = 70

days_since_last_vend = 3

Recency adjustment = +15

Current score = 85
```

---

# 6. Failed-Vend Penalty

Failed-vend behaviour is measured using:

```text
failed_vend_ratio
```

Current rules:

| Failed Vend Ratio |  Adjustment |
| ----------------: | ----------: |
|         Below 30% |           0 |
|        30%–49.99% |         -10 |
|        50%–84.99% |         -20 |
|              85%+ | Hard Reject |

Example:

```text
Current score = 85

failed_vend_ratio = 35%

Penalty = -10

Final score = 75
```

---

# 7. Complete Score Formula

Conceptually:

```text
Behaviour Score
=
50
+ Activity Adjustment
+ Recency Adjustment
- Failed Vend Penalty
```

The result is then constrained to:

```text
0 <= score <= 100
```

Example:

```text
Base Score                    50

10+ Recent Vends             +20

Vend Within 7 Days           +15

Failed Ratio 30%–49.99%      -10
--------------------------------
Final Score                   75
```

---

# 8. Behaviour Bands

The score is mapped to a behavioural band.

Current implementation:

|  Score | Band |
| -----: | :--: |
| 80–100 |   A  |
|  60–79 |   B  |
|  40–59 |   C  |
|   0–39 |   D  |

Examples:

```text
Score 85 → Band A

Score 75 → Band B

Score 55 → Band C

Score 35 → Band D
```

---

# 9. Eligibility and Bands

Bands A, B, C, and D are all eligible under the current implementation provided the meter passed the hard gates.

Band D is not a decline band.

Instead, Band D is restricted to the minimum exposure.

The only automatic declines in the current V0 model come from the hard gates.

---

# 10. Band Caps

Each band has a maximum approved advance.

| Band | Maximum Advance |
| :--: | --------------: |
|   A  |         ₦20,000 |
|   B  |         ₦10,000 |
|   C  |          ₦5,000 |
|   D  |          ₦2,000 |

These are maximums.

The actual approved amount may be lower depending on behavioural capacity and volatility.

---

# 11. Starter User Rule

The current limited-history threshold is:

```text
vend_count_last_60_days < 3
```

If the meter passes the hard gates:

```text
approved_amount = ₦2,000
```

Therefore:

```text
0 recent successful vends → ₦2,000*

1 recent successful vend → ₦2,000

2 recent successful vends → ₦2,000
```

`*` Other fields such as `days_since_last_vend` may still cause a hard rejection.

Limited history itself does not cause rejection.

---

# 12. Credit Limit Calculation

For meters with three or more recent successful vends, the engine calculates a behavioural limit.

The calculation starts from:

```text
median_vend_amount
```

This represents the customer's typical electricity vend size.

---

# 13. Confidence Multiplier

The score is converted into a confidence multiplier using:

```text
confidence_multiplier
=
0.6 + (score / 100 × 0.6)
```

Examples:

| Score | Confidence Multiplier |
| ----: | --------------------: |
|    40 |                  0.84 |
|    50 |                  0.90 |
|    60 |                  0.96 |
|    70 |                  1.02 |
|    80 |                  1.08 |
|    90 |                  1.14 |
|   100 |                  1.20 |

The initial amount is:

```text
base_limit
=
median_vend_amount
×
confidence_multiplier
```

Example:

```text
median_vend_amount = ₦5,000

score = 70

confidence_multiplier = 1.02
```

Therefore:

```text
base_limit
=
₦5,000 × 1.02
=
₦5,100
```

---

# 14. Vend Amount Volatility Dampener

The engine then adjusts the amount using:

```text
vend_amount_volatility
```

Current rules:

| Vend Amount Volatility | Multiplier |
| ---------------------: | ---------: |
|                   ≤ 30 |       1.00 |
|                  31–60 |       0.90 |
|                 61–100 |       0.75 |
|                  > 100 |       0.60 |

Example:

```text
base_limit = ₦5,100

vend_amount_volatility = 50

multiplier = 0.90
```

Result:

```text
₦5,100 × 0.90
=
₦4,590
```

Vend amount volatility affects the limit only.

It does not currently change:

* Eligibility
* Score
* Band

---

# 15. Inter-Vend Variance Dampener

The engine also adjusts the limit using:

```text
inter_vend_variance
```

Current rules:

| Inter-Vend Variance | Multiplier |
| ------------------: | ---------: |
|                ≤ 20 |       1.00 |
|               21–50 |       0.90 |
|              51–100 |       0.80 |
|               > 100 |       0.70 |

Example:

```text
current amount = ₦4,590

inter_vend_variance = 30

multiplier = 0.90
```

Result:

```text
₦4,590 × 0.90
=
₦4,131
```

Inter-vend variance affects the limit only.

It does not currently change:

* Eligibility
* Score
* Band

---

# 16. Rounding

The adjusted limit is rounded to the nearest:

```text
₦500
```

Using the current helper logic:

```python
round(amount / 500) * 500
```

Example:

```text
₦4,131
```

becomes approximately:

```text
₦4,000
```

---

# 17. Band Cap Application

After rounding, the band cap is applied.

Example:

```text
Band = B

Band B cap = ₦10,000
```

If calculated amount is:

```text
₦4,000
```

final remains:

```text
₦4,000
```

If calculated amount is:

```text
₦13,000
```

it becomes:

```text
₦10,000
```

---

# 18. Global Limits

The current global bounds are:

```text
MIN_ADVANCE = ₦2,000

MAX_ADVANCE = ₦20,000
```

After applying the band cap:

```text
approved_amount
=
max(approved_amount, ₦2,000)
```

Then:

```text
approved_amount
=
min(approved_amount, ₦20,000)
```

---

# 19. Complete Limit Formula

For meters with at least three recent vends:

```text
Base Limit
=
Median Vend Amount
×
Confidence Multiplier
```

Then:

```text
Adjusted Limit
=
Base Limit
×
Vend Volatility Dampener
×
Inter-Vend Variance Dampener
```

Then:

```text
Round to nearest ₦500
```

Then:

```text
Apply Band Cap
```

Then:

```text
Apply ₦2,000 Global Minimum
```

Then:

```text
Apply ₦20,000 Global Maximum
```

The result is:

```text
approved_amount
```

---

# 20. Full Example

Inputs:

```json
{
  "vend_count_last_60_days": 12,
  "days_since_last_vend": 3,
  "vend_frequency": 6,
  "median_vend_amount": 5000,
  "vend_amount_volatility": 50,
  "inter_vend_variance": 30,
  "failed_vend_ratio": 35,
  "has_active_obligation": false
}
```

## Hard Gates

```text
Active obligation? No

Failed ratio >= 85%? No

Dormancy > 120 days? No
```

Result:

```text
PASS
```

## Score

```text
Base Score                    50

12 Recent Vends              +20

Last Vend 3 Days Ago         +15

Failed Ratio 35%             -10
--------------------------------
Final Score                   75
```

Band:

```text
B
```

Band cap:

```text
₦10,000
```

## Confidence Multiplier

```text
0.6 + (75 / 100 × 0.6)

= 1.05
```

Base limit:

```text
₦5,000 × 1.05

= ₦5,250
```

## Volatility Adjustment

```text
vend_amount_volatility = 50

multiplier = 0.90
```

Result:

```text
₦5,250 × 0.90

= ₦4,725
```

## Variance Adjustment

```text
inter_vend_variance = 30

multiplier = 0.90
```

Result:

```text
₦4,725 × 0.90

= ₦4,252.50
```

Rounded to nearest ₦500:

```text
₦4,500
```

Band B cap is ₦10,000, so no further reduction is required.

Final:

```text
approved_amount = ₦4,500
```

---

# 21. Important Note on `vend_frequency`

The API currently requires:

```text
vend_frequency
```

but the current implementation does not use this field directly in:

* Hard gates
* Behaviour score
* Behaviour band
* Credit limit calculation

Therefore, changing only `vend_frequency` will not currently change the credit decision.

The field remains available for future model revisions.

---

# 22. Current Decision Summary

## Rejection Rules

```text
Active obligation
→ Reject

Failed vend ratio >= 85%
→ Reject

Days since last vend > 120
→ Reject
```

## Score

```text
Base = 50
```

Activity:

```text
10+ vends → +20

5–9 vends → +10

0–4 vends → +0
```

Recency:

```text
0–7 days → +15

8–30 days → +5

31+ days → +0
```

Failed-vend penalty:

```text
<30% → 0

30–49.99% → -10

50–84.99% → -20
```

## Bands

```text
A = 80–100

B = 60–79

C = 40–59

D = 0–39
```

## Band Caps

```text
A → ₦20,000

B → ₦10,000

C → ₦5,000

D → ₦2,000
```

## Starter Rule

```text
<3 recent successful vends
→ ₦2,000
```

## Global Limits

```text
Minimum = ₦2,000

Maximum = ₦20,000
```

---

# 23. Source of Truth

The current rules are implemented primarily in:

```text
src/credit_engine/config.py

src/credit_engine/hard_gates.py

src/credit_engine/behaviour_score.py

src/credit_engine/limit_engine.py

src/credit_engine/scoring.py
```

