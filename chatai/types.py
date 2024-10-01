from dataclasses import dataclass
from typing import TypedDict


@dataclass
class ChatMessage:
    username: str
    text: str
    
class CompletionMessage(TypedDict):
    role: str
    content: str