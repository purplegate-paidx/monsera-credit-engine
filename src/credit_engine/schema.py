from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MeterSnapshot:
    """
    Behavioural snapshot for a single meter at the time of a credit request.
    All fields should be computed by the feature pipeline.
    """
    meter_id: str
    vend_count_60d: int
    vend_frequency_60d: float          
    days_since_last_vend: int
    spacing_variance: float           
    median_vend_value: float          
    value_volatility: float            
    failed_attempt_ratio: float        
    channel_switch_index: float        
    has_open_obligation: bool        


@dataclass
class CreditInquiry:
    """
    Raw request from a partner system.
    """
    meter_id: str
    requested_value: float         
    channel: str                       
    partner_id: Optional[str] = None


@dataclass
class RiskEnvelope:
    """
    Optional portfolio-level constraints – float, daily caps, etc.
    """
    float_available: Optional[float] = None
    daily_exposure_room: Optional[float] = None
    channel_exposure_room: Optional[float] = None


@dataclass
class ScoreCard:
    """
    Decomposed behaviour score. Total should be between 0 and 100.
    """
    usage_intensity: float            
    usage_stability: float             
    spending_capacity: float           
    operational_reliability: float     

    @property
    def total_score(self) -> float:
        return (
            self.usage_intensity
            + self.usage_stability
            + self.spending_capacity
            + self.operational_reliability
        )


@dataclass
class Decision:
    """
    Final decision returned by the V0 engine.
    """
    eligible: bool
    behaviour_score: float             
    risk_tier: str                     
    approved_value: float            
    explanations: List[str]
    scorecard: Optional[ScoreCard] = None
