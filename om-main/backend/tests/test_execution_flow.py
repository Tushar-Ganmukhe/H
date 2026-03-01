import sys, asyncio

# ensure imports work when executing this script directly
sys.path.append(r"C:\Users\hp\OneDrive\New folder\OneDrive\Desktop\om-main\om-main")
sys.path.append(r"C:\Users\hp\OneDrive\New folder\OneDrive\Desktop\om-main\om-main\backend")

from backend.app.agents.conversational_agent import parse_user_message
from backend.app.agents.decision_agent import DecisionAgent


decision_agent = DecisionAgent()

async def run_flow():
    # ensure there is a registered user with a known id
    from app.services.user_service import UserService
    reg = UserService.register_user("FlowUser", "12345", None, "pw", None, "user")
    session = reg.get("user", {}).get("id")
    # place first order
    user_input = "Order 2 Paracetamol"
    parsed = parse_user_message(user_input)
    # simulate logged-in user by passing the returned session id
    result = await decision_agent.decide(parsed, raw_message=user_input, session_id=session)
    print("Order 1:", result)

    # place second order
    user_input2 = "Order 1 Aspirin"
    parsed2 = parse_user_message(user_input2)
    result2 = await decision_agent.decide(parsed2, raw_message=user_input2, session_id=session)
    print("\nOrder 2:", result2)

    # ask about previous order
    follow_up1 = "what medicine did I book previously?"
    parsed3 = parse_user_message(follow_up1)
    result3 = await decision_agent.decide(parsed3, raw_message=follow_up1, session_id=session)
    print("\nPrevious order:", result3)

    # ask for full history
    follow_up2 = "show my order history"
    parsed4 = parse_user_message(follow_up2)
    result4 = await decision_agent.decide(parsed4, raw_message=follow_up2, session_id=session)
    print("\nFull history:", result4)

    # ask for recent orders
    follow_up3 = "what did I order last month?"
    parsed5 = parse_user_message(follow_up3)
    result5 = await decision_agent.decide(parsed5, raw_message=follow_up3, session_id=session)
    print("\nRecent orders:", result5)

    # ------------------------------------------
    # simulate the 'only quantity' bug
    # ------------------------------------------
    # ask to order something but omit the quantity first
    user_input6 = "Order Cystinol akut"
    parsed6 = parse_user_message(user_input6)
    result6 = await decision_agent.decide(parsed6, raw_message=user_input6, session_id=session)
    print("\nOrder prompt (no quantity):", result6)
    # now reply only with a number; previously this would default to the wrong product
    user_input7 = "5"
    parsed7 = parse_user_message(user_input7)
    result7 = await decision_agent.decide(parsed7, raw_message=user_input7, session_id=session)
    print("\nFinal order after quantity reply:", result7)
    assert "Cystinol" in result7.get("message", ""), "Order should reference Cystinol when quantity given alone"

if __name__ == "__main__":
    asyncio.run(run_flow())
