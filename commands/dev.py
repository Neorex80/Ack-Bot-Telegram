# File: commands/dev.py
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler, filters
from telegram.constants import ParseMode

from utils.permissions import require_permission, Permission
from utils.helpers import send_message_safely
from config import DATA_DIR, ADMIN_USER_ID

# Path to store sudo admins list
SUDO_FILE = DATA_DIR / "sudo_admins.json"

def load_sudo_admins() -> Dict[str, Any]:
    """Load sudo admins from JSON file."""
    if not SUDO_FILE.exists():
        return {"admins": [], "last_updated": datetime.now().isoformat()}
    
    try:
        with open(SUDO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"admins": [], "last_updated": datetime.now().isoformat()}

def save_sudo_admins(data: Dict[str, Any]) -> bool:
    """Save sudo admins to JSON file."""
    try:
        with open(SUDO_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving sudo admins: {e}")
        return False

def is_sudo_admin(user_id: int) -> bool:
    """Check if a user is a sudo admin."""
    # Bot owner is always a sudo admin
    if ADMIN_USER_ID and str(user_id) == str(ADMIN_USER_ID):
        return True
        
    # Check if user is in sudo admins list
    sudo_data = load_sudo_admins()
    return str(user_id) in [str(admin["id"]) for admin in sudo_data["admins"]]

@require_permission(Permission.BOT_OWNER)
async def shutdown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shutdown the bot (owner only)."""
    await update.message.reply_text("🛑 Bot is shutting down...")
    raise SystemExit  # Cleanly exits the bot

@require_permission(Permission.BOT_OWNER)
async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restart the bot (owner only)."""
    # Create a restart flag file
    restart_flag = DATA_DIR / "restart.flag"
    with open(restart_flag, "w") as f:
        f.write(f"{update.effective_chat.id}\n{update.effective_message.message_id}")
    
    await update.message.reply_text("🔄 Bot is restarting...")
    os._exit(42)  # Exit with special code for restart

@require_permission(Permission.BOT_OWNER)
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcast a message to all groups."""
    if not context.args:
        await update.message.reply_text("❌ Usage: /broadcast <message>")
        return
        
    message = " ".join(context.args)
    broadcast_text = f"📢 Broadcast:\n\n{message}"
    
    # Load groups from the groups file
    groups_file = DATA_DIR / "groups.json"
    if not groups_file.exists():
        await update.message.reply_text("❌ No groups found to broadcast to.")
        return
        
    try:
        with open(groups_file, "r", encoding="utf-8") as f:
            groups = json.load(f)
    except Exception as e:
        await update.message.reply_text(f"❌ Error loading groups: {e}")
        return
        
    # Send status message
    status_msg = await update.message.reply_text(f"🔄 Broadcasting to {len(groups)} groups...")
    
    # Send broadcast to all groups
    success_count = 0
    for chat_id in groups:
        try:
            await send_message_safely(
                context=context,
                chat_id=chat_id,
                text=broadcast_text
            )
            success_count += 1
        except Exception:
            pass
    
    # Update status message with results
    await status_msg.edit_text(f"✅ Broadcast sent to {success_count}/{len(groups)} groups.")

@require_permission(Permission.BOT_OWNER)
async def sudo_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all sudo admins."""
    sudo_data = load_sudo_admins()
    admins = sudo_data["admins"]
    
    if not admins:
        await update.message.reply_text("📝 No sudo admins configured yet.")
        return
        
    admin_list = "\n".join([
        f"{i+1}. {admin['name']} (ID: `{admin['id']}`) - Added: {admin['added_date']}"
        for i, admin in enumerate(admins)
    ])
    
    await update.message.reply_text(
        f"🔑 *Sudo Admins List:*\n\n{admin_list}",
        parse_mode=ParseMode.MARKDOWN
    )

@require_permission(Permission.BOT_OWNER)
async def sudo_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a new sudo admin."""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("❌ Usage: /sudo_add <user_id> [name]")
        return
        
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Must be a number.")
        return
        
    # Get name if provided, otherwise use "Admin"
    name = " ".join(context.args[1:]) if len(context.args) > 1 else f"Admin {user_id}"
    
    # Load current sudo admins
    sudo_data = load_sudo_admins()
    
    # Check if already a sudo admin
    if any(str(admin["id"]) == str(user_id) for admin in sudo_data["admins"]):
        await update.message.reply_text(f"⚠️ User {user_id} is already a sudo admin.")
        return
        
    # Add new sudo admin
    sudo_data["admins"].append({
        "id": user_id,
        "name": name,
        "added_date": datetime.now().isoformat(),
        "added_by": update.effective_user.id
    })
    
    sudo_data["last_updated"] = datetime.now().isoformat()
    save_sudo_admins(sudo_data)
    
    await update.message.reply_text(f"✅ Added {name} (ID: {user_id}) as sudo admin.")

@require_permission(Permission.BOT_OWNER)
async def sudo_remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a sudo admin."""
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("❌ Usage: /sudo_remove <user_id>")
        return
        
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Must be a number.")
        return
        
    # Load current sudo admins
    sudo_data = load_sudo_admins()
    
    # Find admin to remove
    admin_to_remove = None
    for admin in sudo_data["admins"]:
        if str(admin["id"]) == str(user_id):
            admin_to_remove = admin
            break
            
    if not admin_to_remove:
        await update.message.reply_text(f"⚠️ User {user_id} is not a sudo admin.")
        return
        
    # Remove admin
    sudo_data["admins"].remove(admin_to_remove)
    sudo_data["last_updated"] = datetime.now().isoformat()
    save_sudo_admins(sudo_data)
    
    await update.message.reply_text(f"✅ Removed {admin_to_remove['name']} (ID: {user_id}) from sudo admins.")

@require_permission(Permission.BOT_OWNER)
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot statistics."""
    # Get groups count
    groups_file = DATA_DIR / "groups.json"
    try:
        with open(groups_file, "r", encoding="utf-8") as f:
            groups = json.load(f)
        group_count = len(groups)
    except Exception:
        group_count = 0

    # Get sudo admins count
    sudo_data = load_sudo_admins()
    sudo_count = len(sudo_data["admins"])
    
    # Build stats message
    stats = [
        "*📊 Bot Statistics:*",
        f"• Groups: {group_count}",
        f"• Sudo Admins: {sudo_count}",
        f"• Uptime: {context.bot_data.get('uptime', 'Unknown')}",
        f"• Commands processed: {context.bot_data.get('cmd_count', 0)}",
        f"• Messages processed: {context.bot_data.get('msg_count', 0)}"
    ]
    
    await update.message.reply_text("\n".join(stats), parse_mode=ParseMode.MARKDOWN)

@require_permission(Permission.BOT_OWNER)
async def maintenance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle maintenance mode."""
    # Toggle maintenance mode
    current_mode = context.bot_data.get("maintenance_mode", False)
    new_mode = not current_mode
    context.bot_data["maintenance_mode"] = new_mode
    
    # Save to persistent storage if available
    if hasattr(context.bot_data, "persistence"):
        context.bot_data.persistence.update_bot_data(context.bot_data)
    
    status = "🔧 Maintenance mode enabled. Only owner commands will work." if new_mode else "✅ Maintenance mode disabled. Bot is fully operational."
    await update.message.reply_text(status)

async def maintenance_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Middleware to check if bot is in maintenance mode."""
    # Always allow owner commands
    if update.effective_user and ADMIN_USER_ID and str(update.effective_user.id) == str(ADMIN_USER_ID):
        return None
        
    # Check if maintenance mode is enabled
    if context.bot_data.get("maintenance_mode", False):
        if update.effective_message:
            await update.effective_message.reply_text(
                "🔧 Bot is currently in maintenance mode. Please try again later."
            )
        return -1  # Skip handler
    return None

@require_permission(Permission.BOT_OWNER)
async def update_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually update the groups list by verifying groups."""
    await update.message.reply_text("🔄 Verifying group memberships...")
    
    # Get verify_groups_membership function from bot.py
    from bot import verify_groups_membership
    
    # Run verification
    await verify_groups_membership(context)
    
    await update.message.reply_text("✅ Group verification complete.")

def register_dev_handler(app):
    """Register all developer command handlers."""
    # Register command handlers
    app.add_handler(CommandHandler("shutdown", shutdown_command))
    app.add_handler(CommandHandler("restart", restart_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("sudo_list", sudo_list_command))
    app.add_handler(CommandHandler("sudo_add", sudo_add_command))
    app.add_handler(CommandHandler("sudo_remove", sudo_remove_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("maintenance", maintenance_command))
    app.add_handler(CommandHandler("update_groups", update_groups_command))
    
    # Add maintenance middleware if not already added
    # Note: This requires additional setup in the main bot.py file