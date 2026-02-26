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
    image: str | None = None  # Accepts Base64 string for Vision AI

@router.post("")
@observe(name="chat_endpoint")
async def chat(request: ChatRequest):
    # Sync Trace with Session ID (Mobile Number)
    client = get_client()
    client.update_current_trace(
        session_id=request.session_id,
        user_id=f"user_{request.session_id}" 
    )

    # 1. Load context from session-based memory
    memory = get_memory(request.session_id)
    # Fetch last 10 turns for deep context
    history_vars = memory.load_memory_variables({})
    history = history_vars.get("history", "")

    # 2. Build Enriched turn-labeled prompt
    enriched_message = f"""
--- CONVERSATION HISTORY ---
{history}

--- CURRENT USER QUERY ---
USER: {request.message}
"""

    # 3. Process through Context-Aware NLP Agent
    # We pass the text message to the NLP agent to determine Intent
    parsed_response = parse_user_message(enriched_message)

    # 4. Save User input and LLM's interpretation into turn history
    # Note: We don't save the massive base64 image string to memory to save tokens
    memory.save_context(
        {"input": request.message}, 
        {"output": parsed_response}
    )

    # 5. Route to Decision Agent for Action
    # PASS THE IMAGE DATA HERE
    result = await decision_agent.decide(
        parsed_response, 
        session_id=request.session_id, 
        image_data=request.image
    ) 

    return result