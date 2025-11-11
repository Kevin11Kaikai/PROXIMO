"""
Assessment and conversation API endpoints for PROXIMO MVP.

This module provides HTTP endpoints for:
- Assessment only
- Assessment + routing
- Assessment + routing + policy execution (with session & persistence)
- Assessment history
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from src.core.logging import get_logger
from src.assessment.proximo_api import assess
from src.conversation.router import decide_route, Route
from src.conversation.engine import ConversationEngine, ConversationRequest
from src.conversation.policies import SAFETY_BANNER
from src.storage.repo import AssessmentRepo
from src.services.ollama_service import OllamaService

logger = get_logger(__name__)
router = APIRouter(prefix="/assess", tags=["assessment"])

# Global service instances (lazy loaded)
_llm_service: Optional[OllamaService] = None
_repo: Optional[AssessmentRepo] = None


async def get_llm_service() -> OllamaService:
    """Get or initialize LLM service."""
    global _llm_service
    if _llm_service is None:
        _llm_service = OllamaService()
        try:
            await _llm_service.load_model()
        except Exception as e:
            logger.warning(f"LLM service not available, will use fallbacks: {e}")
    return _llm_service


def get_repo() -> AssessmentRepo:
    """Get or initialize assessment repository."""
    global _repo
    if _repo is None:
        _repo = AssessmentRepo()
    return _repo


# Valid scales enum
class ScaleEnum(str, Enum):
    """Valid assessment scales."""
    PHQ9 = "phq9"
    GAD7 = "gad7"
    PSS10 = "pss10"


# Request/Response Models
class AssessmentRequest(BaseModel):
    """Request model for assessment."""
    user_id: str = Field(..., description="User identifier")
    scale: str = Field(..., description="Assessment scale (phq9, gad7, pss10)")
    responses: List[str] = Field(..., description="Assessment responses")
    
    @field_validator("scale")
    @classmethod
    def validate_scale(cls, v: str) -> str:
        """Validate scale is one of the allowed values."""
        valid_scales = {"phq9", "gad7", "pss10"}
        if v.lower() not in valid_scales:
            raise ValueError(f"scale must be one of {valid_scales}, got {v}")
        return v.lower()
    
    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Validate user_id is not empty."""
        if not v or not v.strip():
            raise ValueError("user_id cannot be empty")
        return v.strip()


class AssessmentResponse(BaseModel):
    """Response model for assessment only."""
    user_id: str
    assessment: Dict[str, Any]
    timestamp: datetime
    duration_ms: float


class RouteRequest(BaseModel):
    """Request model for assessment + routing."""
    user_id: str = Field(..., description="User identifier")
    scale: str = Field(..., description="Assessment scale (phq9, gad7, pss10)")
    responses: List[str] = Field(..., description="Assessment responses")


class RouteResponse(BaseModel):
    """Response model for assessment + routing."""
    user_id: str
    assessment: Dict[str, Any]
    decision: Dict[str, Any]
    timestamp: datetime
    duration_ms: float


class ExecuteRequest(BaseModel):
    """Request model for full pipeline execution."""
    user_id: str = Field(..., description="User identifier")
    scale: str = Field(default="gad7", description="Assessment scale (phq9, gad7, pss10). Defaults to gad7 for first contact.")
    responses: List[str] = Field(default_factory=list, description="Assessment responses")
    user_message: Optional[str] = Field(None, description="User message for conversation (optional)")
    
    @field_validator("scale")
    @classmethod
    def validate_scale(cls, v: str) -> str:
        """Validate scale is one of the allowed values."""
        valid_scales = {"phq9", "gad7", "pss10"}
        if v.lower() not in valid_scales:
            raise ValueError(f"scale must be one of {valid_scales}, got {v}")
        return v.lower()
    
    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Validate user_id is not empty."""
        if not v or not v.strip():
            raise ValueError("user_id cannot be empty")
        return v.strip()


class ExecuteResponse(BaseModel):
    """Response model for full pipeline execution."""
    user_id: str
    assessment: Dict[str, Any]
    decision: Dict[str, Any]
    policy_result: Optional[Dict[str, Any]] = None
    timestamp: datetime
    duration_ms: float
    safety_banner: Optional[str] = None  # Safety banner for high risk
    context_tail: Optional[List[Dict[str, Any]]] = None  # Last 6 conversation turns


class HistoryResponse(BaseModel):
    """Response model for assessment history."""
    user_id: str
    history: List[Dict[str, Any]]
    count: int


@router.post("", response_model=AssessmentResponse)
async def assess_only(request: AssessmentRequest):
    """
    Assess user responses only (no routing or policy execution).
    
    Returns assessment results without routing or conversation policy.
    """
    start_time = time.time()
    
    try:
        logger.info(
            f"Assessment request for user {request.user_id} (scale={request.scale}, response_count={len(request.responses)})"
        )
        
        # Run assessment
        assessment = await assess(
            scale=request.scale,
            responses=request.responses,
            persona_id=request.user_id,
            simulation_day=0
        )
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Structured logging
        severity = assessment.get("severity_level", "unknown")
        score = assessment.get("total_score", 0.0)
        flags = assessment.get("flags", {})
        high_risk = flags.get("suicidal_ideation", False)
        
        logger.info(
            "Assessment completed",
            user_id=request.user_id,
            scale=request.scale,
            score=score,
            severity=severity,
            duration_ms=duration_ms,
            high_risk=high_risk
        )
        
        return AssessmentResponse(
            user_id=request.user_id,
            assessment=assessment,
            timestamp=datetime.now(),
            duration_ms=duration_ms
        )
        
    except Exception as e:
        logger.error(f"Assessment error for user {request.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/route", response_model=RouteResponse)
async def assess_and_route(request: RouteRequest):
    """
    Assess user responses and determine routing decision.
    
    Returns assessment results + routing decision (low/medium/high).
    """
    start_time = time.time()
    
    try:
        logger.info(
            f"Assessment + routing request for user {request.user_id} (scale={request.scale}, response_count={len(request.responses)})"
        )
        
        # Run assessment
        assessment = await assess(
            scale=request.scale,
            responses=request.responses,
            persona_id=request.user_id,
            simulation_day=0
        )
        
        if not assessment.get("success"):
            raise HTTPException(status_code=400, detail="Assessment failed")
        
        # Determine route
        decision = decide_route(assessment)
        route = decision.get("route")
        rigid_score = decision.get("rigid_score", 0.0)
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Structured logging
        severity = assessment.get("severity_level", "unknown")
        score = assessment.get("total_score", 0.0)
        flags = assessment.get("flags", {})
        high_risk = route == Route.HIGH or flags.get("suicidal_ideation", False)
        
        logger.info(
            "Routing completed",
            user_id=request.user_id,
            scale=request.scale,
            score=score,
            severity=severity,
            rigid=rigid_score,
            route=route,
            duration_ms=duration_ms,
            high_risk=high_risk
        )
        
        return RouteResponse(
            user_id=request.user_id,
            assessment=assessment,
            decision=decision,
            timestamp=datetime.now(),
            duration_ms=duration_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assessment + routing error for user {request.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=ExecuteResponse)
async def assess_route_and_execute(request: ExecuteRequest):
    """
    Full pipeline: Assess → Route → Execute Policy (with session & persistence).
    
    Returns assessment results + routing decision + policy execution result.
    For high risk scenarios, always includes safety_banner and fixed safety script.
    
    Wireframe default: If no prior assessment for user → initiate conversational GAD-7 first.
    """
    start_time = time.time()
    
    try:
        # Get services
        llm_service = await get_llm_service()
        repo = get_repo()
        
        # Run complete pipeline (with session & persistence)
        engine = ConversationEngine(llm_service=llm_service, repo=repo)
        result = await engine.run_pipeline(
            ConversationRequest(
                user_id=request.user_id,
                scale=request.scale,
                responses=request.responses,
                user_message=request.user_message
            )
        )
        
        if not result.assessment.get("success"):
            raise HTTPException(status_code=400, detail=result.assessment.get("error", "Assessment failed"))
        
        # Extract route and safety information
        route = result.decision.get("route")
        rigid_score = result.decision.get("rigid_score", 0.0)
        severity = result.assessment.get("severity_level", "unknown")
        score = result.assessment.get("total_score", 0.0)
        flags = result.assessment.get("flags", {})
        high_risk = route == Route.HIGH or flags.get("suicidal_ideation", False)
        
        # Extract safety banner for high risk
        safety_banner = None
        if route == Route.HIGH:
            # Always include safety banner for high risk
            safety_banner = SAFETY_BANNER
            if result.policy_result and result.policy_result.get("safety_banner"):
                safety_banner = result.policy_result["safety_banner"]
        
        # Structured logging (per requirements)
        logger.info(
            "Pipeline completed",
            user_id=request.user_id,
            scale=request.scale,
            score=score,
            severity=severity,
            rigid=rigid_score,
            route=route,
            duration_ms=result.duration_ms,
            high_risk=high_risk
        )
        
        return ExecuteResponse(
            user_id=request.user_id,
            assessment=result.assessment,
            decision=result.decision,
            policy_result=result.policy_result,
            timestamp=datetime.now(),
            duration_ms=result.duration_ms,
            safety_banner=safety_banner,
            context_tail=result.context_tail
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        # Validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Full pipeline error for user {request.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/history", response_model=HistoryResponse)
async def get_assessment_history(
    user_id: str = Query(..., description="User identifier"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return")
):
    """
    Get assessment history for a user.
    
    Returns recent assessments sorted by timestamp (most recent first).
    """
    try:
        # Validate user_id
        if not user_id or not user_id.strip():
            raise HTTPException(status_code=400, detail="user_id cannot be empty")
        
        user_id = user_id.strip()
        
        # Get repository
        repo = get_repo()
        
        # Retrieve history
        history = await repo.history(user_id, limit=limit)
        
        logger.info(f"Retrieved {len(history)} assessment records for user {user_id}")
        
        return HistoryResponse(
            user_id=user_id,
            history=history,
            count=len(history)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving history for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

