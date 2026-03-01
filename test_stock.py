import sys, asyncio

# ensure imports work
sys.path.append(r"C:\Users\hp\OneDrive\New folder\OneDrive\Desktop\om-main\om-main")
sys.path.append(r"C:\Users\hp\OneDrive\New folder\OneDrive\Desktop\om-main\om-main\backend")

from backend.app.agents.conversational_agent import parse_user_message
from backend.app.agents.decision_agent import DecisionAgent

decision_agent = DecisionAgent()
# Use the shared product service from the execution agent
product_service = decision_agent.execution_agent.product_service

async def test_stock_management():
    print("=" * 60)
    print("STOCK MANAGEMENT TEST")
    print("=" * 60)
    
    # Get initial stock
    product = product_service.get_product_by_name("Paracetamol")
    if product:
        initial_stock = product.get("stock", 0)
        print(f"\n1. Initial Paracetamol stock: {initial_stock}")
    else:
        print("Product not found!")
        return
    
    # Test 1: Order within stock limit
    print("\n2. Attempting to order 2 Paracetamol...")
    user_input = "Order 2 Paracetamol"
    parsed = parse_user_message(user_input)
    result = await decision_agent.decide(parsed, raw_message=user_input)
    if "Confirmed" in result.get("message", ""):
        print("   RESULT: Order confirmed")
    elif "Insufficient" in result.get("message", ""):
        print("   RESULT: Insufficient stock")
    else:
        print("   RESULT: " + result.get("message", "Unknown")[:50])
    
    # Check stock after order
    product = product_service.get_product_by_name("Paracetamol")
    stock_after_order = product.get("stock", 0)
    print(f"\n3. Stock after order: {stock_after_order}")
    print(f"   Expected: {initial_stock - 2}, Actual: {stock_after_order}")
    if stock_after_order == initial_stock - 2:
        print("   [OK] Stock correctly reduced!")
    else:
        print("   [FAIL] Stock not as expected")
    
    # Test 2: Try to order more than available
    print(f"\n4. Attempting to order {stock_after_order + 5} Paracetamol (more than available)...")
    user_input2 = f"Order {stock_after_order + 5} Paracetamol"
    parsed2 = parse_user_message(user_input2)
    result2 = await decision_agent.decide(parsed2, raw_message=user_input2)
    if "Insufficient" in result2.get("message", ""):
        print("   [OK] Correctly rejected order with insufficient stock!")
    else:
        print("   [FAIL] Order should have been rejected")
        msg = result2.get("message", "Unknown")
        try:
            print("   Result: " + msg[:50])
        except:
            print("   Result: [Unicode content]")

if __name__ == "__main__":
    asyncio.run(test_stock_management())
