# File: utils/admin_check.py

import os
import json
from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes
from rich import print as rprint
import logging

logger = logging.getLogger(__name__)

# Load config from .env or hardcode owner ID for now
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "123456789"))  # Replace default if needed

# Optional: Allow a list of globally authorized user IDs
AUTHORIZED_USERS = set()


def _is_owner(user_id: int) -> bool:
    """Check if user is the bot owner."""
    return user_id == BOT_OWNER_ID


def _is_authorized(user_id: int) -> bool:
    """Check if user is authorized to use privileged commands."""
    return user_id in AUTHORIZED_USERS or _is_owner(user_id)


async def _check_admin_permissions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user has admin permissions in the group."""
    if _is_owner(update.effective_user.id):
        return True

    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command only works in group chats!")
        return False

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status in ["administrator", "creator"]:
            return True
        else:
            await update.message.reply_text(
                "🚫 You need to be an *admin* to use this command. Nice try though 😏",
                parse_mode="Markdown",
            )
            return False
    except TelegramError as e:
        logger.error(f"Error checking admin permissions: {e}")
        await update.message.reply_text(
            "❌ I couldn't verify your admin status. Please try again later."
        )
        return False
