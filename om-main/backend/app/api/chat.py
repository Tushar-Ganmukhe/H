from fastapi import APIRouter
from pydantic import BaseModel
from langfuse import observe, get_client

from app.agents.conversational_agent import parse_user_message
from app.agents.decision_agent import DecisionAgent
from app.agents.memory import get_memory, save_memory

router = APIRouter(prefix="/chat", tags=["Agent Chat"])
decision_agent = DecisionAgent()

class ChatRequest(BaseModel):
    message: str
    session_id: str

@router.post("")
@observe(name="chat_endpoint")
async def chat(request: ChatRequest):
    client = get_client()
    client.update_current_trace(
        session_id=request.session_id,
        user_id="react_frontend_user"
    )

    memory = get_memory(request.session_id)
    history = memory.load_memory_variables({}).get("history", "")

    # Send History + New message to the parser
    enriched_message = f"History:\n{history}\n\nCurrent User Message: {request.message}"

    parsed = parse_user_message(enriched_message)

    # forward session_id into decision logic so executions know who is ordering
    result = await decision_agent.decide(parsed, raw_message=request.message, session_id=request.session_id)

    # Save the actual readable bot message to memory, not the JSON
    memory.save_context(
        {"input": request.message}, 
        {"output": result.get("message", "")}
    )
    # Persist conversation to disk for session continuity across restarts
    save_memory(request.session_id)

    return result
