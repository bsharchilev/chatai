from typing import Dict, List
from types import ChatMessage, CompletionMessage


USERNAME_TO_DISPLAY_NAME = {
    "@sanchar13": "Александр Соболь",
    "@yolo322": "Андрей Гайбун",
    "@ushanov_dmitriy": "Дмитрий Ушанов",
    "@vgrigorash": "Виталий Григораш",
    "@ZEMUSHKA": "Андрей Зимовнов",
    "@svyatslv": "Святослав Юшин",
    "@korolpiratov": "Евгения Пономаренко",
    "@bsharchilev": "Борис Шарчилев",
    "@boggeyman_ai_bot": "Бугимен",
}

class Prompt:
    def __init__(self, prompt_file_path: str):
        self.prompt_file_path = prompt_file_path
        
    def generate(self, messages: List[ChatMessage]) -> List[CompletionMessage]:
        with open(self.prompt_file_path, 'r') as f:
            system_prompt = f.read()
        result = [{"role": "system", "content": system_prompt}]
        for message in messages:
            user = USERNAME_TO_DISPLAY_NAME[message.username]
            content = f"(от: {user}) {message.text}"
            result.append({"role": "user", "content": content})
        return result
        