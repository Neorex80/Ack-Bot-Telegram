# File: commands/afk.py
import html
import logging
from datetime import datetime, timezone, timedelta
from telegram import Update, MessageEntity, User
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, MessageHandler, ContextTypes, filters

logger = logging.getLogger(__name__)
afk_users = {}

def format_timedelta(delta: timedelta) -> str:
    seconds = int(delta.total_seconds())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)

def get_user_mention(user: User) -> str:
    return f'<a href="tg://user?id={user.id}">{html.escape(user.first_name)}</a>'

async def afk_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message
    reason = "AFK"
    if context.args:
        reason = " ".join(context.args)
    now = datetime.now(timezone.utc)
    afk_users[user.id] = {'since': now, 'reason': html.escape(reason)}
    user_mention = get_user_mention(user)
    await message.reply_text(
        f"🌙 {user_mention} is now AFK!\n📝 Reason: <i>{reason}</i>",
        parse_mode=ParseMode.HTML
    )

async def handle_afk_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message
    now = datetime.now(timezone.utc)
    if user.id in afk_users:
        afk_info = afk_users.pop(user.id)
        duration = now - afk_info['since']
        await message.reply_text(
            f"👋 Welcome back, {get_user_mention(user)}!\n⏱️ You were AFK for {format_timedelta(duration)}.",
            parse_mode=ParseMode.HTML
        )
        return

    mentions = set()
    if message.reply_to_message and message.reply_to_message.from_user:
        mentions.add(message.reply_to_message.from_user.id)
    for entity in message.entities or []:
        if entity.type == MessageEntity.TEXT_MENTION and entity.user:
            mentions.add(entity.user.id)
    for uid in mentions:
        if uid in afk_users:
            info = afk_users[uid]
            duration = now - info['since']
            chat_member = await context.bot.get_chat_member(update.effective_chat.id, uid)
            user_mention = get_user_mention(chat_member.user)
            await message.reply_text(
                f"⚠️ {user_mention} is AFK: <i>{info['reason']}</i>\n⏱️ Since: {format_timedelta(duration)} ago",
                parse_mode=ParseMode.HTML
            )

def register_all_handlers(app):
    app.add_handler(CommandHandler("afk", afk_command))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND | filters.Entity(MessageEntity.TEXT_MENTION) | filters.REPLY,
        handle_afk_messages
    ))
