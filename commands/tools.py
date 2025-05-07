from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import datetime
from utils.permissions import Permission, check_permissions

# Regular help command accessible by everyone
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide help information for regular users."""
    help_text = (
        "Available commands:\n"
        "/id - Get your user and chat ID\n"
        "/echo - Echo your message\n"
        "/time - Get the current server time\n"
        "/help - Show this help message\n"
        "/meow - Get a random cat image 🐱\n"
        # Add any other general commands here as you add more features
    )
    await update.message.reply_text(help_text)

# Admin/Dev help command
async def admin_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide help information for bot admins/devs."""
    result = await check_permissions(update, context, Permission.BOT_OWNER, silent=True)
    if result.allowed:
        dev_help_text = (
            # Moderation commands
            "\nModeration Commands:\n"
            "/mute - Mute a user\n"
            "/unmute - Unmute a user\n"
            "/kick - Kick a user\n"
            "/ban - Ban a user\n"
            "/unban - Unban a user\n"
            "/tban - Temporary ban a user\n"
            
            # Warn system commands
            "\nWarn System Commands:\n"
            "/warn - Warn a user\n"
            "/unwarn - Unwarn a user\n"
            "/warns - Show user warnings\n"
            "/resetwarns - Reset user warnings\n"
            "/setwarnlimit - Set warning limit\n"
            "/setwarnaction - Set warning action\n"
            
            # Chat settings commands
            "\nChat Settings Commands:\n"
            "/settitle - Set chat title\n"
            "/setdesc - Set chat description\n"
            "/slowmode - Set slow mode\n"
            "/lock - Lock the chat\n"
            "/unlock - Unlock the chat\n"
            "/setlog - Set chat log\n"
            
            # Additional admin commands
            "\nAdmin Commands:\n"
            "/purge - Purge messages\n"
            "/pin - Pin a message\n"
            "/unpin - Unpin a message\n"
            "/unpinall - Unpin all messages\n"
            "/nightmode - Activate night mode\n"
            "/morningmode - Activate morning mode\n"
        )
        await update.message.reply_text(dev_help_text)
    else:
        await update.message.reply_text("🚫 You don't have permission to access developer commands.")

# ID command
async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    await update.message.reply_text(
        f"🧾 Your ID: <code>{user.id}</code>\n"
        f"🗣️ Chat ID: <code>{chat.id}</code>",
        parse_mode="HTML"
    )

# Time command
async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return the current server time."""
    now = datetime.datetime.now()
    await update.message.reply_text(f"🕒 Current server time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# Echo command
async def echo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user's message."""
    await update.message.reply_text(update.message.text)


# Register all the handlers
def register_tools_handler(app):
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("echo", echo_command))
    app.add_handler(CommandHandler("help", help_command))  # Regular help command
    app.add_handler(CommandHandler("time", time_command))  # Register time command
    app.add_handler(CommandHandler("adminhelp", admin_help_command))  # Register devhelp command
