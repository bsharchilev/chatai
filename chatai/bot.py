import asyncio
import os
import yaml
import traceback
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters

from util import MessageCache

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
    # Get the user's message
    user_message = update.message.text
    update_time = update.message.date
    
    # Add to cache
    MESSAGE_CACHE.add_message(user_message, update_time)

    # Send the message to the OpenAI API (fine-tuned model)
    try:
        print("f1")
        context = [{
            "role": "system",
            "content": os.getenv("CHATAI_PROMPT"),
        }]
        context.extend([
            {"role": "user", "content": msg}
            for msg in MESSAGE_CACHE.get_last_n_messages(CONFIG["serving"]["max_messages_in_memory"])
        ])
        context.append({"role": "user", "content": user_message})
        print("f2")
        response = OPENAI_CLIENT.chat.completions.create(
            model=CONFIG["model"]["name"],
            messages=context,
            max_tokens=300,
            n=1,
            stop=None,
            temperature=0.7,
        )
        print("f3")
        # Get the response text
        gpt_response = response.choices[0].message.content.strip()
        print("f4")

        # Send the response back to the user
        await update.message.reply_text(gpt_response)

    except Exception as e:
        # Optional: Log the error for debugging
        print(f"Error: {traceback.format_exc()}")
        await update.message.reply_text("Извините, я обосрался.")

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
