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
    import pyfiglet
    import telebot
    from telebot import types 
    from rich.console import Console
    from cfonts import render
    from bs4 import BeautifulSoup
    from user_agent import generate_user_agent
except ImportError:
    os.system("pip install requests pyTelegramBotAPI pyfiglet rich cfonts beautifulsoup4 user-agent flask")
    import requests
    import telebot
    from telebot import types

# --- CONFIGURATION & GLOBAL STATS ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = 5714613336
STATS = {
    "total_attempts": 0,
    "successful_resets": 0,
    "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

# --- RENDER KEEP-ALIVE SERVER ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running 24/7", 200

def run_flask():
    # Render requires port 10000
    app.run(host='0.0.0.0', port=10000)

# --- ORIGINAL CORE LOGIC (100% UNALTERED) ---
class InstagramResetTool:
    def __init__(self):
        self.chat_id = None
        self.bot_token = os.getenv('BOT_TOKEN') 
        self.colors = {
            'primary': '\x1b[38;5;208m',
            'secondary': '\x1b[38;5;214m',
            'accent': '\x1b[1;31m',
            'warning': '\x1b[1;33m',
            'neutral': '\x1b[2;36m',
            'reset': '\x1b[1;37m',
        }

    def generate_instagram_password(self):
        words = ['hello', 'insta', 'random', 'python', 'absceb', 'summer', 'winter', 'autumn', 'spring', 'monsoon', 'cool', 'new', 'user', 'alpha', 'beta', 'gamma', 'star', 'moon', 'sun', 'earth', 'mars', 'venus']
        formats = [
            lambda w, n: f"{w}{n}!",
            lambda w, n: f"{w}{n}#",
            lambda w, n: f"{w}{n}@",
            lambda w, n: f"{w}{n}$",
            lambda w, n: f"{w}{n}_",
            lambda w, n: f"{w}@{n}",
            lambda w, n: f"{w}_{n}",
            lambda w, n: f"{w}{n}",
            lambda w, n: f"{w[:2]}_{n[:2]}@",
            lambda w, n: f"{w}{n}&",
        ]
        word = random.choice(words)
        numbers = ''.join([str(random.randint(0, 9)) for _ in range(3)])
        format_func = random.choice(formats)
        password = format_func(word, numbers)
        while len(password) < 6:
            password += str(random.randint(0, 9))
        return password

    def send_telegram(self, text):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text}
        try:
            r = requests.post(url, data=payload, timeout=10)
            return r.json()
        except Exception:
            return None

    def generate_device_info(self):
        ANDROID_ID = f"android-{''.join(random.choices(string.hexdigits.lower(), k=16))}"
        USER_AGENT = f"Instagram 394.0.0.46.81 Android ({random.choice(['28/9','29/10','30/11','31/12'])}; {random.choice(['240dpi','320dpi','480dpi'])}; {random.choice(['720x1280','1080x1920','1440x2560'])}; {random.choice(['samsung','xiaomi','huawei','oneplus','google'])}; {random.choice(['SM-G975F','Mi-9T','P30-Pro','ONEPLUS-A6003','Pixel-4'])}; intel; en_US; {random.randint(100000000,999999999)})"
        WATERFALL_ID = str(uuid.uuid4())
        timestamp = int(datetime.now().timestamp())
        PASSWORD = f'#PWD_INSTAGRAM:0:{timestamp}:{self.generate_instagram_password()}'
        return ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD

    def make_headers(self, mid="", user_agent=""):
        return {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Bloks-Version-Id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "X-Mid": mid,
            "User-Agent": user_agent,
            "Content-Length": "9481"
        }

    def reset_instagram_password(self, reset_link):
        try:
            ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD = self.generate_device_info()
            uidb36 = reset_link.split("uidb36=")[1].split("&token=")[0]
            token = reset_link.split("&token=")[1].split(":")[0]

            url = "https://i.instagram.com/api/v1/accounts/password_reset/"
            data = {
                "source": "one_click_login_email",
                "uidb36": uidb36,
                "device_id": ANDROID_ID,
                "token": token,
                "waterfall_id": WATERFALL_ID
            }
            r = requests.post(url, headers=self.make_headers(user_agent=USER_AGENT), data=data)

            if "user_id" not in r.text:
                return {"success": False, "error": f"Error in reset request: {r.text}"}

            mid = r.headers.get("Ig-Set-X-Mid")
            resp_json = r.json()
            user_id = resp_json.get("user_id")
            cni = resp_json.get("cni")
            nonce_code = resp_json.get("nonce_code")
            challenge_context = resp_json.get("challenge_context")

            url2 = "https://i.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/"
            data2 = {
                "user_id": str(user_id),
                "cni": str(cni),
                "nonce_code": str(nonce_code),
                "bk_client_context": '{"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"}',
                "challenge_context": str(challenge_context),
                "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
                "get_challenge": "true"
            }
            r2 = requests.post(url2, headers=self.make_headers(mid, USER_AGENT), data=data2).text

            challenge_context_final = r2.replace('\\', '').split(f'(bk.action.i64.Const, {cni}), "')[1].split('", (bk.action.bool.Const, false)))')[0]

            data3 = {
                "is_caa": "False",
                "source": "",
                "uidb36": "",
                "error_state": {"type_name": "str", "index": 0, "state_id": 1048583541},
                "afv": "",
                "cni": str(cni),
                "token": "",
                "has_follow_up_screens": "0",
                "bk_client_context": {"bloks_version": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd", "styles_id": "instagram"},
                "challenge_context": challenge_context_final,
                "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
                "enc_new_password1": PASSWORD,
                "enc_new_password2": PASSWORD
            }

            requests.post(url2, headers=self.make_headers(mid, USER_AGENT), data=data3)
            new_password = PASSWORD.split(":")[-1]

            return {
                "success": True,
                "password": new_password,
                "user_id": user_id
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# --- TELEGRAM BOT WRAPPER ---
bot = telebot.TeleBot(BOT_TOKEN)

def main_keyboard(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Start Reset", callback_data="start_reset"))
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("📊 Admin Stats", callback_data="admin_stats"))
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    text = (
        "<b>💎 Instagram Reset Premium Tool</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Status: 🟢 Operational\n"
        "Credit: @b44ner\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<i>Ready to process your request.</i>"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=main_keyboard(message.from_user.id))

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "start_reset":
        msg = bot.send_message(call.message.chat.id, "🛰 <b>Send your Instagram Reset Link:</b>", parse_mode="HTML")
        bot.register_next_step_handler(msg, run_process)
    
    elif call.data == "admin_stats" and call.from_user.id == ADMIN_ID:
        uptime = STATS["start_time"]
        stats_text = (
            "<b>🛡 Admin Dashboard</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 Total Attempts: {STATS['total_attempts']}\n"
            f"✅ Successful Resets: {STATS['successful_resets']}\n"
            f"🕒 Online Since: {uptime}\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        bot.send_message(call.message.chat.id, stats_text, parse_mode="HTML")

def run_process(message):
    if "instagram.com" not in message.text:
        bot.reply_to(message, "❌ Invalid Link.")
        return

    status = bot.send_message(message.chat.id, "⏳ <b>Bypassing Protocols...</b>", parse_mode="HTML")
    
    STATS["total_attempts"] += 1
    tool = InstagramResetTool()
    tool.chat_id = message.chat.id
    result = tool.reset_instagram_password(message.text.strip())

    if result.get("success"):
        STATS["successful_resets"] += 1
        resp = (
            "<b>𝐑𝐄𝐒𝐄𝐓 𝐒𝐔𝐂𝐂𝐄𝐒𝐒𝐅𝐔𝐋 ✅</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>User ID:</b> <code>{result.get('user_id')}</code>\n"
            f"🔑 <b>New Pass:</b> <code>{result.get('password')}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Credit: @b44ner"
        )
        bot.edit_message_text(resp, message.chat.id, status.message_id, parse_mode="HTML", reply_markup=main_keyboard(message.from_user.id))
    else:
        err = f"<b>𝐑𝐄𝐒𝐄𝐓 𝐅𝐀𝐈𝐋𝐄𝐃 ❌</b>\n\nError: <code>{result.get('error')}</code>"
        bot.edit_message_text(err, message.chat.id, status.message_id, parse_mode="HTML", reply_markup=main_keyboard(message.from_user.id))

# --- EXECUTION ---
if __name__ == "__main__":
    # Start Keep-Alive Server
    threading.Thread(target=run_flask, daemon=True).start()
    
    print("Bot is starting...")
    bot.infinity_polling()
