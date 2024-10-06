import base64
import os
import yaml
import traceback
from openai import OpenAI
from telegram import Update, Message
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CallbackContext

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
async def handle_message(update: Update, context: CallbackContext):
    if not should_respond(update):
        return
        
    # Get the user's message
    chat_message = await parse_message(update.message, context)
    
    # Add to cache
    MESSAGE_CACHE.add_message(chat_message)

    # Send the message to the OpenAI API (fine-tuned model)
    try:
        prompt = Prompt("prompt.txt")
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
    if update.message.reply_to_message is not None:
        if update.message.reply_to_message.from_user.username == "boggeyman_ai_bot":
            return True
    if update.message.entities:
        for entity in update.message.entities:
            # Check for username mentions using the `mention` entity type
            if entity.type == "mention":
                mentioned_username = update.message.text[entity.offset:entity.offset + entity.length]
                if mentioned_username == "@boggeyman_ai_bot":
                    return True
    return False

async def parse_message(message: Message, context: CallbackContext) -> ChatMessage:
    parsed_reply = None
    if message.reply_to_message is not None:
        with message.reply_to_message._unfrozen():
            message.reply_to_message.reply_to_message = None
        parsed_reply = parse_message(message.reply_to_message)

    text = message.text or message.caption or ""

    # Get the list of photos (Telegram sends different sizes, choose the highest resolution)
    encoded_image = None
    if message.photo is not None:
        photo = message.photo[-1]  # Get the largest size
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    return ChatMessage(
        message.from_user.username,
        text,
        message.date.timestamp(),
        encoded_image,
        parsed_reply,
    )

# Main function to start the bot
def main():
    # Initialize the bot with your Telegram token
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Initialize the application asynchronously

    # Create a filter for private chats that excludes commands
    filt = ~filters.COMMAND

    # Add a message handler that only responds to text messages in private chats
    app.add_handler(MessageHandler(filt, handle_message))

    # Start the bot with polling (this will keep the bot running)
    app.run_polling()

if __name__ == "__main__":
   main()
