from dotenv import load_dotenv
load_dotenv()

import os
from typing import Optional, Literal
from pydantic import BaseModel, Field

# Updated Imports to resolve ModuleNotFoundError
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langfuse import observe, get_client

# Initialize LLM with Groq
llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0
)

# --- 1. DEFINE STRICT SCHEMA (Pydantic) ---
class UserIntentSchema(BaseModel):
    intent: Literal[
        "order", 
        "product_info", 
        "product_description", 
        "symptom_recommendation", 
        "reorder_last", 
        "dosage_instruction", 
        "unknown"
    ] = Field(description="The user's intention")
    
    product_name: Optional[str] = Field(description="Name of the medicine/product", default=None)
    quantity: Optional[int] = Field(description="Quantity requested", default=None)
    symptom: Optional[str] = Field(description="Symptom described by user", default=None)
    missing: Optional[Literal["product_name", "quantity"]] = Field(description="What info is missing", default=None)
    friendly_response: Optional[str] = Field(description="A natural, friendly response to the user", default="Got it. Let me check that for you.")

# Initialize Parser
parser = PydanticOutputParser(pydantic_object=UserIntentSchema)

# FIXED PROMPT: Maintained exact logic for Intent Routing and Entity Resolution
SYSTEM_PROMPT = f"""
You are an expert Pharmacy Assistant with Deep Context Awareness.
You MUST extract structured data from the user's input.

ENTITY RESOLUTION RULES:
1. NEW ENTITY PRIORITY: If the user mentions a NEW medicine name, discard previous context.
2. CONTINUITY: If the user asks a follow-up (e.g., "what is the dose?") without naming a medicine, use the medicine from history.
3. If the user asks for instructions/description but gives no quantity, set missing="quantity" only if intent is 'order'.

INTENT MAPPING:
- order: Purchase / Confirm Reorder.
- product_info: Price / Availability check.
- product_description: Medical details / What is this?
- symptom_recommendation: Diagnostic suggestions.
- reorder_last: Requesting previous order repeat.
- dosage_instruction: Usage / Timing instructions.

CRITICAL INSTRUCTION: You MUST output ONLY valid JSON. Do NOT include any introductory or conversational text. Just the raw JSON format.

{parser.get_format_instructions()}
"""

@observe(name="parse_user_message")
def parse_user_message(user_message: str):
    """Parse user message using Pydantic Validation."""
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ]

    client = get_client()
    langchain_handler = client.get_trace_handler() if hasattr(client, 'get_trace_handler') else None
    
    try:
        # Invoke LLM with Langfuse tracking
        if langchain_handler:
            response = llm.invoke(messages, config={"callbacks": [langchain_handler]})
        else:
            response = llm.invoke(messages)

        # Parse the output content into the Pydantic model
        parsed_obj = parser.parse(response.content)
        return parsed_obj.model_dump() # Return as dict for DecisionAgent

    except Exception as e:
        print(f"⚠️ Parsing Error: {e}. Retrying with fallback...")
        # Maintain stability with a safe fallback response
        return {
            "intent": "unknown",
            "product_name": None,
            "quantity": None,
            "friendly_response": "I'm having a little trouble understanding. Could you please rephrase that?"
        }