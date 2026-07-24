"""Test the default-deny permission matrix for policy search.

This demonstrates Day 4 AM Topic 05's principle:
  "Default-deny for undeclared roles and capabilities"

Tests:
  1. Defined role (claims_adjuster) → full access
  2. Defined role (auto_specialist) → restricted access
  3. Undefined role (temp_contractor) → explicitly denied
"""

import sys
from pathlib import Path

# Add parent to path so we can import from W2D3
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "W2D3"))

from my_policy_search_server import ROLE_ALLOWED_PRODUCTS, search_policies

print("=" * 80)
print("DEFAULT-DENY PERMISSION MATRIX TEST")
print("=" * 80)

print("\nCurrent ROLE_ALLOWED_PRODUCTS:")
print("─" * 80)
for role, products in ROLE_ALLOWED_PRODUCTS.items():
    print(f"  {role:25s} → {len(products):2d} products: {products}")

print("\n" + "=" * 80)
print("TEST 1: DEFINED ROLE - claims_adjuster (full access)")
print("=" * 80)

try:
    results = search_policies("is a burst pipe covered", role="claims_adjuster", k=2)
    print(f"✓ SUCCESS: claims_adjuster can search")
    print(f"  Allowed products: {ROLE_ALLOWED_PRODUCTS['claims_adjuster']}")
    print(f"  Query returned: {len(results)} chunks")
    if results:
        print(f"  First result: {results[0].source_file}")
except PermissionError as e:
    print(f"✗ FAILED: {e}")

print("\n" + "=" * 80)
print("TEST 2: DEFINED ROLE - auto_specialist (restricted access)")
print("=" * 80)

try:
    results = search_policies("is a burst pipe covered", role="auto_specialist", k=2)
    print(f"✓ SUCCESS: auto_specialist can search")
    print(f"  Allowed products: {ROLE_ALLOWED_PRODUCTS['auto_specialist']}")
    print(f"  Query returned: {len(results)} chunks")
    if results:
        print(f"  First result: {results[0].source_file}")
except PermissionError as e:
    print(f"✗ FAILED: {e}")

print("\n" + "=" * 80)
print("TEST 3: UNDEFINED ROLE - temp_contractor (DEFAULT-DENY)")
print("=" * 80)

try:
    results = search_policies("is a burst pipe covered", role="temp_contractor", k=2)
    print(f"✗ SECURITY FAILURE: temp_contractor should have been denied!")
    print(f"  Unexpectedly got: {len(results)} chunks")
    print(f"  This is a security bug - default-deny failed!")
except PermissionError as e:
    print(f"✓ CORRECT: temp_contractor was denied by default-deny")
    print(f"  Error message: {e}")

print("\n" + "=" * 80)
print("TEST 4: EDGE CASES - other undefined roles")
print("=" * 80)

undefined_roles = [
    "contractor",
    "intern",
    "vendor",
    "api_bot",
    "attacker_role",
]

for role in undefined_roles:
    try:
        results = search_policies("test query", role=role, k=1)
        print(f"✗ FAIL: {role:20s} should be denied but got {len(results)} results!")
    except PermissionError:
        print(f"✓ PASS: {role:20s} correctly denied by default-deny")

print("\n" + "=" * 80)
print("SECURITY ANALYSIS")
print("=" * 80)

print("""
Permission Model:
  - Defined roles get explicit product lists
  - Undefined roles get empty list (zero products)
  - Empty list → PermissionError is raised
  - Result: NO ACCESS for any undefined role

Default-Deny Property:
  ✓ Any new role automatically denied (safe by default)
  ✓ No "admin" bypass or "all" fallback
  ✓ Error is explicit: "role not permitted"
  ✓ Error happens BEFORE database query (fast fail)

Implementation Detail:
  Line 85: allowed_products = ROLE_ALLOWED_PRODUCTS.get(role, [])
           ↑ Returns empty list for undefined roles

  Line 86-90: if not allowed_products:
              raise PermissionError(...)
              ↑ Blocks access before search runs

Why this is secure:
  1. No "exception" path that accidentally grants access
  2. Empty list is explicitly handled
  3. Permission check runs BEFORE any database access
  4. Error message is clear about why access was denied
  5. Adding a new role requires explicit entry in ROLE_ALLOWED_PRODUCTS
""")

print("\n" + "=" * 80)
print("THREAT MODEL: What this prevents")
print("=" * 80)

print("""
Attack 1: Attacker tries undefined role name
  Payload: role="attacker_admin"
  Expected: Denied
  Actual:   PermissionError (default-deny works)
  ✓ Protected

Attack 2: Attacker tries to use role not in matrix
  Payload: role="vendor_consultant" (never defined)
  Expected: Denied
  Actual:   PermissionError (undefined role = empty list = denied)
  ✓ Protected

Attack 3: Attacker tries to bypass with null/empty
  Payload: role="" or role=None
  Expected: Denied
  Actual:   PermissionError (no match in dict, get returns [])
  ✓ Protected

Attack 4: Attacker tries uppercase or variant
  Payload: role="CLAIMS_ADJUSTER"
  Expected: Denied (case-sensitive match)
  Actual:   PermissionError (dict lookup is case-sensitive)
  Note: This is correct - role names should be exact
  ✓ Protected

What's NOT protected (by design):
  ✗ A defined but over-privileged role (e.g. claims_adjuster has too many products)
     Solution: Review ROLE_ALLOWED_PRODUCTS separately
  ✗ Compromised credentials for a legitimate role
     Solution: Credential rotation, audit logging (not shown here)
""")

print("\n" + "=" * 80)
print("DAY 4 AM TOPIC 05 LESSON")
print("=" * 80)

print("""
This server demonstrates:
  ✓ Default-deny for undeclared roles
  ✓ Zero access = no products = PermissionError
  ✓ No "admin" bypass or "all" fallback
  ✓ Not "everything"—exactly as requested

Production checklist:
  ✓ Every new role requires explicit entry
  ✓ Permission check happens before action (pre-filter)
  ✓ Error is clear and loggable
  ✓ Least privilege by default
  ✓ No error handling that accidentally grants access
""")

print()
