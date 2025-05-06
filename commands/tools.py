# File: commands/tools.py
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import datetime

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    await update.message.reply_text(
        f"🧾 Your ID: <code>{user.id}</code>\n"
        f"🗣️ Chat ID: <code>{chat.id}</code>",
        parse_mode="HTML"
    )

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return the current server time."""
    now = datetime.datetime.now()
    await update.message.reply_text(f"🕒 Current server time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide help information."""
    help_text = (
        "Available commands:\n"
        "/id - Get your user and chat ID\n"
        "/echo - Echo your message\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(help_text)

async def echo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user's message."""
    await update.message.reply_text(update.message.text)

def register_tools_handler(app):
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("echo", echo_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("time", time_command))  # Register time command
