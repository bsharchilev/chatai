import os
import traceback
import yaml
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from pprint import pformat


# Define the Telegram bot token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_STRUCTURE_ECHO_BOT_TOKEN")

# Function to handle user messages
async def handle_message(update: Update, context):
    try:
        await update.message.reply_text(pformat(update))
    except Exception as e:
        # Optional: Log the error for debugging
        print(f"Error: {e}")
        await update.message.reply_text(traceback.format_exc())

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
