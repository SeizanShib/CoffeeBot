import os
import json
import logging
import random
import time
from flask import Flask, request
from telegram import Update, constants
from telegram.ext import Application, CommandHandler, ContextTypes

from logging.handlers import RotatingFileHandler

# Logging setup
LOG_FILE = "coffee.log"
log_handler = RotatingFileHandler(LOG_FILE, maxBytes=1000000, backupCount=3)
logging.basicConfig(handlers=[log_handler], level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("CoffeeBot")

# Telegram Bot Token
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN er ikke satt i miljøvariabler")

# Flask app for webhook
app = Flask(__name__)

# Path til bildene
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DICE_PATH = os.path.join(BASE_DIR, "Dice")

# Path til gruppedata
GROUP_DATA_FILE = os.path.join(BASE_DIR, "group_data.json")
if not os.path.exists(GROUP_DATA_FILE):
    with open(GROUP_DATA_FILE, "w") as f:
        json.dump({}, f)

# Path til blacklist
BLACKLIST_FILE = os.path.join(BASE_DIR, "blacklist.json")
if not os.path.exists(BLACKLIST_FILE):
    with open(BLACKLIST_FILE, "w") as f:
        json.dump([], f)

ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

# Last/save helpers
def load_group_data():
    with open(GROUP_DATA_FILE, "r") as f:
        return json.load(f)

def save_group_data(data):
    with open(GROUP_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_blacklist():
    with open(BLACKLIST_FILE, "r") as f:
        return json.load(f)

def save_blacklist(data):
    with open(BLACKLIST_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Notify admin
def notify_admin(context, message):
    try:
        if ADMIN_USER_ID:
            context.bot.send_message(chat_id=int(ADMIN_USER_ID), text=message)
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")

# Coffee handler
async def coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or not update.message.text:
        return

    chat = update.effective_chat
    user = update.effective_user
    chat_id = str(chat.id)
    user_id = str(user.id)

    logger.info(f"/coffee by {user.username or user_id} in chat {chat.title or chat_id}")

    if chat.type != "private" and chat_id in load_blacklist():
        await update.message.reply_text("🚫 This group is blacklisted from using CoffeeBot.")
        return

    group_data = load_group_data()
    group = group_data.get(chat_id, {})

    if chat.type != "private" and not group.get("enabled", True):
        await update.message.reply_text("🛑 CoffeeBot is currently off in this group.\nWaiting for fresh beans... ☕")
        return

    last_used = group.get("last_used", {}).get(user_id, 0)
    if time.time() - last_used < 15:
        await update.message.reply_text("⏳ Whoa there, barista!\nWait a few more sips before the next brew.")
        return

    roll = random.randint(1, 20)
    image_path = os.path.join(DICE_PATH, f"{roll}.png")

    captions = {
        1: "☕ Result: Burnt catastrophe",
        2: "☕ Result: Weak sauce",
        3: "☕ Result: Lukewarm regret",
        4: "☕ Result: Overbrewed sludge",
        5: "☕ Result: Coffee? More like tea",
        6: "☕ Result: Slightly satisfying",
        7: "☕ Result: Basic brew",
        8: "☕ Result: Meh morning fix",
        9: "☕ Result: Not bad at all",
        10: "☕ Result: Solid morning fuel",
        11: "☕ Result: Steamy goodness",
        12: "☕ Result: Aromatic delight",
        13: "☕ Result: Pleasant surprise",
        14: "☕ Result: Magical morning blend",
        15: "☕ Result: Brewmaster approved",
        16: "☕ Result: Barista sang while making it",
        17: "☕ Result: Inspirational nectar",
        18: "☕ Result: Divine intervention",
        19: "☕ Result: Legendary roast",
        20: "☕ Result: COFFEE OF THE GODS"
    }

    if not os.path.exists(image_path):
        await update.message.reply_text("⚠️ Coffee image missing!")
        return

    caption = f"🎲 You rolled a *{roll}*\n_{captions[roll]}_"
    with open(image_path, "rb") as photo:
        await update.message.reply_photo(photo=photo, caption=caption, parse_mode=constants.ParseMode.MARKDOWN)

    group.setdefault("last_used", {})[user_id] = time.time()
    group_data[chat_id] = group
    save_group_data(group_data)

# Toggle bot on/off
async def enable_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    chat = update.effective_chat
    chat_id = str(chat.id)
    if chat_id in load_blacklist():
        await update.message.reply_text("🚫 This group is blacklisted from using CoffeeBot.")
        return

    if chat.type == "private":
        return await update.message.reply_text("This command must be used in a group.")

    member = await context.bot.get_chat_member(chat.id, update.effective_user.id)
    if member.status not in ["creator", "administrator"]:
        return await update.message.reply_text("Only an admin can enable CoffeeBot in this group.")

    data = load_group_data()
    data[chat_id] = {"enabled": True, "title": chat.title, "last_used": {}}
    save_group_data(data)
    await update.message.reply_text("✅ CoffeeBot has been enabled in this group.")

async def disable_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    chat = update.effective_chat
    chat_id = str(chat.id)
    if chat_id in load_blacklist():
        await update.message.reply_text("🚫 This group is blacklisted from using CoffeeBot.")
        return

    if chat.type == "private":
        return await update.message.reply_text("This command must be used in a group.")

    member = await context.bot.get_chat_member(chat.id, update.effective_user.id)
    if member.status not in ["creator", "administrator"]:
        return await update.message.reply_text("Only an admin can disable CoffeeBot in this group.")

    data = load_group_data()
    data[chat_id] = {"enabled": False, "title": chat.title, "last_used": {}}
    save_group_data(data)
    await update.message.reply_text("☕ CoffeeBot has been disabled in this group.")

# Admin-only ban/whitelist
async def ban_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_USER_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /coffeeban <group_id>")
        return

    group_id = context.args[0]
    blacklist = load_blacklist()
    if group_id not in blacklist:
        blacklist.append(group_id)
        save_blacklist(blacklist)
        await update.message.reply_text(f"✅ Group {group_id} is now blacklisted.")
    else:
        await update.message.reply_text(f"Group {group_id} is already blacklisted.")

async def whitelist_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_USER_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /coffeewhitelist <group_id>")
        return

    group_id = context.args[0]
    blacklist = load_blacklist()
    if group_id in blacklist:
        blacklist.remove(group_id)
        save_blacklist(blacklist)
        await update.message.reply_text(f"✅ Group {group_id} is no longer blacklisted.")
    else:
        await update.message.reply_text(f"Group {group_id} was not blacklisted.")

# Build app
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("coffee", coffee))
application.add_handler(CommandHandler("coffeeon", enable_bot))
application.add_handler(CommandHandler("coffeeoff", disable_bot))
application.add_handler(CommandHandler("coffeeban", ban_group))
application.add_handler(CommandHandler("coffeewhitelist", whitelist_group))
application.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("☕ Type /coffee to brew!")))
application.add_handler(CommandHandler("help", lambda u, c: u.message.reply_text("Use /coffee to get coffee. Admins: /coffeeon /coffeeoff. Owner: /coffeeban /coffeewhitelist.")))

@app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
def webhook(secret):
    if secret != WEBHOOK_SECRET:
        return "Unauthorized", 403
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK"

@app.route("/")
def index():
    return "CoffeeBot is live ☕"
