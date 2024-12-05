import logging
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, JobQueue

# Import modul kustom
import config
import database

# Konfigurasi logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update) -> None:
    """
    Handler untuk perintah /start
    Menyapa pengguna dan menyimpan informasi pengguna ke database
    """
    user = update.effective_user
    if user is not None:
        # Simpan informasi pengguna ke database
        database.insert_or_update_user(
            telegram_user_id = user.id,
            username = user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        if update.message:
            await update.message.reply_text(
                f"Hai {user.first_name}! 👋\n"
                "Gunakan /set <detik> untuk mengatur alarm\n"
                "Gunakan /history untuk melihat riwayat timer"
                )
            
async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler untuk mengatur timer
    """
    if update.effective_message:
        chat_id = update.effective_message.chat_id
    user = update.effective_user
    try:
        # Ambil durasi timer dari argumen
        if context.args:
            due = float(context.args[0])
            
            # Validasi durasi timer
            if due < config.MIN_TIMER_DURATION:
                await update.effective_message.reply_text(
                    f"Maaf, timer minimal {config.MIN_TIMER_DURATION} detik!"
                )
                return
        
            if due > config.MAX_TIMER_DURATION:
                await update.effective_message.reply_text(
                    f"Maaf, timer maksimal {config.MAX_TIMER_DURATION} detik (24 jam)!"
                )
                return
        else:
            return
            
        # Simpan informasi timer ke database
        user_db_id = database.insert_or_update_user(
            telegram_user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        if user_db_id:
            database.insert_timer(user_db_id, due)
        
        # Jadwalkan alarm
        job_queue: JobQueue = context.application.job_queue
        job_queue.run_once(
            alarm,
            due,
            chat_id=chat_id,
            name=str(chat_id),
            data=due
        )
        
        await update.effective_message.reply_text(
            f"⏰ Timer berhasil diatur untuk {due} detik!"
        )
    
    except (IndexError, ValueError):
        await update.effective_message.reply_text(
            "Penggunaan: /set <detik>\n"
            "Contoh: /set 60 (untuk timer 60 detik)"
        )

async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Fungsi untuk mengirim pesan alarm
    """
    job = context.job
    if job:
        await context.bot.send_message(
            job.chat_id,
            text=f"⏰ Waktu habis! {job.data} detik telah berlalu."
        )

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Menampilkan riwayat timer pengguna
    """
    user = update.effective_user
    # Ambil riwayat timer
    timers = database.get_user_timers(user.id)
    
    if not timers:
        await update.message.reply_text("Anda belum punya riwayat timer.")
        return
    
    # Format pesan riwayat
    history_text = "📅 Riwayat Timer:\n\n"
    for timer in timers:
        history_text += f"⏱️ Durasi: {timer[1]} detik\n"
        history_text += f"🕒 Waktu: {timer[2]}\n\n"
    
    await update.message.reply_text(history_text)

def main() -> None:
    """
    Fungsi utama untuk menjalankan bot
    """
    # Buat aplikasi bot dengan job queue
    application = (Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .build())
    
    # Tambahkan handler untuk berbagai perintah
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_timer))
    application.add_handler(CommandHandler("history", history))
    
    # Jalankan bot
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()