"""
Tests for risk mapping module.
"""

import pytest
from src.risk.mapping import (
    DEFAULT,
    RiskMappingConfig,
    compute_rigid_from_severity,
    is_hard_lock,
    normalize_sev,
    severity_to_risk,
    risk_to_rigid,
    load_config,
)


class TestNormalizeSeverity:
    """Test severity normalization."""
    
    def test_normalize_basic(self):
        """Test basic normalization."""
        assert normalize_sev("minimal") == "minimal"
        assert normalize_sev("mild") == "mild"
        assert normalize_sev("moderate") == "moderate"
        assert normalize_sev("severe") == "severe"
    
    def test_normalize_case_insensitive(self):
        """Test case insensitivity."""
        assert normalize_sev("Minimal") == "minimal"
        assert normalize_sev("MILD") == "mild"
        assert normalize_sev("Moderate") == "moderate"
        assert normalize_sev("SEVERE") == "severe"
    
    def test_normalize_spaces(self):
        """Test space normalization."""
        assert normalize_sev("moderately severe") == "moderately_severe"
        assert normalize_sev("  minimal  ") == "minimal"


class TestSeverityToRisk:
    """Test severity to risk score conversion."""
    
    def test_mapping_defaults(self):
        """Test default mapping values."""
        assert abs(severity_to_risk("minimal", DEFAULT) - 0.15) < 1e-9
        assert abs(severity_to_risk("mild", DEFAULT) - 0.35) < 1e-9
        assert abs(severity_to_risk("moderate", DEFAULT) - 0.60) < 1e-9
        assert abs(severity_to_risk("severe", DEFAULT) - 0.95) < 1e-9
    
    def test_unknown_severity(self):
        """Test unknown severity falls back to moderate."""
        result = severity_to_risk("unknown", DEFAULT)
        assert abs(result - 0.60) < 1e-9  # Should default to moderate


class TestRiskToRigid:
    """Test risk to rigidness conversion."""
    
    def test_linear_transformation(self):
        """Test linear transformation."""
        # With default a=1.0, b=0.0, rigid = risk
        assert abs(risk_to_rigid(0.5, DEFAULT) - 0.5) < 1e-9
        assert abs(risk_to_rigid(0.0, DEFAULT) - 0.0) < 1e-9
        assert abs(risk_to_rigid(1.0, DEFAULT) - 1.0) < 1e-9
    
    def test_clamping(self):
        """Test clamping to [0.0, 1.0]."""
        # Create config with transformation that would go out of bounds
        cfg = RiskMappingConfig(
            severity_to_risk={},
            a=2.0,
            b=-0.5,
            crisis_item9_lock=True,
            crisis_severity_lock=set(),
        )
        result = risk_to_rigid(0.8, cfg)
        assert 0.0 <= result <= 1.0


class TestComputeRigidFromSeverity:
    """Test computing rigidness from severity."""
    
    def test_compute_rigid_defaults(self):
        """Test computing rigidness with default config."""
        assert abs(compute_rigid_from_severity("minimal", DEFAULT) - 0.15) < 1e-9
        assert abs(compute_rigid_from_severity("mild", DEFAULT) - 0.35) < 1e-9
        assert abs(compute_rigid_from_severity("moderate", DEFAULT) - 0.60) < 1e-9
        assert abs(compute_rigid_from_severity("severe", DEFAULT) - 0.95) < 1e-9
    
    def test_compute_rigid_case_insensitive(self):
        """Test case insensitivity."""
        assert abs(compute_rigid_from_severity("Minimal", DEFAULT) - 0.15) < 1e-9
        assert abs(compute_rigid_from_severity("SEVERE", DEFAULT) - 0.95) < 1e-9


class TestHardLock:
    """Test hard lock detection."""
    
    def test_hard_lock_item9_suicidal_ideation(self):
        """Test hard lock triggered by suicidal ideation flag."""
        # Using actual field name from assess() output
        flags = {"suicidal_ideation": True}
        assert is_hard_lock("mild", flags, DEFAULT) is True
    
    def test_hard_lock_item9_score(self):
        """Test hard lock triggered by suicidal ideation score >= 2."""
        flags = {"suicidal_ideation_score": 2}
        assert is_hard_lock("mild", flags, DEFAULT) is True
        
        flags = {"suicidal_ideation_score": 3}
        assert is_hard_lock("mild", flags, DEFAULT) is True
    
    def test_hard_lock_item9_no_trigger(self):
        """Test no hard lock when suicidal ideation is False or score < 2."""
        flags = {"suicidal_ideation": False, "suicidal_ideation_score": 0}
        assert is_hard_lock("mild", flags, DEFAULT) is False
        
        flags = {"suicidal_ideation_score": 1}
        assert is_hard_lock("mild", flags, DEFAULT) is False
    
    def test_hard_lock_severity_severe(self):
        """Test hard lock triggered by severe severity."""
        flags = {}
        assert is_hard_lock("severe", flags, DEFAULT) is True
    
    def test_hard_lock_severity_no_trigger(self):
        """Test no hard lock for non-severe severity levels."""
        flags = {}
        assert is_hard_lock("minimal", flags, DEFAULT) is False
        assert is_hard_lock("mild", flags, DEFAULT) is False
        assert is_hard_lock("moderate", flags, DEFAULT) is False
    
    def test_hard_lock_severity_case_insensitive(self):
        """Test severity hard lock is case insensitive."""
        flags = {}
        assert is_hard_lock("Severe", flags, DEFAULT) is True
        assert is_hard_lock("SEVERE", flags, DEFAULT) is True
    
    def test_hard_lock_item9_disabled(self):
        """Test hard lock when item9 lock is disabled."""
        cfg = RiskMappingConfig(
            severity_to_risk={},
            a=1.0,
            b=0.0,
            crisis_item9_lock=False,  # Disabled
            crisis_severity_lock={"severe"},
        )
        flags = {"suicidal_ideation": True}
        assert is_hard_lock("mild", flags, cfg) is False  # Should not trigger
    
    def test_hard_lock_priority(self):
        """Test that item9 lock takes priority over severity."""
        flags = {"suicidal_ideation": True}
        # Even with mild severity, suicidal ideation should trigger hard lock
        assert is_hard_lock("mild", flags, DEFAULT) is True


class TestLoadConfig:
    """Test configuration loading."""
    
    def test_load_config_returns_config(self):
        """Test that load_config returns a valid config."""
        cfg = load_config()
        assert isinstance(cfg, RiskMappingConfig)
        assert "minimal" in cfg.severity_to_risk
        assert "severe" in cfg.severity_to_risk
        assert cfg.a > 0
        assert isinstance(cfg.crisis_severity_lock, set)


