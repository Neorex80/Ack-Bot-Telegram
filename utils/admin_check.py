from typing import Optional, List, Union
from telegram import Update, Chat, User, ChatMember
from telegram.ext import ContextTypes
from telegram.error import TelegramError
from telegram.constants import ChatType

import logging
logger = logging.getLogger(__name__)

async def is_user_admin(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    silent: bool = False
) -> bool:
    """
    Check if the user is an admin in the current group.
    
    Args:
        update: The update object from Telegram
        context: The context object from the handler
        silent: If True, no messages will be sent to the chat
        
    Returns:
        bool: True if the user is an admin, False otherwise
    """
    chat = update.effective_chat
    user = update.effective_user
    
    # Handle None values (could happen in callbacks or other update types)
    if not chat or not user:
        logger.warning("Missing chat or user in update")
        return False
    
    # Check if we're in a group chat
    if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        if not silent:
            await update.effective_message.reply_text("⚠️ This command can only be used in group chats.")
        return False
    
    try:
        # Get chat member and check admin status
        member = await context.bot.get_chat_member(chat.id, user.id)
        
        # Check admin status
        if member.status in ["administrator", "creator"]:
            return True
        
        # User is not an admin
        if not silent:
            await update.effective_message.reply_text("🚫 Only admins can use this command!")
        return False
        
    except TelegramError as e:
        logger.error(f"Admin check error: {e}")
        if not silent:
            await update.effective_message.reply_text("❌ Couldn't verify admin status. Try again later.")
        return False

async def get_chat_admins(
    context: ContextTypes.DEFAULT_TYPE, 
    chat_id: Union[str, int]
) -> List[ChatMember]:
    """
    Get a list of all admins in a chat.
    
    Args:
        context: The context object from the handler
        chat_id: The ID of the chat
        
    Returns:
        list: List of ChatMember objects who are admins in the chat
    """
    try:
        admins = await context.bot.get_chat_administrators(chat_id)
        return admins
    except TelegramError as e:
        logger.error(f"Error getting chat admins: {e}")
        return []

async def is_bot_admin(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: Union[str, int]
) -> bool:
    """
    Check if the bot has admin privileges in the specified chat.
    
    Args:
        context: The context object from the handler
        chat_id: The ID of the chat to check
        
    Returns:
        bool: True if the bot is an admin, False otherwise
    """
    try:
        bot_id = context.bot.id
        member = await context.bot.get_chat_member(chat_id, bot_id)
        return member.status in ["administrator", "creator"]
    except TelegramError as e:
        logger.error(f"Error checking bot admin status: {e}")
        return False