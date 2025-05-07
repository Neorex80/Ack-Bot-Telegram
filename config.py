DEVELOPERS = [7985094672]  # Replace with your Telegram user ID

# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = 7985094672

# Directory structure
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Bot settings
BOT_NAME = os.getenv("BOT_NAME", "TelegramHelperBot")
BOT_VERSION = "1.0.7"

# Feature flags
ENABLE_WELCOME_MESSAGES = True
ENABLE_MODERATION = True
ENABLE_AFK_TRACKING = True

# Timeouts and limits
COMMAND_TIMEOUT = 60  # seconds
FLOOD_LIMIT = 5  # messages per minute