"""
Test persistence: Order with one instance, verify with fresh instance
"""
import asyncio
import sys
sys.path.insert(0, r"c:\Users\hp\OneDrive\New folder\OneDrive\Desktop\om-main\om-main")

from backend.app.services.product_service import ProductService

async def test_persistence():
    """Test that stock persists across application restarts"""
    print("\n" + "="*70)
    print("TEST: Stock Persistence Across Application Instances")
    print("="*70)
    
    # Instance 1: Place an order
    print("\n[Phase 1] FIRST INSTANCE: Place order and check stock")
    print("-" * 70)
    service1 = ProductService()
    
    product = service1.get_product_by_name("NORSAN Omega-3 Total")
    stock_before = product['stock']
    print(f"Stock before order: {stock_before}")
    
    # Place order for 3 units
    order_qty = 3
    print(f"Placing order for {order_qty} units...")
    service1.reduce_stock("NORSAN Omega-3 Total", order_qty)
    
    product = service1.get_product_by_name("NORSAN Omega-3 Total")
    stock_after_order = product['stock']
    print(f"Stock after order (in memory): {stock_after_order}")
    
    # Instance 2: Fresh service (simulates app restart)
    print("\n[Phase 2] FRESH INSTANCE: Restart application and verify stock")
    print("-" * 70)
    service2 = ProductService()  # New instance, reloads from Excel
    
    product = service2.get_product_by_name("NORSAN Omega-3 Total")
    stock_after_restart = product['stock']
    print(f"Stock after app restart: {stock_after_restart}")
    
    # Verification
    print("\n[Phase 3] VERIFICATION")
    print("-" * 70)
    expected = stock_before - order_qty
    print(f"Expected stock: {expected}")
    print(f"Stock after restart: {stock_after_restart}")
    
    if stock_after_restart == expected:
        print("\n[SUCCESS] Stock persisted correctly across application instances!")
        return True
    else:
        print(f"\n[FAILED] Stock mismatch!")
        print(f"  Expected: {expected}, Got: {stock_after_restart}")
        return False

async def main():
    result = await test_persistence()
    print("\n" + "="*70)
    print(f"PERSISTENCE TEST: {'[PASSED]' if result else '[FAILED]'}")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())
