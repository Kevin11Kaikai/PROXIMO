"""
Test script for risk mapping and conversation routing integration.

This script demonstrates the complete flow:
1. Assess user responses using proximo_api.assess()
2. Decide conversation route based on assessment results
3. Display routing decision and rigidness score
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.assessment.proximo_api import assess
from src.conversation.router import decide_route, Route


async def test_risk_routing():
    """Test risk routing with different scenarios."""
    
    print("=" * 80)
    print("Risk Mapping & Conversation Routing Test")
    print("=" * 80)
    
    # Test Case 1: Low Risk (Minimal severity)
    print("\n[Test 1] Low Risk Scenario (Minimal severity)")
    print("-" * 80)
    assessment1 = await assess("phq9", ["0", "0", "1", "0", "1", "0", "1", "0", "0"])
    if assessment1["success"]:
        print(f"  Assessment: {assessment1['severity_level']} (Score: {assessment1['total_score']})")
        route1 = decide_route(assessment1)
        print(f"  Route: {route1['route']}")
        print(f"  Rigidness Score: {route1['rigid_score']:.2f}")
        print(f"  Reason: {route1['reason']}")
    
    # Test Case 2: Medium Risk (Moderate severity)
    print("\n[Test 2] Medium Risk Scenario (Moderate severity)")
    print("-" * 80)
    assessment2 = await assess("phq9", ["1", "1", "2", "2", "1", "2", "1", "2", "0"])
    if assessment2["success"]:
        print(f"  Assessment: {assessment2['severity_level']} (Score: {assessment2['total_score']})")
        route2 = decide_route(assessment2)
        print(f"  Route: {route2['route']}")
        print(f"  Rigidness Score: {route2['rigid_score']:.2f}")
        print(f"  Reason: {route2['reason']}")
    
    # Test Case 3: High Risk (Hard lock - Suicidal ideation)
    print("\n[Test 3] High Risk Scenario (Hard lock - Suicidal ideation)")
    print("-" * 80)
    assessment3 = await assess("phq9", ["1", "1", "1", "1", "1", "1", "1", "1", "2"])
    if assessment3["success"]:
        print(f"  Assessment: {assessment3['severity_level']} (Score: {assessment3['total_score']})")
        print(f"  Suicidal Ideation: {assessment3['flags']['suicidal_ideation']}")
        print(f"  Suicidal Risk: {assessment3['suicidal_risk']}")
        route3 = decide_route(assessment3)
        print(f"  Route: {route3['route']}")
        print(f"  Rigidness Score: {route3['rigid_score']:.2f}")
        print(f"  Reason: {route3['reason']}")
        print("  [WARNING] HIGH RISK (Hard lock): Immediate attention required!")
    
    # Test Case 4: High Risk (Hard lock - Severe severity)
    print("\n[Test 4] High Risk Scenario (Hard lock - Severe severity)")
    print("-" * 80)
    assessment4 = await assess("phq9", ["3", "3", "3", "3", "3", "3", "3", "3", "0"])
    if assessment4["success"]:
        print(f"  Assessment: {assessment4['severity_level']} (Score: {assessment4['total_score']})")
        route4 = decide_route(assessment4)
        print(f"  Route: {route4['route']}")
        print(f"  Rigidness Score: {route4['rigid_score']:.2f}")
        print(f"  Reason: {route4['reason']}")
        print("  [WARNING] HIGH RISK (Hard lock): Immediate attention required!")
    
    # Test Case 5: GAD-7 Assessment
    print("\n[Test 5] GAD-7 Assessment")
    print("-" * 80)
    assessment5 = await assess("gad7", ["1", "1", "2", "1", "2", "1", "1"])
    if assessment5["success"]:
        print(f"  Assessment: {assessment5['severity_level']} (Score: {assessment5['total_score']})")
        route5 = decide_route(assessment5)
        print(f"  Route: {route5['route']}")
        print(f"  Rigidness Score: {route5['rigid_score']:.2f}")
        print(f"  Reason: {route5['reason']}")
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_risk_routing())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

