from telegram import Update
from telegram.constants import ChatMemberStatus

async def is_user_admin(update: Update) -> bool:
    user_id = update.effective_user.id
    chat = update.effective_chat

    # Fetch list of chat administrators
    chat_admins = await chat.get_administrators()
    admin_ids = [admin.user.id for admin in chat_admins]

    return user_id in admin_ids

async def require_admin(update: Update, context, command_name: str = "") -> bool:
    if not await is_user_admin(update):
        await update.message.reply_text(
            f"😼 Oops! You need to be an *admin* to use `{command_name}`.\n"
            "Nice try though. I'll make sure the real admins hear about this... maybe. 😼",
            parse_mode="Markdown"
        )
        return False
    return True
