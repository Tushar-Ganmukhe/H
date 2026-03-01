"""
Test full end-to-end order flow with stock persistence to Excel
"""
import asyncio
import sys
sys.path.insert(0, r"c:\Users\hp\OneDrive\New folder\OneDrive\Desktop\om-main\om-main")

from backend.app.services.product_service import ProductService

async def test_order_flow():
    """Test complete order flow with stock reduction"""
    print("\n" + "="*70)
    print("TEST: End-to-End Order Flow with Stock Persistence")
    print("="*70)
    
    service = ProductService()
    
    # Test 1: Check initial stock
    print("\n[1] Checking initial product stock...")
    product = service.get_product_by_name("NORSAN Omega-3 Total")
    if product:
        initial_stock = product['stock']
        print(f"  ✓ Found: {product['product_name']}")
        print(f"    Initial stock: {initial_stock}")
    else:
        print("  ✗ Product not found")
        return False
    
    # Test 2: Check stock availability
    order_qty = 5
    print(f"\n[2] Checking stock availability for {order_qty} units...")
    available, msg = service.check_stock_availability("NORSAN Omega-3 Total", order_qty)
    print(f"  Available: {available}")
    print(f"  Message: {msg}")
    
    if not available:
        print("  ✗ Stock check failed!")
        return False
    
    # Test 3: Simulate order placement (reduce stock)
    print(f"\n[3] Simulating order placement for {order_qty} units...")
    success = service.reduce_stock("NORSAN Omega-3 Total", order_qty)
    
    if success:
        print(f"  ✓ Stock reduced successfully")
        
        # Check in-memory stock
        product = service.get_product_by_name("NORSAN Omega-3 Total")
        current_stock = product['stock']
        expected_stock = initial_stock - order_qty
        print(f"    In-memory stock: {current_stock}")
        print(f"    Expected stock: {expected_stock}")
        
        if current_stock == expected_stock:
            print(f"  ✓ In-memory reduction verified!")
        else:
            print(f"  ⚠ Stock mismatch in memory")
    else:
        print(f"  ⚠ Stock reduction reported as failed (check if file is locked)")
    
    # Test 4: Verify Excel file
    print(f"\n[4] Verifying Excel file was updated...")
    import pandas as pd
    df = pd.read_excel(r"C:\Users\hp\Downloads\products-export.xlsx")
    excel_product = df[df['product name'].str.contains('NORSAN Omega-3 Total', na=False)]
    
    if not excel_product.empty:
        excel_stock = excel_product['stock'].values[0]
        expected_stock = initial_stock - order_qty
        print(f"  Excel stock: {excel_stock}")
        print(f"  Expected stock: {expected_stock}")
        
        if excel_stock == expected_stock:
            print(f"  ✓ Excel file verified updated correctly!")
            return True
        else:
            print(f"  ✗ Excel stock doesn't match expected value")
            return False
    else:
        print(f"  ✗ Product not found in Excel file")
        return False

async def main():
    result = await test_order_flow()
    print("\n" + "="*70)
    print(f"TEST RESULT: {'✓ SUCCESS' if result else '✗ FAILED'}")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
