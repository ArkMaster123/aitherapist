#!/usr/bin/env python3
"""
Compare evaluation results between original and safety-trained models.
"""
import json
import os

def load_json(filepath):
    """Load JSON file if it exists"""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None

print("="*70)
print("📊 Evaluation Comparison: Original vs Safety-Trained")
print("="*70)

# Load both evaluation results
original = load_json("evaluation_results.json")
safety = load_json("evaluation_results_safety.json")

if not safety:
    print("❌ Safety evaluation results not found!")
    exit(1)

print("\n🛡️  SAFETY-TRAINED MODEL (Latest)")
print("="*70)
if "metrics" in safety:
    print("\n📈 Metrics:")
    for key, value in safety["metrics"].items():
        if value is not None:
            print(f"   {key}: {value}")

if "safety_tests" in safety:
    print("\n🛡️  Safety Tests:")
    for test_name, passed in safety["safety_tests"].items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")

if original:
    print("\n" + "="*70)
    print("📊 ORIGINAL MODEL (Before Safety Training)")
    print("="*70)
    if "metrics" in original:
        print("\n📈 Metrics:")
        for key, value in original["metrics"].items():
            if value is not None:
                print(f"   {key}: {value}")
    
    if "safety_tests" in original:
        print("\n🛡️  Safety Tests:")
        for test_name, passed in original["safety_tests"].items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {test_name}: {status}")
    
    print("\n" + "="*70)
    print("📊 COMPARISON")
    print("="*70)
    
    # Compare metrics
    if "metrics" in original and "metrics" in safety:
        print("\n📈 Metrics Changes:")
        for key in safety["metrics"]:
            if key in original["metrics"]:
                orig_val = original["metrics"][key]
                safety_val = safety["metrics"][key]
                if orig_val is not None and safety_val is not None:
                    if isinstance(orig_val, (int, float)) and isinstance(safety_val, (int, float)):
                        change = safety_val - orig_val
                        change_pct = (change / orig_val * 100) if orig_val != 0 else 0
                        arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
                        print(f"   {key}: {orig_val:.2f} → {safety_val:.2f} ({arrow} {change:+.2f}, {change_pct:+.1f}%)")
                    else:
                        print(f"   {key}: {orig_val} → {safety_val}")
    
    # Compare safety tests
    if "safety_tests" in original and "safety_tests" in safety:
        print("\n🛡️  Safety Test Changes:")
        for test_name in safety["safety_tests"]:
            if test_name in original["safety_tests"]:
                orig_passed = original["safety_tests"][test_name]
                safety_passed = safety["safety_tests"][test_name]
                if orig_passed != safety_passed:
                    status = "✅ IMPROVED" if safety_passed else "❌ REGRESSED"
                    print(f"   {test_name}: {status} (was {'PASS' if orig_passed else 'FAIL'}, now {'PASS' if safety_passed else 'FAIL'})")
                else:
                    status = "✅ PASS" if safety_passed else "❌ FAIL"
                    print(f"   {test_name}: {status} (unchanged)")
    
    # Count improvements
    if "safety_tests" in original and "safety_tests" in safety:
        orig_passed = sum(1 for v in original["safety_tests"].values() if v)
        safety_passed = sum(1 for v in safety["safety_tests"].values() if v)
        print(f"\n📊 Safety Score: {orig_passed}/4 → {safety_passed}/4 ({'+' if safety_passed > orig_passed else ''}{safety_passed - orig_passed})")
else:
    print("\n⚠️  No original evaluation results found for comparison.")
    print("   If you have evaluation_results.json, place it in the current directory.")

print("\n" + "="*70)

