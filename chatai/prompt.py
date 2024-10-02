from typing import Dict, List
from type_names import ChatMessage, CompletionMessage


USERNAME_TO_DISPLAY_NAME = {
    "sanchar13": "Александр Соболь",
    "yolo322": "Андрей Гайбун",
    "ushanov_dmitriy": "Дмитрий Ушанов",
    "vgrigorash": "Виталий Григораш",
    "ZEMUSHKA": "Андрей Зимовнов",
    "svyatslv": "Святослав Юшин",
    "korolpiratov": "Евгения Пономаренко",
    "bsharchilev": "Борис Шарчилев",
    "boggeyman_ai_bot": "Бугимен",
}

FOCUS_PROMPT = "Always respond to the last user message. Only use prior user messages if explicitly needed for the topic at hand."

class Prompt:
    def __init__(self, prompt_file_path: str):
        self.prompt_file_path = prompt_file_path
        
    def generate(self, messages: List[ChatMessage]) -> List[CompletionMessage]:
        with open(self.prompt_file_path, 'r') as f:
            system_prompt = f.read()
        result = [{"role": "system", "content": system_prompt}]
        for message in messages:
            role = "assistant" if message.username == "boggeyman_ai_bot" else "user"
            content = self.encode(message)
            result.append({"role": role, "content": content})
        result.append({"role": "system", "content": FOCUS_PROMPT})
        return result
        
    def encode(self, message: ChatMessage) -> str:
        user = USERNAME_TO_DISPLAY_NAME[message.username]
        user_part = f"(от: {user}) "
        
        reply_part = ""
        if message.reply_to_message is not None:
            reply_part = f"(ответ на: {self.encode(message.reply_to_message)}) "
            
        return user_part + reply_part + message.text
        