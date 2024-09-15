import asyncio
import os
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters

# Set up OpenAI client
OPENAI_CLIENT = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define the Telegram bot token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Function to handle user messages
async def handle_message(update: Update, context):
    # Get the user's message
    user_message = update.message.text

    # Send the message to the OpenAI API (fine-tuned model)
    try:
        response = OPENAI_CLIENT.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": user_message}],
            max_tokens=150,
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
        await update.message.reply_text("Извините, я обосрался.")

# Main function to start the bot
def main():
    # Initialize the bot with your Telegram token
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Initialize the application asynchronously

    # Create a filter for private chats that excludes commands
    private_text_filter = filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND

    # Add a message handler that only responds to text messages in private chats
    app.add_handler(MessageHandler(private_text_filter, handle_message))

    # Start the bot with polling (this will keep the bot running)
    app.run_polling()

if __name__ == "__main__":
   main()
