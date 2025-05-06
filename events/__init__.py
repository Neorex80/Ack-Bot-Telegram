from telegram.ext import ChatMemberHandler
from events.welcome import welcome_new_member

def register_all_handlers(app):
    app.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))
