"""
Risk mapping module for converting assessment severity levels to risk scores and rigidness.

This module provides functions to:
1. Map severity levels (minimal/mild/moderate/severe) to risk scores (0.0 - 1.0)
2. Convert risk scores to rigidness scores using linear transformation
3. Detect crisis conditions (hard lock triggers)
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path

from src.core.experiment_config import experiment_config

logger = logging.getLogger(__name__)


@dataclass
class RiskMappingConfig:
    """Configuration for risk mapping."""
    
    severity_to_risk: Dict[str, float]
    a: float  # Linear transformation coefficient
    b: float  # Linear transformation intercept
    crisis_item9_lock: bool  # Whether to trigger hard lock on suicidal ideation
    crisis_severity_lock: set  # Severity levels that trigger hard lock


DEFAULT = RiskMappingConfig(
    severity_to_risk={
        "minimal": 0.15,
        "mild": 0.35,
        "moderate": 0.60,
        "severe": 0.95,
    },
    a=1.0,
    b=0.0,
    crisis_item9_lock=True,
    crisis_severity_lock={"severe"},
)


def load_config() -> RiskMappingConfig:
    """
    Load risk mapping configuration from experiment config.
    
    Falls back to DEFAULT if config file is missing or invalid.
    
    Returns:
        RiskMappingConfig: Loaded configuration
    """
    try:
        # Try to load from experiment_config
        config = experiment_config.get_config("risk_mapping")
        if config:
            sev = config.get("severity_to_risk_score", {})
            rigid = config.get("rigid_transform", {})
            crises = config.get("crisis_rules", {})
            
            return RiskMappingConfig(
                severity_to_risk={**DEFAULT.severity_to_risk, **sev},
                a=float(rigid.get("a", DEFAULT.a)),
                b=float(rigid.get("b", DEFAULT.b)),
                crisis_item9_lock=bool(
                    crises.get("phq9_item9_flag_to_hard_lock", DEFAULT.crisis_item9_lock)
                ),
                crisis_severity_lock=set(
                    crises.get("severity_hard_lock", list(DEFAULT.crisis_severity_lock))
                ),
            )
    except Exception as e:
        logger.warning(f"Failed to load risk_mapping config, using defaults: {e}")
    
    # Fall back to default configuration
    return DEFAULT


def normalize_sev(sev: str) -> str:
    """
    Normalize severity string to lowercase with underscores.
    
    Args:
        sev: Severity string (e.g., "Minimal", "moderately severe")
        
    Returns:
        Normalized string (e.g., "minimal", "moderately_severe")
    """
    return sev.strip().lower().replace(" ", "_")


def severity_to_risk(severity: str, cfg: RiskMappingConfig) -> float:
    """
    Convert severity level to risk score.
    
    Args:
        severity: Severity level (minimal/mild/moderate/severe)
        cfg: Risk mapping configuration
        
    Returns:
        Risk score (0.0 - 1.0)
    """
    normalized = normalize_sev(severity)
    return cfg.severity_to_risk.get(normalized, cfg.severity_to_risk["moderate"])


def risk_to_rigid(risk: float, cfg: RiskMappingConfig) -> float:
    """
    Convert risk score to rigidness score using linear transformation.
    
    Formula: rigid_score = a * risk_score + b
    Clamped to [0.0, 1.0]
    
    Args:
        risk: Risk score (0.0 - 1.0)
        cfg: Risk mapping configuration
        
    Returns:
        Rigidness score (0.0 - 1.0)
    """
    x = cfg.a * float(risk) + cfg.b
    return max(0.0, min(1.0, x))


def compute_rigid_from_severity(
    severity: str, cfg: Optional[RiskMappingConfig] = None
) -> float:
    """
    Compute rigidness score from severity level.
    
    Args:
        severity: Severity level (minimal/mild/moderate/severe)
        cfg: Optional risk mapping configuration (loads from config if None)
        
    Returns:
        Rigidness score (0.0 - 1.0)
    """
    if cfg is None:
        cfg = load_config()
    risk = severity_to_risk(severity, cfg)
    return risk_to_rigid(risk, cfg)


def is_hard_lock(
    severity: str, flags: Dict[str, Any], cfg: Optional[RiskMappingConfig] = None
) -> bool:
    """
    Check if assessment should trigger hard lock (crisis mode).
    
    Hard lock triggers:
    1. Suicidal ideation flag is present (if crisis_item9_lock is True)
    2. Severity level is in crisis_severity_lock set
    
    Args:
        severity: Severity level (minimal/mild/moderate/severe)
        flags: Assessment flags dictionary (from assess() output)
        cfg: Optional risk mapping configuration (loads from config if None)
        
    Returns:
        True if hard lock should be triggered, False otherwise
    """
    if cfg is None:
        cfg = load_config()
    
    # Check suicidal ideation (using actual field names from assess() output)
    item9 = bool(
        flags.get("suicidal_ideation", False)
        or flags.get("suicidal_ideation_score", 0) >= 2
    )
    if cfg.crisis_item9_lock and item9:
        return True
    
    # Check severity level
    normalized_sev = normalize_sev(severity)
    return normalized_sev in cfg.crisis_severity_lock

