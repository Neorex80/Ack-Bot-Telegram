# utils/helpers.py

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

import logging
logger = logging.getLogger(__name__)

async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True if the user is an admin in the current group."""
    chat = update.effective_chat
    user = update.effective_user

    # Only works in group/supergroup
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("⚠️ This command can only be used in group chats.")
        return False

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ["administrator", "creator"]:
            return True

        await update.message.reply_text("🚫 Only admins can use this command!")
        return False

    except TelegramError as e:
        logger.error(f"Admin check error: {e}")
        await update.message.reply_text("❌ Couldn't verify admin status. Try again later.")
        return False
