import os
import json
import logging
import random
import time
from flask import Flask, request
from telegram import Update, constants
from telegram.ext import Application, CommandHandler, ContextTypes, MyChatMemberHandler
import telegram
print(f"telegram library version: {telegram.__version__}")


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
        await update.message.reply_text("\ud83d\udeab This group is blacklisted from using CoffeeBot.")
        return

    group_data = load_group_data()
    group = group_data.get(chat_id, {})

    if chat.type != "private" and not group.get("enabled", True):
        await update.message.reply_text("\ud83d\uded1 CoffeeBot is currently off in this group.\nWaiting for fresh beans... \u2615")
        return

    last_used = group.get("last_used", {}).get(user_id, 0)
    if time.time() - last_used < 15:
        await update.message.reply_text("\u23f3 Whoa there, barista!\nWait a few more sips before the next brew.")
        return

    roll = random.randint(1, 20)
    image_path = os.path.join(DICE_PATH, f"{roll}.png")

    captions = {
        1: "\u2615 Result: Burnt catastrophe",
        2: "\u2615 Result: Weak sauce",
        3: "\u2615 Result: Lukewarm regret",
        4: "\u2615 Result: Overbrewed sludge",
        5: "\u2615 Result: Coffee? More like tea",
        6: "\u2615 Result: Slightly satisfying",
        7: "\u2615 Result: Basic brew",
        8: "\u2615 Result: Meh morning fix",
        9: "\u2615 Result: Not bad at all",
        10: "\u2615 Result: Solid morning fuel",
        11: "\u2615 Result: Steamy goodness",
        12: "\u2615 Result: Aromatic delight",
        13: "\u2615 Result: Pleasant surprise",
        14: "\u2615 Result: Magical morning blend",
        15: "\u2615 Result: Brewmaster approved",
        16: "\u2615 Result: Barista sang while making it",
        17: "\u2615 Result: Inspirational nectar",
        18: "\u2615 Result: Divine intervention",
        19: "\u2615 Result: Legendary roast",
        20: "\u2615 Result: COFFEE OF THE GODS"
    }

    if not os.path.exists(image_path):
        await update.message.reply_text("\u26a0\ufe0f Coffee image missing!")
        return

    caption = f"\ud83c\udfb2 You rolled a *{roll}*\n_{captions[roll]}_"
    with open(image_path, "rb") as photo:
        await update.message.reply_photo(photo=photo, caption=caption, parse_mode=constants.ParseMode.MARKDOWN)

    group.setdefault("last_used", {})[user_id] = time.time()
    group_data[chat_id] = group
    save_group_data(group_data)

# ... (resten av funksjonene beholdes uendret)
