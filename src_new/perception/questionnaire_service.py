"""Wrapper around legacy questionnaire assessment APIs."""

from __future__ import annotations

from typing import Dict, Any, List, Optional

from src.assessment import proximo_api


class QuestionnaireService:
    """Expose questionnaire assessments (PHQ-9 / GAD-7 / PSS-10) via new API."""

    async def assess(
        self,
        scale: str,
        responses: List[str],
        persona_id: Optional[str] = None,
        simulation_day: int = 0,
    ) -> Dict[str, Any]:
        """Delegate to the existing assessment proximo API."""

        return await proximo_api.assess(
            scale=scale,
            responses=responses,
            persona_id=persona_id,
            simulation_day=simulation_day,
        )

