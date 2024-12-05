# Alarm BOT
Tugas Alarm Bot + SQL

## About
- Tugas ini menggunakan [pytelegrambot](https://github.com/python-telegram-bot/python-telegram-bot/) dan [sqlite](https://github.com/sqlite/sqlite)

## Instalasi
```bash
# Clone dulu
git clone https://github.com/alfarez/alarm_bot.git

# Buat path .venv agar tidak mempengaruhi projek lain
python -m venv .venv

# Install Dependensi
pip install -r requirement.txt

```
## File .env (Workspace Data)
- Buat file .env dalam root folder kalian
```notepad .env / touch .env / echo "PROJEK A" >> .env```
- pastiin buat token di [botfather](https://t.me/BotFather) dan daftarkan id bot nya di .env ```TELEGRAM_BOT_TOKEN=xxxx```
- database nya menggunakan sqlite3 karena lebih simple

## Running
```bash
python bot.py
```

## Command
- ```/start``` inisialisasi user ke db
- ```/set``` membuat waktu alarm dalam satuan detik serta menyimpan data username, id , waktu ke db
- ```/history``` melihat alarm yang pernah di set sebelumnya
