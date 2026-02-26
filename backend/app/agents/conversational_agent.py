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


# --- FIX: ADDED STRICT KEY-CHECKING TO PREVENT TYPOS ---
SYSTEM_PROMPT = f"""
You are an expert Pharmacy Assistant. Your task is to extract structured data from user input and respond ONLY in valid JSON format.

**CRITICAL RULES:**
1.  **Strict JSON Schema:** You MUST use the exact field names provided in the schema. Double-check your spelling. The valid field names are: `intent`, `product_name`, `quantity`, `symptom`, `missing`, `friendly_response`. Do not misspell them (e.g., 'prroduct_name' is invalid).
2.  **Context Awareness:** If the user asks a follow-up without naming a medicine (e.g., "what is the dose?"), use the medicine from the conversation history. If they name a NEW medicine, prioritize the new one.

**INTENT MAPPING:**
- `order`: User wants to purchase or reorder.
- `product_info`: User asks for price or availability.
- `product_description`: User asks "what is this?" or for medical details.
- `symptom_recommendation`: User describes a symptom and asks for a recommendation.
- `reorder_last`: User asks to repeat their last order.
- `dosage_instruction`: User asks how or when to take a medicine.

You MUST only output raw JSON. Do not include any other text.

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