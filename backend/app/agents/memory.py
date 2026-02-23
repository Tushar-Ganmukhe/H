
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
    # Provide a minimal fallback implementation compatible with how
    # this project uses ConversationBufferMemory (load_memory_variables
    # and save_context). This avoids crashing when langchain isn't
    # installed or has different packaging.
    class _ConversationBufferMemory:
        def __init__(self, return_messages: bool = False):
            self.return_messages = return_messages
            self._history = []

        def load_memory_variables(self, _input: dict):
            # Return a dict with a 'history' key (string) to match usage
            # in `app.api.chat` which does `.get('history', '')`.
            if self.return_messages:
                return {"history": list(self._history)}
            return {"history": "\n".join(self._history)}

        def save_context(self, inputs: dict, outputs: dict):
            # Append a simple textual representation to history.
            inp = inputs.get("input") or inputs.get("message") or str(inputs)
            out = outputs.get("output") if isinstance(outputs, dict) else str(outputs)
            entry = f"User: {inp}\nAgent: {out}"
            self._history.append(entry)

memory_store = {}

def get_memory(session_id: str):
    if session_id not in memory_store:
        memory_store[session_id] = _ConversationBufferMemory(return_messages=True)
    return memory_store[session_id]