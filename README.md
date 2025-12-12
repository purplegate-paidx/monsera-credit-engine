# Monsera v0 Credit Scoring & Advancement Model


This repository contains the **V0 rule-based credit scoring engine** used for determining user eligibility and deciding the advancement (credit) amount offered to electricity meter users.
The V0 model is deterministic, explainable, and designed as the foundation for more advanced ML-powered versions.


## Project Purpose

The Monsera Credit Engine computes:

- A **credit score** (0–100) using simple behavioral rules
- A **risk category**
- An **advance limit** (₦2,000–₦20,000)


This v0 is deliberately **deterministic and transparent**. It is designed to be:
- Easy to implement and audit
- A safe starting point before full AI/ML scorecards
- A foundation for future versions (V1/V2: statistical & ML models) :contentReference[oaicite:0]{index=0}


---

## Scoring Bands

The model assumes a **score between 0 and 100** (inclusive), and maps it to four
risk buckets:

| Score Range | Category     | Description |
|------------|--------------|-------------|
| 0–39       | High Risk    | Not eligible for advance |
| 40–59      | Marginal     | Eligible for minimum advance only |
| 60–79      | Bankable     | Eligible for moderate advance |
| 80–100     | Prime Meter  | Eligible for maximum advance |

---

## Advancement Limits & Eligibility Rules (v0)

All amounts are in **Naira (₦)** by default.

Global limits:

- **Minimum advance:** `₦2,000`
- **Maximum advance:** `₦20,000` (or capped lower by advisory/team policy)
- **Available float:** the maximum that can be disbursed at that moment
  (e.g. wallet balance or liquidity pool)

High-level rules:

1. **New users**  
   - Only eligible for **minimum** advance (₦2,000)

2. **Existing users**  
   - Must have score ≥ 40 to be eligible.
   - Per-band caps (applied on top of global max and available float):

     | Band        | Score Range | Band Cap (default) |
     |------------|-------------|--------------------|
     | HIGH_RISK  | 0–39        | ₦0 (not eligible)  |
     | MARGINAL   | 40–59       | 25% of global max  |
     | BANKABLE   | 60–79       | 50% of global max  |
     | PRIME      | 80–100      | 100% of global max |

   The **final recommended advance** is the minimum of:
   - Band cap
   - Global max advance
   - Available float
   - An optional advisory cap (e.g. from risk team, product config)

3. **Available float always wins**  
   If available float is less than:
   - The minimum advance → the user is considered **temporarily ineligible**
     (no liquidity).
   - The calculated band cap → recommend only up to the available float.

4. **Team advisory cap**  
   The product / risk team can set a **runtime advisory cap** (e.g. for a
   specific cohort, campaign, or pilot). This cap further constrains the
   maximum advance recommended by the engine.

---

## Scoring Inputs

The V0 model uses the following inputs:

- `tenure_months` – How long the meter has been active  
- `avg_monthly_spend` – Average monthly utility spend  
- `vend_frequency` – Average number of vends per month  
- `amount_volatility` – Variability in vend amounts (percentage)  
- `failed_vend_ratio` – Percentage of failed vending attempts  
- `is_new_user` – Boolean flag for first-time users  

---


### Project Structure (Explanation)

The repository is organized to clearly separate **business logic**, **delivery (API)**, **testing**, and **documentation**, making the project easy to understand, maintain, and extend.

* **`src/credit_engine/`**
  Contains the core V0 credit scoring logic. This is where all business rules live.

  * `scoring.py` – Implements the V0 scoring, risk classification, and advance calculation logic
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

This validates both the scoring logic and the API behavior.

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