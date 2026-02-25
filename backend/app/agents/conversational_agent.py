from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langfuse import observe, get_client
import os

# Initialize LLM
llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0
)

SYSTEM_PROMPT = """
You are an expert Pharmacy Assistant with Deep Context Awareness and Entity Tracking. 
You MUST output ONLY valid JSON.

Schema:
{
  "intent": "order | product_info | product_description | symptom_recommendation | reorder_last | dosage_instruction | unknown",
  "product_name": string | null,
  "quantity": integer | null,
  "symptom": string | null,
  "missing": "product_name" | "quantity" | null,
  "friendly_response": string
}

ENTITY RESOLUTION RULES:
1. NEW ENTITY PRIORITY: If the user mentions a NEW medicine name in their query (e.g., "Tell me about Norsan Omega-3"), you MUST discard any previous medicine from the history and make the NEW one the active context.
2. CONTINUITY: If the user asks a follow-up (e.g., "what is the dose?", "how much?") without naming a medicine, use the medicine mentioned most recently in the history.
3. If the user asks for dosage_instruction or product_description and provides no quantity, set missing="quantity" but keep the correct intent.

INTENT MAPPING:
- order: Purchase / Confirm Reorder.
- product_info: Price / Availability check.
- product_description: Medical details / What is this?
- symptom_recommendation: Diagnostic suggestions based on illness.
- reorder_last: Requesting previous order repeat.
- dosage_instruction: Usage / Timing instructions.

In 'friendly_response', acknowledge the specific medicine being discussed.
"""

@observe(name="parse_user_message")
def parse_user_message(user_message: str):
    """Parse user message with context-priority logic."""
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ]

    client = get_client()
    langchain_handler = client.get_trace_handler() if hasattr(client, 'get_trace_handler') else None
    
    if langchain_handler:
        response = llm.invoke(messages, config={"callbacks": [langchain_handler]})
    else:
        response = llm.invoke(messages)

    return response.content