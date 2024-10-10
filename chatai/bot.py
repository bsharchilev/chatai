import base64
import os
import yaml
import traceback
import signal
import atexit

from crontab import CronTab
from telegram import Update, Message
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackContext
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError

from chatai import OPENAI_CLIENT
from chatai.util import MessageCache
from chatai.type_names import ChatMessage
from chatai.prompt import Prompt
from chatai.sql import Session
from chatai.sql.tables import Message as MessageRow
from chatai.memory.schedule import get_shutdown_handler, create_cron_job, remove_cron_job

# Define the Telegram bot token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Config
with open("chatai/config.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)
    
# Remember messages to feed as context
MESSAGE_CACHE = MessageCache(CONFIG["serving"]["max_messages_in_memory"])

# Function to handle user messages
async def handle_message(update: Update, context: CallbackContext):
    try:
        if not update.message.chat.type == "private" and not update.message.text and not update.message.caption:
            return

        # Get the user's message
        chat_message = await parse_message(update.message, context)
        # Persist in context for future trend extraction
        log_message(chat_message, update)

        # Abort if should not respond
        if not should_respond(update):
            return

        # Add to cache
        MESSAGE_CACHE.add_message(chat_message)

        prompt = Prompt("chatai/prompt.txt")
        prev_messages = MESSAGE_CACHE.get_last_n_messages(
            CONFIG["serving"]["max_messages_in_memory"],
        )
        if update.message.text == "!контекст":
            await update.message.reply_text(str(prompt.generate(prev_messages)[1:]))
            return
        response = OPENAI_CLIENT.chat.completions.create(
            model=CONFIG["model"]["name"],
            messages=prompt.generate(prev_messages),
            max_tokens=300,
            n=1,
            temperature=0.7,
        )
        # Get the response text
        gpt_response = response.choices[0].message.content.strip()

        # Send the response back to the user
        await update.message.reply_text(gpt_response)

    except Exception as e:
        # Optional: Log the error for debugging
        print(f"Error: {e}")
        await update.message.reply_text(traceback.format_exc())

def should_respond(update: Update) -> bool:
    if update.message.chat.type == "private":
        return True
    if update.message.reply_to_message is not None:
        if update.message.reply_to_message.from_user.username == "boggeyman_ai_bot":
            return True
    if update.message.entities and has_bot_mention(update.message.text, update.message.entities):
        return True
    if update.message.caption_entities and has_bot_mention(update.message.caption, update.message.caption_entities):
        return True
    return False

def has_bot_mention(text, entities) -> bool:
    for entity in entities:
        # Check for username mentions using the `mention` entity type
        if entity.type == "mention":
            mentioned_username = text[entity.offset:entity.offset + entity.length]
            if mentioned_username == "@boggeyman_ai_bot":
                return True

async def parse_message(message: Message, context: CallbackContext) -> ChatMessage:
    parsed_reply = None
    if message.reply_to_message is not None:
        with message.reply_to_message._unfrozen():
            message.reply_to_message.reply_to_message = None
        parsed_reply = await parse_message(message.reply_to_message, context)

    text = message.text or message.caption or ""

    # Get the list of photos (Telegram sends different sizes, choose the highest resolution)
    encoded_image = None
    if message.photo is not None and len(message.photo) > 0:
        photo = list(message.photo)[-1]  # Get the largest size
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    return ChatMessage(
        message.from_user.username,
        text,
        int(message.date.timestamp()),
        encoded_image,
        parsed_reply,
    )

def log_message(message: ChatMessage, update: Update):
    try:
        session = Session()

        message_row = _build_orm(
            message,
            update.message.id,
            update.effective_chat.id,
            update.message.reply_to_message.id if update.message.reply_to_message else None,
        )
        session.add(message_row)

        if message.reply_to_message:
            reply_message_row = _build_orm(
                message.reply_to_message,
                update.message.reply_to_message.id,
                update.effective_chat.id,
                None,
            )
            session.merge(reply_message_row)

        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        raise e
    finally:
        session.close()

def _build_orm(message: ChatMessage, message_id: int, chat_id: int, reply_to_id: Optional[int]) -> MessageRow:
    return MessageRow(
        id=message_id,
        chat_id=chat_id,
        username=message.username,
        text=message.text,
        unixtime=message.unixtime,
        image_b64_encoded=message.image_b64_encoded,
        reply_to_message_id=reply_to_id,
    )

# Main function to start the bot
def main():
    cron = CronTab(user=True)

    shutdown_handler = get_shutdown_handler(cron)
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    atexit.register(remove_cron_job)
    create_cron_job(cron)

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    filt = ~filters.COMMAND
    app.add_handler(MessageHandler(filt, handle_message))

    try:
        app.run_polling()
    except Exception as e:
        print(f"Error: {e}")
        # remove_cron_job(cron)

if __name__ == "__main__":
   main()
