#!/usr/bin/env python
"""
Test script to validate the symptom matching system.
This tests the real-world pharmacy symptom-to-medicine matching.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.product_service import ProductService
from app.services.symptom_matcher import SymptomMatcher

def test_symptom_matching():
    """Test the symptom matching functionality."""
    print("=" * 80)
    print("PHARMACY SYMPTOM MATCHER - REAL WORLD TEST")
    print("=" * 80)
    
    # Initialize services
    product_service = ProductService()
    symptom_matcher = SymptomMatcher()
    
    # Get all products
    all_products = product_service.get_all_products()
    print(f"\n✅ Loaded {len(all_products)} products from inventory\n")
    
    # Show some products with stock info
    print("Sample products in inventory:")
    for p in all_products[:5]:
        print(f"  • {p['product_name']}")
        print(f"    Stock: {p['stock']}, Price: ${p['price']}\n")
    
    # Test symptom matching
    test_symptoms = [
        "i have a bad headache",
        "i fell fever",        # simple fever test
        "mein magen tut weh",  # German: stomach ache
        "ich habe husten",     # German: I have cough
        "eye pain and redness",
        "can't sleep at night"
    ]
    
    print("\n" + "=" * 80)
    print("TESTING SYMPTOM MATCHING")
    print("=" * 80)
    
    for symptom in test_symptoms:
        print(f"\n🔍 Symptom: '{symptom}'")
        print("-" * 80)
        
        result = symptom_matcher.match_symptom_to_products(
            symptom=symptom,
            products=all_products,
            threshold=0.45
        )
        
        total = result["total_matches"]
        categories = result["symptom_categories"]
        matches = result["matches"]
        
        print(f"  Categories detected: {', '.join(categories) if categories else 'general'}")
        print(f"  Total matches: {total}")
        
        if total > 0:
            print(f"\n  Results (top {len(matches)}):")
            for i, match in enumerate(matches, 1):
                print(f"\n    {i}. {match['product_name']}")
                print(f"       Relevance: {match['similarity']*100:.1f}%")
                print(f"       Price: ${match['price']}")
                print(f"       Stock: {match['stock']} units")
                print(f"       Description: {match['description'][:80]}...")
                if not match.get('suitable', True):
                    print("       ⚠️ marked not suitable for this symptom")
        else:
            print("  ❌ No suitable products found for this symptom.")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_symptom_matching()
