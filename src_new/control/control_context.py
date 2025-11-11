"""Shared data structures used by the control layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Literal
from datetime import datetime

Route = Literal["low", "medium", "high"]


@dataclass
class ControlContext:
    """Context for control layer decisions.
    
    Contains all information needed for routing and policy decisions.
    """
    user_id: str
    route: Route
    rigid_score: float
    guardrails_enabled: bool = True
    
    # Perception Layer outputs
    psyguard_score: Optional[float] = None
    questionnaire_phq9_score: Optional[float] = None
    questionnaire_gad7_score: Optional[float] = None
    phq9_q9_score: Optional[int] = None  # Suicidal ideation score
    
    # Routing metadata
    route_reason: Optional[str] = None
    route_source: Optional[str] = None  # "questionnaire", "chat_content", "legacy"
    
    # Timestamps
    route_established_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    
    # Additional metadata
    extras: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.route_established_at is None:
            self.route_established_at = datetime.now()
        if self.last_updated_at is None:
            self.last_updated_at = datetime.now()
    
    def update_route(self, new_route: Route, reason: Optional[str] = None):
        """Update route and timestamp."""
        if new_route != self.route:
            self.route = new_route
            self.last_updated_at = datetime.now()
            if reason:
                self.route_reason = reason


__all__ = ["ControlContext", "Route"]

