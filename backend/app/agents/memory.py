import importlib

_ConversationBufferMemory = None
for candidate in (
    "langchain.memory",
    "langchain.memory.buffer",
    "langchain.memory.buffer_memory",
):
    try:
        mod = importlib.import_module(candidate)
        if hasattr(mod, "ConversationBufferMemory"):
            _ConversationBufferMemory = getattr(mod, "ConversationBufferMemory")
            break
    except Exception:
        continue

if _ConversationBufferMemory is None:
    class _ConversationBufferMemory:
        def __init__(self, return_messages: bool = False):
            self.return_messages = return_messages
            self._history = []
            self.buffer_limit = 10 # Keep last 10 messages (5 turns)

        def load_memory_variables(self, _input: dict):
            # Return history limited to the last 10 entries for deep context
            recent_history = self._history[-self.buffer_limit:]
            if self.return_messages:
                return {"history": list(recent_history)}
            return {"history": "\n".join(recent_history)}

        def save_context(self, inputs: dict, outputs: dict):
            # Format inputs/outputs for history string
            inp = inputs.get("input") or inputs.get("message") or str(inputs)
            # Try to extract the friendly message part if output is a JSON string
            out_val = str(outputs)
            
            entry = f"User: {inp}\nAssistant: {out_val}"
            self._history.append(entry)
            
            # Maintenance: Trim memory if it exceeds limit to save LLM tokens
            if len(self._history) > 20:
                self._history = self._history[-20:]

memory_store = {}

def get_memory(session_id: str):
    """Retrieves or initializes a 5-exchange deep context buffer for the user."""
    if session_id not in memory_store:
        # return_messages=False ensures history comes back as a single formatted string
        memory_store[session_id] = _ConversationBufferMemory(return_messages=False)
    return memory_store[session_id]