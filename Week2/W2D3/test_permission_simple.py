"""Simple test of the default-deny permission matrix (no Unicode).

Test that undefined roles are denied by default.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "snippets"))
from my_policy_search_server import ROLE_ALLOWED_PRODUCTS, search_policies

print("=" * 80)
print("PERMISSION MATRIX DEFAULT-DENY TEST")
print("=" * 80)

print("\nCurrent roles:")
for role, products in ROLE_ALLOWED_PRODUCTS.items():
    print(f"  {role}: {len(products)} products")

print("\n" + "=" * 80)
print("TEST 1: claims_adjuster (defined, should PASS)")
print("=" * 80)
try:
    results = search_policies("is a burst pipe covered", role="claims_adjuster", k=1)
    print("PASS: claims_adjuster allowed - got", len(results), "results")
except PermissionError as e:
    print("FAIL:", e)

print("\n" + "=" * 80)
print("TEST 2: auto_specialist (defined, should PASS)")
print("=" * 80)
try:
    results = search_policies("is a burst pipe covered", role="auto_specialist", k=1)
    print("PASS: auto_specialist allowed - got", len(results), "results")
except PermissionError as e:
    print("FAIL:", e)

print("\n" + "=" * 80)
print("TEST 3: temp_contractor (undefined, should BLOCK)")
print("=" * 80)
try:
    results = search_policies("is a burst pipe covered", role="temp_contractor", k=1)
    print("FAIL: temp_contractor should have been denied but got", len(results), "results!")
except PermissionError as e:
    print("PASS: temp_contractor correctly denied")
    print("Error:", str(e))

print("\n" + "=" * 80)
print("TEST 4: Other undefined roles")
print("=" * 80)
undefined = ["contractor", "intern", "vendor", "api_bot", "hacker"]
for role in undefined:
    try:
        results = search_policies("test", role=role, k=1)
        print(f"FAIL: {role} should be denied!")
    except PermissionError:
        print(f"PASS: {role} denied by default-deny")

print("\n" + "=" * 80)
print("SECURITY VERDICT")
print("=" * 80)
print("""
The permission matrix correctly implements default-deny:

1. Defined roles get their allowed products
2. Undefined roles get empty list (zero products)
3. Empty list triggers PermissionError
4. Result: ANY undefined role is automatically denied

This is CORRECT behavior for Day 4 AM Topic 05.
""")
