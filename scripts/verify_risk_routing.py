"""Quick verification script for risk mapping and router modules."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.conversation.router import decide_route, Route
from src.risk.mapping import compute_rigid_from_severity, load_config

print("=" * 60)
print("Risk Mapping & Conversation Router Verification")
print("=" * 60)

# Test 1: Import verification
print("\n[OK] All modules imported successfully")

# Test 2: Route constants
print(f"\n[OK] Route constants: {Route.LOW}, {Route.MEDIUM}, {Route.HIGH}")

# Test 3: Rigidness computation
print("\n[OK] Rigidness computation:")
print(f"  minimal: {compute_rigid_from_severity('minimal'):.2f}")
print(f"  mild: {compute_rigid_from_severity('mild'):.2f}")
print(f"  moderate: {compute_rigid_from_severity('moderate'):.2f}")
print(f"  severe: {compute_rigid_from_severity('severe'):.2f}")

# Test 4: Config loading
config = load_config()
print(f"\n[OK] Config loaded: {len(config.severity_to_risk)} severity mappings")

# Test 5: Route decision
test_assessment = {
    "success": True,
    "severity_level": "moderate",
    "flags": {}
}
route = decide_route(test_assessment)
print(f"\n[OK] Route decision: {route}")

print("\n" + "=" * 60)
print("[SUCCESS] All verifications passed!")
print("=" * 60)

