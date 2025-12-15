from typing import Dict, List, Tuple
COMPONENT_WEIGHTS: Dict[str, float] = {
    "usage_intensity": 30.0,       
    "usage_stability": 25.0,       
    "spending_capacity": 25.0,    
    "operational_reliability": 20.0,  
}

# Hard gate thresholds
GATE_LIMITS: Dict[str, float] = {
    "min_vends_60d": 6,            
    "max_idle_days": 30,           
    "max_failed_ratio": 0.40,      
    "max_channel_switch": 0.95,    
}

# Scoring thresholds (soft)
SCORE_LIMITS: Dict[str, float] = {
    "freq_high": 8.0,
    "freq_mid": 4.0,
    "freq_low": 1.0,
    "recency_fresh": 7,
    "recency_stale": 21,
    "spacing_var_low": 3.0,
    "spacing_var_high": 10.0,
    "value_vol_low": 0.25,
    "value_vol_high": 0.75,
    "failed_low": 0.05,
    "failed_high": 0.30,
}

# Risk tiers based on total behaviour score
RISK_BUCKETS: List[Tuple[str, int, int]] = [
    ("PRIME", 80, 100),
    ("BANKABLE", 60, 79),
    ("MARGINAL", 40, 59),
    ("HIGH_RISK", 0, 39),
]

# Limit policy per bucket
BUCKET_LIMIT_POLICY: Dict[str, Dict[str, float]] = {
    "PRIME": {"cap": 20_000.0, "median_multiplier": 1.0},
    "BANKABLE": {"cap": 15_000.0, "median_multiplier": 0.8},
    "MARGINAL": {"cap": 8_000.0, "median_multiplier": 0.5},
    "HIGH_RISK": {"cap": 0.0, "median_multiplier": 0.0},
}

# Global bounds from PM note
GLOBAL_MIN_ADVANCE: float = 2_000.0
GLOBAL_MAX_ADVANCE: float = 20_000.0
