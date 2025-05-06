# File: commands.py or welcome.py (depending on your structure)
import random
import logging
from telegram import Update, ChatMemberUpdated
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcomes new members in a group with a cute cat GIF and custom message."""
    chat = update.effective_chat

    # Only respond in groups/supergroups
    if chat.type not in ["group", "supergroup"]:
        return

    # Ensure this is a join event and not a bot promotion or other state change
    member_update: ChatMemberUpdated = update.chat_member
    if member_update.new_chat_member.status != "member":
        return

    if member_update.from_user.id == member_update.new_chat_member.user.id:
        return

    new_member = member_update.new_chat_member.user
    logger.info(f"👤 New member joined: {new_member.full_name} (ID: {new_member.id})")

    # Cute cat GIFs for welcome
    cat_gifs = [
        "https://media.giphy.com/media/vFKqnCdLPNOKc/giphy.gif",      # Keyboard cat
        "https://media.giphy.com/media/l0MYJnJQ4EiYLxvQ4/giphy.gif",  # Welcome cat
        "https://media.giphy.com/media/3oKIPnAiaMCws8nOsE/giphy.gif", # Cat waving paw
        "https://media.giphy.com/media/BzyTuYCmvSORqs1ABM/giphy.gif", # Hello cat
        "https://media.giphy.com/media/Vbtc9VG51NtzT1Qnv1/giphy.gif"  # Happy jumping cat
    ]
    selected_gif = random.choice(cat_gifs)

    wave_emoji = "👋"
    paw_emoji = "🐾"
    sparkle_emoji = "✨"
    id_emoji = "🆔"
    bot_emoji = "🤖"

    welcome_text = (
        f"{wave_emoji} <b>Welcome to the group, {new_member.mention_html()}!</b> {paw_emoji}\n\n"
        f"{sparkle_emoji} Feel free to introduce yourself and join the chat!\n"
        f"{id_emoji} <b>Your ID:</b> <code>{new_member.id}</code>\n"
        f"{bot_emoji} <b>Username:</b> @{new_member.username or 'None'}\n\n"
        f"Type <code>/help</code> to get started!"
    )

    try:
        # Send GIF
        await context.bot.send_animation(
            chat_id=chat.id,
            animation=selected_gif,
            caption=f"Welcome to the group, {new_member.first_name}! {wave_emoji}"
        )

        # Send message
        await context.bot.send_message(
            chat_id=chat.id,
            text=welcome_text,
            parse_mode=ParseMode.HTML
        )

    except TelegramError as e:
        logger.error(f"❌ Error sending welcome message: {e}")


# File: commands/welcome.py

from telegram.ext import CommandHandler

async def welcome_command(update, context):
    """Send a welcome message when the command /welcome is issued."""
    await update.message.reply_text("Welcome to the group!")

def register_welcome_handler(app):
    """Register the /welcome command handler."""
    app.add_handler(CommandHandler("welcome", welcome_command))
