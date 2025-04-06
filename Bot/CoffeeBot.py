import os
import json
import logging
import random
import time
import asyncio
from flask import Flask, request
from telegram import Update, Bot, constants
from telegram.ext import Application, CommandHandler, ContextTypes
from logging.handlers import RotatingFileHandler

# Logging setup
LOG_FILE = "coffee.log"
log_handler = RotatingFileHandler(LOG_FILE, maxBytes=1000000, backupCount=3)
logging.basicConfig(handlers=[log_handler], level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("CoffeeBot")

# Telegram Bot Token og Secret
TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")

if not TOKEN or not BASE_URL or not WEBHOOK_SECRET:
    raise ValueError("Miljøvariabler BOT_TOKEN, BASE_URL eller WEBHOOK_SECRET mangler")

# Flask app
app = Flask(__name__)

# Path til bildene og data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DICE_PATH = os.path.join(BASE_DIR, "Dice")
GROUP_DATA_FILE = os.path.join(BASE_DIR, "group_data.json")
BLACKLIST_FILE = os.path.join(BASE_DIR, "blacklist.json")

if not os.path.exists(GROUP_DATA_FILE):
    with open(GROUP_DATA_FILE, "w") as f:
        json.dump({}, f)
if not os.path.exists(BLACKLIST_FILE):
    with open(BLACKLIST_FILE, "w") as f:
        json.dump([], f)

# Helpers
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

def notify_admin(context, message):
    try:
        if ADMIN_USER_ID:
            context.bot.send_message(chat_id=int(ADMIN_USER_ID), text=message)
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")

# Kommando: /coffee
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
        1: "☕ Result: Burnt catastrophe", 2: "☕ Result: Weak sauce", 3: "☕ Result: Lukewarm regret",
        4: "☕ Result: Overbrewed sludge", 5: "☕ Result: Coffee? More like tea", 6: "☕ Result: Slightly satisfying",
        7: "☕ Result: Basic brew", 8: "☕ Result: Meh morning fix", 9: "☕ Result: Not bad at all",
        10: "☕ Result: Solid morning fuel", 11: "☕ Result: Steamy goodness", 12: "☕ Result: Aromatic delight",
        13: "☕ Result: Pleasant surprise", 14: "☕ Result: Magical morning blend", 15: "☕ Result: Brewmaster approved",
        16: "☕ Result: Barista sang while making it", 17: "☕ Result: Inspirational nectar",
        18: "☕ Result: Divine intervention", 19: "☕ Result: Legendary roast", 20: "☕ Result: COFFEE OF THE GODS"
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

# Toggle on/off og admin kommandoer er som før (utelatt her for korthet)
# ...

# Telegram Application bygges
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("coffee", coffee))
application.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("☕ Type /coffee to brew!")))
application.add_handler(CommandHandler("help", lambda u, c: u.message.reply_text("Use /coffee to get coffee.")))

# Webhook endpoint
@app.route(f"/webhook/<secret>", methods=["POST"])
def webhook(secret):
    if secret != WEBHOOK_SECRET:
        return "Unauthorized", 403

    try:
        update = Update.de_json(request.get_json(force=True), application.bot)

        async def safe_process(update):
            try:
                await application.process_update(update)
            except Exception as e:
                logger.exception("process_update feilet!")

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.create_task(safe_process(update))
        return "OK", 200

    except Exception as e:
        logger.exception("Feil i webhook-handler")
        return f"Webhook internal error: {e}", 500


# Hjemmerute setter webhook automatisk
@app.route("/")
def index():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(Bot(TOKEN).set_webhook(url=f"{BASE_URL}/webhook/{WEBHOOK_SECRET}", secret_token=WEBHOOK_SECRET))
        return "CoffeeBot webhook satt! ☕", 200
    except Exception as e:
        return f"Feil ved webhook-setup: {str(e)}", 500
