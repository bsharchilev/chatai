from dataclasses import dataclass
from typing import TypedDict, Optional, Literal, List


@dataclass
class ChatMessage:
    username: str
    text: str
    unixtime: int
    image_b64_encoded: Optional[str] = None
    reply_to_message: Optional['ChatMessage'] = None

class ImageUrl(TypedDict):
    url: str

class TypedContent(TypedDict):
    type: Literal['text', 'image_url']
    text: Optional[str]
    image_url: Optional[ImageUrl]
    
class CompletionMessage(TypedDict):
    role: str
    content: str | List[TypedContent]