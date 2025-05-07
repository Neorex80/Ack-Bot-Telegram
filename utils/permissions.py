# utils/permissions.py
from typing import Optional, Union, List
from enum import Enum
from telegram import Update, Chat
from telegram.ext import ContextTypes
from utils.admin_check import is_user_admin, is_bot_admin
import logging

logger = logging.getLogger(__name__)

class Permission(Enum):
    EVERYONE = 0       # Anyone can use
    MEMBERS = 1        # Only group members (not new joiners)
    ADMINS = 2         # Only group admins
    BOT_ADMIN = 3      # Only when bot is admin
    BOT_OWNER = 4      # Only the bot owner

class PermissionResult:
    def __init__(self, allowed: bool, reason: Optional[str] = None):
        self.allowed = allowed
        self.reason = reason

    def __repr__(self):
        return f"<PermissionResult allowed={self.allowed} reason={self.reason}>"

async def check_permissions(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    required_permission: Union[Permission, List[Permission]],
    silent: bool = False
) -> PermissionResult:
    chat: Optional[Chat] = update.effective_chat
    user = update.effective_user

    if not chat or not user:
        return PermissionResult(False, "Missing chat or user data")

    if isinstance(required_permission, list):
        for perm in required_permission:
            result = await check_permissions(update, context, perm, silent=True)
            if result.allowed:
                return PermissionResult(True)
        if not silent:
            await update.effective_message.reply_text("🚫 You don't have permission to use this command.")
        return PermissionResult(False, f"User lacks one of the required permissions: {[p.name for p in required_permission]}")

    # EVERYONE
    if required_permission == Permission.EVERYONE:
        return PermissionResult(True)

    # ADMINS or BOT_ADMIN
    if required_permission in [Permission.ADMINS, Permission.BOT_ADMIN]:
        is_admin = await is_user_admin(update, context, silent=True)
        if not is_admin:
            if not silent:
                await update.effective_message.reply_text("🚫 Only admins can use this command!")
            logger.info(f"Permission denied: user {user.id} is not admin in chat {chat.id}")
            return PermissionResult(False, "User is not an admin")

    # BOT_ADMIN
    if required_permission == Permission.BOT_ADMIN:
        bot_is_admin = await is_bot_admin(context, chat.id)
        if not bot_is_admin:
            if not silent:
                await update.effective_message.reply_text("⚠️ I need admin privileges to perform this action!")
            logger.info(f"Permission denied: bot is not admin in chat {chat.id}")
            return PermissionResult(False, "Bot is not an admin")

    # BOT_OWNER
    if required_permission == Permission.BOT_OWNER:
        try:
            from config import ADMIN_USER_ID
        except ImportError:
            logger.error("ADMIN_USER_ID not found in config")
            return PermissionResult(False, "Bot owner ID not configured")

        if not ADMIN_USER_ID:
            logger.warning("ADMIN_USER_ID is not set in config")
            return PermissionResult(False, "Bot owner ID not configured")

        if str(user.id) != str(ADMIN_USER_ID):
            if not silent:
                await update.effective_message.reply_text("🔒 This command is only for the bot owner.")
            logger.info(f"Permission denied: user {user.id} is not the bot owner")
            return PermissionResult(False, "User is not the bot owner")

    return PermissionResult(True)

def require_permission(permission_level: Union[Permission, List[Permission]]):
    def decorator(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            result = await check_permissions(update, context, permission_level)
            if result.allowed:
                return await func(update, context)
            return None
        return wrapper
    return decorator
