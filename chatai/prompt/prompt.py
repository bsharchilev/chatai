from ruamel import yaml
import random
from abc import abstractmethod, ABCMeta
from typing import Any, Dict, List

from sqlalchemy.dialects.mysql.mariadb import loader


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
        result = dict()
        result["type"] = "text"
        result["text"] = self.text
        return result

class ListSection(PromptSection):
    def __init__(self, title: str, items: List[PromptSection]):
        self.title = title
        self.items = items

    def __str__(self):
        bullets = "\n\n".join(f"{i + 1}: {str(item)}" for i, item in enumerate(self.items))
        return \
            f"""{self.title}
            
{bullets}"""

    @staticmethod
    def parse(config: Dict[str, Any]) -> 'PromptSection':
        return ListSection(
            config["title"],
            Prompt.parse_config(config["items"]),
        )

    def serialize_config(self) -> Dict[str, Any]:
        result = dict()
        result["type"] = "list"
        result["title"] = self.title
        result["items"] = [item.serialize_config() for item in self.items]
        return result

class MainCharacter(PromptSection):
    def __init__(
            self,
            name: str,
            nickname: str,
            core_facts: List[str],
            recent_facts: List[str],
            message_examples: List[str]
    ):
        self.name = name
        self.nickname = nickname
        self.core_facts = core_facts
        self.recent_facts = recent_facts
        self.message_examples = message_examples

    def __str__(self):
        facts = self.core_facts + self.recent_facts
        random.shuffle(facts)
        facts_str = "\n".join(f"* {fact}" for fact in facts)
        message_examples = "\n".join(f"* {message}" for message in self.message_examples)
        return \
        f"""{self.name} ({self.nickname})
Интересные факты:
{facts_str}
        
Примеры сообщений:
{message_examples}"""

    @staticmethod
    def parse(config: Dict[str, Any]) -> 'PromptSection':
        return MainCharacter(
            config["name"],
            config["nickname"],
            config["core_facts"],
            config["recent_facts"],
            config["message_examples"],
        )

    def serialize_config(self) -> Dict[str, Any]:
        result = dict()
        result["type"] = "main_character"
        result["name"] = self.name
        result["nickname"] = self.nickname
        result["core_facts"] = self.core_facts
        result["recent_facts"] = self.recent_facts
        result["message_examples"] = self.message_examples
        return result

class Prompt:
    def __init__(self, config_path: str):
        self.config_path = config_path
        with open(config_path, "r") as f:
            _config = yaml.load(f, Loader=yaml.RoundTripLoader)
        self.config = Prompt.parse_config(_config)

    def print(self):
        return "\n\n".join(str(c) for c in self.config)

    @classmethod
    def parse_config(cls, config) -> List[PromptSection]:
        components = []
        for block in config:
            t = block["type"]
            if t == "text":
                components.append(Text.parse(block))
            if t == "list":
                components.append(ListSection.parse(block))
            if t == "main_character":
                components.append(MainCharacter.parse(block))
        return components

    def save_config(self, path: str):
        result = [component.serialize_config() for component in self.config]
        print(result)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(result, f, allow_unicode=True, Dumper=yaml.RoundTripDumper)