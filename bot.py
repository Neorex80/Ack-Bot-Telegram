# File: bot.py
import os
from dotenv import load_dotenv
from telegram.ext import Application
from commands import register_all_handlers
from events import register_all_handlers as register_event_handlers  # Corrected import statement
from rich.logging import RichHandler
import logging

# Load env vars
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Set up rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("bot")

def notify_groups_on_startup(app):
    """Send a notification to all groups indicating the bot is up."""
    async def send_startup_message(context):
        # Assuming you have a list of chat IDs stored somewhere
        chat_ids = []  # Replace with actual chat IDs
        for chat_id in chat_ids:
            try:
                await context.bot.send_message(chat_id=chat_id, text="🚀 Bot is up and running!")
            except Exception as e:
                logger.error(f"Failed to send startup message to chat {chat_id}: {e}")

    app.job_queue.run_once(send_startup_message, 0)

def reset_bot_state():
    """Reset all bot state variables to start fresh."""
    from commands.afk import afk_users
    
    # Clear AFK users dictionary
    afk_users.clear()
    
    logger.info("🔄 Bot state has been reset.")

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ Missing TELEGRAM_BOT_TOKEN in .env file!")
        return

    # Reset bot state
    reset_bot_state()

    # Initialize the Application with JobQueue
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(lambda app: app.job_queue.start()).build()

    register_all_handlers(app)
    register_event_handlers(app)

    logger.info("✅ Bot initialized and ready to run.")
    notify_groups_on_startup(app)  # Notify groups on startup
    logger.info("🚀 Starting polling...")
    try:
        app.run_polling()
    except Exception as e:
        logger.exception("🔥 Bot crashed due to an unexpected error!")

if __name__ == '__main__':
    main()
