from dataclasses import dataclass
from typing import Optional
from chatbot.intent_type import IntentType

@dataclass
class ChatResponse:
    message: str
    intent: IntentType
    action_taken: bool = False
    order_id: Optional[str] = None
    error: Optional[str] = None