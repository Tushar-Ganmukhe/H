import sys, os, asyncio

# ensure backend root is in path
sys.path.append(os.getcwd())

from app.agents.decision_agent import DecisionAgent
from app.services.user_service import UserService

print("starting debug")
agent = DecisionAgent()
reg = UserService.register_user("Debugger", "555", None, "pw", None, "user")
print("registered", reg)
session = reg.get("user", {}).get("id")
print("session id", session, type(session))
parsed1 = {"intent":"order","product_name":"Cystinol akut","quantity":None,"missing":"quantity","symptom":None,"friendly_response":""}
res1 = asyncio.run(agent.decide(parsed1, raw_message="Order Cystinol akut", session_id=session))
print("first response", res1)
print("pending after first", agent.pending_orders)
parsed2 = {"intent":"order","product_name":None,"quantity":5,"missing":None,"symptom":None,"friendly_response":""}
res2 = asyncio.run(agent.decide(parsed2, raw_message="5", session_id=session))
print("second response", res2)
print("pending after second", agent.pending_orders)
