import os
import time
import json
from dataclasses import dataclass
from typing import Dict, List
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError

from chatai import OPENAI_CLIENT
from chatai.type_names import ChatMessage
from chatai.sql import Session
from chatai.sql.tables import Message, Memory
from chatai.prompt import Prompt


@dataclass
class ChatInfo:
    id: int
    character_names: List[str]

def extract_memories(
        chat_info: ChatInfo,
        start_unixtime_inclusive: int,
        end_unixtime_exclusive: int,
        model: str,
        max_tokens: int,
):
    print("Reading prompts...")
    with open(os.getenv("SYSTEM_MEMORY_PROMPT_PATH"), "r") as f:
        system_prompt = f.read()
    with open(os.getenv("EXTRACT_MEMORY_PROMPT_PATH"), "r") as f:
        memory_prompt = f.read()

    print("Reading messages...")
    message_rows = read_messages(chat_info.id, start_unixtime_inclusive, end_unixtime_exclusive)
    print("Reading quoted messages...")
    for m in message_rows:
        if not hasattr(m, "username"):
            print(type(m))
            print(str(m))
    quoted_message_rows = read_messages_by_ids(
        list(set(m.reply_to_message_id for m in message_rows if hasattr(m, "reply_to_message_id")))
    )
    print("Encoding messages...")
    chat_messages = encode_messages(message_rows, quoted_message_rows)
    print(len(chat_messages), chat_messages[-20:])
    chat_messages = [m for m in chat_messages if not (("(от: Бугимен)" in m) or ("(ответ на: Бугимен" in m))]
    print(len(chat_messages))

    print("Making request...")
    request_id = f"memory_extraction_{chat_info.id}_{start_unixtime_inclusive}_{end_unixtime_exclusive}"
    request = make_request(
        request_id,
        chat_info.character_names,
        chat_messages,
        system_prompt,
        memory_prompt,
        model,
        max_tokens,
    )
    print("Submitting request...")
    response = submit_and_wait_batch_task(OPENAI_CLIENT, [request], request_id)
    print("Parsing results...")
    memories = [json.loads(n.strip('\n')) for n in response.text.split('\n')[:-1]]

    print("Dumping results...")
    dump_memories(memories, chat_info.id, start_unixtime_inclusive, end_unixtime_exclusive)

def read_messages(chat_id: int, start_unixtime_inclusive: int, end_unixtime_exclusive: int) -> List[Message]:
    try:
        session = Session()

        select_statement = select(Message).where(
            and_(
                Message.chat_id == chat_id,
                Message.unixtime >= start_unixtime_inclusive,
                Message.unixtime < end_unixtime_exclusive,
            )
        )
        return session.execute(select_statement).all()

    except SQLAlchemyError as e:
        session.rollback()
        raise e
    finally:
        session.close()


def read_messages_by_ids(ids: List[int]) -> List[Message]:
    try:
        session = Session()

        select_statement = select(Message).where(
            Message.id.in_(ids)
        )
        return session.execute(select_statement).all()

    except SQLAlchemyError as e:
        session.rollback()
        raise e
    finally:
        session.close()

def encode_messages(message_rows: List[Message], quoted_messages: List[Message]) -> List[str]:
    quoted_message_by_id = {m.id: m for m in quoted_messages}

    prompt = Prompt(os.getenv("SYSTEM_MEMORY_PROMPT_PATH"))
    chat_messages = []
    for row in message_rows:
        quoted_message = None
        if hasattr(row, "reply_to_message_id"):
            quoted_message_row = quoted_message_by_id[row.reply_to_message_id]
            quoted_message = ChatMessage(
                quoted_message_row.username,
                quoted_message_row.text,
                quoted_message_row.unixtime,
                quoted_message_row.image_b64_encoded,
                None,
            )
        chat_messages.append(
            prompt.encode(
                ChatMessage(
                    row.username,
                    row.text,
                    row.unixtime,
                    row.image_b64_encoded,
                    quoted_message,
                )
            )
        )
    return chat_messages


def make_request(
        custom_id: str,
        character_names: List[str],
        messages: List[str],
        system_prompt: str,
        memory_prompt: str,
        model: str,
        max_tokens: int,
) -> Dict[str, ...]:
    schema = {
        "type": "json_schema",
        "json_schema": {
            "strict": True,
            "name": "character_facts",
            "schema": {
                "type": "object",
                "properties": {
                    "facts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "character_name": {
                                    "type": "string",
                                    "description": "Имя основного персонажа, про которого этот факт",
                                    "enum": character_names,
                                },
                                "fact": {"type": "string", "description": "Текст факта про персонажа"},
                                "interest_score": {"type": "number",
                                                   "description": "Скор интересности факта. Число от 0 до 1"},
                            },
                            "additionalProperties": False,
                            "required": ["character_name", "fact", "interest_score"],
                            "description": "Структура, описывающая факт про персонажа",
                        },
                        "description": "Список фактов про персонажа",
                    },
                },
                "required": ["facts"],
                "additionalProperties": False,
            }
        }
    }

    input_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": memory_prompt},
    ]
    for message in messages:
        input_messages.append({"role": "user", "content": message})
    return {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
            "max_tokens": max_tokens,
            "messages": input_messages,
            "response_format": schema,
        }
    }

def submit_and_wait_batch_task(client, batch, name):
    filename = f'{name}.jsonl'
    with open(filename, 'w') as f:
        f.writelines([json.dumps(r) + '\n' for r in batch])

    batch_input_file = client.files.create(
      file=open(filename, "rb"),
      purpose="batch"
    )

    batch_input_file_id = batch_input_file.id
    bc = client.batches.create(
        input_file_id=batch_input_file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={
          "description": filename[:-6]
        }
    )

    while True:
        b = client.batches.retrieve(bc.id)
        if b.status in ("validating", "in_progress", "finalizing"):
            time.sleep(60)
        else:
            break

    return client.files.content(b.output_file_id)

def dump_memories(memories, chat_id: int, start_unixtime: int, end_unixtime: int):
    try:
        session = Session()

        for row in memories:
            memories_structs = json.loads(row["response"]["body"]["choices"][0]["message"]["content"])["facts"]
            for struct in memories_structs:
                session.add(Memory(
                    chat_id=chat_id,
                    start_unixtime=start_unixtime,
                    end_unixtime=end_unixtime,
                    character_name=struct["character_name"],
                    fact=struct["fact"],
                    interest_score=struct["interest_score"],
                ))
        session.commit()

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    names = [
                                    "Александр Соболь",
                                    "Борис Шарчилев",
                                    "Дмитрий Ушанов",
                                    "Евгения Помонаренко",
                                    "Виталий Григораш",
                                    "Святослав Юшин",
                                    "Андрей Зимовнов",
                                    "Андрей Гайбун",
                                ]
    extract_memories(
        ChatInfo(-1001783745747, names),
        1728428400,
        1728601200,
        "gpt-4o-2024-08-06",
        1000,
    )