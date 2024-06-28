import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import logging
import mysql.connector
from mysql.connector import pooling
import os
from urllib.parse import urlparse

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

db_url = os.getenv('DATABASE_URL')
url = urlparse(db_url)
db_config = {
    'host': url.hostname,
    'port': url.port,
    'user': url.username,
    'password': url.password
}

# Buat Pooling DB
cnxpool = pooling.MySQLConnectionPool(pool_name="mypool",
                                      pool_size=5,
                                      **db_config)

def connect_db():
    try:
        conn = cnxpool.get_connection()
        logger.info("Terhubung ke db MySQL lewat pool.")
        return conn
    except mysql.connector.Error as err:
        logger.error(f"Error koneksi ke MySQL: {err}")
        raise

def setup_database():
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS telegram_bot")
        cursor.execute("USE telegram_bot")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                telegram_id INT NOT NULL UNIQUE,
                username VARCHAR(255),
                active BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alarms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                time TIME NOT NULL,
                status ENUM('PENDING', 'OK', 'MISSED') DEFAULT 'PENDING',
                message_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()
        logger.info("Database 'telegram_bot' dan tabel 'users' serta 'alarms' sudah dibuat atau sudah ada.")
    except mysql.connector.Error as err:
        logger.error(f"error setting database: {err}")
    finally:
        cursor.close()
        conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"User {user.id} start bot dengan username {user.username}.")
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("USE telegram_bot")

        cursor.execute(
            "INSERT INTO users (telegram_id, username, active) VALUES (%s, %s, TRUE) "
            "ON DUPLICATE KEY UPDATE username = VALUES(username), active = TRUE",
            (user.id, user.username)
        )

        context.user_data[user.id] = {'alarm_active': True}

        cursor.execute(
            "SELECT time FROM alarms WHERE user_id = (SELECT id FROM users WHERE telegram_id = %s) AND status = 'PENDING'",
            (user.id,)
        )
        active_alarm_times = [str(row[0]) for row in cursor.fetchall()]

        if active_alarm_times:
            await update.message.reply_text(
                f'Anda memiliki alarm aktif di jam : {", ".join(active_alarm_times)}.'
            )
            logger.info(f"User {user.id} memiliki alarm Pending pada jam : {', '.join(active_alarm_times)}.")

        else:
            alarm_times = ['08:00', '12:00', '15:00']
            reminder_message = await update.message.reply_text(
                'Pengingat alarm diaktifkan!\nAnda akan menerima pengingat pada jam 08:00, 12:00, dan 15:00.'
            )
            message_id = reminder_message.message_id
            for time in alarm_times:
                cursor.execute(
                    "INSERT INTO alarms (user_id, time, status, message_id, created_at) VALUES ((SELECT id FROM users WHERE telegram_id = %s), %s, 'PENDING', %s, CURRENT_TIMESTAMP())",
                    (user.id, time, message_id)
                )
                conn.commit()
                logger.info(f"User {user.id} terdaftar untuk pengingat alarm pada jam {time}.")

    except mysql.connector.Error as err:
        logger.error(f"Error perintah /start: {err}")
    finally:
        cursor.close()
        conn.close()

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"User {user.id} stop bot.")
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("USE telegram_bot")

        cursor.execute(
            "DELETE FROM alarms WHERE user_id = (SELECT id FROM users WHERE telegram_id = %s)",
            (user.id,)
        )

        cursor.execute(
            "UPDATE users SET active = FALSE WHERE telegram_id = %s",
            (user.id,)
        )
        conn.commit()

        if user.id in context.user_data:
            del context.user_data[user.id]

        cursor.execute(
            "SELECT COUNT(*) FROM alarms WHERE user_id = (SELECT id FROM users WHERE telegram_id = %s)",
            (user.id,)
        )
        result = cursor.fetchone()

        if result[0] > 0:
            await update.message.reply_text(
                'Pengingat alarm di matikan dan semua alarm sudah dihapus.'
            )
        else:
            await update.message.reply_text(
                'Pengingat: alarm di matikan dan gak ada alarm aktif ditemukan.'
            )

        logger.info(f"User {user.id} menonaktifkan pengingat alarm dan menghapus semua alarm.")

    except mysql.connector.Error as err:
        logger.error(f"Error perintah /stop: {err}")
    finally:
        cursor.close()
        conn.close()

async def cek_status_alarm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("USE telegram_bot")

        cursor.execute(
            "SELECT COUNT(*) FROM alarms WHERE user_id = (SELECT id FROM users WHERE telegram_id = %s)",
            (user.id,)
        )
        total_alarms = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM alarms WHERE user_id = (SELECT id FROM users WHERE telegram_id = %s) AND status = 'OK'",
            (user.id,)
        )
        ok_alarms = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM alarms WHERE user_id = (SELECT id FROM users WHERE telegram_id = %s) AND status = 'MISSED'",
            (user.id,)
        )
        missed_alarms = cursor.fetchone()[0]

        await update.message.reply_text(
            f"Total alarm terkirim: {total_alarms}\nAlarm OK dilaporkan: {ok_alarms}\nAlarm terlewat: {missed_alarms}"
        )

    except mysql.connector.Error as err:
        logger.error(f"Error mengambil statistik alarm: {err}")
    finally:
        cursor.close()
        conn.close()

async def check_alarm_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("USE telegram_bot")
    try:
        jam_sekarang = datetime.now().strftime('%H:%M:%S')
        logger.info(f"ngecek alarm jam sekarang : {jam_sekarang}")
        
        # ambil alarm "PENDING" dan bandingkan dengan waktu sekarang
        cursor.execute(
            "SELECT id, user_id, time, message_id FROM alarms WHERE status = 'PENDING' AND time = %s",
            (jam_sekarang,)
        )
        notif_alarm = cursor.fetchall()

        for alarm in notif_alarm:
            alarm_id, user_id, alarm_time, pesan.id = alarm
            logger.info(f"Alarm ditemukan: ID={alarm_id}, UserID={user_id}, Waktu={alarm_time}")
            
            # ambil telegram_id user
            cursor.execute(
                "SELECT telegram_id FROM users WHERE id = %s",
                (user_id,)
            )
            telegram_id = cursor.fetchone()[0]
            
            # Kirim pesan ke user dengan inline keyboard
            pesan = await context.bot.send_message(telegram_id, f'Waktu alarm {alarm_time} telah tercapai!')
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("OK", callback_data=f"confirm_{alarm_id}")]])
            await pesan.reply_text("Konfirmasi Alarm?", reply_markup=keyboard)
            logger.info(f"ngirim pesan ke user {telegram_id} alarm id {alarm_id}")

            # jadwalkan job untuk menandai sebagai "MISSEd" jika ga ada konfirmasi selama 15 menit
            context.job_queue.run_once(
                lambda ctx: mark_as_missed(ctx, alarm_id, pesan.message_id, telegram_id),
                timedelta(minutes=15) # satuan dalam timedelta
            )

    except mysql.connector.Error as err:
        logger.error(f"Error check alarm disini: {err}")
    finally:
        cursor.close()
        conn.close()
        await asyncio.sleep(10)
        logger.info("Finished checking alarms")

async def mark_as_missed(context: ContextTypes, alarm_id: int, message_id: int, telegram_id: int) -> None:
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("USE telegram_bot")
    try:
        # cek alarm apakah masih "PENDING"
        cursor.execute(
            "SELECT status FROM alarms WHERE id = %s",
            (alarm_id,)
        )
        current_status = cursor.fetchone()[0]

        if current_status == 'PENDING':
            # Update status nya ke MISSED
            cursor.execute(
                "UPDATE alarms SET status = 'MISSED' WHERE id = %s",
                (alarm_id,)
            )
            conn.commit()
            logger.info(f"Alarm ID {alarm_id} ditandain 'MISSED' karena ga ada respon selama 15 menit.")
            
            # hapus pesan yang sudah terkirim ke user
            await context.bot.delete_message(chat_id=telegram_id, message_id=message_id)
            
    except mysql.connector.Error as err:
        logger.error(f"gagal membuat alarm: {err}")
    finally:
        cursor.close()
        conn.close()

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    logger.info(f"callback query: {query.data}")

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("USE telegram_bot")
    try:
        # parse alarm_id untuk callback_data
        alarm_id = int(query.data.split('_')[1])
        logger.info(f"handling konfirmasi untuk alarm_id : {alarm_id}")

        # update status ke ok
        cursor.execute(
            "UPDATE alarms SET status = 'OK' WHERE id = %s",
            (alarm_id,)
        )
        conn.commit()
        logger.info(f"Alarm ID {alarm_id} updated ke 'OK'")

        # kirim pesan konfirmasi
        await query.answer("Terima kasih! Alarm sudah dikonfirmasi.")
        await query.edit_message_reply_markup(reply_markup=None)
        
    except mysql.connector.Error as err:
        logger.error(f"Error handling: {err}")
        await query.answer("Maaf, terjadi kesalahan dalam memproses konfirmasi.")
    
    except Exception as e:
        logger.error(f"error!: {e}")
        await query.answer("Maaf, terjadi kesalahan.")

    finally:
        cursor.close()
        conn.close()
