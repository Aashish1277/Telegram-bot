import os
import re
import time
import random
import threading
import requests
import telebot
from telebot import types
from flask import Flask

# --- WEB SERVER FOR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_web_server():
    # Render uses the PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
# Use Environment Variable for security
API_TOKEN = os.getenv('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

BASE = "https://www.instagram.com"
TOTAL = 100

WEB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE}/",
    "Origin": BASE,
    "Connection": "keep-alive",
}

user_data = {}
active_tasks = {}

# --- INSTAGRAM LOGIC ---

def init_session(session):
    try:
        r = session.get(f"{BASE}/accounts/login/", headers=WEB_HEADERS, timeout=15)
        csrf = session.cookies.get("csrftoken", domain=".instagram.com")
        if not csrf:
            match = re.search(r'"csrf_token":"([^"]+)"', r.text)
            csrf = match.group(1) if match else ""
        session.headers.update({"X-CSRFToken": csrf, "Referer": f"{BASE}/accounts/login/"})
        return csrf
    except:
        return None

def login_step(session, username, password):
    csrf = session.cookies.get("csrftoken")
    if csrf: session.headers["X-CSRFToken"] = csrf
    login_url = f"{BASE}/api/v1/web/accounts/login/ajax/"
    data = {
        "username": username,
        "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}",
        "queryParams": "{}",
        "optIntoOneTap": "false"
    }
    return session.post(login_url, data=data)

def change_profile_pic(session, image_path):
    csrf = session.cookies.get("csrftoken")
    headers = {
        **WEB_HEADERS, 
        "X-CSRFToken": csrf, 
        "X-IG-App-ID": "936619743392459", 
        "Referer": f"{BASE}/accounts/edit/"
    }
    with open(image_path, "rb") as f:
        files = {"profile_pic": ("profilepic.jpg", f, "image/jpeg")}
        r = session.post(f"{BASE}/accounts/web_change_profile_picture/", files=files, headers=headers)
    return r.status_code == 200

def download_random_image(path):
    url = f"https://picsum.photos/400/400?random={random.randint(1, 100000)}"
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(path, "wb") as f:
            for chunk in r.iter_content(8192): f.write(chunk)

# --- KEYBOARDS ---

def main_menu():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚀 Start Remover", callback_data="begin"))
    return markup

def cancel_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🛑 Stop & Cancel", callback_data="stop"))
    return markup

# --- BOT HANDLERS ---

@bot.message_handler(commands=['start'])
def start_cmd(message):
    welcome = (
        "<b>⚡ Former Username Remover ⚡</b>\n\n"
        "Status: <b>Ready</b> 🟢\n"
        "Target: 100 Profile Rotations\n\n"
        "Press the button below to start."
    )
    bot.reply_to(message, welcome, parse_mode="HTML", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    cid = call.message.chat.id
    if call.data == "begin":
        bot.edit_message_text("👤 <b>Send Instagram Username:</b>", cid, call.message.message_id, parse_mode="HTML")
        bot.register_next_step_handler(call.message, get_user)
    elif call.data == "stop":
        active_tasks[cid] = False
        bot.answer_callback_query(call.id, "Stopping task...")
        bot.send_message(cid, "❌ <b>Task Terminated.</b>", parse_mode="HTML")

def get_user(message):
    user_data[message.chat.id] = {'u': message.text}
    bot.send_message(message.chat.id, "🔑 <b>Send Instagram Password:</b>", parse_mode="HTML")
    bot.register_next_step_handler(message, get_pass)

def get_pass(message):
    if message.chat.id in user_data:
        user_data[message.chat.id]['p'] = message.text
        execute_logic(message)

def execute_logic(message):
    cid = message.chat.id
    username = user_data[cid]['u']
    password = user_data[cid]['p']
    
    status = bot.send_message(cid, "📡 <b>Initializing...</b>", parse_mode="HTML")
    
    session = requests.Session()
    session.headers.update(WEB_HEADERS)
    
    if not init_session(session):
        bot.edit_message_text("❌ <b>Connection Error.</b>", cid, status.message_id, parse_mode="HTML")
        return

    response = login_step(session, username, password)
    try:
        data = response.json()
    except:
        bot.edit_message_text("❌ <b>IG Request Blocked.</b>", cid, status.message_id, parse_mode="HTML")
        return

    if data.get("authenticated"):
        bot.edit_message_text(f"✅ <b>Login Success!</b>\nTarget: <code>@{username}</code>", cid, status.message_id, parse_mode="HTML")
        
        active_tasks[cid] = True
        temp_img = f"img_{cid}.jpg"
        
        for i in range(1, TOTAL + 1):
            if not active_tasks.get(cid): break
            
            try:
                download_random_image(temp_img)
                if change_profile_pic(session, temp_img):
                    if i % 2 == 0:
                        bot.edit_message_text(
                            f"⚙️ <b>Processing Task</b>\nProgress: <code>{i}/{TOTAL}</code>\nTarget: <code>@{username}</code>", 
                            cid, status.message_id, parse_mode="HTML",
                            reply_markup=cancel_keyboard()
                        )
                time.sleep(1.5)
            except: continue

        if active_tasks.get(cid):
            bot.send_message(cid, f"🏁 <b>Finished!</b>\nHistory for <code>@{username}</code> has been updated.")
        
        if os.path.exists(temp_img): os.remove(temp_img)
    else:
        reason = data.get("message", "Incorrect credentials.")
        bot.edit_message_text(f"❌ <b>Login Failed:</b> {reason}", cid, status.message_id, parse_mode="HTML")

# --- STARTUP LOGIC ---
if __name__ == "__main__":
    # 1. Start the Flask server in a separate thread
    threading.Thread(target=run_web_server, daemon=True).start()
    
    print("-------------------------------")
    print("      BOT IS NOW RUNNING       ")
    print("   Status: Active & Online     ")
    print("-------------------------------")
    
    # 2. Start the Telegram Bot polling (Main Thread)
    bot.infinity_polling()
