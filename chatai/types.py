from dataclasses import dataclass
from typing import TypedDict


@dataclass
class ChatMessage:
    username: str
    text: str
    unixtime: int
    
class CompletionMessage(TypedDict):
    role: str
    content: str