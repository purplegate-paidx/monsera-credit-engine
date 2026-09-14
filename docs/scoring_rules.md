# Scoring Rules – V0 Behaviour Model

This document describes how the behaviour score (0–100) is calculated.

---

## 1. Frequency Score (0–30)

Higher vend frequency implies more repayment checkpoints.

| Frequency | Score |
|---------|-------|
| ≥5 | 30 |
| 3–4 | 20 |
| 1–2 | 10 |
| <1 | 0 |

---

## 2. Consistency Score (0–25)

Consistency combines:
- Inter-vend interval variance
- Vend amount volatility

Lower volatility and predictable timing score higher.

---

## 3. Capacity Score (0–25)

Capacity is based on **median vend amount**, not total spend.

High volatility reduces effective capacity.

---

## 4. Reliability Score (0–20)

Based on:
- Failed vend attempts
- Transaction friction

High failure rates reduce reliability.

---

## Score Bands

| Score | Band |
|------|------|
| 80–100 | A |
| 65–79 | B |
| 50–64 | C |
| <50 | D |

Only bands A–C are eligible for advances.
