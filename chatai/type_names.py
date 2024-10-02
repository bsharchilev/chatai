from dataclasses import dataclass
from typing import TypedDict, Optional


@dataclass
class ChatMessage:
    username: str
    text: str
    unixtime: int
    reply_to_message: Optional['ChatMessage']
    
class CompletionMessage(TypedDict):
    role: str
    content: str