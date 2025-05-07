# File: commands/lock.py

from telegram import Update, ChatPermissions
from telegram.ext import CommandHandler, ContextTypes
from utils.helpers import is_user_admin

# Night Mode (Lock)
async def nightmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        return

    chat_id = update.effective_chat.id
    permissions = ChatPermissions(can_send_messages=False)

    await context.bot.set_chat_permissions(chat_id, permissions)
    await update.message.reply_text("🌙 Night mode activated. Group is now locked!")

# Morning Mode (Unlock)
async def morningmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        return

    chat_id = update.effective_chat.id
    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_invite_users=True
    )

    await context.bot.set_chat_permissions(chat_id, permissions)
    await update.message.reply_text("☀️ Morning mode activated. Group is now unlocked!")

# Register handlers
def register_lock_handler(app):
    app.add_handler(CommandHandler("nightmode", nightmode_command))
    app.add_handler(CommandHandler("morningmode", morningmode_command))
