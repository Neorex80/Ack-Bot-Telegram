# File: commands/lock.py

from telegram import Update, ChatPermissions
from telegram.ext import CommandHandler, ContextTypes
from utils.helpers import is_user_admin
import logging

logger = logging.getLogger(__name__)

# Lock the group
async def lock_group(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    permissions = ChatPermissions(can_send_messages=False)
    try:
        await context.bot.set_chat_permissions(chat_id, permissions)
        await context.bot.send_message(chat_id, "🌙 Night mode activated. Group is now locked!")
    except Exception as e:
        logger.error(f"Failed to lock group {chat_id}: {e}")

# Unlock the group
async def unlock_group(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_invite_users=True
    )
    try:
        await context.bot.set_chat_permissions(chat_id, permissions)
        await context.bot.send_message(chat_id, "☀️ Morning mode activated. Group is now unlocked!")
    except Exception as e:
        logger.error(f"Failed to unlock group {chat_id}: {e}")

# /nightmode [minutes]
async def nightmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        return
    
    chat_id = update.effective_chat.id

    # Handle timer
    if context.args and context.args[0].isdigit():
        delay_minutes = int(context.args[0])
        delay_seconds = delay_minutes * 60
        context.job_queue.run_once(lambda ctx: lock_group(ctx, chat_id), delay_seconds)
        await update.message.reply_text(f"⏳ Night mode will activate in {delay_minutes} minutes.")
    else:
        await lock_group(context, chat_id)

# /morningmode [minutes]
async def morningmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        return
    
    chat_id = update.effective_chat.id

    # Handle timer
    if context.args and context.args[0].isdigit():
        delay_minutes = int(context.args[0])
        delay_seconds = delay_minutes * 60
        context.job_queue.run_once(lambda ctx: unlock_group(ctx, chat_id), delay_seconds)
        await update.message.reply_text(f"⏳ Morning mode will activate in {delay_minutes} minutes.")
    else:
        await unlock_group(context, chat_id)

# Register handlers
def register_lock_handler(app):
    app.add_handler(CommandHandler("nightmode", nightmode_command))
    app.add_handler(CommandHandler("morningmode", morningmode_command))
