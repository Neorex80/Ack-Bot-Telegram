# File: commands/tools.py
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    await update.message.reply_text(
        f"🧾 Your ID: <code>{user.id}</code>\n"
        f"🗣️ Chat ID: <code>{chat.id}</code>",
        parse_mode="HTML"
    )

def register_tools_handler(app):
    app.add_handler(CommandHandler("id", id_command))
