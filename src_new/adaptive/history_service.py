"""History service for adaptive learning."""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.storage.repo import AssessmentRepo
from src_new.adaptive.feedback import FeedbackScore, FeedbackCollector

logger = logging.getLogger(__name__)


class HistoryService:
    """Service for accessing conversation and assessment history.
    
    Provides history data for adaptive learning and feedback analysis.
    """
    
    def __init__(self, assessment_repo: Optional[AssessmentRepo] = None):
        """Initialize history service."""
        self.assessment_repo = assessment_repo or AssessmentRepo()
        self.feedback_collector = FeedbackCollector()
    
    async def get_user_history(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get assessment history for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of entries to return
            
        Returns:
            List of assessment history entries
        """
        try:
            history = await self.assessment_repo.history(
                user_id=user_id,
                limit=limit
            )
            return history
        except Exception as e:
            logger.error(f"Error getting user history: {e}", exc_info=True)
            return []
    
    def get_user_feedback(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[FeedbackScore]:
        """
        Get feedback history for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of entries to return
            
        Returns:
            List of FeedbackScore objects
        """
        return self.feedback_collector.get_user_feedback(user_id, limit)
    
    async def get_user_complete_history(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get complete history (assessments + feedback) for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of entries to return
            
        Returns:
            Dictionary with assessments and feedback
        """
        assessments = await self.get_user_history(user_id, limit)
        feedback = self.get_user_feedback(user_id, limit)
        
        return {
            "user_id": user_id,
            "assessments": assessments,
            "feedback": [f.to_dict() for f in feedback],
            "total_assessments": len(assessments),
            "total_feedback": len(feedback)
        }
    
    def collect_feedback(
        self,
        user_id: str,
        conversation_id: str,
        route: str,
        **kwargs
    ) -> FeedbackScore:
        """
        Collect feedback (wrapper around FeedbackCollector).
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            route: Risk route (low/medium/high)
            **kwargs: Additional feedback parameters
            
        Returns:
            FeedbackScore object
        """
        return self.feedback_collector.collect_feedback(
            user_id=user_id,
            conversation_id=conversation_id,
            route=route,
            **kwargs
        )
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """
        Get feedback statistics.
        
        Returns:
            Dictionary with feedback statistics
        """
        return self.feedback_collector.get_statistics()
    
    async def get_route_history(
        self,
        route: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get assessment history for a specific route.
        
        Args:
            route: Risk route (low/medium/high)
            limit: Maximum number of entries to return
            
        Returns:
            List of assessment entries for the route
        """
        try:
            # Get all history and filter by route
            all_history = await self.assessment_repo.history(limit=1000)  # Get more to filter
            filtered = [
                entry for entry in all_history
                if entry.get("route") == route
            ]
            
            if limit:
                return filtered[:limit]
            return filtered
        except Exception as e:
            logger.error(f"Error getting route history: {e}", exc_info=True)
            return []


__all__ = ["HistoryService"]
