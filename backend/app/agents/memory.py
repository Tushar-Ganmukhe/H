import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DialogueState(BaseModel):
    transaction_state: str = "IDLE"  # IDLE, RECOMMENDING, PENDING_CONFIRMATION, AWAITING_PRESCRIPTION
    current_slots: Dict[str, Any] = Field(default_factory=lambda: {"product_name": None, "quantity": 1})
    entity_stack: List[str] = Field(default_factory=list)
    prescription_verified: bool = False # <--- NEW: Track safety status
    last_action_summary: str = ""

class Tier3Memory:
    def __init__(self):
        self.states: Dict[str, DialogueState] = {}

    def get_state(self, session_id: str) -> DialogueState:
        if session_id not in self.states:
            self.states[session_id] = DialogueState()
        return self.states[session_id]

    def update_entity_stack(self, session_id: str, entity: str):
        state = self.get_state(session_id)
        if entity and entity not in state.entity_stack:
            state.entity_stack.insert(0, entity)
            state.entity_stack = state.entity_stack[:5]

    def clear_slots(self, session_id: str):
        state = self.get_state(session_id)
        state.current_slots = {"product_name": None, "quantity": 1}
        state.transaction_state = "IDLE"
        state.prescription_verified = False # <--- NEW: Reset safety

# Global Instance
memory_store = Tier3Memory()