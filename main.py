# main.py
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
import logging
import os
from src.alarm import setup_database, start, stop, cek_status_alarm, check_alarm_time, button
from dotenv import load_dotenv

# Load dotenv file
load_dotenv(".env")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main():
    try:
        # set-up db
        setup_database()

        # load .env
        token = os.getenv('TELEGRAM_BOT_TOKEN')

        # Initialize application builder
        app = (
            ApplicationBuilder()
            .token(token)
            .build()
        )

        # Add command handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("stop", stop))
        app.add_handler(CommandHandler("status", cek_status_alarm))
        app.add_handler(CallbackQueryHandler(button))

        # buat job_queue
        job_queue = app.job_queue

        # run berkala buat ngecek dalam db
        job_queue.run_repeating(check_alarm_time, interval=60, first=0)  # interval dalam detik

        # run bot sampe di abort user
        app.run_polling(drop_pending_updates=True)

    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
