from __future__ import annotations

from typing import Optional

from .schema import (
    CreditInquiry,
    MeterSnapshot,
    RiskEnvelope,
    Decision,
)
from .eligibility import run_gate_checks
from .behaviour import build_scorecard
from .limits import map_score_to_bucket, compute_limit
from .config_v0 import GLOBAL_MIN_ADVANCE


class BehaviouralV0Engine:
    """
    High-level orchestration for V0 credit decisions.

    Usage:
        engine = BehaviouralV0Engine()
        decision = engine.assess(inquiry, snapshot, risk_env)
    """

    def assess(
        self,
        inquiry: CreditInquiry,
        snapshot: MeterSnapshot,
        risk_env: Optional[RiskEnvelope] = None,
    ) -> Decision:
        # 1) Hard gates
        gates_ok, gate_notes = run_gate_checks(snapshot)
        if not gates_ok:
            return Decision(
                eligible=False,
                behaviour_score=0.0,
                risk_tier="HIGH_RISK",
                approved_value=0.0,
                explanations=gate_notes,
                scorecard=None,
            )

        # 2) Behaviour score
        card = build_scorecard(snapshot)
        total_score = card.total_score
        bucket = map_score_to_bucket(total_score)

        # 3) Limit computation
        approved, limit_notes = compute_limit(
            score_bucket=bucket,
            snapshot=snapshot,
            inquiry=inquiry,
            envelope=risk_env or RiskEnvelope(),
        )

        reasons = list(dict.fromkeys(gate_notes + limit_notes))

        eligible = approved >= GLOBAL_MIN_ADVANCE and bucket != "HIGH_RISK"
        if not eligible:
            approved = 0.0

        return Decision(
            eligible=eligible,
            behaviour_score=round(float(total_score), 1),
            risk_tier=bucket,
            approved_value=float(round(approved, 2)),
            explanations=reasons,
            scorecard=card,
        )
