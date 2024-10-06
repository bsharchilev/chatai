from typing import Dict, List

from type_names import ChatMessage, CompletionMessage, TypedContent


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

FOCUS_PROMPT = "Отвечай только на текст последнего сообщения. Иногда сообщение может начинаться с «(от: …)», тут будет написано имя того, кто тебе пишет, используй это, чтобы сделать ответ контекстным, но помимо этого не используй эту часть. Иногда сообщение может начинаться с «(ответ на: …)», в таких случаях сообщение - это ответ на другое сообщение, его текст приведен в этом блоке. Если нужно, используй его, чтобы сделать ответ контекстным. Но твоя основная задача - ответить на основной текст сообщения, для этого используй только текст после вступительных секций «от» и «ответ на». НИКОГДА и ни при каких условиях не добавляй в ответ цитируемые сообщения, «от» или «ответ на»."

class Prompt:
    def __init__(self, prompt_file_path: str):
        self.prompt_file_path = prompt_file_path
        
    def generate(self, messages: List[ChatMessage]) -> List[CompletionMessage]:
        with open(self.prompt_file_path, 'r') as f:
            system_prompt = f.read()
        result = [{"role": "system", "content": system_prompt}, {"role": "system", "content": FOCUS_PROMPT}]
        for message in messages:
            role = "assistant" if message.username == "boggeyman_ai_bot" else "user"
            content = self.encode(message)
            result.append({"role": role, "content": content})
        return result
        
    def encode(self, message: ChatMessage) -> str | List[TypedContent]:
        user = USERNAME_TO_DISPLAY_NAME.get(message.username, "Незнакомец")
        user_part = f"(от: {user}) "
        
        reply_part = ""
        reply_image = None
        if message.reply_to_message is not None:
            reply_content = self.encode(message.reply_to_message)
            if isinstance(reply_content, str):
                reply_part = reply_content
            else:
                for component in reply_content:
                    if component["type"] == "text":
                        reply_part = component["text"]
                    else:
                        reply_image = component["image_url"]
            reply_part = f"(ответ на: {reply_part})"

        text = user_part + reply_part + message.text
        images = []
        if reply_image is not None:
            images.append(reply_image)
        if message.image_b64_encoded is not None:
            images.append({"url": f"data:image/jpeg;base64,{message.image_b64_encoded}"})
        if len(images) > 0 is not None:
            result = []
            if len(text) > 0:
                result.append({"type": "text", "text": text})
            for image in images:
                result.append({"type": "image_url", "image_url": image})
            return result
        else:
            return text
        