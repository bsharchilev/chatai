import asyncio
import os
import yaml
import traceback
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters

from util import MessageCache
from type_names import ChatMessage
from prompt import Prompt

# Set up OpenAI client
OPENAI_CLIENT = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define the Telegram bot token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Config
with open("config.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)
    
# Remember messages to feed as context
MESSAGE_CACHE = MessageCache(CONFIG["serving"]["max_messages_in_memory"])

# Function to handle user messages
async def handle_message(update: Update, context):
    if not should_respond(update):
        return
        
    # Get the user's message
    reply_to_message = update.message.reply_to_message
    chat_message = ChatMessage(
        update.message.from_user.username,
        update.message.text,
        update.message.date.timestamp(),
        None if reply_to_message is None else ChatMessage(
            reply_to_message.from_user.username,
            reply_to_message.text,
            reply_to_message.date.timestamp(),
        )
    )
    
    # Add to cache
    MESSAGE_CACHE.add_message(chat_message)

    # Send the message to the OpenAI API (fine-tuned model)
    try:
        prompt = Prompt("prompt.txt")
        prev_messages = MESSAGE_CACHE.get_last_n_messages(
            CONFIG["serving"]["max_messages_in_memory"],
        )
        response = OPENAI_CLIENT.chat.completions.create(
            model=CONFIG["model"]["name"],
            messages=prompt.generate(prev_messages),
            max_tokens=300,
            n=1,
            stop=None,
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
    if update.message.entities:
        for entity in update.message.entities:
            # Check for username mentions using the `mention` entity type
            if entity.type == "mention":
                mentioned_username = update.message.text[entity.offset:entity.offset + entity.length]
                if mentioned_username == "@boggeyman_ai_bot":
                    return True
    return False

# Main function to start the bot
def main():
    # Initialize the bot with your Telegram token
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Initialize the application asynchronously

    # Create a filter for private chats that excludes commands
    text_filter = filters.TEXT & ~filters.COMMAND

    # Add a message handler that only responds to text messages in private chats
    app.add_handler(MessageHandler(text_filter, handle_message))

    # Start the bot with polling (this will keep the bot running)
    app.run_polling()

if __name__ == "__main__":
   main()
