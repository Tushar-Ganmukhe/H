from fastapi import APIRouter
from pydantic import BaseModel
from langfuse import observe, get_client

from app.agents.conversational_agent import parse_user_message
from app.agents.decision_agent import DecisionAgent
from app.agents.memory import get_memory

router = APIRouter(prefix="/chat", tags=["Agent Chat"])
decision_agent = DecisionAgent()

class ChatRequest(BaseModel):
    message: str
    session_id: str

@router.post("")
@observe(name="chat_endpoint")
async def chat(request: ChatRequest):
    # Tell Langfuse to group these logs under the React frontend's session_id
    client = get_client()
    client.update_current_trace(
        session_id=request.session_id,
        user_id="react_frontend_user" 
    )

    memory = get_memory(request.session_id)
    history = memory.load_memory_variables({}).get("history", "")

    enriched_message = f"History: {history}\nUser: {request.message}"

    parsed = parse_user_message(enriched_message)

    memory.save_context({"input": request.message}, {"output": parsed})

    result = await decision_agent.decide(parsed) 

    return result