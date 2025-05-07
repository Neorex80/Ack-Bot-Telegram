# File: commands/moderation.py

from telegram import Update, ChatPermissions, User, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
from utils.helpers import is_user_admin
from datetime import timedelta, datetime
import re

# Helper function to parse duration strings like "1h30m"
def parse_duration(duration_str):
    if not duration_str:
        return timedelta(hours=1)  # Default: 1 hour
    
    total_minutes = 0
    # Match patterns like 1h, 30m, 1d, etc.
    matches = re.findall(r'(\d+)([dhm])', duration_str.lower())
    
    if not matches:
        try:
            # If just a number is provided, interpret as minutes
            return timedelta(minutes=int(duration_str))
        except ValueError:
            return None
    
    for value, unit in matches:
        value = int(value)
        if unit == 'd':
            total_minutes += value * 24 * 60
        elif unit == 'h':
            total_minutes += value * 60
        elif unit == 'm':
            total_minutes += value
    
    return timedelta(minutes=total_minutes)

# Format a timedelta nicely for display
def format_time_delta(delta):
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes or (not days and not hours):  # Always show minutes if no days/hours
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    
    return " ".join(parts)

# Get a user's name with ID for logging
def get_user_info(user: User):
    user_name = user.full_name
    user_id = user.id
    username = f" (@{user.username})" if user.username else ""
    return f"{user_name}{username} [ID: {user_id}]"

# Log moderation actions to a specified channel or group
async def log_action(context, action, mod_user, target_user, reason=None, duration=None):
    log_channel = context.bot_data.get("MOD_LOG_CHANNEL")
    if not log_channel:
        return  # No log channel configured
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mod_info = get_user_info(mod_user)
    target_info = get_user_info(target_user)
    
    message = f"🔶 <b>Moderation Action</b> 🔶\n\n"
    message += f"<b>Action:</b> {action}\n"
    message += f"<b>Moderator:</b> {mod_user.mention_html()}\n"
    message += f"<b>Target:</b> {target_user.mention_html()}\n"
    message += f"<b>Time:</b> {timestamp}\n"
    
    if duration:
        message += f"<b>Duration:</b> {format_time_delta(duration)}\n"
    
    if reason:
        message += f"<b>Reason:</b> {reason}\n"
    
    try:
        await context.bot.send_message(
            chat_id=log_channel,
            text=message,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        # If sending to log channel fails, send to the current chat
        print(f"Failed to log to channel: {e}")

# Mute user
async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❗ Please reply to the user you want to mute.")
        return
    
    user_to_mute: User = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    
    # Check if we're trying to mute an admin
    try:
        member = await context.bot.get_chat_member(chat_id, user_to_mute.id)
        if member.status in ['administrator', 'creator']:
            await update.message.reply_text("❌ I can't mute administrators or the chat creator.")
            return
    except Exception as e:
        await update.message.reply_text(f"Error checking user status: {e}")
        return
    
    # Parse duration and reason
    duration = timedelta(hours=1)  # Default: 1 hour
    reason = "No reason provided"
    
    args = context.args
    if args:
        duration_str = args[0]
        parsed_duration = parse_duration(duration_str)
        
        if parsed_duration is None:
            await update.message.reply_text("⏱️ Invalid duration format. Examples: 30m, 1h, 1h30m, 1d")
            return
        
        duration = parsed_duration
        reason = " ".join(args[1:]) if len(args) > 1 else reason
    
    until_date = update.message.date + duration
    
    permissions = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_polls=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False
    )
    
    try:
        await context.bot.restrict_chat_member(
            chat_id, 
            user_to_mute.id, 
            permissions=permissions, 
            until_date=until_date
        )
        
        # Log the action
        await log_action(
            context, 
            "MUTE", 
            update.effective_user, 
            user_to_mute, 
            reason, 
            duration
        )
        
        await update.message.reply_text(
            f"🔇 Muted {user_to_mute.mention_html()} for {format_time_delta(duration)}.\n"
            f"Reason: {reason}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await update.message.reply_text(f"Failed to mute user: {e}")

# Unmute user
async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❗ Please reply to the user you want to unmute.")
        return
    
    user_to_unmute: User = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    
    reason = " ".join(context.args) if context.args else "No reason provided"
    
    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )
    
    try:
        await context.bot.restrict_chat_member(chat_id, user_to_unmute.id, permissions=permissions)
        
        # Log the action
        await log_action(
            context, 
            "UNMUTE", 
            update.effective_user, 
            user_to_unmute, 
            reason
        )
        
        await update.message.reply_text(
            f"🔊 Unmuted {user_to_unmute.mention_html()}.\n"
            f"Reason: {reason}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await update.message.reply_text(f"Failed to unmute user: {e}")

# Kick user
async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❗ Please reply to the user you want to kick.")
        return
    
    user_to_kick: User = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    
    # Check if we're trying to kick an admin
    try:
        member = await context.bot.get_chat_member(chat_id, user_to_kick.id)
        if member.status in ['administrator', 'creator']:
            await update.message.reply_text("❌ I can't kick administrators or the chat creator.")
            return
    except Exception as e:
        await update.message.reply_text(f"Error checking user status: {e}")
        return
    
    reason = " ".join(context.args) if context.args else "No reason provided"
    
    try:
        await context.bot.ban_chat_member(chat_id, user_to_kick.id)
        await context.bot.unban_chat_member(chat_id, user_to_kick.id)  # Allow rejoin
        
        # Log the action
        await log_action(
            context, 
            "KICK", 
            update.effective_user, 
            user_to_kick, 
            reason
        )
        
        await update.message.reply_text(
            f"👢 Kicked {user_to_kick.mention_html()}.\n"
            f"Reason: {reason}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await update.message.reply_text(f"Failed to kick user: {e}")

# Ban user
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❗ Please reply to the user you want to ban.")
        return
    
    user_to_ban: User = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    
    # Check if we're trying to ban an admin
    try:
        member = await context.bot.get_chat_member(chat_id, user_to_ban.id)
        if member.status in ['administrator', 'creator']:
            await update.message.reply_text("❌ I can't ban administrators or the chat creator.")
            return
    except Exception as e:
        await update.message.reply_text(f"Error checking user status: {e}")
        return
    
    reason = " ".join(context.args) if context.args else "No reason provided"
    
    try:
        await context.bot.ban_chat_member(chat_id, user_to_ban.id)
        
        # Log the action
        await log_action(
            context, 
            "BAN", 
            update.effective_user, 
            user_to_ban, 
            reason
        )
        
        await update.message.reply_text(
            f"🚫 Banned {user_to_ban.mention_html()}.\n"
            f"Reason: {reason}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await update.message.reply_text(f"Failed to ban user: {e}")

# Unban user
async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("❗ Please provide the user ID to unban.")
        return
    
    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❗ Invalid user ID. Please provide a numeric ID.")
        return
    
    chat_id = update.effective_chat.id
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
    
    try:
        await context.bot.unban_chat_member(chat_id, user_id)
        
        # Try to get user info - this might fail if user is not in any common chats
        try:
            user_info = await context.bot.get_chat(user_id)
            user_mention = user_info.mention_html()
        except:
            user_mention = f"User [ID: {user_id}]"
        
        await log_action(
            context, 
            "UNBAN", 
            update.effective_user, 
            user_info if 'user_info' in locals() else None, 
            reason
        )
        
        await update.message.reply_text(
            f"✅ Unbanned {user_mention}.\n"
            f"Reason: {reason}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await update.message.reply_text(f"Failed to unban user: {e}")

# Warn system
async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❗ Please reply to the user you want to warn.")
        return
    
    user_to_warn: User = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    
    # Check if we're trying to warn an admin
    try:
        member = await context.bot.get_chat_member(chat_id, user_to_warn.id)
        if member.status in ['administrator', 'creator']:
            await update.message.reply_text("❌ I can't warn administrators or the chat creator.")
            return
    except Exception as e:
        await update.message.reply_text(f"Error checking user status: {e}")
        return
    
    reason = " ".join(context.args) if context.args else "No reason provided"
    
    # Initialize warns dict in chat_data if not exists
    if "warns" not in context.chat_data:
        context.chat_data["warns"] = {}
    
    # Get user's current warns
    user_id_str = str(user_to_warn.id)
    if user_id_str not in context.chat_data["warns"]:
        context.chat_data["warns"][user_id_str] = {"count": 0, "reasons": []}
    
    # Get warn settings
    warn_limit = context.bot_data.get("WARN_LIMIT", 3)
    warn_action = context.bot_data.get("WARN_ACTION", "mute")  # Default: mute
    
    # Add warn
    context.chat_data["warns"][user_id_str]["count"] += 1
    context.chat_data["warns"][user_id_str]["reasons"].append(reason)
    current_warns = context.chat_data["warns"][user_id_str]["count"]
    
    # Log the action
    await log_action(
        context, 
        "WARN", 
        update.effective_user, 
        user_to_warn, 
        reason
    )
    
    warning_message = (
        f"⚠️ {user_to_warn.mention_html()} has been warned ({current_warns}/{warn_limit}).\n"
        f"Reason: {reason}"
    )
    
    # Check if user reached warn limit
    if current_warns >= warn_limit:
        warning_message += f"\n\n🚫 User has reached the warning limit. Taking action: {warn_action}"
        
        # Reset warns
        context.chat_data["warns"][user_id_str]["count"] = 0
        
        # Take action based on settings
        if warn_action == "mute":
            # Mute for 1 day
            permissions = ChatPermissions(can_send_messages=False)
            duration = timedelta(days=1)
            until_date = update.message.date + duration
            
            await context.bot.restrict_chat_member(
                chat_id, user_to_warn.id, permissions=permissions, until_date=until_date
            )
            
            warning_message += f"\nMuted for {format_time_delta(duration)}."
            
        elif warn_action == "kick":
            await context.bot.ban_chat_member(chat_id, user_to_warn.id)
            await context.bot.unban_chat_member(chat_id, user_to_warn.id)
            warning_message += "\nUser has been kicked."
            
        elif warn_action == "ban":
            await context.bot.ban_chat_member(chat_id, user_to_warn.id)
            warning_message += "\nUser has been banned."
    
    await update.message.reply_text(warning_message, parse_mode=ParseMode.HTML)

# Remove warn
async def unwarn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❗ Please reply to the user you want to remove a warning from.")
        return
    
    user: User = update.message.reply_to_message.from_user
    user_id_str = str(user.id)
    
    if "warns" not in context.chat_data or user_id_str not in context.chat_data["warns"]:
        await update.message.reply_text(f"User {user.mention_html()} has no warnings.", parse_mode=ParseMode.HTML)
        return
    
    reason = " ".join(context.args) if context.args else "No reason provided"
    
    # Reduce warn count
    if context.chat_data["warns"][user_id_str]["count"] > 0:
        context.chat_data["warns"][user_id_str]["count"] -= 1
    
    current_warns = context.chat_data["warns"][user_id_str]["count"]
    
    await log_action(
        context, 
        "UNWARN", 
        update.effective_user, 
        user, 
        reason
    )
    
    await update.message.reply_text(
        f"✅ Removed warning from {user.mention_html()}. "
        f"Current warnings: {current_warns}\n"
        f"Reason: {reason}",
        parse_mode=ParseMode.HTML
    )

# Check warns
async def warns_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message.reply_to_message:
        # Check own warns if not replying
        user = update.effective_user
    else:
        user = update.message.reply_to_message.from_user
    
    user_id_str = str(user.id)
    
    if "warns" not in context.chat_data or user_id_str not in context.chat_data["warns"]:
        await update.message.reply_text(f"{user.mention_html()} has no warnings.", parse_mode=ParseMode.HTML)
        return
    
    warn_data = context.chat_data["warns"][user_id_str]
    warn_count = warn_data["count"]
    warn_limit = context.bot_data.get("WARN_LIMIT", 3)
    
    if warn_count == 0:
        await update.message.reply_text(f"{user.mention_html()} has no warnings.", parse_mode=ParseMode.HTML)
        return
    
    message = f"⚠️ {user.mention_html()} has {warn_count}/{warn_limit} warnings:\n\n"
    
    for i, reason in enumerate(warn_data["reasons"][-warn_count:], 1):
        message += f"{i}. {reason}\n"
    
    await update.message.reply_text(message, parse_mode=ParseMode.HTML)

# Reset all warns for a user
async def resetwarns_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❗ Please reply to the user whose warnings you want to reset.")
        return
    
    user: User = update.message.reply_to_message.from_user
    user_id_str = str(user.id)
    
    if "warns" not in context.chat_data or user_id_str not in context.chat_data["warns"]:
        await update.message.reply_text(f"{user.mention_html()} has no warnings.", parse_mode=ParseMode.HTML)
        return
    
    reason = " ".join(context.args) if context.args else "No reason provided"
    
    # Reset warns
    old_count = context.chat_data["warns"][user_id_str]["count"]
    context.chat_data["warns"][user_id_str]["count"] = 0
    context.chat_data["warns"][user_id_str]["reasons"] = []
    
    await log_action(
        context, 
        "RESETWARNS", 
        update.effective_user, 
        user, 
        reason
    )
    
    await update.message.reply_text(
        f"✅ Reset all warnings for {user.mention_html()}. "
        f"Previous warning count: {old_count}\n"
        f"Reason: {reason}",
        parse_mode=ParseMode.HTML
    )

# Temporary ban (tban)
async def tban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❗ Please reply to the user you want to temporarily ban.")
        return
    
    user_to_ban: User = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    
    # Check if we're trying to ban an admin
    try:
        member = await context.bot.get_chat_member(chat_id, user_to_ban.id)
        if member.status in ['administrator', 'creator']:
            await update.message.reply_text("❌ I can't ban administrators or the chat creator.")
            return
    except Exception as e:
        await update.message.reply_text(f"Error checking user status: {e}")
        return
    
    # Parse duration and reason
    if not context.args:
        await update.message.reply_text("❗ Please specify a ban duration (e.g., 1d, 6h, 30m).")
        return
    
    duration_str = context.args[0]
    parsed_duration = parse_duration(duration_str)
    
    if parsed_duration is None:
        await update.message.reply_text("⏱️ Invalid duration format. Examples: 30m, 1h, 1h30m, 1d")
        return
    
    duration = parsed_duration
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
    
    until_date = update.message.date + duration
    
    try:
        await context.bot.ban_chat_member(chat_id, user_to_ban.id, until_date=until_date)
        
        await log_action(
            context, 
            "TEMPBAN", 
            update.effective_user, 
            user_to_ban, 
            reason,
            duration
        )
        
        await update.message.reply_text(
            f"⏱️ Temporarily banned {user_to_ban.mention_html()} for {format_time_delta(duration)}.\n"
            f"Reason: {reason}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await update.message.reply_text(f"Failed to ban user: {e}")



# Set chat title
async def settitle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("❗ Please provide a new title for the chat.")
        return
    
    chat_id = update.effective_chat.id
    new_title = " ".join(context.args)
    
    try:
        await context.bot.set_chat_title(chat_id, new_title)
        await update.message.reply_text(f"✅ Chat title changed to: {new_title}")
    except Exception as e:
        await update.message.reply_text(f"Failed to set chat title: {e}")

# Set chat description
async def setdesc_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("❗ Please provide a new description for the chat.")
        return
    
    chat_id = update.effective_chat.id
    new_description = " ".join(context.args)
    
    try:
        await context.bot.set_chat_description(chat_id, new_description)
        await update.message.reply_text("✅ Chat description updated successfully!")
    except Exception as e:
        await update.message.reply_text(f"Failed to set chat description: {e}")

# Slowmode
async def slowmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if not context.args:
        await update.message.reply_text(
            "❗ Please specify the slowmode delay in seconds, or 0 to disable.\n\n"
            "Example: /slowmode 10"
        )
        return
    
    try:
        delay = int(context.args[0])
        if delay < 0 or delay > 6 * 60 * 60:  # Max 6 hours allowed by Telegram
            await update.message.reply_text("❗ Delay must be between 0 and 21600 seconds (6 hours).")
            return
        
        await context.bot.set_chat_slow_mode_delay(chat_id, delay)
        
        if delay == 0:
            await update.message.reply_text("⏱️ Slow mode disabled.")
        else:
            await update.message.reply_text(f"⏱️ Slow mode set to {delay} seconds.")
    except ValueError:
        await update.message.reply_text("❗ Please provide a valid number for delay.")
    except Exception as e:
        await update.message.reply_text(f"Failed to set slow mode: {e}")

# Lock/unlock chat permissions
async def lock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if not context.args:
        await update.message.reply_text(
            "❗ Please specify what to lock. Options:\n"
            "- all: Lock all permissions\n"
            "- messages: Lock sending messages\n"
            "- media: Lock sending media\n"
            "- polls: Lock creating polls\n"
            "- links: Lock web page previews\n"
            "- invite: Lock inviting users\n"
            "- pin: Lock pinning messages\n"
            "- info: Lock changing info"
        )
        return
    
    lock_type = context.args[0].lower()
    
    # Default - all permissions are allowed
    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_add_web_page_previews=True,
        can_invite_users=True,
        can_pin_messages=True,
        can_change_info=True
    )
    
    success_msg = "🔒 Locked "
    
    if lock_type == "all":
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_add_web_page_previews=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_change_info=False
        )
        success_msg += "all permissions."
    
    elif lock_type == "messages":
        permissions.can_send_messages = False
        success_msg += "sending messages."
    
    elif lock_type == "media":
        permissions.can_send_media_messages = False
        success_msg += "sending media."
    
    elif lock_type == "polls":
        permissions.can_send_polls = False
        success_msg += "creating polls."
    
    elif lock_type == "links":
        permissions.can_add_web_page_previews = False
        success_msg += "web page previews."
    
    elif lock_type == "invite":
        permissions.can_invite_users = False
        success_msg += "inviting users."
    
    elif lock_type == "pin":
        permissions.can_pin_messages = False
        success_msg += "pinning messages."
    
    elif lock_type == "info":
        permissions.can_change_info = False
        success_msg += "changing chat info."
    
    else:
        await update.message.reply_text("❗ Unknown lock type.")
        return
    
    try:
        await context.bot.set_chat_permissions(chat_id, permissions)
        await update.message.reply_text(success_msg)
    except Exception as e:
        await update.message.reply_text(f"Failed to lock chat permissions: {e}")

# Unlock command
async def unlock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    chat_id = update.effective_chat.id
    
    if not context.args:
        await update.message.reply_text(
            "❗ Please specify what to unlock. Options:\n"
            "- all: Unlock all permissions\n"
            "- messages: Unlock sending messages\n"
            "- media: Unlock sending media\n"
            "- polls: Unlock creating polls\n"
            "- links: Unlock web page previews\n"
            "- invite: Unlock inviting users\n"
            "- pin: Unlock pinning messages\n"
            "- info: Unlock changing info"
        )
        return
    
    unlock_type = context.args[0].lower()
    
    try:
        # Get current permissions
        current_permissions = (await context.bot.get_chat(chat_id)).permissions
        
        # Create new permissions object based on the current one
        new_permissions = ChatPermissions(
            can_send_messages=current_permissions.can_send_messages,
            can_send_media_messages=current_permissions.can_send_media_messages,
            can_send_polls=current_permissions.can_send_polls,
            can_add_web_page_previews=current_permissions.can_add_web_page_previews,
            can_invite_users=current_permissions.can_invite_users,
            can_pin_messages=current_permissions.can_pin_messages,
            can_change_info=current_permissions.can_change_info
        )
        
        success_msg = "🔓 Unlocked "
        
        if unlock_type == "all":
            new_permissions = ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_add_web_page_previews=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_change_info=True
            )
            success_msg += "all permissions."
        
        elif unlock_type == "messages":
            new_permissions.can_send_messages = True
            success_msg += "sending messages."
        
        elif unlock_type == "media":
            new_permissions.can_send_media_messages = True
            success_msg += "sending media."
        
        elif unlock_type == "polls":
            new_permissions.can_send_polls = True
            success_msg += "creating polls."
        
        elif unlock_type == "links":
            new_permissions.can_add_web_page_previews = True
            success_msg += "web page previews."
        
        elif unlock_type == "invite":
            new_permissions.can_invite_users = True
            success_msg += "inviting users."
        
        elif unlock_type == "pin":
            new_permissions.can_pin_messages = True
            success_msg += "pinning messages."
        
        elif unlock_type == "info":
            new_permissions.can_change_info = True
            success_msg += "changing chat info."
        
        else:
            await update.message.reply_text("❗ Unknown unlock type.")
            return
        
        await context.bot.set_chat_permissions(chat_id, new_permissions)
        await update.message.reply_text(success_msg)
    except Exception as e:
        await update.message.reply_text(f"Failed to unlock chat permissions: {e}")

# Command to set warn limit and action
async def setwarnlimit_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❗ Please specify the number of warnings before action is taken.\n\n"
            "Example: /setwarnlimit 3"
        )
        return
    
    try:
        limit = int(context.args[0])
        if limit < 1:
            await update.message.reply_text("❗ Warn limit must be at least 1.")
            return
        
        context.bot_data["WARN_LIMIT"] = limit
        await update.message.reply_text(f"✅ Warning limit set to {limit}.")
    except ValueError:
        await update.message.reply_text("❗ Please provide a valid number for the warning limit.")

# Command to set warn action
async def setwarnaction_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❗ Please specify the action to take when the warn limit is reached.\n\n"
            "Options: mute, kick, ban\n"
            "Example: /setwarnaction mute"
        )
        return
    
    action = context.args[0].lower()
    if action not in ["mute", "kick", "ban"]:
        await update.message.reply_text("❗ Invalid action. Please choose from: mute, kick, ban")
        return
    
    context.bot_data["WARN_ACTION"] = action
    await update.message.reply_text(f"✅ Warning action set to: {action}")

# Set log channel
async def setlog_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ You don't have permission to use this command.")
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❗ Please specify the channel ID or username for logging.\n\n"
            "Example: /setlog -1001234567890\n"
            "Or: /setlog @channel_username"
        )
        return
    
    log_channel = context.args[0]
    
    # Try to send a test message to the channel
    try:
        test_msg = await context.bot.send_message(
            chat_id=log_channel,
            text="🔶 <b>Test Moderation Log</b> 🔶\n\nThis channel is now set to receive moderation logs.",
            parse_mode=ParseMode.HTML
        )
        
        # If successful, set the log channel
        context.bot_data["MOD_LOG_CHANNEL"] = log_channel
        await update.message.reply_text(f"✅ Log channel set successfully! Test message sent.")
    except Exception as e:
        await update.message.reply_text(f"Failed to set log channel: {e}\n\nMake sure the bot is an admin in the channel.")

# Help command for moderation
async def modhelp_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "<b>🛡️ Moderation Commands:</b>\n\n"
        "• /mute [duration] [reason] - Mute a user\n"
        "• /unmute [reason] - Unmute a user\n"
        "• /kick [reason] - Kick a user from the group\n"
        "• /ban [reason] - Ban a user from the group\n"
        "• /unban [user_id] [reason] - Unban a user\n"
        "• /tban [duration] [reason] - Temporarily ban a user\n"
        "• /warn [reason] - Warn a user\n"
        "• /unwarn [reason] - Remove a warning from a user\n"
        "• /warns - Check warnings for a user\n"
        "• /resetwarns [reason] - Reset all warnings for a user\n"
        "• /purge - Delete all messages between the command and replied message\n"
        "• /pin [silent] - Pin a message (add 'silent' for no notification)\n"
        "• /unpin - Unpin a specific message or the most recent one\n"
        "• /unpinall - Unpin all messages in the chat\n"
        "• /settitle [new title] - Change the chat title\n"
        "• /setdesc [new description] - Change the chat description\n"
        "• /slowmode [seconds] - Set slow mode delay (0 to disable)\n"
        "• /lock [type] - Lock specific chat permissions\n"
        "• /unlock [type] - Unlock specific chat permissions\n"
        "• /setwarnlimit [number] - Set the warning limit\n"
        "• /setwarnaction [action] - Set action when warn limit is reached\n"
        "• /setlog [channel] - Set channel for moderation logs\n\n"
        "<i>For more details on each command, use /modhelp [command] (e.g., /modhelp mute)</i>"
    )
    
    if context.args:
        # Show help for a specific command
        command = context.args[0].lower().strip("/")
        
        if command == "mute":
            specific_help = (
                "<b>Command:</b> /mute\n"
                "<b>Usage:</b> /mute [duration] [reason]\n\n"
                "<b>Examples:</b>\n"
                "• /mute - Mute for 1 hour (default)\n"
                "• /mute 30m Spamming - Mute for 30 minutes with reason\n"
                "• /mute 2h Inappropriate content - Mute for 2 hours\n"
                "• /mute 1d Breaking rules - Mute for 1 day\n\n"
                "<b>Duration format:</b>\n"
                "• m = minutes (e.g., 30m)\n"
                "• h = hours (e.g., 2h)\n"
                "• d = days (e.g., 1d)\n"
                "• Can combine: 1d6h = 1 day and 6 hours"
            )
        elif command == "tban":
            specific_help = (
                "<b>Command:</b> /tban\n"
                "<b>Usage:</b> /tban [duration] [reason]\n\n"
                "<b>Examples:</b>\n"
                "• /tban 2h - Ban for 2 hours\n"
                "• /tban 1d Spamming - Ban for 1 day with reason\n"
                "• /tban 7d Repeated violations - Ban for 7 days\n\n"
                "<b>Duration format:</b>\n"
                "• m = minutes (e.g., 30m)\n"
                "• h = hours (e.g., 2h)\n"
                "• d = days (e.g., 1d)\n"
                "• Can combine: 1d6h = 1 day and 6 hours"
            )
        elif command == "warn" or command == "warns":
            specific_help = (
                "<b>Warning System:</b>\n\n"
                "<b>Commands:</b>\n"
                "• /warn [reason] - Add a warning to a user\n"
                "• /unwarn [reason] - Remove a warning\n"
                "• /warns - Check warnings for a user\n"
                "• /resetwarns [reason] - Reset all warnings\n"
                "• /setwarnlimit [number] - Set warning limit (default: 3)\n"
                "• /setwarnaction [action] - Set action when limit reached\n\n"
                "<b>Actions:</b> mute (1 day), kick, ban"
            )
        elif command == "lock" or command == "unlock":
            specific_help = (
                "<b>Commands:</b> /lock and /unlock\n"
                "<b>Usage:</b> /lock [type] or /unlock [type]\n\n"
                "<b>Lock types:</b>\n"
                "• all - All permissions\n"
                "• messages - Sending messages\n"
                "• media - Sending media\n"
                "• polls - Creating polls\n"
                "• links - Web page previews\n"
                "• invite - Inviting users\n"
                "• pin - Pinning messages\n"
                "• info - Changing info\n\n"
                "<b>Examples:</b>\n"
                "• /lock all - Lock all permissions\n"
                "• /lock media - Lock sending media only\n"
                "• /unlock messages - Allow sending messages"
            )
        else:
            specific_help = "Detailed help for this command is not available."
        
        await update.message.reply_text(specific_help, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

# Register all moderation commands
def register_moderation_handlers(app):
    # Basic moderation
    app.add_handler(CommandHandler("mute", mute_command))
    app.add_handler(CommandHandler("unmute", unmute_command))
    app.add_handler(CommandHandler("kick", kick_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("unban", unban_command))
    app.add_handler(CommandHandler("tban", tban_command))
    
    # Warn system
    app.add_handler(CommandHandler("warn", warn_command))
    app.add_handler(CommandHandler("unwarn", unwarn_command))
    app.add_handler(CommandHandler("warns", warns_command))
    app.add_handler(CommandHandler("resetwarns", resetwarns_command))
    app.add_handler(CommandHandler("setwarnlimit", setwarnlimit_command))
    app.add_handler(CommandHandler("setwarnaction", setwarnaction_command))
      
    # Chat settings
    app.add_handler(CommandHandler("settitle", settitle_command))
    app.add_handler(CommandHandler("setdesc", setdesc_command))
    app.add_handler(CommandHandler("slowmode", slowmode_command))
    app.add_handler(CommandHandler("lock", lock_command))
    app.add_handler(CommandHandler("unlock", unlock_command))
    app.add_handler(CommandHandler("setlog", setlog_command))
    
    # Help
    app.add_handler(CommandHandler("modhelp", modhelp_command))