"""
Conversation policies for different risk levels.

This module defines behavioral policies for low, medium, and high risk conversations,
including temperature settings and safety protocols.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from src.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

# Safety banner for high-risk scenarios
SAFETY_BANNER = "If you are in immediate danger, call or text 988 (US). If outside the US, contact local emergency services."

# Policy temperature settings (base values, will be adjusted by rigidity)
TEMPERATURE_LOW = 0.9      # Empathetic & flexible
TEMPERATURE_MEDIUM = 0.6   # Semi-structured
TEMPERATURE_HIGH = 0.2     # Safety-oriented & structured (updated from 0.0 to 0.2 per wireframe)

# Fixed safety script for high-risk scenarios
FIXED_SAFETY_SCRIPT = """I'm here to support you, and I want to make sure you're safe. 

Right now, the most important thing is your safety. If you're having thoughts of hurting yourself or ending your life, please reach out for immediate help:

• Call or text 988 (US National Suicide & Crisis Lifeline) - available 24/7
• If outside the US, contact your local emergency services
• Reach out to a trusted adult, friend, or healthcare provider

You don't have to go through this alone. There are people who want to help and support you.

Would you like help finding resources in your area, or would you prefer to speak with someone right now?"""


@dataclass
class PolicyContext:
    """Context for policy execution."""
    user_id: str
    user_message: str
    assessment: Dict[str, Any]
    route: str
    rigid_score: float
    conversation_history: Optional[list] = None


def apply_rigidity(rigid: float, base_temp: float, base_max_tokens: int) -> Tuple[float, int]:
    """
    Apply rigidity adjustments to LLM parameters.
    
    Args:
        rigid: Rigidity score (0.0 - 1.0)
        base_temp: Base temperature
        base_max_tokens: Base max tokens
        
    Returns:
        Tuple of (adjusted_temperature, adjusted_max_tokens)
    """
    # Temperature decreases with rigidity: max(0.1, base - 0.8*rigid)
    adjusted_temp = max(0.1, base_temp - 0.8 * rigid)
    
    # Max tokens decreases with rigidity: base - 300*rigid
    adjusted_max_tokens = int(base_max_tokens - 300 * rigid)
    adjusted_max_tokens = max(100, adjusted_max_tokens)  # Minimum 100 tokens
    
    return adjusted_temp, adjusted_max_tokens


class ConversationPolicies:
    """Conversation policies for different risk levels."""
    
    def __init__(self, llm_service: Optional[OllamaService] = None):
        """Initialize conversation policies."""
        self.llm_service = llm_service or OllamaService()
    
    async def run_low_policy(self, ctx: PolicyContext) -> Dict[str, Any]:
        """
        Low risk policy: conversational GAD-7 intake → coping skills suggestions → empathetic closure.
        
        Wireframe behavior:
        - Conversational GAD-7 intake (if first contact)
        - Coping skills suggestions
        - Empathetic closure
        - High flexibility, natural conversation
        """
        try:
            logger.info(
                f"Running low policy for user {ctx.user_id} (route={ctx.route}, rigid_score={ctx.rigid_score})"
            )
            
            # Apply rigidity adjustments
            temp, max_tokens = apply_rigidity(ctx.rigid_score, TEMPERATURE_LOW, 512)
            
            # Generate empathetic response
            response = await self._generate_response(
                ctx=ctx,
                temperature=temp,
                system_prompt=self._get_low_system_prompt(),
                max_tokens=max_tokens
            )
            
            return {
                "policy": "low",
                "temperature": temp,
                "response": response,
                "safety_banner": None,
                "structured": False,
                "text": response  # Alias for consistency
            }
        except Exception as e:
            logger.error(f"Error in low policy: {e}")
            return {
                "policy": "low",
                "error": str(e),
                "response": "I'm here to listen. How can I help you today?",
                "text": "I'm here to listen. How can I help you today?",
                "safety_banner": None
            }
    
    async def run_medium_policy(self, ctx: PolicyContext) -> Dict[str, Any]:
        """
        Medium risk policy: acknowledge anxiety → suggest peer group → handle resistance → confirm join.
        
        Wireframe behavior:
        - Acknowledge anxiety/concerns
        - Suggest peer group (with safety note: "*peer group has a moderator for safety*")
        - Handle resistance (2-3 reasons & counters)
        - Confirm join
        - Flexible with guardrails
        """
        try:
            logger.info(
                f"Running medium policy for user {ctx.user_id} (route={ctx.route}, rigid_score={ctx.rigid_score})"
            )
            
            # Apply rigidity adjustments
            temp, max_tokens = apply_rigidity(ctx.rigid_score, TEMPERATURE_MEDIUM, 512)
            
            # Generate semi-structured response
            response = await self._generate_response(
                ctx=ctx,
                temperature=temp,
                system_prompt=self._get_medium_system_prompt(),
                max_tokens=max_tokens
            )
            
            return {
                "policy": "medium",
                "temperature": temp,
                "response": response,
                "safety_banner": None,
                "structured": True,
                "text": response
            }
        except Exception as e:
            logger.error(f"Error in medium policy: {e}")
            return {
                "policy": "medium",
                "error": str(e),
                "response": "I understand this is important. Let's work through this together.",
                "text": "I understand this is important. Let's work through this together.",
                "safety_banner": None
            }
    
    async def run_high_policy(self, ctx: PolicyContext) -> Dict[str, Any]:
        """
        High risk policy: fixed safety script, no free chat.
        
        Wireframe behavior:
        - Detect high risk or suicidal language
        - Show 988 banner
        - Provide fixed safety script (NO free-form chat)
        - Encourage calling crisis hotline
        - Do not continue free-form conversation in this response
        """
        try:
            severity = ctx.assessment.get("severity_level", "unknown")
            hard_lock = ctx.assessment.get("flags", {}).get("suicidal_ideation", False)
            logger.warning(
                f"Running high policy for user {ctx.user_id} (route={ctx.route}, rigid_score={ctx.rigid_score}, severity={severity}, hard_lock={hard_lock})"
            )
            
            # HIGH RISK: Use fixed safety script, NO free-form LLM response
            # This ensures consistent, safe messaging for crisis scenarios
            response = FIXED_SAFETY_SCRIPT
            
            return {
                "policy": "high",
                "temperature": 0.0,  # Not used (fixed script), but logged for consistency
                "response": response,
                "text": response,  # Alias
                "safety_banner": SAFETY_BANNER,
                "structured": True,
                "safety_priority": True,
                "fixed_script": True  # Flag indicating this is a fixed script, not LLM-generated
            }
        except Exception as e:
            logger.error(f"Error in high policy: {e}")
            # Even on error, return fixed safety script
            return {
                "policy": "high",
                "error": str(e),
                "response": FIXED_SAFETY_SCRIPT,
                "text": FIXED_SAFETY_SCRIPT,
                "safety_banner": SAFETY_BANNER,
                "fixed_script": True
            }
    
    async def _generate_response(
        self,
        ctx: PolicyContext,
        temperature: float,
        system_prompt: str,
        max_tokens: int = 150
    ) -> str:
        """Generate response using LLM service with specified temperature."""
        try:
            # Build conversation prompt
            prompt = self._build_prompt(ctx, system_prompt)
            
            # Use Ollama service directly with temperature control
            # We'll call the Ollama API directly since we need temperature control
            # and don't need persona-specific formatting
            if not self.llm_service.is_loaded:
                await self.llm_service.load_model()
            
            import httpx
            
            # Make direct API call to Ollama with temperature
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.post(
                        f"{self.llm_service.base_url}/api/generate",
                        json={
                            "model": self.llm_service.model_name,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "num_predict": max_tokens,
                                "temperature": temperature,
                                "top_p": 0.9,
                                "top_k": 40,
                                "num_ctx": 2048,
                                "repeat_penalty": 1.1,
                            }
                        },
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        generated_text = result.get("response", "").strip()
                        return generated_text
                    else:
                        logger.warning(f"Ollama API returned error status: {response.status_code}, using fallback")
                        return self._get_fallback_response(ctx.route)
                        
                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    logger.warning(f"Ollama service connection failed: {type(e).__name__}, using fallback response")
                    return self._get_fallback_response(ctx.route)
                except httpx.RequestError as e:
                    logger.warning(f"Ollama API request error: {type(e).__name__}, using fallback response")
                    return self._get_fallback_response(ctx.route)
                    
        except Exception as e:
            logger.warning(f"Error generating LLM response: {type(e).__name__}: {e}, using fallback")
            # Fallback response - ensure pipeline continues even if LLM fails
            return self._get_fallback_response(ctx.route)
    
    def _build_prompt(self, ctx: PolicyContext, system_prompt: str) -> str:
        """Build conversation prompt from context."""
        prompt_parts = [system_prompt]
        
        # Add conversation history if available
        if ctx.conversation_history:
            prompt_parts.append("\n\nPrevious conversation:")
            for msg in ctx.conversation_history[-5:]:  # Last 5 messages
                prompt_parts.append(f"- {msg}")
        
        # Add current user message
        prompt_parts.append(f"\n\nUser: {ctx.user_message}")
        prompt_parts.append("\n\nAssistant:")
        
        return "\n".join(prompt_parts)
    
    def _get_low_system_prompt(self) -> str:
        """
        Get system prompt for low risk policy.
        
        Wireframe: conversational GAD-7 intake → coping skills suggestions → empathetic closure
        """
        return """You are a supportive and empathetic mental health assistant for teens.

Your role is to:
1. Conduct conversational GAD-7 intake (if first contact) - ask about anxiety naturally
2. Suggest coping skills and self-care strategies
3. Provide empathetic closure and encouragement

Guidelines:
- Be warm, understanding, and conversational
- Use natural language, not clinical jargon
- Offer practical, age-appropriate coping strategies
- Keep responses personal and supportive
- Focus on building rapport and trust

Keep responses natural, flexible, and empathetic."""
    
    def _get_medium_system_prompt(self) -> str:
        """
        Get system prompt for medium risk policy.
        
        Wireframe: acknowledge anxiety → suggest peer group → handle resistance → confirm join
        """
        return """You are a professional mental health assistant for teens.

Your role is to:
1. Acknowledge the teen's anxiety/concerns with empathy
2. Suggest joining a peer support group (always mention: "*the peer group has a moderator for safety*")
3. Handle resistance by:
   - Acknowledging 2-3 common concerns (e.g., "I don't know anyone", "I'm embarrassed", "What if people judge me?")
   - Providing gentle counters to each concern
   - Reassuring about safety and confidentiality
4. Confirm join and provide next steps

Guidelines:
- Be supportive but structured
- Address resistance with understanding, not pressure
- Always emphasize peer group safety (moderator present)
- Provide clear, actionable next steps
- Maintain professional boundaries

Keep responses balanced, professional, and supportive."""
    
    def _get_high_system_prompt(self, ctx: PolicyContext) -> str:
        """
        Get system prompt for high risk policy.
        
        Note: This is not used in run_high_policy() as we use FIXED_SAFETY_SCRIPT instead.
        Kept for consistency and potential future use.
        """
        severity = ctx.assessment.get("severity_level", "unknown")
        flags = ctx.assessment.get("flags", {})
        has_suicidal_ideation = flags.get("suicidal_ideation", False)
        
        prompt = f"""CRITICAL SAFETY PROTOCOL: High risk detected.

Severity: {severity}
Suicidal ideation: {has_suicidal_ideation}

IMPORTANT: Use fixed safety script. Do not generate free-form responses.
Always provide crisis resources (988) and encourage immediate help."""
        
        return prompt
    
    def _get_fallback_response(self, route: str) -> str:
        """Get fallback response when LLM generation fails."""
        fallbacks = {
            "low": "I'm here to listen. How can I help you today?",
            "medium": "I understand this is important. Let's work through this together.",
            "high": "I'm here to help. Please know that support is available. If you're in immediate danger, please call or text 988."
        }
        return fallbacks.get(route, "How can I help you today?")
    
    def apply_rigidity(self, base_response: str, rigid_score: float) -> str:
        """
        Apply rigidity adjustment to response based on rigid_score.
        
        Higher rigidity = more structured, less flexible response.
        """
        # For now, this is a placeholder
        # In future, could modify response structure based on rigid_score
        # For example, add more structure, remove ambiguity, etc.
        if rigid_score > 0.75:
            # High rigidity: ensure response is clear and structured
            if not base_response.endswith(('.', '!', '?')):
                base_response += "."
        return base_response


# Convenience functions for direct policy execution
async def run_low_policy(ctx: PolicyContext, llm_service: Optional[OllamaService] = None) -> Dict[str, Any]:
    """Run low risk policy."""
    policies = ConversationPolicies(llm_service)
    return await policies.run_low_policy(ctx)


async def run_medium_policy(ctx: PolicyContext, llm_service: Optional[OllamaService] = None) -> Dict[str, Any]:
    """Run medium risk policy."""
    policies = ConversationPolicies(llm_service)
    return await policies.run_medium_policy(ctx)


async def run_high_policy(ctx: PolicyContext, llm_service: Optional[OllamaService] = None) -> Dict[str, Any]:
    """Run high risk policy."""
    policies = ConversationPolicies(llm_service)
    return await policies.run_high_policy(ctx)

