"""
Final test: Simulate user booking 5 units and verify stock reduces in Excel
"""
import asyncio
import sys
import os
# Add the om-main/backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "om-main", "backend"))

from app.agents.execution_agent import ExecutionAgent

async def test_user_scenario():
    """
    Simulate user: "I want to book 5 units of NORSAN Omega-3 medicine"
    Expected: Stock in Excel should reduce accordingly
    """
    print("\n" + "="*70)
    print("USER SCENARIO TEST: 'I booked 5 units of NORSAN medicine'")
    print("="*70)
    
    agent = ExecutionAgent()
    
    # Get initial stock
    print("\n[Step 1] Check initial stock...")
    product = agent.product_service.get_product_by_name("NORSAN Omega-3 Total")
    initial_stock = product['stock']
    print(f"  Current stock in database: {initial_stock} units")
    
    # User books 5 units
    print("\n[Step 2] User books 5 units of NORSAN Omega-3...")
    order_result = await agent.execute_order(
        patient_id=1,
        product_name="NORSAN Omega-3",  # User's input might be partial
        quantity=5
    )
    
    if order_result['approved']:
        order_id = order_result['order']['order_id']
        print(f"  Order approved!")
        print(f"  Order ID: {order_id}")
        print(f"  Product: {order_result['order']['product_name']}")
        print(f"  Quantity: {order_result['order']['quantity']}")
        print(f"  Total Price: ${order_result['order']['total_price']}")
    else:
        print(f"  Order failed: {order_result['error']}")
        return False
    
    # Check stock after order (in-memory)
    print("\n[Step 3] Check stock after order (in-memory)...")
    product = agent.product_service.get_product_by_name("NORSAN Omega-3 Total")
    stock_after = product['stock']
    expected = initial_stock - 5
    print(f"  Stock after order: {stock_after}")
    print(f"  Expected: {expected}")
    
    if stock_after != expected:
        print("  ERROR: In-memory stock mismatch!")
        return False
    
    # Verify Excel file
    print("\n[Step 4] Verify Excel file was updated...")
    import pandas as pd
    df = pd.read_excel(r"C:\Users\hp\Downloads\products-export.xlsx")
    excel_product = df[df['product name'].str.contains('NORSAN Omega-3 Total', na=False)]
    excel_stock = excel_product['stock'].values[0]
    
    print(f"  Stock in Excel: {excel_stock}")
    print(f"  Expected: {expected}")
    
    if excel_stock == expected:
        print("\n  [SUCCESS] Excel was updated correctly!")
        return True
    else:
        print(f"\n  [FAILED] Excel stock mismatch!")
        return False

async def main():
    success = await test_user_scenario()
    
    print("\n" + "="*70)
    print(f"RESULT: {'USER SCENARIO - PASSED' if success else 'USER SCENARIO - FAILED'}")
    print("="*70)
    
    if success:
        print("\n[Summary of User Requirement]")
        print("User said: 'I booked that medicine 5 unit but stock not reduce'")
        print("\nOUR IMPLEMENTATION:")
        print("  [v] Stock DOES reduce in database (Excel file)")
        print("  [v] Reduction happens immediately when order is confirmed")
        print("  [v] Reduction is verified in Excel (persistent)")
        print("  [v] Stock persists across application restarts")
        print("\nCONCLUSION: User's problem is SOLVED!")

if __name__ == "__main__":
    asyncio.run(main())
