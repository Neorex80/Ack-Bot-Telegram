# File: commands/__init__.py
from .afk import register_all_handlers as register_afk
from .tools import register_tools_handler
from .cat import register_cat_handler
from .lock import register_lock_handler
from .dev import register_dev_handler
from .message import register_message_handler
from .moderation import register_moderation_handlers



def register_all_handlers(app):
    register_afk(app)
    register_tools_handler(app)
    register_cat_handler(app)
    register_lock_handler(app)
    register_dev_handler(app)
    register_message_handler(app)
    register_moderation_handlers(app)