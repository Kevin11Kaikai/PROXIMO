"""
Conversation orchestration engine for PROXIMO MVP.

This module orchestrates the complete conversation flow:
1. Assessment → 2. Routing → 3. Policy Execution

Integrated with:
- SessionManager: Multi-turn conversation context
- AssessmentRepo: Persistence and history
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.assessment.proximo_api import assess
from src.conversation.router import decide_route, Route
from src.conversation.policies import (
    ConversationPolicies,
    PolicyContext,
    SAFETY_BANNER
)
from src.conversation.session_manager import SessionManager
from src.storage.repo import AssessmentRepo
from src.services.ollama_service import OllamaService
from src.services.guardrails_service import GuardrailsService, get_guardrails_service
from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ConversationRequest:
    """Request for conversation orchestration."""
    user_id: str
    scale: str  # "phq9", "gad7", or "pss10"
    responses: List[str]
    user_message: Optional[str] = None
    conversation_history: Optional[List[str]] = None


@dataclass
class ConversationResult:
    """Result of conversation orchestration."""
    assessment: Dict[str, Any]
    decision: Dict[str, Any]
    policy_result: Optional[Dict[str, Any]] = None
    duration_ms: float = 0.0
    context_tail: Optional[List[Dict[str, Any]]] = None  # Last 6 conversation turns


class ConversationEngine:
    """Orchestrates the complete conversation flow."""
    
    def __init__(
        self,
        llm_service: Optional[OllamaService] = None,
        repo: Optional[AssessmentRepo] = None,
        guardrails_service: Optional[GuardrailsService] = None
    ):
        """
        Initialize conversation engine.
        
        Args:
            llm_service: Optional LLM service instance
            repo: Optional assessment repository for persistence
            guardrails_service: Optional Guardrails service instance
        """
        self.llm_service = llm_service or OllamaService()
        self.policies = ConversationPolicies(self.llm_service)
        self.repo = repo or AssessmentRepo()
        self.guardrails = guardrails_service or get_guardrails_service()
    
    async def run_pipeline(
        self,
        request: ConversationRequest
    ) -> ConversationResult:
        """
        Run complete conversation pipeline.
        
        Flow:
        1. Get session context
        2. Assessment → 3. Routing → 4. Policy Execution
        5. Persist results → 6. Update session
        
        Args:
            request: Conversation request with user inputs
            
        Returns:
            ConversationResult with assessment, routing decision, policy result, and context
        """
        start_time = time.time()
        
        try:
            # Get conversation context
            ctx = SessionManager.get_context(request.user_id)
            
            # Wireframe default: if no prior assessment → initiate conversational GAD-7 first
            scale = request.scale
            if not await self.repo.has_prior_assessment(request.user_id) and not request.responses:
                # First contact - default to GAD-7 intake
                scale = "gad7"
                logger.info(f"First contact for user {request.user_id}, defaulting to GAD-7 intake")
            
            # Step 1: Assessment
            logger.info(f"Starting assessment for user {request.user_id} (scale={scale})")
            assessment = await assess(
                scale=scale,
                responses=request.responses,
                persona_id=request.user_id,
                simulation_day=0
            )
            
            if not assessment.get("success"):
                logger.error(f"Assessment failed for user {request.user_id}")
                return ConversationResult(
                    assessment=assessment,
                    decision={},
                    policy_result=None,
                    duration_ms=(time.time() - start_time) * 1000,
                    context_tail=SessionManager.get_recent_turns(request.user_id, 6)
                )
            
            # Step 2: Routing
            logger.info(
                f"Routing decision for user {request.user_id} (severity={assessment.get('severity_level')}, total_score={assessment.get('total_score')})"
            )
            decision = decide_route(assessment)
            route = decision.get("route")
            rigid_score = decision.get("rigid_score", 0.0)
            
            # Step 3: Policy Execution
            # Use conversation context from SessionManager if available
            conversation_history = None
            if ctx:
                # Convert context to list of strings for policy
                conversation_history = [f"{turn['role']}: {turn['text']}" for turn in ctx[-6:]]
            
            # Initialize Guardrails if not already initialized
            if not self.guardrails.is_initialized():
                await self.guardrails.initialize()
            
            policy_result = None
            if request.user_message:
                logger.info(
                    f"Executing {route} policy for user {request.user_id} (route={route}, rigid_score={rigid_score})"
                )
                
                # For high-risk scenarios, prioritize Guardrails
                high_risk = route == Route.HIGH or assessment.get("flags", {}).get("suicidal_ideation", False)
                
                if high_risk and self.guardrails.is_initialized():
                    logger.info(f"High-risk scenario detected, using Guardrails for user {request.user_id}")
                    policy_result = await self._run_policy_with_guardrails(
                        route=route,
                        rigid_score=rigid_score,
                        context=PolicyContext(
                            user_id=request.user_id,
                            user_message=request.user_message,
                            assessment=assessment,
                            route=route,
                            rigid_score=rigid_score,
                            conversation_history=conversation_history
                        ),
                        ctx=ctx
                    )
                else:
                    policy_result = await self._run_policy(
                        route=route,
                        rigid_score=rigid_score,
                        context=PolicyContext(
                            user_id=request.user_id,
                            user_message=request.user_message,
                            assessment=assessment,
                            route=route,
                            rigid_score=rigid_score,
                            conversation_history=conversation_history
                        )
                    )
                    
                    # Apply Guardrails filtering to all responses (if enabled)
                    if self.guardrails.is_initialized() and policy_result and policy_result.get("response"):
                        guardrails_result = await self.guardrails.filter_response(
                            user_message=request.user_message,
                            proposed_response=policy_result.get("response", ""),
                            context=[{"role": turn.get("role", "user"), "content": turn.get("text", "")} for turn in (ctx or [])]
                        )
                        
                        if guardrails_result.get("filtered"):
                            logger.info(f"Guardrails filtered response for user {request.user_id}")
                            policy_result["response"] = guardrails_result["final_response"]
                            policy_result["guardrails_filtered"] = True
                            policy_result["guardrails_reason"] = guardrails_result.get("reason")
            
            # Step 4: Persist results
            try:
                await self.repo.save(request.user_id, assessment, decision, policy_result)
            except Exception as e:
                logger.error(f"Error persisting assessment for user {request.user_id}: {e}", exc_info=True)
            
            # Step 5: Update session
            if request.user_message:
                SessionManager.append_turn(request.user_id, "user", request.user_message)
            if policy_result:
                response_text = policy_result.get("response", "")
                if response_text:
                    SessionManager.append_turn(request.user_id, "bot", response_text)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Structured logging
            high_risk = route == Route.HIGH or assessment.get("flags", {}).get("suicidal_ideation", False)
            guardrails_used = policy_result and policy_result.get("guardrails_filtered", False)
            logger.info(
                "Pipeline completed",
                user_id=request.user_id,
                scale=scale,
                score=assessment.get("total_score"),
                severity=assessment.get("severity_level"),
                rigid=rigid_score,
                route=route,
                duration_ms=duration_ms,
                high_risk=high_risk,
                guardrails_used=guardrails_used
            )
            
            # Get updated context tail
            context_tail = SessionManager.get_recent_turns(request.user_id, 6)
            
            return ConversationResult(
                assessment=assessment,
                decision=decision,
                policy_result=policy_result,
                duration_ms=duration_ms,
                context_tail=context_tail
            )
            
        except Exception as e:
            logger.error(f"Error in conversation pipeline for user {request.user_id}: {e}", exc_info=True)
            duration_ms = (time.time() - start_time) * 1000
            return ConversationResult(
                assessment={"success": False, "error": str(e)},
                decision={},
                policy_result=None,
                duration_ms=duration_ms,
                context_tail=SessionManager.get_recent_turns(request.user_id, 6)
            )
    
    async def _run_policy(
        self,
        route: str,
        rigid_score: float,
        context: PolicyContext
    ) -> Dict[str, Any]:
        """Execute policy based on route."""
        try:
            if route == Route.LOW:
                return await self.policies.run_low_policy(context)
            elif route == Route.MEDIUM:
                return await self.policies.run_medium_policy(context)
            elif route == Route.HIGH:
                return await self.policies.run_high_policy(context)
            else:
                logger.warning(f"Unknown route: {route}, defaulting to medium policy")
                return await self.policies.run_medium_policy(context)
        except Exception as e:
            logger.error(f"Error executing {route} policy: {e}", exc_info=True)
            return {
                "policy": route,
                "error": str(e),
                "response": "I'm here to help. How can I assist you?",
                "safety_banner": SAFETY_BANNER if route == Route.HIGH else None
            }
    
    async def _run_policy_with_guardrails(
        self,
        route: str,
        rigid_score: float,
        context: PolicyContext,
        ctx: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Execute policy with Guardrails for high-risk scenarios.
        
        For high-risk scenarios, we use Guardrails to generate the response directly,
        ensuring all safety rules are applied.
        """
        try:
            # Build conversation context for Guardrails
            guardrails_context = None
            if ctx:
                guardrails_context = [
                    {"role": turn.get("role", "user"), "content": turn.get("text", "")}
                    for turn in ctx[-5:]
                ]
            
            # Use Guardrails to generate safe response
            safe_response = await self.guardrails.generate_safe_response(
                user_message=context.user_message,
                context=guardrails_context
            )
            
            logger.info(f"Guardrails generated safe response for {route} route")
            
            return {
                "policy": route,
                "response": safe_response,
                "text": safe_response,
                "safety_banner": SAFETY_BANNER,
                "guardrails_generated": True,
                "rigid_score": rigid_score
            }
            
        except Exception as e:
            logger.error(f"Error in Guardrails policy execution: {e}", exc_info=True)
            # Fallback to standard high policy
            logger.warning("Falling back to standard high policy due to Guardrails error")
            return await self.policies.run_high_policy(context)


# Convenience function for simple pipeline execution
async def run_pipeline(
    scale: str,
    responses: List[str],
    user_id: str,
    user_message: Optional[str] = None,
    conversation_history: Optional[List[str]] = None,
    llm_service: Optional[OllamaService] = None
) -> ConversationResult:
    """
    Run complete conversation pipeline (convenience function).
    
    Args:
        scale: Assessment scale ("phq9", "gad7", or "pss10")
        responses: Assessment responses
        user_id: User identifier
        user_message: Optional user message for policy execution
        conversation_history: Optional conversation history
        llm_service: Optional LLM service instance
        
    Returns:
        ConversationResult with assessment, routing, and policy result
    """
    engine = ConversationEngine(llm_service)
    request = ConversationRequest(
        user_id=user_id,
        scale=scale,
        responses=responses,
        user_message=user_message,
        conversation_history=conversation_history
    )
    return await engine.run_pipeline(request)

