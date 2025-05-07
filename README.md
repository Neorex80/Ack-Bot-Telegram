# Telegram Bot Framework

A robust and extensible Telegram bot framework with built-in admin features, group tracking, and moderation tools.

## Features

- **Group Tracking**: Automatically tracks and manages groups the bot is a member of
- **Sudo Admin System**: Delegate bot management to trusted users
- **Developer Commands**: Powerful tools for bot management and maintenance
- **Permission System**: Granular control over command access
- **Moderation Tools**: Keep your groups safe and clean
- **Automatic Restart Handling**: Bot can gracefully restart and notify when it's back online

## Setup

1. Clone the repository
2. Create a `.env` file with the following variables:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ADMIN_USER_ID=your_telegram_id_here
   CAT_API_KEY=your_catsite_api_key
   ```
3. Install dependencies: `pip install -r requirements.txt`
4. Run the bot: `python bot.py`

## Developer Commands

| Command | Description | Permission |
|---------|-------------|------------|
| `/sudo_add <user_id> [name]` | Add a user as sudo admin | BOT_OWNER |
| `/sudo_remove <user_id>` | Remove a sudo admin | BOT_OWNER |
| `/sudo_list` | List all sudo admins | BOT_OWNER |
| `/broadcast <message>` | Send message to all groups | BOT_OWNER |
| `/stats` | Show bot statistics | BOT_OWNER |
| `/maintenance` | Toggle maintenance mode | BOT_OWNER |
| `/shutdown` | Shut down the bot | BOT_OWNER |
| `/restart` | Restart the bot | BOT_OWNER |
| `/update_groups` | Verify group memberships | BOT_OWNER |

## Permission Levels

The bot uses a hierarchical permission system:

1. **EVERYONE**: Anyone can use these commands
2. **MEMBERS**: Only confirmed group members
3. **ADMINS**: Only group administrators
4. **BOT_ADMIN**: Only when bot is an admin in the group
5. **SUDO_ADMIN**: Only users with sudo admin privileges
6. **BOT_OWNER**: Only the bot owner

## Directory Structure

```
.
├── bot.py              # Main bot entry point
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── commands/           # Command modules
│   ├── __init__.py     # Command registry
│   ├── afk.py          # AFK status commands
│   ├── cat.py          # Cat picture commands
│   ├── dev.py          # Developer commands
│   ├── lock.py         # Chat locking commands
│   ├── message.py      # Message handling
│   ├── moderation.py   # Moderation tools
│   └── tools.py        # Utility tools
├── events/             # Event handlers
│   ├── __init__.py     # Event registry
│   └── welcome.py      # Welcome message handler
├── utils/              # Utility functions
│   ├── __init__.py     # Utilities registry
│   ├── admin_check.py  # Admin verification
│   ├── helpers.py      # Helper functions
│   └── permissions.py  # Permission system
└── data/               # Data storage
    ├── groups.json     # Group tracking data
    └── sudo_admins.json # Sudo admins list
```

## Adding Commands

To add a new command module:

1. Create a new file in the `commands/` directory
2. Define your command handlers with the appropriate permission decorators
3. Add a `register_*_handler(app)` function to register your commands
4. Import and call your registration function in `commands/__init__.py`

Example:

```python
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from utils.permissions import require_permission, Permission

@require_permission(Permission.ADMINS)
async def my_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("This is a custom command!")

def register_my_handler(app):
    app.add_handler(CommandHandler("mycommand", my_command))
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
