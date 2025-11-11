"""Feedback collection service for Adaptive Layer."""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AcceptanceLevel(str, Enum):
    """Acceptance level for suggestions."""
    ACCEPTED = "accepted"
    PARTIALLY = "partially"
    REJECTED = "rejected"


class FollowUpBehavior(str, Enum):
    """Follow-up behavior after conversation."""
    HOTLINE = "hotline"
    PEER_GROUP = "peer_group"
    APPOINTMENT = "appointment"
    NONE = "none"


@dataclass
class FeedbackScore:
    """Feedback score data structure.
    
    Collects feedback from users after conversations to support
    future RLHF (Reinforcement Learning from Human Feedback).
    """
    # Core fields
    timestamp: datetime
    user_id: str
    conversation_id: str
    route: str  # "low" / "medium" / "high"
    
    # Low/Medium Risk feedback
    satisfaction: Optional[int] = None  # 1-5, High Risk does not collect
    acceptance: Optional[str] = None  # "accepted" / "partially" / "rejected"
    follow_up_behavior: Optional[str] = None  # "hotline" / "peer_group" / "appointment" / "none"
    
    # High Risk special feedback
    sought_help: Optional[bool] = None  # Whether user contacted hotline/sought help
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "route": self.route,
            "satisfaction": self.satisfaction,
            "acceptance": self.acceptance,
            "follow_up_behavior": self.follow_up_behavior,
            "sought_help": self.sought_help,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeedbackScore":
        """Create from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        
        return cls(
            timestamp=timestamp,
            user_id=data["user_id"],
            conversation_id=data["conversation_id"],
            route=data["route"],
            satisfaction=data.get("satisfaction"),
            acceptance=data.get("acceptance"),
            follow_up_behavior=data.get("follow_up_behavior"),
            sought_help=data.get("sought_help"),
            metadata=data.get("metadata", {})
        )


class FeedbackCollector:
    """Collects feedback from users after conversations.
    
    Current stage: Only collect and store, no real-time adjustment.
    Future use: RLHF (Reinforcement Learning from Human Feedback).
    """
    
    def __init__(self):
        """Initialize feedback collector."""
        self._storage: Dict[str, list[FeedbackScore]] = {}  # In-memory storage
    
    def collect_feedback(
        self,
        user_id: str,
        conversation_id: str,
        route: str,
        satisfaction: Optional[int] = None,
        acceptance: Optional[str] = None,
        follow_up_behavior: Optional[str] = None,
        sought_help: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FeedbackScore:
        """
        Collect feedback from user.
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            route: Risk route (low/medium/high)
            satisfaction: Satisfaction score (1-5), None for High Risk
            acceptance: Acceptance level (accepted/partially/rejected)
            follow_up_behavior: Follow-up behavior (hotline/peer_group/appointment/none)
            sought_help: Whether user sought help (High Risk only)
            metadata: Additional metadata
            
        Returns:
            FeedbackScore object
        """
        # Validate satisfaction (1-5)
        if satisfaction is not None:
            if not (1 <= satisfaction <= 5):
                raise ValueError(f"Satisfaction must be between 1 and 5, got {satisfaction}")
            # High Risk should not have satisfaction
            if route == "high":
                logger.warning(f"High Risk route should not collect satisfaction, ignoring")
                satisfaction = None
        
        # Validate acceptance
        if acceptance is not None:
            valid_acceptance = [a.value for a in AcceptanceLevel]
            if acceptance not in valid_acceptance:
                raise ValueError(f"Acceptance must be one of {valid_acceptance}, got {acceptance}")
        
        # Validate follow_up_behavior
        if follow_up_behavior is not None:
            valid_behaviors = [b.value for b in FollowUpBehavior]
            if follow_up_behavior not in valid_behaviors:
                raise ValueError(f"Follow-up behavior must be one of {valid_behaviors}, got {follow_up_behavior}")
        
        # Create feedback score
        feedback = FeedbackScore(
            timestamp=datetime.now(),
            user_id=user_id,
            conversation_id=conversation_id,
            route=route,
            satisfaction=satisfaction,
            acceptance=acceptance,
            follow_up_behavior=follow_up_behavior,
            sought_help=sought_help,
            metadata=metadata or {}
        )
        
        # Store feedback
        if user_id not in self._storage:
            self._storage[user_id] = []
        self._storage[user_id].append(feedback)
        
        logger.info(
            f"Collected feedback: user={user_id}, route={route}, "
            f"satisfaction={satisfaction}, acceptance={acceptance}"
        )
        
        return feedback
    
    def get_user_feedback(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> list[FeedbackScore]:
        """
        Get feedback history for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of feedback entries to return
            
        Returns:
            List of FeedbackScore objects (most recent first)
        """
        if user_id not in self._storage:
            return []
        
        feedback_list = self._storage[user_id]
        if limit:
            return feedback_list[-limit:]
        return feedback_list
    
    def get_feedback_by_route(
        self,
        route: str,
        limit: Optional[int] = None
    ) -> list[FeedbackScore]:
        """
        Get feedback for a specific route.
        
        Args:
            route: Risk route (low/medium/high)
            limit: Maximum number of feedback entries to return
            
        Returns:
            List of FeedbackScore objects
        """
        all_feedback = []
        for user_feedback in self._storage.values():
            for feedback in user_feedback:
                if feedback.route == route:
                    all_feedback.append(feedback)
        
        # Sort by timestamp (most recent first)
        all_feedback.sort(key=lambda f: f.timestamp, reverse=True)
        
        if limit:
            return all_feedback[:limit]
        return all_feedback
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get feedback statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_feedback = sum(len(feedbacks) for feedbacks in self._storage.values())
        
        route_counts = {"low": 0, "medium": 0, "high": 0}
        satisfaction_scores = []
        acceptance_counts = {"accepted": 0, "partially": 0, "rejected": 0}
        follow_up_counts = {"hotline": 0, "peer_group": 0, "appointment": 0, "none": 0}
        sought_help_count = 0
        
        for user_feedback in self._storage.values():
            for feedback in user_feedback:
                route_counts[feedback.route] = route_counts.get(feedback.route, 0) + 1
                
                if feedback.satisfaction is not None:
                    satisfaction_scores.append(feedback.satisfaction)
                
                if feedback.acceptance:
                    acceptance_counts[feedback.acceptance] = acceptance_counts.get(feedback.acceptance, 0) + 1
                
                if feedback.follow_up_behavior:
                    follow_up_counts[feedback.follow_up_behavior] = follow_up_counts.get(feedback.follow_up_behavior, 0) + 1
                
                if feedback.sought_help is True:
                    sought_help_count += 1
        
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else None
        
        return {
            "total_feedback": total_feedback,
            "route_counts": route_counts,
            "average_satisfaction": avg_satisfaction,
            "acceptance_counts": acceptance_counts,
            "follow_up_counts": follow_up_counts,
            "sought_help_count": sought_help_count
        }


__all__ = [
    "FeedbackScore",
    "FeedbackCollector",
    "AcceptanceLevel",
    "FollowUpBehavior"
]
