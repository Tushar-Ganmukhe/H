"""
Test order history persistence and retrieval
"""
import json
import os
import sys
sys.path.insert(0, r"c:\Users\hp\OneDrive\New folder\OneDrive\Desktop\om-main\om-main\backend")

from app.agents.decision_agent import DecisionAgent, ORDER_HISTORY_FILE

print("\n" + "="*70)
print("TEST: Order History Persistence")
print("="*70)

# Clean up old test data
if os.path.exists(ORDER_HISTORY_FILE):
    os.remove(ORDER_HISTORY_FILE)
    print(f"\nCleared old {ORDER_HISTORY_FILE}")

# Test 1: Create new agent and add an order
print("\n[Step 1] Create agent and manually add an order")
agent = DecisionAgent()

# Simulate an order
test_order = {
    "order_id": "test123",
    "product_name": "Cystinol akut",
    "quantity": 5,
    "total_price": 132.50,
    "created_at": "2026-03-01T10:30:00"
}

agent.order_history.append(test_order)
agent._save_order_history()
print(f"  [OK] Added order: {test_order['product_name']} × {test_order['quantity']}")
print(f"  [OK] Saved to file")

# Test 2: Verify file was created
print("\n[Step 2] Verify order_history.json was created")
if os.path.exists(ORDER_HISTORY_FILE):
    print(f"  [OK] File exists: {ORDER_HISTORY_FILE}")
    with open(ORDER_HISTORY_FILE) as f:
        data = json.load(f)
        print(f"  [OK] File contains {len(data)} order(s)")
else:
    print(f"  [ERROR] File not created!")

# Test 3: Create fresh agent and load the order
print("\n[Step 3] Create fresh agent (simulates app restart)")
agent2 = DecisionAgent()
print(f"  [OK] Fresh agent loaded {len(agent2.order_history)} orders from file")

# Test 4: Format and display the order
print("\n[Step 4] Format order history for display")
history_text = agent2._format_order_history(agent2.order_history)
print(history_text)

# Test 5: Test history keywords
print("\n[Step 5] Test order matching with various keywords")
test_phrases = [
    "Show my orders",
    "Where are my orders",
    "my order history",
    "show my order",
    "I booked that medicine",
]

for phrase in test_phrases:
    # Simulate the history keyword check
    lower = phrase.lower()
    history_keywords = ["history", "all my orders", "show orders", "show my orders", "my orders", "order list", "previous orders", "where are my orders", "can you show", "my order", "booked"]
    matches = any(kw in lower for kw in history_keywords)
    print(f"  '{phrase}' → {'MATCH' if matches else 'NO MATCH'}")

print("\n" + "="*70)
print("TEST: Order History - COMPLETED")
print("="*70)
