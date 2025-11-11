"""Route update logic for one-way risk level adjustment."""

from __future__ import annotations

from typing import Literal, Optional

from src_new.perception.psyguard_service import (
    MEDIUM_RISK_THRESHOLD,
    HIGH_RISK_DIRECT_THRESHOLD
)

Route = Literal["low", "medium", "high"]


class RouteUpdater:
    """Manages route updates based on real-time PsyGUARD scores.
    
    Rules:
    - One-way upgrade only (Low → Medium → High)
    - Low can upgrade to Medium (if PsyGUARD >= 0.70)
    - Medium cannot downgrade to Low (maintains Medium)
    - High cannot downgrade (must complete fixed script)
    - Direct upgrade to High (if PsyGUARD >= 0.95)
    """
    
    @staticmethod
    def update_route(
        current_route: Route,
        new_psyguard_score: float
    ) -> Route:
        """
        Update route based on new PsyGUARD score.
        
        Args:
            current_route: Current route ("low", "medium", or "high")
            new_psyguard_score: New PsyGUARD risk score (0.0 - 1.0)
            
        Returns:
            Updated route (may be same or upgraded)
        """
        # High Risk: cannot downgrade
        if current_route == "high":
            return "high"
        
        # Direct upgrade to High (extremely high risk)
        if new_psyguard_score >= HIGH_RISK_DIRECT_THRESHOLD:
            return "high"
        
        # Low → Medium upgrade
        if current_route == "low" and new_psyguard_score >= MEDIUM_RISK_THRESHOLD:
            return "medium"
        
        # Medium: maintain (no downgrade)
        if current_route == "medium":
            return "medium"
        
        # Low: maintain if below threshold
        return current_route
    
    @staticmethod
    def should_upgrade(
        current_route: Route,
        new_psyguard_score: float
    ) -> bool:
        """
        Check if route should be upgraded.
        
        Args:
            current_route: Current route
            new_psyguard_score: New PsyGUARD score
            
        Returns:
            True if upgrade is needed
        """
        new_route = RouteUpdater.update_route(current_route, new_psyguard_score)
        return new_route != current_route
    
    @staticmethod
    def get_upgrade_target(
        current_route: Route,
        new_psyguard_score: float
    ) -> Optional[Route]:
        """
        Get target route if upgrade is needed.
        
        Args:
            current_route: Current route
            new_psyguard_score: New PsyGUARD score
            
        Returns:
            Target route if upgrade needed, None otherwise
        """
        new_route = RouteUpdater.update_route(current_route, new_psyguard_score)
        if new_route != current_route:
            return new_route
        return None


__all__ = ["RouteUpdater", "Route"]

