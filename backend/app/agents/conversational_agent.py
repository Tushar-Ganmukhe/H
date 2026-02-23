from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langfuse import observe, get_client
import os


llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0
)


SYSTEM_PROMPT = """
You are an expert Pharmacy Assistant. You MUST output ONLY valid JSON.

Schema:
{
  "intent": "order | product_info | unknown",
  "product_name": string | null,
  "quantity": integer | null,
  "missing": "product_name" | "quantity" | null,
  "friendly_response": string
}

Rules:
1. If the user wants to buy/order/purchase -> intent="order".
2. If the user asks for PRICE, AVAILABILITY, or INFO -> intent="product_info".
3. Always try to identify the product_name mentioned.
4. If they ask for price but didn't specify the medicine, set missing="product_name".
5. In 'friendly_response', talk like ChatGPT: "I'll check the price of [product] for you right now."
"""

@observe(name="parse_user_message")
def parse_user_message(user_message: str):
    """Parse user message and extract intent, product, quantity using LLM."""
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ]

    # Get Langfuse client for LLM tracing
    client = get_client()
    langchain_handler = client.get_trace_handler() if hasattr(client, 'get_trace_handler') else None
    if langchain_handler:
        response = llm.invoke(messages, config={"callbacks": [langchain_handler]})
    else:
        response = llm.invoke(messages)

    return response.content