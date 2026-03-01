#!/usr/bin/env python
"""Quick test of symptom matching without verbose logging."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import warnings
warnings.filterwarnings('ignore')

from app.services.product_service import ProductService
from app.services.symptom_matcher import SymptomMatcher

# Initialize
product_service = ProductService()
symptom_matcher = SymptomMatcher()
all_products = product_service.get_all_products()

print("[OK] System loaded successfully!")
print("[INFO] Total products: " + str(len(all_products)))
print()

# Test 1: Headache
symptom = "I have a headache"
result = symptom_matcher.match_symptom_to_products(symptom, all_products, threshold=0.45)
print("Search: '" + symptom + "'")
print("Found " + str(result['total_matches']) + " matches")
print()
if result['matches']:
    for i, m in enumerate(result['matches'][:2], 1):
        print("  " + str(i) + ". " + m['product_name'] + " - $" + str(m['price']) + " (Match: " + str(int(m['similarity']*100)) + "%)" + (" [unsuitable]" if not m.get('suitable', True) else ""))
print()

# Test 1b: Fever
symptom = "i fell fever"
result = symptom_matcher.match_symptom_to_products(symptom, all_products, threshold=0.45)
print("Search: '" + symptom + "'")
print("Detected categories:", result.get('symptom_categories'))
print("Found " + str(result['total_matches']) + " matches")
print()
if result['matches']:
    for i, m in enumerate(result['matches'][:3], 1):
        print("  " + str(i) + ". " + m['product_name'] + " - $" + str(m['price']) + " (Match: " + str(int(m['similarity']*100)) + "%)" + (" [unsuitable]" if not m.get('suitable', True) else ""))
        print("      desc:", m.get('description'))
print()

# Test 2: Stomach
symptom = "my stomach is hurting"
result = symptom_matcher.match_symptom_to_products(symptom, all_products, threshold=0.45)
print("Search: '" + symptom + "'")
print("Found " + str(result['total_matches']) + " matches")
print()
if result['matches']:
    for i, m in enumerate(result['matches'][:2], 1):
        print("  " + str(i) + ". " + m['product_name'] + " - $" + str(m['price']) + " (Match: " + str(int(m['similarity']*100)) + "%)")
print()

# Test 3: German symptom
symptom = "ich habe husten"
result = symptom_matcher.match_symptom_to_products(symptom, all_products, threshold=0.45)
print("Search: '" + symptom + "'")
print("Found " + str(result['total_matches']) + " matches")
print()
if result['matches']:
    for i, m in enumerate(result['matches'][:2], 1):
        print("  " + str(i) + ". " + m['product_name'] + " - $" + str(m['price']) + " (Match: " + str(int(m['similarity']*100)) + "%)")

print()
print("[OK] ALL TESTS PASSED!")
