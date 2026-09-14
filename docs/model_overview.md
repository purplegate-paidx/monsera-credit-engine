# Model Overview – V0 Behavioural Credit Engine

The V0 model is Monsera’s foundational decision engine for prepaid utility advances.

It is designed for early-stage deployment where:
- Credit bureau data is unavailable
- Behavioural signals are strong
- Explainability is mandatory
- Risk must be tightly controlled

---

## Design Principles

The model follows four core principles:

1. Behaviour over identity  
2. Eligibility before scoring  
3. Exposure proportional to observed behaviour  
4. Portfolio safety over individual optimisation  

---

## Inputs

The model relies on Tier-1 behavioural data, including:

- Vend frequency
- Median vend amount
- Vend amount volatility
- Inter-vend interval variance
- Failed vend attempts
- Recency of usage
- Existing obligations

---

## Outputs

For each request, the engine returns:

- Eligibility decision (pass/fail)
- Decline reason (if failed)
- Behaviour score (0–100)
- Score band (A–D)
- Approved advance amount

---

## New User Handling

Meters with insufficient history are restricted to minimum exposure or declined until enough behaviour is observed.

This allows learning while controlling downside risk.

---

## Role in the Credit Lifecycle

The V0 model:
- Enables initial lending safely
- Generates labelled repayment data
- Informs feature selection for V1/V2 models

It is not a final underwriting solution, but a **necessary foundation**.
