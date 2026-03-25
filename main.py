import os
import random
import string
import uuid
import base64
import json
import threading
from threading import Thread, Lock
from datetime import datetime
from hashlib import md5

# Flask for Render Keep-Alive
from flask import Flask

try:
    import requests
    import pyfiglet
    import telebot # Bot framework
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    from cfonts import render, say
except ImportError:
    os.system("pip install requests telethon pyfiglet rich cfonts pyTelegramBotAPI flask")
    import requests
    import pyfiglet
    import telebot
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    from cfonts import render, say

from bs4 import BeautifulSoup
from user_agent import generate_user_agent

# --- FLASK SERVER (Keep-Alive) ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is alive", 200

def run_flask():
    # Render requires port 10000
    app.run(host='0.0.0.0', port=10000)

# --- ORIGINAL CORE LOGIC (100% Unaltered) ---

class InstagramResetTool:
    def __init__(self):
        self.chat_id = None
        # Mandate: Environment Variable for Token
        self.bot_token = os.getenv('BOT_TOKEN') 
        self.console = Console()
        self.colors = {
            'primary': '\x1b[38;5;208m',
            'secondary': '\x1b[38;5;214m',
            'accent': '\x1b[1;31m',
            'warning': '\x1b[1;33m',
            'neutral': '\x1b[2;36m',
            'reset': '\x1b[1;37m',
            'bg': '\x1b[38;5;{}m'
        }
        self.b = random.randint(5, 208)
        self.colors['base'] = self.colors['bg'].format(self.b)

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
        except Exception as e:
            print(f"Telegram send error: {e}")
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

# --- TELEGRAM INTERFACE ---

bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Bot is active. Send me an Instagram Reset Link.")

@bot.message_handler(func=lambda message: "instagram.com" in message.text)
def handle_reset(message):
    # Initialize the logic class
    tool = InstagramResetTool()
    tool.chat_id = message.chat.id
    reset_link = message.text.strip()
    
    bot.send_message(message.chat.id, "⏳ Processing...")
    
    # Execute the original logic
    result = tool.reset_instagram_password(reset_link)
    
    if result.get("success"):
        new_password = result.get("password")
        msg = f"𝐑𝐄𝐒𝐄𝐓 𝐃𝐎𝐍𝐄\n\n🔑 𝗣𝗔𝗦𝗦𝗪𝗢𝗥𝗗: {new_password}\n\n👤 @abhya • 📢 @flicktools"
        bot.send_message(message.chat.id, msg)
    else:
        bot.send_message(message.chat.id, f"❌ FAILED\nError: {result.get('error')}")

if __name__ == "__main__":
    # Start Flask "Keep-Alive" thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start Bot polling
    print("Bot is running...")
    bot.infinity_polling()
