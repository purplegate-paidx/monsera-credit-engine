# Monsera V0 Credit Decision Engine

Monsera V0 is a deterministic, rule-based credit decision engine for prepaid electricity meters.

The engine analyses a meter's recent vending behaviour and determines:

* Whether the meter is eligible for an electricity advance
* A behavioural score from `0–100`
* A behavioural credit band
* The maximum advance Monsera is willing to provide
* A clear reason when a meter is rejected

The V0 model is intentionally transparent and explainable. It is designed as the first stage of Monsera's credit infrastructure before sufficient repayment data exists to train statistical or machine-learning models.

---

## 1. Purpose

Monsera provides embedded electricity credit through utility aggregators.

Instead of assessing customers using traditional credit bureau information, salary information, or demographic information, V0 primarily evaluates the behaviour of the electricity meter.

The basic idea is:

```text
Historical Vending Data
        ↓
Behavioural Features
        ↓
Hard Eligibility Checks
        ↓
Behaviour Score
        ↓
Credit Band
        ↓
Advance Limit
        ↓
Credit Decision
```

The engine answers two main questions:

1. **Should Monsera provide credit to this meter?**
2. **If yes, what is the maximum amount Monsera should expose?**

---

# 2. Current V0 Architecture

The system can be understood as three separate layers.

## Layer 1 — Feature Engineering

The partner/backend retrieves the meter's transaction history and converts it into behavioural features.

These include:

* Number of successful vends
* Recency of the last vend
* Typical vend amount
* Vend amount volatility
* Consistency of vend timing
* Failed vend ratio
* Existing Monsera obligation

## Layer 2 — Credit Decision Engine

The Monsera API receives those features and performs:

* Hard eligibility checks
* Behaviour scoring
* Band assignment
* Advance limit calculation

## Layer 3 — Transaction and Obligation Management

The partner/backend uses the decision to:

* Present the credit offer
* Record acceptance or decline
* Complete the electricity vend
* Create an outstanding Monsera obligation
* Recover the obligation on future transactions
* Mark the obligation as cleared after repayment

The current repository primarily implements **Layer 2**, while the Streamlit demo provides a simplified example of Layer 1 and parts of Layer 3.

---

# 3. Project Structure

```text
monsera-credit-engine/
│
├── api/
│   ├── __init__.py
│   └── main.py
│
├── src/
│   └── credit_engine/
│       ├── __init__.py
│       ├── behaviour_score.py
│       ├── config.py
│       ├── hard_gates.py
│       ├── limit_engine.py
│       ├── scoring.py
│       └── utils.py
│
├── demo/
│   ├── app.py
│   └── data/
│
├── analysis/
│   ├── __init__.py
│   └── generate_excel_output.py
│
├── docs/
│   ├── model_overview.md
│   ├── scoring_rules.md
│   └── usage_guide.md
│
├── tests/
│   ├── test_api.py
│   └── test_scoring.py
│
├── Dockerfile
├── render.yaml
├── requirements.txt
├── pytest.ini
└── README.md
```

---

# 4. API

The credit decision service is exposed through FastAPI.

## Endpoint

```http
POST /decision
```

The endpoint accepts behavioural features for a meter and returns the V0 credit decision.

---

# 5. Request Payload

Example request:

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

# 6. Input Definitions

## `vend_count_last_60_days`

```text
Type: Integer
Minimum: 0
```

The number of successful electricity vending transactions completed within the most recent 60-day period.

Example:

```text
10 transaction attempts
8 successful
2 failed
```

Then:

```json
"vend_count_last_60_days": 8
```

This field is currently used directly in the behavioural score and in the starter-user rule.

---

## `days_since_last_vend`

```text
Type: Integer
Minimum: 0
```

The number of days since the meter's most recent successful electricity vend.

Example:

```text
Current date: September 22
Last successful vend: September 19

days_since_last_vend = 3
```

Recent vending activity increases the behavioural score.

Extremely long inactivity can cause a hard rejection.

---

## `vend_frequency`

```text
Type: Float
Minimum: 0
```

Represents the meter's estimated average vending frequency.

In the current demo, this is calculated as:

```python
vend_frequency = vend_count_last_60_days / 2
```

because the feature window covers approximately two months.

Example:

```text
12 successful vends in 60 days

12 / 2 = 6
```

Therefore:

```json
"vend_frequency": 6
```

### Important

`vend_frequency` is currently accepted and validated by the API, but it is **not directly used in the current V0 behaviour score or limit formula**.

It remains available for future scoring revisions.

---

## `median_vend_amount`

```text
Type: Float
Minimum: 0
Currency: Nigerian Naira
```

The median value of successful electricity vends during the analysis period.

Example:

```text
₦2,000
₦3,000
₦3,000
₦4,000
₦10,000
```

Median:

```text
₦3,000
```

Therefore:

```json
"median_vend_amount": 3000
```

The median vend amount is the primary capacity signal used when determining the credit limit.

Median is preferred because it is less affected by unusually high or unusually low transactions.

---

## `vend_amount_volatility`

```text
Type: Float
Minimum: 0
```

Measures how much the customer's successful vend amounts vary.

The demo approximately calculates:

```python
vend_amount_volatility =
    standard_deviation_of_successful_vends
    / median_vend_amount
    * 100
```

Stable example:

```text
₦4,000
₦4,100
₦3,900
₦4,200
₦4,000
```

Unstable example:

```text
₦1,000
₦9,000
₦2,000
₦12,000
₦1,500
```

Higher volatility does **not automatically reject a customer**.

Instead, it reduces the amount Monsera is willing to expose.

---

## `inter_vend_variance`

```text
Type: Float
Minimum: 0
```

Measures the variability of the number of days between successful vends.

Example of predictable behaviour:

```text
Day 1
Day 8
Day 15
Day 22
```

The meter purchases approximately every seven days.

Example of irregular behaviour:

```text
Day 1
Day 2
Day 20
Day 21
Day 50
```

Higher inter-vend variance reduces the advance amount.

It does not directly cause rejection.

---

## `failed_vend_ratio`

```text
Type: Float
Minimum: 0
Maximum: 100
```

The percentage of recent transaction attempts that were unsuccessful.

Formula:

```text
Failed Transactions
------------------- × 100
Total Attempts
```

Example:

```text
10 total attempts
8 successful
2 failed
```

Then:

```text
2 / 10 × 100 = 20%
```

Therefore:

```json
"failed_vend_ratio": 20
```

Moderate failure rates reduce the behavioural score.

Extremely high failure rates trigger a hard rejection.

---

## `has_active_obligation`

```text
Type: Boolean
```

Indicates whether the meter currently has an unpaid Monsera advance.

Example:

```json
"has_active_obligation": true
```

A meter with an active obligation is currently rejected from receiving another advance.

In production, this value should be retrieved from Monsera's obligation registry.

---

# 7. Feature Engineering in the Demo

The Streamlit demo uses transaction data to generate the V0 features.

Successful statuses are currently defined as:

```python
SUCCESS_STATUSES = {
    "SUCCESS",
    "COMPLETED",
    "SUCCESSFUL"
}
```

The reference date in the demo is:

```python
today = meter_df["Transaction_Date"].max()
```

The 60-day window is then created using:

```python
recent = meter_df[
    meter_df["Transaction_Date"] >= today - timedelta(days=60)
]
```

Successful transactions are:

```python
successful = recent[
    recent["Status"].isin(SUCCESS_STATUSES)
]
```

---

# 8. Hard Eligibility Gates

Before calculating a score, the engine evaluates hard gates.

Hard gates are intentionally reserved for extreme cases.

There are currently three hard rejection rules.

---

## 8.1 Active Obligation

If:

```text
has_active_obligation = true
```

the request is rejected.

Reason:

```text
ACTIVE_OBLIGATION
```

Approved amount:

```text
₦0
```

---

## 8.2 Extreme Failed Attempts

If:

```text
failed_vend_ratio >= 85
```

the request is rejected.

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
20% → Not automatically rejected
40% → Not automatically rejected
60% → Not automatically rejected
80% → Not automatically rejected
85% → Rejected
90% → Rejected
```

---

## 8.3 Long Dormancy

If:

```text
days_since_last_vend > 120
```

the meter is rejected.

Reason:

```text
LONG_DORMANCY
```

Examples:

```text
30 days  → Pass
60 days  → Pass
90 days  → Pass
120 days → Pass
121 days → Reject
150 days → Reject
```

---

# 9. Hard Gate Summary

| Condition                             | Result              |
| ------------------------------------- | ------------------- |
| Active Monsera obligation             | Reject              |
| Failed vend ratio ≥ 85%               | Reject              |
| Days since last successful vend > 120 | Reject              |
| None of the above                     | Continue to scoring |

A rejected meter receives:

```json
{
  "eligible": false,
  "approved_amount": 0,
  "reason": "REJECTION_REASON",
  "score": 0,
  "band": "REJECTED"
}
```

---

# 10. Behaviour Score

Meters that pass the hard gates receive a behavioural score.

The score starts at:

```text
50
```

This acts as the neutral baseline.

The current score uses three signals:

1. Recent activity
2. Recency
3. Failed vend behaviour

The score is always constrained between:

```text
0 and 100
```

---

# 11. Activity Score

The engine uses:

```text
vend_count_last_60_days
```

Current scoring:

| Successful Vends in 60 Days | Points |
| --------------------------: | -----: |
|                         10+ |    +20 |
|                         5–9 |    +10 |
|                         0–4 |     +0 |

Example:

```text
Starting score = 50

12 successful vends
Activity points = +20

Current score = 70
```

---

# 12. Recency Score

The engine uses:

```text
days_since_last_vend
```

Current scoring:

| Days Since Last Successful Vend | Points |
| ------------------------------: | -----: |
|                             0–7 |    +15 |
|                            8–30 |     +5 |
|                             31+ |     +0 |

Example:

```text
Current score = 70

Last vend = 3 days ago

Recency = +15

Current score = 85
```

---

# 13. Failed Vend Penalty

The failed-vend ratio can reduce the score.

| Failed Vend Ratio | Score Adjustment |
| ----------------: | ---------------: |
|         Below 30% |                0 |
|        30%–49.99% |              -10 |
|        50%–84.99% |              -20 |
|              85%+ |   Hard rejection |

Example:

```text
Current score = 85

Failed vend ratio = 35%

Penalty = -10

Final score = 75
```

---

# 14. Behaviour Score Summary

Current calculation:

```text
Start with 50
      ↓
Add Activity Points
      ↓
Add Recency Points
      ↓
Subtract Failed-Vend Penalty
      ↓
Clamp Score Between 0 and 100
```

Example:

```text
Base Score                   50
10+ Vends                   +20
Vend Within Last 7 Days     +15
Failed Ratio 30%–49.99%     -10
--------------------------------
Final Score                  75
```

---

# 15. Credit Bands

The current implementation maps scores into four bands.

|  Score | Band |
| -----: | :--: |
| 80–100 |   A  |
|  60–79 |   B  |
|  40–59 |   C  |
|   0–39 |   D  |

Example:

```text
Score 85 → A
Score 75 → B
Score 55 → C
Score 35 → D
```

### Important

Band D is **not automatically rejected** by the current implementation.

A meter that passes all hard gates remains:

```text
eligible = true
```

even if its score falls into Band D.

Band D is instead restricted to the minimum credit exposure.

---

# 16. Band Caps

Each band has a maximum advance.

| Band | Maximum Advance |
| :--: | --------------: |
|   A  |         ₦20,000 |
|   B  |         ₦10,000 |
|   C  |          ₦5,000 |
|   D  |          ₦2,000 |

These values represent maximum exposure.

Being Band A does **not** automatically mean that a meter receives ₦20,000.

The actual amount is still calculated from the meter's normal purchasing behaviour.

---

# 17. Global Limits

The current V0 configuration defines:

```python
MIN_ADVANCE = 2000
MAX_ADVANCE = 20000
```

Therefore:

```text
Minimum advance = ₦2,000
Maximum advance = ₦20,000
```

An eligible meter will not receive less than ₦2,000 under the current implementation.

No meter can receive more than ₦20,000.

---

# 18. Starter / Limited-History Users

The engine uses a starter rule for meters with limited transaction history.

If:

```text
vend_count_last_60_days < 3
```

the approved amount is:

```text
₦2,000
```

provided that the meter passed all hard gates.

Therefore:

```text
0 successful recent vends → ₦2,000*
1 successful recent vend  → ₦2,000
2 successful recent vends → ₦2,000
```

`*` A meter with no recent successful vends may still fail the dormancy rule depending on the `days_since_last_vend` value supplied by the backend.

The purpose of the starter amount is to allow Monsera to learn the repayment behaviour of limited-history meters while keeping initial exposure controlled.

---

# 19. Advance Limit Calculation

For meters with at least three successful recent vends, the advance is calculated from behavioural capacity and confidence.

The main formula is:

```text
Median Vend Amount
        ×
Confidence Multiplier
        ×
Vend Amount Volatility Dampener
        ×
Inter-Vend Variance Dampener
        ↓
Round to nearest ₦500
        ↓
Apply Band Cap
        ↓
Apply Global Minimum
        ↓
Apply Global Maximum
```

---

# 20. Confidence Multiplier

The behavioural score is converted into a confidence multiplier.

Formula:

```python
confidence_multiplier = 0.6 + (score / 100) * 0.6
```

Examples:

| Score | Multiplier |
| ----: | ---------: |
|    40 |       0.84 |
|    50 |       0.90 |
|    60 |       0.96 |
|    70 |       1.02 |
|    80 |       1.08 |
|    90 |       1.14 |
|   100 |       1.20 |

The initial behavioural limit is:

```text
median_vend_amount × confidence_multiplier
```

Example:

```text
Median vend = ₦5,000
Score = 70
```

Confidence multiplier:

```text
0.6 + (70 / 100 × 0.6)

= 0.6 + 0.42

= 1.02
```

Base limit:

```text
₦5,000 × 1.02
= ₦5,100
```

---

# 21. Vend Amount Volatility Dampener

The current volatility multipliers are:

| Vend Amount Volatility | Multiplier |
| ---------------------: | ---------: |
|                   ≤ 30 |       1.00 |
|        30 < value ≤ 60 |       0.90 |
|       60 < value ≤ 100 |       0.75 |
|                  > 100 |       0.60 |

High volatility reduces exposure rather than automatically removing access.

Example:

```text
Base limit = ₦5,100
Volatility = 50
Multiplier = 0.90
```

Then:

```text
₦5,100 × 0.90
= ₦4,590
```

---

# 22. Inter-Vend Variance Dampener

The current interval-variance multipliers are:

| Inter-Vend Variance | Multiplier |
| ------------------: | ---------: |
|                ≤ 20 |       1.00 |
|     20 < value ≤ 50 |       0.90 |
|    50 < value ≤ 100 |       0.80 |
|               > 100 |       0.70 |

Example:

```text
Current limit = ₦4,590
Inter-vend variance = 30
Multiplier = 0.90
```

Then:

```text
₦4,590 × 0.90
= ₦4,131
```

---

# 23. Rounding

The result is rounded to the nearest:

```text
₦500
```

using:

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

# 24. Band Cap

After behavioural adjustments and rounding, the appropriate band cap is applied.

Example:

```text
Score = 70
Band = B

Band B maximum = ₦10,000
```

If the calculated amount is:

```text
₦4,000
```

the approved amount remains:

```text
₦4,000
```

If the calculated amount were:

```text
₦13,000
```

it would be reduced to:

```text
₦10,000
```

because Band B cannot exceed ₦10,000.

---

# 25. Full Decision Example

Request:

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

## Step 1 — Hard Gates

```text
Active obligation? No

Failed vend ratio >= 85%? No

Days since last vend > 120? No
```

Result:

```text
PASS
```

## Step 2 — Score

```text
Base Score                     50

12 Recent Vends               +20

Last Vend 3 Days Ago          +15

Failed Ratio = 35%            -10
---------------------------------
Final Score                    75
```

## Step 3 — Band

```text
Score = 75

Band = B
```

Band B maximum:

```text
₦10,000
```

## Step 4 — Confidence Multiplier

```text
0.6 + (75 / 100 × 0.6)

= 0.6 + 0.45

= 1.05
```

Base amount:

```text
₦5,000 × 1.05
= ₦5,250
```

## Step 5 — Volatility Dampener

Volatility:

```text
50
```

Multiplier:

```text
0.90
```

Calculation:

```text
₦5,250 × 0.90
= ₦4,725
```

## Step 6 — Inter-Vend Variance Dampener

Variance:

```text
30
```

Multiplier:

```text
0.90
```

Calculation:

```text
₦4,725 × 0.90
= ₦4,252.50
```

## Step 7 — Round to ₦500

Approximately:

```text
₦4,500
```

## Step 8 — Apply Band Cap

Band B maximum:

```text
₦10,000
```

Therefore final approval:

```text
₦4,500
```

---

# 26. Successful API Response

Example:

```json
{
  "eligible": true,
  "score": 75,
  "band": "B",
  "approved_amount": 4500,
  "reason": "APPROVED"
}
```

Interpretation:

```text
Eligible: Yes

Behaviour Score: 75

Band: B

Maximum Current Monsera Advance: ₦4,500
```

---

# 27. Rejected API Response

Example request with an active obligation:

```json
{
  "vend_count_last_60_days": 8,
  "days_since_last_vend": 5,
  "vend_frequency": 4,
  "median_vend_amount": 4000,
  "vend_amount_volatility": 30,
  "inter_vend_variance": 20,
  "failed_vend_ratio": 10,
  "has_active_obligation": true
}
```

Response:

```json
{
  "eligible": false,
  "score": 0,
  "band": "REJECTED",
  "approved_amount": 0,
  "reason": "ACTIVE_OBLIGATION"
}
```

Possible current rejection reasons:

```text
ACTIVE_OBLIGATION

EXTREME_FAILED_ATTEMPTS

LONG_DORMANCY
```

---

# 28. How the Backend Should Use the Approved Amount

`approved_amount` represents the **maximum amount Monsera is willing to expose** for the transaction.

It is not necessarily the amount the customer will actually use.

Example:

```text
Customer wants electricity = ₦5,000

Customer wallet balance = ₦1,000

Monsera approved amount = ₦4,000
```

The transaction can be:

```text
Customer Funds       ₦1,000
Monsera Credit       ₦4,000
                     -------
Electricity Vend     ₦5,000
```

---

# 29. Zero Wallet Balance

A zero wallet balance does not automatically make the meter ineligible.

Example:

```text
Wallet Balance = ₦0

Electricity Requested = ₦4,000

Monsera Approved = ₦4,000
```

The transaction may still proceed for:

```text
₦4,000
```

Wallet balance is not currently an input to the V0 scoring API.

---

# 30. Requested Amount vs Approved Limit

The current `/decision` endpoint does **not receive the requested electricity amount**.

It calculates the maximum behavioural limit independently.

Therefore, the backend should separately determine the amount of credit actually required.

A suitable transaction-layer calculation is:

```text
Credit Needed =
max(Requested Vend Amount - Customer Available Funds, 0)
```

The amount actually used should not exceed the Monsera-approved amount.

Therefore:

```text
Credit Used =
min(Credit Needed, Approved Amount)
```

Example:

```text
Requested Vend = ₦5,000

Wallet Balance = ₦1,000

Credit Needed = ₦4,000

Approved Amount = ₦6,000
```

Actual Monsera credit used:

```text
₦4,000
```

not ₦6,000.

The approved amount should be treated as a ceiling.

---

# 31. Credit Is for Electricity, Not Cash

The intended Monsera product flow is:

```text
Customer Requests Electricity
            ↓
Aggregator Identifies Meter
            ↓
Monsera Credit Assessment
            ↓
Credit Approved
            ↓
Customer Accepts
            ↓
Electricity Vend Completed
            ↓
Monsera Obligation Created
```

The Monsera advance should be tied to the utility transaction.

It should not ordinarily operate as a cash loan paid directly into the customer's bank account.

---

# 32. Obligation Management

When Monsera credit is actually used, the transaction layer should create an obligation.

Example:

```json
{
  "meter_number": "01234567890",
  "credit_used": 4000,
  "outstanding_amount": 4000,
  "status": "ACTIVE"
}
```

Future scoring requests should therefore send:

```json
"has_active_obligation": true
```

while the debt remains outstanding.

The current V0 decision engine will reject another advance while this value is `true`.

---

# 33. Repayment Concept

The current demo communicates a meter-level repayment model in which Monsera credit is recovered from a future successful vend.

Example:

```text
Outstanding Monsera Advance = ₦4,000

Customer's Next Payment = ₦10,000
```

A transaction system could process:

```text
Customer Payment              ₦10,000

Monsera Recovery              -₦4,000
                              -------
Remaining Electricity Value    ₦6,000
```

After the outstanding amount reaches zero:

```text
Obligation Status = CLEARED
```

Future credit assessment can then use:

```json
"has_active_obligation": false
```

The actual repayment and settlement implementation belongs to the transaction/obligation layer and is not performed by the current `/decision` endpoint.

---

# 34. Backend Integration Flow

Recommended integration:

```text
1. Customer initiates electricity vend.

2. Aggregator identifies the customer's meter.

3. Backend retrieves the meter's transaction history.

4. Backend selects the recent 60-day transaction window.

5. Backend calculates the required behavioural features.

6. Backend queries Monsera's obligation registry.

7. Backend constructs the /decision request.

8. Backend sends the behavioural features to Monsera.

9. Monsera evaluates hard gates.

10. If hard gates pass, Monsera calculates the behaviour score.

11. Monsera assigns a behavioural band.

12. Monsera calculates the maximum approved advance.

13. Monsera returns the credit decision.

14. Backend compares:
    - Requested electricity amount
    - Customer available funds
    - Monsera approved amount

15. Backend determines the actual credit required.

16. Customer accepts or declines the offer.

17. If accepted, the electricity transaction is completed.

18. Backend records the actual Monsera credit used.

19. An ACTIVE obligation is created.

20. Future requests identify the existing obligation.

21. Repayments reduce the outstanding obligation.

22. Once fully repaid, the obligation becomes CLEARED.
```

---

# 35. Running the Project Locally

## Prerequisites

Recommended:

* Python 3.12
* `pip`
* Git

---

## Clone the Repository

```bash
git clone https://github.com/purplegate-paidx/monsera-credit-engine.git
cd monsera-credit-engine
```

---

## Create a Virtual Environment

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 36. Run the API

From the repository root:

```bash
uvicorn api.main:app --reload
```

The local API will normally be available at:

```text
http://127.0.0.1:8000
```

Interactive FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

Alternative API documentation:

```text
http://127.0.0.1:8000/redoc
```

---

# 37. Test the API Locally

Example using `curl`:

```bash
curl -X POST \
  "http://127.0.0.1:8000/decision" \
  -H "Content-Type: application/json" \
  -d '{
    "vend_count_last_60_days": 8,
    "days_since_last_vend": 5,
    "vend_frequency": 4,
    "median_vend_amount": 4000,
    "vend_amount_volatility": 30,
    "inter_vend_variance": 20,
    "failed_vend_ratio": 10,
    "has_active_obligation": false
  }'
```

Example response:

```json
{
  "eligible": true,
  "score": 75,
  "band": "B",
  "approved_amount": 4000,
  "reason": "APPROVED"
}
```

The exact approved amount depends on the supplied features.

---

# 38. Python Integration Example

```python
import requests

API_URL = "http://127.0.0.1:8000/decision"

payload = {
    "vend_count_last_60_days": 8,
    "days_since_last_vend": 5,
    "vend_frequency": 4,
    "median_vend_amount": 4000,
    "vend_amount_volatility": 30,
    "inter_vend_variance": 20,
    "failed_vend_ratio": 10,
    "has_active_obligation": False,
}

response = requests.post(
    API_URL,
    json=payload,
    timeout=30,
)

response.raise_for_status()

decision = response.json()

print(decision)
```

---

# 39. JavaScript / Node.js Integration Example

```javascript
const payload = {
  vend_count_last_60_days: 8,
  days_since_last_vend: 5,
  vend_frequency: 4,
  median_vend_amount: 4000,
  vend_amount_volatility: 30,
  inter_vend_variance: 20,
  failed_vend_ratio: 10,
  has_active_obligation: false
};

const response = await fetch(
  "http://127.0.0.1:8000/decision",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  }
);

if (!response.ok) {
  throw new Error(`Monsera API returned ${response.status}`);
}

const decision = await response.json();

console.log(decision);
```

---

# 40. Running Tests

Run all automated tests from the project root:

```bash
pytest
```

For more detailed output:

```bash
pytest -v
```

The current tests cover areas including:

* Active obligations
* Extreme failed-vend ratios
* Long dormancy
* Limited-history users
* High volatility
* High inter-vend variance
* Median vend capacity
* Band caps
* Global maximum
* API behaviour

---

# 41. Deployment on Render

The repository contains:

```text
render.yaml
```

with the current web service configuration.

The configured start command is:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 10000
```

The build command is:

```bash
pip install -r requirements.txt
```

The current demo references:

```text
https://monsera-credit-engine.onrender.com/decision
```

as the deployed decision endpoint.

Deployment environments should verify the correct production URL before integrating.

---

# 42. Current API Authentication Status

The current `api/main.py` implementation does **not currently enforce API-key authentication**.

The `/decision` endpoint currently accepts a valid request payload without an API key.

Therefore:

```text
API key authentication is not part of the current uploaded V0 implementation.
```

Before production rollout, authentication should be implemented separately so only authorized aggregators and Monsera services can call the decision API.

API credentials should be stored in environment variables and should never be committed directly into the repository.

---

# 43. Important Current Implementation Notes

## `vend_frequency`

The field exists in the API request schema but is not currently used directly in:

* Hard gates
* Behaviour scoring
* Limit calculation

Changing only `vend_frequency` will therefore not currently change the decision.

---

## Volatility and Variance

These fields:

```text
vend_amount_volatility
inter_vend_variance
```

do not currently change the behavioural score or band.

They affect the **approved amount only**.

This is intentional in the current implementation.

High instability reduces Monsera's financial exposure rather than automatically denying access.

---

## Limited History

Having fewer than three successful vends is **not a hard rejection**.

Eligible limited-history meters receive:

```text
₦2,000
```

---

## Band D

Band D is **not currently a decline band**.

If the meter passes all hard gates, it remains eligible and Band D is capped at:

```text
₦2,000
```

---

## Requested Amount

The `/decision` API does not currently receive:

```text
requested_amount
```

Therefore, the endpoint determines the customer's maximum approved exposure rather than the exact amount to be disbursed for a specific transaction.

The partner/backend should determine actual credit used after receiving the decision.

---

## Wallet Balance

Wallet balance is not currently part of the V0 scoring request.

It belongs to the transaction layer.

---

## Active Obligation

The demo currently sets:

```python
"has_active_obligation": False
```

during feature construction.

For production, this must not be hardcoded.

It should come from Monsera's live obligation registry or another authoritative obligation-management source.

---

# 44. Configuration

Current key V0 settings are located in:

```text
src/credit_engine/config.py
```

Current configuration:

```python
MIN_ADVANCE = 2000
MAX_ADVANCE = 20000

LOOKBACK_DAYS = 60

MIN_HISTORY_VENDS = 3

MAX_FAILED_VEND_RATIO = 85
MAX_DORMANCY_DAYS = 120
```

The band caps are currently located in:

```text
src/credit_engine/limit_engine.py
```

Current values:

```python
BAND_CAPS = {
    "A": 20000,
    "B": 10000,
    "C": 5000,
    "D": 2000,
}
```

---

# 45. Current Decision Rules Summary

## Hard Gates

```text
Active Obligation
→ REJECT

Failed Vend Ratio >= 85%
→ REJECT

Days Since Last Successful Vend > 120
→ REJECT
```

---

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

Failed transactions:

```text
Below 30% → 0

30%–49.99% → -10

50%–84.99% → -20

85%+ → Hard Reject
```

---

## Bands

```text
A = 80–100

B = 60–79

C = 40–59

D = 0–39
```

---

## Band Caps

```text
A → ₦20,000

B → ₦10,000

C → ₦5,000

D → ₦2,000
```

---

## Starter Rule

```text
Fewer than 3 recent successful vends
→ ₦2,000
```

subject to passing all hard gates.

---

## Global Limits

```text
Minimum = ₦2,000

Maximum = ₦20,000
```

---

# 46. Current Limit Formula

For meters with at least three successful recent vends:

```text
Base Limit
=
Median Vend Amount
×
[0.6 + (Score / 100 × 0.6)]
```

Then:

```text
Adjusted Limit
=
Base Limit
×
Volatility Dampener
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
Apply ₦2,000 Minimum
```

Then:

```text
Apply ₦20,000 Maximum
```

Result:

```text
approved_amount
```

---

# 47. Source of Truth

The current decision implementation is defined primarily by:

```text
src/credit_engine/config.py

src/credit_engine/hard_gates.py

src/credit_engine/behaviour_score.py

src/credit_engine/limit_engine.py

src/credit_engine/scoring.py

api/main.py
```

When documentation conflicts with these files, the current running implementation should be treated as the source of truth until the documentation and code are deliberately versioned and synchronized.

---

# 48. V0 Design Philosophy

Monsera V0 follows several core principles.

### 1. Extreme conditions block access

Only clear hard-gate conditions create automatic rejection.

### 2. Uncertainty should reduce exposure before removing access

Volatility and irregular behaviour primarily reduce the approved amount.

### 3. Limited-history customers should be learnable

Thin-history meters can start at controlled minimum exposure rather than being automatically excluded.

### 4. Capacity should come from observed utility behaviour

Median electricity spending provides the primary reference point for advance sizing.

### 5. Every decision should be explainable

The V0 model is deterministic.

Given the same inputs and configuration, it produces the same result.

### 6. V0 should generate data for future models

The long-term purpose of V0 is not only to make credit decisions.

It should also generate reliable repayment-performance data that can later support statistical credit scorecards and machine-learning models.

---

# 49. Future Development

Expected future improvements may include:

* Production obligation registry integration
* API authentication and authorization
* Persistent accept/decline logging
* Repayment event tracking
* Partner-level configuration
* Portfolio-level exposure controls
* DisCo-level rules
* Real-time feature calculation
* Additional behavioural features
* Fraud detection
* Model monitoring
* Experiment/version tracking
* Statistical behavioural scorecards
* Probability-of-default modelling
* Machine-learning models
* Explainability and reason codes
* Model drift monitoring

These future capabilities are not part of the current V0 decision logic unless explicitly implemented.

---

# 50. Summary

Monsera V0 is a behavioural electricity-credit decision engine.

In simple terms:

```text
Look at the meter's recent vending behaviour
              ↓
Reject only extreme cases
              ↓
Calculate behavioural confidence
              ↓
Estimate normal purchasing capacity
              ↓
Reduce exposure when behaviour is uncertain
              ↓
Apply risk-band limits
              ↓
Return the maximum safe advance
```

The current model is:

* Deterministic
* Explainable
* Behaviour-based
* Meter-focused
* Conservative on exposure
* Designed for continuous learning
* Built as the foundation for future AI/ML credit models

---

## License

See the `LICENSE` file in this repository for applicable licensing terms.
