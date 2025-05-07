# File: bot.py
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime, time
from dotenv import load_dotenv
from telegram.ext import Application, filters, ChatMemberHandler
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from telegram.constants import ChatType
from telegram.ext import MessageHandler


from commands import register_all_handlers
from events import register_all_handlers as register_event_handlers
from utils.helpers import send_message_safely

from rich.logging import RichHandler
import logging

# Load env vars
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# File paths
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
GROUPS_FILE = DATA_DIR / "groups.json"

# Set up rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("bot")

def load_groups() -> dict:
    """Load the list of groups from the JSON file."""
    if not GROUPS_FILE.exists():
        return {}
    
    try:
        with open(GROUPS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"❌ Error decoding {GROUPS_FILE}. Using empty groups list.")
        return {}
    except Exception as e:
        logger.error(f"❌ Failed to load groups: {e}")
        return {}

def save_groups(groups: dict) -> bool:
    """Save the list of groups to the JSON file."""
    try:
        with open(GROUPS_FILE, "w", encoding="utf-8") as f:
            json.dump(groups, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"❌ Failed to save groups: {e}")
        return False

async def notify_groups_on_startup(context: ContextTypes.DEFAULT_TYPE):
    """Send a notification to all groups indicating the bot is up."""
    groups = load_groups()
    if not groups:
        logger.info("ℹ️ No groups to notify on startup.")
        return

    logger.info(f"🔔 Notifying {len(groups)} groups about bot startup...")
    
    success_count = 0
    for chat_id, info in list(groups.items()):
        # Skip if the group has notifications disabled
        if info.get("notifications_disabled", False):
            continue
            
        result = await send_message_safely(
            context=context,
            chat_id=chat_id,
            text="🚀 Bot is up and running!"
        )
        
        if result is False:
            # Bot might have been kicked - mark for verification
            groups[chat_id]["needs_verification"] = True
            logger.warning(f"⚠️ Failed to send message to group {chat_id}. Marked for verification.")
        else:
            success_count += 1
            # Update last activity
            groups[chat_id]["last_active"] = datetime.now().isoformat()
    
    save_groups(groups)
    logger.info(f"✅ Successfully notified {success_count}/{len(groups)} groups")

async def verify_groups_membership(context: ContextTypes.DEFAULT_TYPE):
    """Verify that the bot is still a member of all saved groups."""
    groups = load_groups()
    if not groups:
        return
        
    logger.info(f"🔍 Verifying membership in {len(groups)} groups...")
    
    for chat_id, info in list(groups.items()):
        try:
            # Try to get chat info - will fail if bot is not in the group
            chat = await context.bot.get_chat(chat_id)
            groups[chat_id]["needs_verification"] = False
            groups[chat_id]["verified_at"] = datetime.now().isoformat()
            groups[chat_id]["title"] = chat.title
        except TelegramError:
            logger.info(f"❌ Bot is no longer in group {chat_id}. Removing from groups list.")
            del groups[chat_id]
    
    save_groups(groups)
    logger.info(f"✅ Group verification complete. {len(groups)} active groups.")

async def add_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the bot being added to a group."""
    chat = update.effective_chat
    
    # Only process group chats
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return
        
    groups = load_groups()
    
    # Check if this is a new group
    is_new = str(chat.id) not in groups
    
    # Update or add the group
    groups[str(chat.id)] = {
        "title": chat.title,
        "first_joined": groups.get(str(chat.id), {}).get("first_joined", datetime.now().isoformat()),
        "last_active": datetime.now().isoformat(),
        "needs_verification": False,
        "type": chat.type,
        "notifications_disabled": False
    }
    
    save_groups(groups)
    
    if is_new:
        logger.info(f"➕ Bot added to new group: {chat.title} (ID: {chat.id})")
        await send_message_safely(
            context=context,
            chat_id=chat.id,
            text="👋 Hello! I've been added to this group. Use /help to see what I can do!"
        )
    else:
        logger.info(f"🔄 Bot activity in existing group: {chat.title} (ID: {chat.id})")

async def remove_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the bot being removed from a group."""
    chat = update.effective_chat
    
    # Only process group chats
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return
        
    groups = load_groups()
    
    # Check if the group is in our list
    if str(chat.id) in groups:
        del groups[str(chat.id)]
        save_groups(groups)
        logger.info(f"➖ Bot removed from group: {chat.title} (ID: {chat.id})")

def reset_bot_state():
    """Reset all bot state variables to start fresh."""
    from commands.afk import afk_users
    
    # Clear AFK users dictionary
    afk_users.clear()
    
    logger.info("🔄 Bot state has been reset.")

async def notify_admin_on_startup(context: ContextTypes.DEFAULT_TYPE):
    """Notify the admin that the bot has started."""
    if not ADMIN_USER_ID:
        return
        
    try:
        groups = load_groups()
        group_count = len(groups)
        
        message = (
            f"🤖 Bot startup complete!\n"
            f"📊 Currently in {group_count} groups\n"
            f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=message
        )
        logger.info("✅ Admin notification sent")
    except Exception as e:
        logger.error(f"❌ Failed to notify admin: {e}")

async def startup_sequence(app: Application):
    """Run all startup tasks in sequence."""
    try:
        # Wait a moment for the bot to fully initialize
        await asyncio.sleep(2)
        
        # First verify group membership
        await verify_groups_membership(app.create_context())
        
        # Then notify groups
        await notify_groups_on_startup(app.create_context())
        
        # Finally notify admin
        await notify_admin_on_startup(app.create_context())
    except Exception as e:
        logger.error(f"❌ Error in startup sequence: {e}")

def schedule_tasks(app: Application):
    """Schedule periodic tasks."""
    # Verify group membership once per day
    app.job_queue.run_daily(
        verify_groups_membership,
        time=time(hour=0, minute=0)  # Use the imported time class
    )

def register_group_tracking(app: Application):
    """Register handlers for tracking group membership."""
    # Track when bot is added to groups
    app.add_handler(ChatMemberHandler(add_group, chat_member_types=ChatMemberHandler.MY_CHAT_MEMBER))
    
    # Ensure activity is tracked on any message
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & ~filters.COMMAND,
        lambda u, c: add_group(u, c),
        block=False
    ))

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ Missing TELEGRAM_BOT_TOKEN in .env file!")
        return
    
    # Reset bot state
    reset_bot_state()
    
    # Initialize the Application with JobQueue
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Register command handlers
    register_all_handlers(app)
    register_event_handlers(app)
    
    # Register group tracking handlers
    register_group_tracking(app)
    
    # Add maintenance middleware
    from commands.dev import maintenance_middleware
    app.add_handler(MessageHandler(filters.ALL, maintenance_middleware, block=False), group=-1)
    
    # Initialize command counter
    app.bot_data["cmd_count"] = 0
    app.bot_data["msg_count"] = 0
    app.bot_data["uptime"] = datetime.now().isoformat()
    
    # Schedule tasks
    schedule_tasks(app)
    
    # Check for restart flag
    restart_flag = DATA_DIR / "restart.flag"
    if restart_flag.exists():
        try:
            with open(restart_flag, "r") as f:
                lines = f.read().strip().split("\n")
                chat_id, message_id = lines[0], int(lines[1])
                
            # Send notification that restart is complete
            app.job_queue.run_once(
                lambda ctx: ctx.bot.send_message(
                    chat_id=chat_id,
                    text="✅ Restart completed successfully!",
                    reply_to_message_id=message_id
                ),
                0
            )
            
            # Remove restart flag
            restart_flag.unlink()
        except Exception as e:
            logger.error(f"❌ Error processing restart flag: {e}")
    
    # Run startup tasks
    app.job_queue.run_once(lambda context: asyncio.create_task(startup_sequence(app)), 0)
    
    logger.info("✅ Bot initialized and ready to run.")
    logger.info("🚀 Starting polling...")
    
    try:
        app.run_polling()
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.exception("🔥 Bot crashed due to an unexpected error!")

if __name__ == '__main__':
    main()