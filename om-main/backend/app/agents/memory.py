
import importlib
import os
import json

# where session-specific conversation history will be stored
MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "session_memory")
if not os.path.exists(MEMORY_DIR):
    os.makedirs(MEMORY_DIR, exist_ok=True)

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

# fallthrough section: redefine get_memory with persistence and add save_memory

def _memory_file(session_id: str) -> str:
    return os.path.join(MEMORY_DIR, f"{session_id}.json")


def get_memory(session_id: str):
    """Return memory object for session, loading persisted history if available.

    This definition shadows the previous simple version; the latter is
    overwritten when this code executes, since it appears later in the file.
    """
    if session_id not in memory_store:
        mem = _ConversationBufferMemory(return_messages=True)
        path = _memory_file(session_id)
        if os.path.exists(path):
            try:
                data = json.load(open(path, "r"))
                for entry in data.get("history", []):
                    mem._history.append(entry)
            except Exception:
                pass
        memory_store[session_id] = mem
    return memory_store[session_id]


def save_memory(session_id: str):
    """Persist conversation for a session to disk."""
    mem = memory_store.get(session_id)
    if not mem:
        return
    path = _memory_file(session_id)
    try:
        with open(path, "w") as f:
            json.dump({"history": mem._history}, f)
    except Exception:
        pass
