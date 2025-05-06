# File: commands/__init__.py
from .afk import register_all_handlers as register_afk
from .tools import register_tools_handler
from .cat import register_cat_handler  


def register_all_handlers(app):
    register_afk(app)
    register_tools_handler(app)
    register_cat_handler(app) 
 