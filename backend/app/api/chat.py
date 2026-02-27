from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.agents.conversational_agent import parse_user_message
from app.agents.decision_agent import DecisionAgent
from app.agents.memory import memory_store

router = APIRouter(prefix="/chat", tags=["Tier 3 Agentic Chat"])
decision_agent = DecisionAgent()

class ChatRequest(BaseModel):
    message: str
    session_id: str
    image: Optional[str] = None # Base64 Image from React
    user_lang: Optional[str] = "en"

@router.post("")
async def chat_endpoint(request: ChatRequest):
    # 1. Get current state
    current_state = memory_store.get_state(request.session_id)
    state_json = current_state.json()

    # 2. Update Slots
    nlp_res = parse_user_message(request.message, state_json)

    # 3. Decision with Vision Analysis
    final_res = await decision_agent.decide(
        nlp_res, 
        request.session_id, 
        user_lang=request.user_lang,
        image_data=request.image # <--- PASS IMAGE DATA
    )

    return final_res