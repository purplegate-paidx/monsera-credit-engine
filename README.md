# Monsera v0 Credit Scoring & Advancement Model


This repository contains the **V0 behavioural and rule-based credit scoring engine** used for determining user eligibility and deciding the advancement (credit) amount offered to electricity meter users.
The V0 model is deterministic, explainable, and designed as the foundation for more advanced ML-powered versions.


## Project Purpose

The Monsera Credit Engine is designed to:

- Determine **whether a meter is eligible** for an advance
- Compute a **behaviour score** (0–100) based on observed vending patterns
- Assign a **risk band**
- Recommend an **advance amount** within safe limits


This v0 is deliberately **deterministic and transparent**. It is designed to be:
- Easy to implement and audit
- A safe starting point before full AI/ML scorecards
- A foundation for future versions (V1/V2: statistical & ML models) :contentReference[oaicite:0]{index=0}


---

## High-Level Decision Flow (v0)

The V0 engine operates as a **layered decision system**, not a single score:

Meter Behavioural Data
↓
Hard Gates (Eligibility)
↓
Behaviour Score (0–100)
↓
Risk Band Assignment
↓
Advance Limit Sizing
↓
Portfolio / Liquidity Constraints


Each stage serves a distinct risk-control purpose.

---

## Stage 1: Hard Gates (Eligibility)

Before any scoring occurs, meters must pass mandatory **eligibility checks**.

A meter is immediately **ineligible** if any of the following apply:

- Active outstanding obligation
- Insufficient recent vending history
- Dormant usage pattern (no recent vends)
- Excessive failed vend attempts
- Severe instability or suspicious behaviour

If a hard gate fails, **no score is computed**, and the request is declined with a clear reason.

---

## Stage 2: Behaviour Score (0–100)

Eligible meters are scored using **observable vending behaviour only**.

The behaviour score captures:

- **Repayment opportunities** – vend frequency
- **Predictability** – inter-vend consistency and amount volatility
- **Typical capacity** – median vend amount (not total spend)
- **Reliability** – failed vend attempts and transaction friction

The score is mapped into four bands:

| Score Range | Band | Meaning     |
|------------|------|-------------|
| 80–100     | A    | Strong      |
| 65–79      | B    | Good        |
| 50–64      | C    | Marginal    |
| <50        | D    | Decline     |

Only bands **A–C** are eligible for an advance.

---

## Stage 3: Advance Limit Sizing

Advance amounts are derived from **observed behaviour**, not requested amounts alone.

Limit sizing follows these steps:

1. Compute a **base limit** from median vend behaviour
2. Apply **band-specific caps**
3. Apply **risk multipliers** (e.g. low frequency, high volatility)
4. Enforce minimum and maximum advance limits

Final rule:

Approved Advance = min(Requested Amount, Adjusted Behavioural Limit)


This ensures exposure remains proportional to how the meter typically behaves.

---

## Stage 4: Portfolio & Liquidity Constraints

Independent of meter-level decisions, the system enforces:

- Available float / wallet balance
- Daily portfolio caps
- Channel or cohort-specific limits
- Emergency kill switches

If available float is below the minimum advance, the user is **temporarily ineligible due to liquidity**, even if otherwise eligible.

---

## Advancement Limits (v0 Defaults)

All amounts are in **Naira (₦)**.

- **Minimum advance:** ₦2,000
- **Maximum advance:** ₦20,000 (subject to policy and liquidity)
- **New users:** restricted to minimum exposure only

Final approved amounts are always constrained by:
- Behaviour-derived limit
- Global maximum
- Available float
- Optional advisory or risk-team caps

---

## Behavioural Inputs

The V0 model relies on the following inputs (computed from vending data):

- Vend count over recent period
- Days since last vend
- Vend frequency
- Median vend amount
- Vend amount volatility
- Inter-vend interval variance
- Failed vend ratio
- Active obligation flag
- New user indicator

No credit bureau, income, or demographic data is used.

---

## Project Structure

The repository is organized to separate **decision logic**, **delivery**, **testing**, and **documentation**.

* **`src/credit_engine/`**
  Contains the core V0 credit scoring logic. This is where all business rules live.

  * `hard_gates.py` - Eligibility Checks
  * `behaviour_score.py` - Behaviour Score (0 - 100)
  * `limit_engine.py` - Advanced Sizing Logic 
  * `scoring.py` – Implements the decision orchestrator
  * `config.py` – Centralized configuration for thresholds, weights, and limits
  * `utils.py` – Shared helper functions used across the project

* **`api/`**
  Contains the FastAPI application used to expose the scoring engine as an HTTP service.

  * `main.py` – API entry point and request handling

* **`tests/`**
  Contains unit tests to validate scoring logic and API behavior.

  * `test_scoring.py` – Tests for the V0 scoring engine
  * `test_api.py` – Tests for the API endpoints

* **`docs/`**
  Contains detailed documentation for understanding and using the model.

  * `model_overview.md` – High-level explanation of the V0 model
  * `scoring_rules.md` – Detailed breakdown of scoring logic and weights
  * `usage_guide.md` – Examples and instructions for using the model

---

## Prerequisites

Before running this project, ensure you have the following installed:

* **Python 3.9+**
* **pip** (Python package manager)
* **Git**

---

## Getting Started

### Step 1: Clone the repository

```bash
git clone https://github.com/purplegate-paidx/monsera-credit-engine.git
cd monsera-credit-engine
```

### Step 2: Create a virtual environment

```bash
python -m venv .venv
```

### Step 3: Activate the virtual environment

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

### Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Scoring API

The project includes a FastAPI application that exposes the V0 scoring model.

Start the API server:

```bash
uvicorn api.main:app --reload
```

Once running, open your browser and navigate to:

```
http://127.0.0.1:8000/docs
```

This page provides an interactive interface for testing the scoring endpoint.

---

## Example Scoring Request

**POST** `/score`

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

**Example Response:**

```json
{
  "score": 68,
  "risk_band": "Bankable",
  "credit_limit": 4500
}
```

---

## Running Tests

To run all unit tests:

```bash
pytest
```

This validates:
- Hard gate logic
- Behaviour scoring
- Limit sizing
Api integration

---

## Documentation

Additional documentation is available in the `docs/` directory:

* **Model Overview** – Explains the purpose and design of the V0 model
* **Scoring Rules** – Details how scores and risk bands are calculated
* **Usage Guide** – Shows how to use the scoring engine directly or via API

---

## Future Enhancements

This repository is intentionally structured to support future iterations:

* **V1:** Statistical scorecard (logistic regression)
* **V2:** Machine learning models (e.g., XGBoost, LightGBM)
* **V3:** Time-series and sequence-based models

Each new version can be introduced without breaking the existing V0 logic.

---

## Disclaimer

The V0 model is a rule-based system intended for early-stage deployment and controlled experimentation.
All thresholds, limits, and rules should be continuously reviewed as real-world performance data becomes available.

---

## Ownership

This project is part of the Monsera platform initiative and is maintained by the Monsera engineering and data teams.

---