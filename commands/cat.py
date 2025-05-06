import logging
import requests
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from dotenv import load_dotenv
import os

# Load the API key from .env (ensure CAT_API_KEY is in your .env)
load_dotenv()
CAT_API_URL = "https://api.thecatapi.com/v1/images/search"  # Example API URL
CAT_API_KEY = os.getenv("CAT_API_KEY")

# Logger setup
logger = logging.getLogger(__name__)

async def meow_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a random cat image when the command /meow is issued."""
    logger.info(f"Received /meow command from chat: {update.effective_chat.id}")
    fetching_message = await update.message.reply_text("Fetching a cute cat for you... 🐱")

    try:
        # Prepare headers if API key is available
        headers = {}
        if CAT_API_KEY:
            headers["x-api-key"] = CAT_API_KEY

        # Make request to Cat API with a timeout
        response = requests.get(CAT_API_URL, headers=headers, timeout=10)  # Set timeout to 10 seconds
        response.raise_for_status()  # Check if the request was successful

        data = response.json()
        if data and isinstance(data, list) and len(data) > 0:
            cat_url = data[0].get("url")
            if cat_url:
                # Edit the fetching message to include the cat image
                await context.bot.edit_message_media(
                    chat_id=update.effective_chat.id,
                    message_id=fetching_message.message_id,
                    media={'type': 'photo', 'media': cat_url}
                )
                # Edit the caption separately
                await context.bot.edit_message_caption(
                    chat_id=update.effective_chat.id,
                    message_id=fetching_message.message_id,
                    caption="Meow! 🐾"
                )
            else:
                await fetching_message.edit_text("Oops! Couldn't find a cat image. Try again later! 😿")
        else:
            await fetching_message.edit_text("Oops! The cat API returned unexpected data. Try again later! 😿")

    except requests.exceptions.Timeout:
        logger.error("Request timed out.")
        await fetching_message.edit_text("The request timed out. Please try again later. 😞")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        await fetching_message.edit_text("Something went wrong while fetching a cat. Please try again later. 😞")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        await fetching_message.edit_text("Oops! An error occurred. Please try again later. 😓")


def register_cat_handler(app):
    """Register the /meow command handler."""
    app.add_handler(CommandHandler("meow", meow_command))
