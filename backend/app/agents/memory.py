import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

# Configuration
BUFFER_SIZE = 5  # Keep last 5 messages raw
MAX_HISTORY = 20 # Safety limit

class _SummaryConversationMemory:
    def __init__(self):
        self._history = [] # Raw list of "User: ... \n Assistant: ..."
        self._summary = "" # Long-term summarized context
        self._metadata = {} # State management (e.g., pending_verification)
        
        # LLM for background summarization
        self.llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.1-8b-instant",
            temperature=0
        )

    def load_memory_variables(self, _input: dict):
        """Returns the context: Summary + Recent Buffer"""
        # Get recent messages (Buffer)
        recent_messages = self._history[-BUFFER_SIZE:]
        buffer_str = "\n".join(recent_messages)
        
        # Combine Summary + Buffer
        if self._summary:
            context = f"--- LONG-TERM CONTEXT (SUMMARY) ---\n{self._summary}\n\n--- RECENT CONVERSATION ---\n{buffer_str}"
        else:
            context = f"--- CONVERSATION HISTORY ---\n{buffer_str}"
            
        return {"history": context}

    def save_context(self, inputs: dict, outputs: dict):
        """Saves new turn and triggers summarization if buffer gets full"""
        inp = inputs.get("input") or inputs.get("message") or str(inputs)
        out_val = str(outputs)
        
        # Format entry
        entry = f"User: {inp}\nAssistant: {out_val}"
        self._history.append(entry)

        # Maintenance: Summarize if history grows too long
        if len(self._history) > (BUFFER_SIZE + 2):
            self._summarize_oldest()

    def _summarize_oldest(self):
        """Compresses older messages into the summary string"""
        # Take messages older than the buffer
        to_summarize = self._history[:-BUFFER_SIZE]
        # Keep the buffer in history
        self._history = self._history[-BUFFER_SIZE:]
        
        text_to_compress = "\n".join(to_summarize)
        
        prompt = f"""
        You are a memory manager. 
        Current Summary: {self._summary}
        
        New Lines to Add:
        {text_to_compress}
        
        Task: Update the summary to include relevant medical info (symptoms, medicines, allergies) 
        and user preferences. Keep it concise.
        """
        
        try:
            response = self.llm.invoke([
                SystemMessage(content="Update the conversation summary."),
                HumanMessage(content=prompt)
            ])
            self._summary = response.content
        except Exception as e:
            print(f"⚠️ Memory Summarization Failed: {e}")

    # --- STATE MANAGEMENT (Fix for Prescription Amnesia) ---
    def set_state(self, key: str, value: any):
        self._metadata[key] = value
    
    def get_state(self, key: str):
        return self._metadata.get(key)

    def clear_state(self, key: str):
        if key in self._metadata:
            del self._metadata[key]

# Global Store
memory_store = {}

def get_memory(session_id: str):
    """Retrieves or initializes the Summary Memory for the user."""
    if session_id not in memory_store:
        memory_store[session_id] = _SummaryConversationMemory()
    return memory_store[session_id]