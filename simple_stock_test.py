"""
Direct test of stock management without ExecutionAgent
"""
import sys
sys.path.insert(0, r"c:\Users\hp\OneDrive\New folder\OneDrive\Desktop\om-main\om-main\backend")

from app.services.product_service import ProductService
import pandas as pd

print("\n" + "="*70)
print("STOCK MANAGEMENT TEST: User Booking Scenario")
print("="*70)

service = ProductService()

# Initial stock
print("\n[1] Initial State")
product = service.get_product_by_name("NORSAN Omega-3 Total")
initial_stock = product['stock']
print(f"  Stock in database: {initial_stock} units")

# Check availability for 5 units
print("\n[2] User wants to book 5 units")
available, msg = service.check_stock_availability("NORSAN Omega-3 Total", 5)
print(f"  Can we provide 5 units? {available}")
print(f"  Message: {msg}")

if available:
    # Reduce stock
    print("\n[3] Reducing stock by 5 units...")
    success = service.reduce_stock("NORSAN Omega-3 Total", 5)
    print(f"  Reduction successful: {success}")
    
    # Check in-memory
    product = service.get_product_by_name("NORSAN Omega-3 Total")
    after_stock = product['stock']
    expected = initial_stock - 5
    print(f"  Stock after order (in-memory): {after_stock}")
    print(f"  Expected: {expected}")
    
    # Check Excel
    print("\n[4] Verifying Excel file...")
    df = pd.read_excel(r"C:\Users\hp\Downloads\products-export.xlsx")
    excel_product = df[df['product name'].str.contains('NORSAN Omega-3 Total', na=False)]
    excel_stock = excel_product['stock'].values[0]
    print(f"  Stock in Excel: {excel_stock}")
    print(f"  Expected: {expected}")
    
    if excel_stock == expected:
        print("\n[SUCCESS] Stock correctly reduced in Excel database!")
    else:
        print("\n[FAILED] Excel stock mismatch!")
else:
    print("  ERROR: Not enough stock available")

print("\n" + "="*70)
print("SUMMARY: When user books medicine, stock reduces in database")
print("="*70)
