import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Database Configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'alarm_bot.db')

# Bot Configuration
MAX_TIMER_DURATION = 86400  # Maximum timer duration (24 hours in seconds)
MIN_TIMER_DURATION = 1  # Minimum timer duration (1 second)