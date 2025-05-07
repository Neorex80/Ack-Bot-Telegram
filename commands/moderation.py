# File: commands/moderation.py

from telegram import Update, ChatPermissions, User
from telegram.ext import CommandHandler, ContextTypes
from utils.helpers import is_user_admin
from datetime import timedelta

# Mute user
async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❗Please reply to the user you want to mute.")
        return

    user_to_mute: User = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id

    # Default mute duration = 1 hour
    duration = timedelta(hours=1)

    if context.args:
        try:
            duration = timedelta(minutes=int(context.args[0]))
        except ValueError:
            await update.message.reply_text("⏱️ Invalid duration. Please provide minutes as a number.")
            return

    until_date = update.message.date + duration

    permissions = ChatPermissions(can_send_messages=False)
    await context.bot.restrict_chat_member(chat_id, user_to_mute.id, permissions=permissions, until_date=until_date)

    await update.message.reply_text(f"🔇 Muted {user_to_mute.mention_html()} for {duration.total_seconds() // 60:.0f} minutes.", parse_mode="HTML")


# Unmute user
async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❗Please reply to the user you want to unmute.")
        return

    user_to_unmute: User = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id

    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )

    await context.bot.restrict_chat_member(chat_id, user_to_unmute.id, permissions=permissions)

    await update.message.reply_text(f"🔊 Unmuted {user_to_unmute.mention_html()}.", parse_mode="HTML")


# Kick user
async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❗Please reply to the user you want to kick.")
        return

    user_to_kick: User = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id

    await context.bot.ban_chat_member(chat_id, user_to_kick.id)
    await context.bot.unban_chat_member(chat_id, user_to_kick.id)  # Optional: allow rejoin

    await update.message.reply_text(f"👢 Kicked {user_to_kick.mention_html()}.", parse_mode="HTML")


# Ban user
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❗Please reply to the user you want to ban.")
        return

    user_to_ban: User = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id

    await context.bot.ban_chat_member(chat_id, user_to_ban.id)

    await update.message.reply_text(f"🚫 Banned {user_to_ban.mention_html()}.", parse_mode="HTML")


# Register all moderation commands
def register_moderation_handler(app):
    app.add_handler(CommandHandler("mute", mute_command))
    app.add_handler(CommandHandler("unmute", unmute_command))
    app.add_handler(CommandHandler("kick", kick_command))
    app.add_handler(CommandHandler("ban", ban_command))
