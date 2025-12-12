# Model Overview – V0 Credit Engine

## Purpose of the V0 Model

The V0 Credit Engine is a **rule-based, deterministic scoring model** designed to assess eligibility and determine advance limits for prepaid utility users.

This model serves three primary purposes:

1. Enable safe, explainable credit decisions during early deployment
2. Minimize risk exposure while historical repayment data is limited
3. Generate labeled outcomes to support future machine learning models

Unlike later versions (V1, V2), the V0 model does **not** rely on statistical or machine learning techniques. All decisions are driven by transparent, predefined business rules.

---

## Design Philosophy

The V0 model is built around the following principles:

- **Explainability**  
  Every score and decision can be traced back to explicit rules and thresholds.

- **Determinism**  
  Identical inputs always produce identical outputs.

- **Separation of concerns**  
  Business logic is isolated from API and infrastructure layers.

- **Extensibility**  
  The structure supports seamless transition to ML-based models in future versions.

---

## Inputs

The model evaluates users using behavioral and operational signals derived from utility vending activity:

- `tenure_months` – Duration the meter has been active
- `avg_monthly_spend` – Average utility spend per month
- `vend_frequency` – Number of vends per month
- `amount_volatility` – Variability in vend amounts
- `failed_vend_ratio` – Percentage of failed vending attempts
- `is_new_user` – Flag indicating first-time users

---

## Outputs

The model produces three outputs:

- **Credit Score** (0–100)
- **Risk Band** (High Risk, Marginal, Bankable, Prime Meter)
- **Credit Limit** (₦0–₦20,000)

---

## New User Handling

Users with insufficient or no historical data are treated as **new users**.  
New users bypass full scoring and are automatically assigned:

- Score: 45  
- Risk Band: Marginal  
- Credit Limit: ₦2,000  

This approach allows controlled onboarding while limiting exposure.

---

## Role in the Model Lifecycle

The V0 model represents the foundation of the Monsera credit decision system.

As the platform matures:
- V0 decisions will generate repayment labels
- These labels will feed V1 statistical scorecards
- V2 and beyond will incorporate machine learning and time-series modeling

V0 remains valuable as a fallback, benchmark, and audit reference even as more advanced models are introduced.
