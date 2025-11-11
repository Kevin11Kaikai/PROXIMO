"""Shared pydantic models for cross-layer communication."""

from __future__ import annotations

from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from pydantic import BaseModel, Field


class PerceptionSummary(BaseModel):
    user_id: str
    aggregated_score: float = Field(ge=0.0, le=1.0)
    signals: List[Dict[str, Any]] = Field(default_factory=list)


class PipelineResult(BaseModel):
    assessment: Dict[str, Any]
    routing: Dict[str, Any]
    result: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class ConversationTurn:
    """A single conversation turn."""
    role: str  # "user" or "bot"
    text: str
    timestamp: Optional[str] = None


__all__ = ["PerceptionSummary", "PipelineResult", "ConversationTurn"]

