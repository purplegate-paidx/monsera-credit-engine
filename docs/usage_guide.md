# Usage Guide – Monsera V0 Credit Engine

## 1. Overview

This guide explains how to prepare inputs, call the Monsera V0 Credit Decision Engine, interpret the response, and use the decision within a utility-vending backend.

The V0 engine receives pre-calculated behavioural features for a meter.

It does not currently receive the full transaction history directly.

The overall integration flow is:

```text
Meter Transaction History
        ↓
Calculate Behavioural Features
        ↓
Check Existing Monsera Obligation
        ↓
Call POST /decision
        ↓
Receive Eligibility + Limit
        ↓
Calculate Actual Credit Required
        ↓
Customer Accepts / Declines
        ↓
Complete Electricity Vend
        ↓
Create / Update Obligation
```

---

# 2. Feature Preparation

The backend or aggregator should calculate behavioural features for each meter.

The current API requires:

```text
vend_count_last_60_days

days_since_last_vend

vend_frequency

median_vend_amount

vend_amount_volatility

inter_vend_variance

failed_vend_ratio

has_active_obligation
```

---

# 3. Analysis Window

The current V0 configuration uses:

```text
LOOKBACK_DAYS = 60
```

Therefore, behavioural transaction features should be calculated over the most recent 60-day period unless otherwise explicitly defined.

The backend should use a consistent reference date when generating these features.

---

# 4. Successful Transactions

The demo currently treats the following statuses as successful:

```text
SUCCESS

COMPLETED

SUCCESSFUL
```

Partner implementations should map their transaction statuses into a consistent success/failure definition before feature calculation.

---

# 5. Preparing `vend_count_last_60_days`

Count successful vends during the most recent 60-day period.

Example:

```text
Total Attempts = 10

Successful = 8

Failed = 2
```

Then:

```json
{
  "vend_count_last_60_days": 8
}
```

---

# 6. Preparing `days_since_last_vend`

Calculate the number of days between the reference date and the most recent successful vend.

Example:

```text
Reference Date: September 22

Last Successful Vend: September 19
```

Then:

```text
days_since_last_vend = 3
```

Request value:

```json
{
  "days_since_last_vend": 3
}
```

---

# 7. Preparing `vend_frequency`

In the current demo implementation:

```text
vend_frequency
=
vend_count_last_60_days / 2
```

because the analysis window is approximately two months.

Example:

```text
12 successful vends / 2
=
6 vends per month
```

Request:

```json
{
  "vend_frequency": 6
}
```

### Current Implementation Note

`vend_frequency` is required by the API request model, but it is not currently used directly in the V0 decision logic.

It should still be calculated and sent so that the request conforms to the current API contract.

---

# 8. Preparing `median_vend_amount`

Take the median of successful transaction amounts in the analysis window.

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

Request:

```json
{
  "median_vend_amount": 3000
}
```

---

# 9. Preparing `vend_amount_volatility`

Vend amount volatility measures how inconsistent successful transaction amounts are.

The current demo approximately calculates:

```text
Standard Deviation of Successful Vend Amounts
----------------------------------------------
Median Vend Amount
× 100
```

The result should be supplied as a non-negative numeric value.

Example:

```json
{
  "vend_amount_volatility": 35
}
```

This feature affects the approved amount but does not directly change eligibility or score.

---

# 10. Preparing `inter_vend_variance`

Calculate the number of days between consecutive successful vends and then calculate the variance of those intervals.

Example:

```text
Successful Vends:

Day 1
Day 8
Day 15
Day 22
```

Intervals:

```text
7
7
7
```

This pattern has low variance.

A more irregular pattern produces higher variance.

Example request:

```json
{
  "inter_vend_variance": 30
}
```

This feature affects the approved amount but not the current score or eligibility directly.

---

# 11. Preparing `failed_vend_ratio`

Formula:

```text
Failed Transaction Attempts
---------------------------
Total Transaction Attempts
× 100
```

Example:

```text
10 attempts

2 failed
```

Then:

```text
2 / 10 × 100
=
20
```

Request:

```json
{
  "failed_vend_ratio": 20
}
```

The allowed API range is:

```text
0–100
```

---

# 12. Preparing `has_active_obligation`

This field must indicate whether the meter currently has an unpaid Monsera advance.

Example:

```json
{
  "has_active_obligation": false
}
```

In production, this value should come from an authoritative Monsera obligation registry.

It should not be permanently hardcoded.

If:

```text
has_active_obligation = true
```

the current engine rejects the request.

---

# 13. Calling the Decision Engine Programmatically

The core Python function is:

```python
from src.credit_engine.scoring import v0_decision
```

Example:

```python
from src.credit_engine.scoring import v0_decision

features = {
    "vend_count_last_60_days": 12,
    "days_since_last_vend": 3,
    "vend_frequency": 6,
    "median_vend_amount": 5000,
    "vend_amount_volatility": 50,
    "inter_vend_variance": 30,
    "failed_vend_ratio": 35,
    "has_active_obligation": False,
}

decision = v0_decision(features)

print(decision)
```

Possible result:

```python
{
    "eligible": True,
    "approved_amount": 4500,
    "reason": "APPROVED",
    "score": 75,
    "band": "B",
}
```

---

# 14. API Usage

The FastAPI endpoint is:

```http
POST /decision
```

Example request:

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

---

# 15. Successful Response

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
eligible
=
Meter passed all hard gates

score
=
Behaviour score

band
=
Behavioural credit band

approved_amount
=
Maximum amount Monsera is currently willing to expose

reason
=
Decision reason
```

---

# 16. Rejected Responses

The current model has three hard rejection reasons.

---

## Active Obligation

Example:

```json
{
  "eligible": false,
  "score": 0,
  "band": "REJECTED",
  "approved_amount": 0,
  "reason": "ACTIVE_OBLIGATION"
}
```

---

## Extreme Failed Transactions

Example:

```json
{
  "eligible": false,
  "score": 0,
  "band": "REJECTED",
  "approved_amount": 0,
  "reason": "EXTREME_FAILED_ATTEMPTS"
}
```

This occurs when:

```text
failed_vend_ratio >= 85
```

---

## Long Dormancy

Example:

```json
{
  "eligible": false,
  "score": 0,
  "band": "REJECTED",
  "approved_amount": 0,
  "reason": "LONG_DORMANCY"
}
```

This occurs when:

```text
days_since_last_vend > 120
```

---

# 17. Limited-History Users

Limited transaction history is not currently a rejection condition.

If:

```text
vend_count_last_60_days < 3
```

and all hard gates are passed:

```text
approved_amount = ₦2,000
```

Example:

```json
{
  "vend_count_last_60_days": 2,
  "days_since_last_vend": 5,
  "vend_frequency": 1,
  "median_vend_amount": 3000,
  "vend_amount_volatility": 20,
  "inter_vend_variance": 10,
  "failed_vend_ratio": 5,
  "has_active_obligation": false
}
```

The customer is not rejected solely because of limited history.

The intended starter exposure is:

```text
₦2,000
```

---

# 18. Understanding `approved_amount`

The value returned in:

```text
approved_amount
```

represents the maximum Monsera exposure currently approved for the meter.

It is not automatically the amount the customer must borrow.

Example:

```text
approved_amount = ₦6,000

customer requests = ₦4,000
```

The customer should not automatically receive ₦6,000.

The transaction layer should calculate the amount actually required.

---

# 19. Requested Vend Amount

The current `/decision` endpoint does not receive:

```text
requested_amount
```

Therefore, the scoring engine calculates behavioural capacity independently from the transaction amount.

The backend should separately calculate:

```text
Credit Needed
=
max(
    Requested Vend Amount
    -
    Customer Available Funds,
    0
)
```

Then:

```text
Credit Used
=
min(
    Credit Needed,
    Approved Amount
)
```

---

# 20. Example Transaction Calculation

Assume:

```text
Requested Electricity = ₦5,000

Customer Wallet = ₦1,000

Monsera Approved Amount = ₦6,000
```

Credit needed:

```text
₦5,000 - ₦1,000
=
₦4,000
```

Credit actually used:

```text
min(₦4,000, ₦6,000)
=
₦4,000
```

Transaction:

```text
Customer Contribution    ₦1,000

Monsera Credit            ₦4,000
                          -------
Electricity Vend          ₦5,000
```

Only ₦4,000 should become the Monsera obligation.

---

# 21. Zero Wallet Balance

A zero wallet balance does not automatically cause rejection.

Example:

```text
Wallet Balance = ₦0

Requested Vend = ₦4,000

Monsera Approved Amount = ₦4,000
```

Then:

```text
Credit Needed = ₦4,000

Credit Used = ₦4,000
```

Wallet balance is not currently part of the scoring API.

It belongs to the transaction layer.

---

# 22. Offer Acceptance

After receiving the decision, the partner application may present the offer to the customer.

Possible actions:

```text
ACCEPT

DECLINE
```

If the customer declines:

```text
No Monsera obligation should be created.
```

If the customer accepts:

```text
Proceed with electricity vend

Record actual credit used

Create an active obligation
```

---

# 23. Obligation Creation

Example obligation record:

```json
{
  "meter_number": "01234567890",
  "approved_limit": 6000,
  "credit_used": 4000,
  "outstanding_amount": 4000,
  "status": "ACTIVE"
}
```

The obligation should track the amount actually used, not simply the maximum approved limit.

---

# 24. Future Credit Requests

While the obligation remains active:

```text
has_active_obligation = true
```

must be sent to the Monsera decision engine.

The current engine will return:

```text
eligible = false
```

with:

```text
reason = ACTIVE_OBLIGATION
```

---

# 25. Repayment

The current V0 scoring API does not itself process repayments.

Repayment belongs to the transaction/obligation layer.

A possible meter-level recovery flow is:

```text
Customer Makes Future Vend
            ↓
Check Outstanding Monsera Obligation
            ↓
Recover Outstanding Amount
            ↓
Apply Remaining Funds to Electricity
            ↓
Update Obligation Balance
```

Example:

```text
Outstanding Monsera Balance = ₦4,000

Customer Pays = ₦10,000
```

Possible allocation:

```text
Customer Payment             ₦10,000

Monsera Recovery             -₦4,000
                             -------
Remaining Electricity Value   ₦6,000
```

The obligation becomes:

```text
CLEARED
```

once the outstanding amount reaches zero.

---

# 26. Python API Example

```python
import requests

API_URL = "http://127.0.0.1:8000/decision"

payload = {
    "vend_count_last_60_days": 12,
    "days_since_last_vend": 3,
    "vend_frequency": 6,
    "median_vend_amount": 5000,
    "vend_amount_volatility": 50,
    "inter_vend_variance": 30,
    "failed_vend_ratio": 35,
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

# 27. JavaScript API Example

```javascript
const payload = {
  vend_count_last_60_days: 12,
  days_since_last_vend: 3,
  vend_frequency: 6,
  median_vend_amount: 5000,
  vend_amount_volatility: 50,
  inter_vend_variance: 30,
  failed_vend_ratio: 35,
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

# 28. Local API Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn api.main:app --reload
```

Default local URL:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 29. Input Validation

The current FastAPI request model validates:

```text
vend_count_last_60_days >= 0

days_since_last_vend >= 0

vend_frequency >= 0

median_vend_amount >= 0

vend_amount_volatility >= 0

inter_vend_variance >= 0

0 <= failed_vend_ratio <= 100

has_active_obligation must be boolean
```

Invalid input will be rejected by FastAPI validation before the decision engine runs.

---

# 30. API Authentication

The current uploaded implementation does not enforce API-key authentication in:

```text
api/main.py
```

Therefore, authentication should be added before production deployment.

Recommended production requirements include:

* API key or service-to-service authentication
* Secrets stored in environment variables
* HTTPS only
* Request logging
* Partner identification
* Rate limiting where appropriate

Secrets should never be committed directly into the repository.

---

# 31. Operational Logging

Production implementations should log at minimum:

```text
Request ID

Partner / Aggregator

Meter Number

Request Timestamp

Input Features

Eligibility Result

Score

Band

Approved Amount

Decision Reason

Requested Vend Amount

Actual Credit Used

Customer Acceptance / Decline

Obligation ID
```

Repayment outcomes should later be linked back to the original decision.

---

# 32. Monitoring

Recommended monitoring metrics include:

```text
Approval Rate

Rejection Rate

Rejection Reasons

Average Approved Amount

Median Approved Amount

Approval Rate by Band

Credit Utilisation Rate

Acceptance Rate

Repayment Rate

Days to Repayment

Delinquency Rate

Default Rate

Outstanding Exposure

Exposure by Aggregator

Exposure by DisCo
```

These metrics will be critical when determining whether the V0 rules should be recalibrated.

---

# 33. Common Use Cases

The V0 engine can be used for:

* Real-time embedded electricity credit
* Aggregator backend decisioning
* Portfolio simulation
* Historical scenario testing
* Partner demonstrations
* Rule calibration
* Baseline comparison with future ML models

---

# 34. Current Behaviour Summary

## Hard Rejections

```text
Active obligation
→ Reject

Failed vend ratio >= 85%
→ Reject

Days since last vend > 120
→ Reject
```

## Starter User

```text
Fewer than 3 recent successful vends
→ ₦2,000
```

provided hard gates pass.

## Global Limits

```text
Minimum = ₦2,000

Maximum = ₦20,000
```

## Bands

```text
A = 80–100

B = 60–79

C = 40–59

D = 0–39
```

Band D remains eligible under the current implementation.

---

# 35. Best Practices

## Keep Feature Definitions Consistent

All partners should calculate features using the same definitions.

For example:

```text
vend_count_last_60_days
```

must mean the same thing across every aggregator.

---

## Separate Decisioning From Transactions

The credit engine should answer:

```text
How much is Monsera willing to expose?
```

The transaction system should answer:

```text
How much credit is actually required and used?
```

These should remain separate responsibilities.

---

## Keep Obligation State Authoritative

`has_active_obligation` should come from a single trusted obligation-management source.

Do not calculate this independently in multiple systems.

---

## Log Every Decision

Decision inputs and outcomes should be stored so that Monsera can later evaluate:

* Rule performance
* Repayment performance
* Default behaviour
* Model drift
* Future ML training datasets

---

## Version the Model

Future rule changes should be associated with an explicit model version.

For example:

```text
v0.1

v0.2

v0.3
```

Each decision record should ideally store the version that generated it.

---

# 36. Current Source of Truth

The current scoring implementation is defined primarily in:

```text
src/credit_engine/config.py

src/credit_engine/hard_gates.py

src/credit_engine/behaviour_score.py

src/credit_engine/limit_engine.py

src/credit_engine/scoring.py

api/main.py
```

