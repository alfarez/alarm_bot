# Alarm BOT
Tugas Alarm Bot + SQL

## About
- Tugas ini menggunakan [pytelegrambot](https://github.com/python-telegram-bot/python-telegram-bot/) dan Mysql XAMPP

## Instalasi
```bash
# Clone dulu
git clone https://github.com/alfarez/alarm_bot.git

# Buat path .venv agar tidak mempengaruhi projek lain
python -m venv .venv

# Install Dependensi
pip install -r req.txt

```
## File .env (Workspace Data)
- Buat file .env dalam root folder
```notepad .env / touch .env```
- pastiin buat token di [botfather](https://t.me/BotFather) dan daftarkan id bot nya di .env ```TELEGRAM_BOT_TOKEN=xxxx```
- daftarkan mysql kalian di .env ```DATABASE_URL=mysql://user:pass@ip_lokal:port_db/nama_db```

## Running
```bash
python main.py
```

## Command
- ```/start``` inisialisasi user ke db dan buat alarm dan record dengan user tertentu
- ```/stop``` hapus semua alarm dan menjadikan user tidak aktif
- ```/status``` melihat alarm aktif