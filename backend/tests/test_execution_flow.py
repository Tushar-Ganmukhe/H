from backend.app.agents.conversational_agent import parse_user_message
from backend.app.agents.decision_agent import DecisionAgent
from backend.app.agents.execution_agent import ExecutionAgent


decision_agent = DecisionAgent()

user_input = "Order 2 Paracetamol"

parsed = parse_user_message(user_input)
print("Parsed:", parsed)

result = decision_agent.decide(parsed)
print("Final Result:", result)