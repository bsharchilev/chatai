import yaml
from abc import abstractmethod, ABCMeta
from typing import Any, Dict, List, Optional


class PromptSection:
    __metaclass__ = ABCMeta

    @abstractmethod
    def __str__(self):
        pass

    @staticmethod
    @abstractmethod
    def parse(config: Dict[str, Any]) -> 'PromptSection':
        pass

    @abstractmethod
    def serialize_config(self) -> Dict[str, Any]:
        pass

class Text(PromptSection):
    def __init__(self, text: str):
        self.text = text

    def __str__(self):
        return self.text

    @staticmethod
    def parse(config: Dict[str, Any]) -> PromptSection:
        return Text(config["text"])

    def serialize_config(self) -> Dict[str, Any]:
        return {
            "type": "text",
            "text": self.text,
        }

class MainCharacter(PromptSection):
    def __init__(self, name: str, nickname: str, core_facts: str, recent_facts: str, message_examples: str):
        self.name = name
        self.nickname = nickname
        self.core_facts = core_facts
        self.recent_facts = recent_facts
        self.message_examples = message_examples

    def __str__(self):
        return \
        f"""    {self.name} ({self.nickname})
        Основные факты:
        {self.core_facts}
        
        Свежие факты:
        {self.recent_facts}
        
        Примеры сообщений:
        {self.message_examples}
        """

    @staticmethod
    def parse(config: Dict[str, Any]) -> 'PromptSection':
        return MainCharacter(
            config["name"],
            config["nickname"],
            "\n".join(f"* {fact}" for fact in config["core_facts"]),
            "\n".join(f"* {fact}" for fact in config["recent_facts"]),
            "\n".join(f"* {message}" for message in config["message_examples"])
        )

    def serialize_config(self) -> Dict[str, Any]:
        return {
            "type": "main_character"
        }

class Prompt:
    def __init__(self, config_path: str):
        self.config_path = config_path
        with open(config_path, "r") as f:
            _config = yaml.safe_load(f)
        self.config = Prompt.parse_config(_config)

    def print(self):
        return "\n\n".join(str(c) for c in self.config)

    @classmethod
    def parse_config(cls, config) -> List[PromptSection]:
        components = []
        for block in config:
            t = config["type"]
            if t == "text":
                components.append(Text.parse(block))
            if t == "main_character":
                components.append(MainCharacter.parse(block))
        return components

    def save_config(self, path: Optional[str] = None):
        path = path or self.config_path
        result = [component.serialize_config() for component in self.config]
        with open(path, "w") as f:
            yaml.safe_dump(result, f)