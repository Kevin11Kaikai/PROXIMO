"""
Risk mapping module for converting assessment results to risk scores and rigidness.
"""

from .mapping import (
    RiskMappingConfig,
    DEFAULT,
    load_config,
    normalize_sev,
    severity_to_risk,
    risk_to_rigid,
    compute_rigid_from_severity,
    is_hard_lock,
)

__all__ = [
    "RiskMappingConfig",
    "DEFAULT",
    "load_config",
    "normalize_sev",
    "severity_to_risk",
    "risk_to_rigid",
    "compute_rigid_from_severity",
    "is_hard_lock",
]


