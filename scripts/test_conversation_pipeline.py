"""
Test script for complete conversation pipeline (Assessment → Route → Policy).

This script demonstrates the end-to-end flow:
1. Assessment using proximo_api.assess()
2. Routing decision based on risk level
3. Policy execution with appropriate conversation behavior

Note: If Ollama service is not available, the pipeline will automatically use
fallback responses. This allows testing the assessment and routing logic even
without a running LLM service.
"""

import asyncio
import sys
from pathlib import Path
import httpx

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.assessment.proximo_api import assess
from src.conversation.engine import ConversationEngine, ConversationRequest
from src.conversation.router import Route
from src.services.ollama_service import OllamaService
from src.core.config import settings


async def check_ollama_connection() -> bool:
    """Check if Ollama service is available."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                if settings.MODEL_NAME in model_names:
                    return True
                else:
                    print(f"\n[WARN] Model '{settings.MODEL_NAME}' not found in Ollama.")
                    print(f"       Available models: {model_names}")
                    return False
            else:
                return False
    except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as e:
        return False
    except Exception as e:
        print(f"\n[WARN] Unexpected error checking Ollama: {e}")
        return False


async def test_complete_pipeline():
    """Test complete conversation pipeline."""
    
    print("=" * 80)
    print("PROXIMO Conversation Pipeline Test")
    print("=" * 80)
    
    # Check Ollama connection first
    print("\n[INFO] Checking Ollama service connection...")
    ollama_available = await check_ollama_connection()
    
    if ollama_available:
        print(f"[OK] Ollama service is available at {settings.OLLAMA_URL}")
        print(f"[OK] Model '{settings.MODEL_NAME}' is ready")
    else:
        print(f"[WARN] Ollama service is NOT available at {settings.OLLAMA_URL}")
        print(f"[INFO] The pipeline will use fallback responses (no LLM calls)")
        print(f"[INFO] Assessment and routing will still work correctly")
        print(f"[INFO] To enable LLM responses, ensure Ollama is running:")
        print(f"       1. Start Ollama service: ollama serve")
        print(f"       2. Pull the model: ollama pull {settings.MODEL_NAME}")
    
    # Initialize LLM service
    llm_service = OllamaService()
    if ollama_available:
        try:
            await llm_service.load_model()
            if llm_service.is_loaded:
                print(f"[OK] LLM service initialized successfully")
            else:
                print(f"[WARN] LLM service failed to load, will use fallbacks")
        except Exception as e:
            print(f"[WARN] Error loading LLM service: {e}")
            print(f"[INFO] Will use fallback responses instead")
    else:
        print(f"[INFO] Skipping LLM service initialization (Ollama not available)")
    
    engine = ConversationEngine(llm_service)
    
    # Test Case 1: Low Risk
    print("\n" + "=" * 80)
    print("[Test 1] Low Risk Scenario")
    print("=" * 80)
    
    request1 = ConversationRequest(
        user_id="user_001",
        scale="phq9",
        responses=["0", "0", "1", "0", "1", "0", "1", "0", "0"],  # Minimal severity
        user_message="I'm feeling okay today, just a bit tired."
    )
    
    result1 = await engine.run_pipeline(request1)
    
    print(f"\nAssessment:")
    print(f"  Severity: {result1.assessment.get('severity_level')}")
    print(f"  Total Score: {result1.assessment.get('total_score')}")
    
    print(f"\nRouting Decision:")
    print(f"  Route: {result1.decision.get('route')}")
    print(f"  Rigid Score: {result1.decision.get('rigid_score'):.2f}")
    print(f"  Reason: {result1.decision.get('reason')}")
    
    if result1.policy_result:
        print(f"\nPolicy Result:")
        print(f"  Policy: {result1.policy_result.get('policy')}")
        print(f"  Temperature: {result1.policy_result.get('temperature')}")
        response_text = result1.policy_result.get('response', 'N/A')
        if len(response_text) > 100:
            print(f"  Response: {response_text[:100]}...")
        else:
            print(f"  Response: {response_text}")
        print(f"  Safety Banner: {result1.policy_result.get('safety_banner', 'None')}")
        if result1.policy_result.get('error'):
            print(f"  [NOTE] Used fallback response (LLM unavailable)")
    
    print(f"\nDuration: {result1.duration_ms:.2f} ms")
    
    # Test Case 2: Medium Risk
    print("\n" + "=" * 80)
    print("[Test 2] Medium Risk Scenario")
    print("=" * 80)
    
    request2 = ConversationRequest(
        user_id="user_002",
        scale="phq9",
        responses=["1", "1", "2", "2", "1", "2", "1", "2", "0"],  # Moderate severity
        user_message="I've been feeling anxious and having trouble sleeping."
    )
    
    result2 = await engine.run_pipeline(request2)
    
    print(f"\nAssessment:")
    print(f"  Severity: {result2.assessment.get('severity_level')}")
    print(f"  Total Score: {result2.assessment.get('total_score')}")
    
    print(f"\nRouting Decision:")
    print(f"  Route: {result2.decision.get('route')}")
    print(f"  Rigid Score: {result2.decision.get('rigid_score'):.2f}")
    print(f"  Reason: {result2.decision.get('reason')}")
    
    if result2.policy_result:
        print(f"\nPolicy Result:")
        print(f"  Policy: {result2.policy_result.get('policy')}")
        print(f"  Temperature: {result2.policy_result.get('temperature')}")
        response_text = result2.policy_result.get('response', 'N/A')
        if len(response_text) > 100:
            print(f"  Response: {response_text[:100]}...")
        else:
            print(f"  Response: {response_text}")
        print(f"  Structured: {result2.policy_result.get('structured')}")
        if result2.policy_result.get('error'):
            print(f"  [NOTE] Used fallback response (LLM unavailable)")
    
    print(f"\nDuration: {result2.duration_ms:.2f} ms")
    
    # Test Case 3: High Risk (Hard Lock - Suicidal Ideation)
    print("\n" + "=" * 80)
    print("[Test 3] High Risk Scenario (Hard Lock - Suicidal Ideation)")
    print("=" * 80)
    
    request3 = ConversationRequest(
        user_id="user_003",
        scale="phq9",
        responses=["1", "1", "1", "1", "1", "1", "1", "1", "2"],  # Item 9 = 2 (suicidal ideation)
        user_message="I don't see the point anymore."
    )
    
    result3 = await engine.run_pipeline(request3)
    
    print(f"\nAssessment:")
    print(f"  Severity: {result3.assessment.get('severity_level')}")
    print(f"  Total Score: {result3.assessment.get('total_score')}")
    print(f"  Suicidal Ideation: {result3.assessment.get('flags', {}).get('suicidal_ideation')}")
    print(f"  Suicidal Risk: {result3.assessment.get('suicidal_risk')}")
    
    print(f"\nRouting Decision:")
    print(f"  Route: {result3.decision.get('route')}")
    print(f"  Rigid Score: {result3.decision.get('rigid_score'):.2f}")
    print(f"  Reason: {result3.decision.get('reason')}")
    
    if result3.policy_result:
        print(f"\nPolicy Result:")
        print(f"  Policy: {result3.policy_result.get('policy')}")
        print(f"  Temperature: {result3.policy_result.get('temperature')}")
        response_text = result3.policy_result.get('response', 'N/A')
        if len(response_text) > 100:
            print(f"  Response: {response_text[:100]}...")
        else:
            print(f"  Response: {response_text}")
        print(f"  Safety Banner: {result3.policy_result.get('safety_banner', 'None')}")
        print(f"  Safety Priority: {result3.policy_result.get('safety_priority')}")
        if result3.policy_result.get('error'):
            print(f"  [NOTE] Used fallback response (LLM unavailable)")
    
    print(f"\nDuration: {result3.duration_ms:.2f} ms")
    
    # Test Case 4: High Risk (Severe Severity)
    print("\n" + "=" * 80)
    print("[Test 4] High Risk Scenario (Severe Severity)")
    print("=" * 80)
    
    request4 = ConversationRequest(
        user_id="user_004",
        scale="phq9",
        responses=["3", "3", "3", "3", "3", "3", "3", "3", "0"],  # Severe severity
        user_message="I can't function anymore."
    )
    
    result4 = await engine.run_pipeline(request4)
    
    print(f"\nAssessment:")
    print(f"  Severity: {result4.assessment.get('severity_level')}")
    print(f"  Total Score: {result4.assessment.get('total_score')}")
    
    print(f"\nRouting Decision:")
    print(f"  Route: {result4.decision.get('route')}")
    print(f"  Rigid Score: {result4.decision.get('rigid_score'):.2f}")
    print(f"  Reason: {result4.decision.get('reason')}")
    
    if result4.policy_result:
        print(f"\nPolicy Result:")
        print(f"  Policy: {result4.policy_result.get('policy')}")
        print(f"  Temperature: {result4.policy_result.get('temperature')}")
        response_text = result4.policy_result.get('response', 'N/A')
        if len(response_text) > 100:
            print(f"  Response: {response_text[:100]}...")
        else:
            print(f"  Response: {response_text}")
        print(f"  Safety Banner: {result4.policy_result.get('safety_banner', 'None')}")
        if result4.policy_result.get('error'):
            print(f"  [NOTE] Used fallback response (LLM unavailable)")
    
    print(f"\nDuration: {result4.duration_ms:.2f} ms")
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)
    print("\nSummary:")
    print(f"  Test 1: {result1.decision.get('route')} route (low risk)")
    print(f"  Test 2: {result2.decision.get('route')} route (medium risk)")
    print(f"  Test 3: {result3.decision.get('route')} route (high risk - hard lock)")
    print(f"  Test 4: {result4.decision.get('route')} route (high risk - severe)")
    
    if not ollama_available:
        print("\n" + "=" * 80)
        print("NOTE: Ollama service was not available during this test.")
        print("All responses used fallback text. To enable LLM-generated responses:")
        print("  1. Ensure Ollama is running: ollama serve")
        print(f"  2. Pull the model: ollama pull {settings.MODEL_NAME}")
        print(f"  3. Verify connection: curl {settings.OLLAMA_URL}/api/tags")
        print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_complete_pipeline())
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error occurred: {e}")
        print("\n[INFO] This might be due to:")
        print("  1. Ollama service not running (normal, will use fallbacks)")
        print("  2. Network connectivity issues")
        print("  3. Configuration problems")
        print("\n[INFO] Full error details:")
        import traceback
        traceback.print_exc()
        print("\n[INFO] Note: The pipeline has fallback mechanisms.")
        print("       Even if Ollama is unavailable, assessment and routing should work.")
        sys.exit(1)

