import os
import json
import logging
import random
import time
import asyncio
from flask import Flask, request
from telegram import Update, constants
from telegram.ext import Application, CommandHandler, ContextTypes

# === Logging ===
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("CoffeeBot")

# === Miljøvariabler ===
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

if not TOKEN or not WEBHOOK_SECRET:
    raise ValueError("BOT_TOKEN og WEBHOOK_SECRET må være satt som miljøvariabler")

# === Flask-app ===
app = Flask(__name__)

# === Filstier ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DICE_PATH = os.path.join(BASE_DIR, "Dice")
GROUP_DATA_FILE = os.path.join(BASE_DIR, "group_data.json")

# === Init tomme JSON-filer hvis de ikke finnes eller er tomme ===
if not os.path.exists(GROUP_DATA_FILE) or os.path.getsize(GROUP_DATA_FILE) == 0:
    with open(GROUP_DATA_FILE, "w") as f:
        json.dump({}, f)

# === JSON helpers ===
def load_group_data():
    with open(GROUP_DATA_FILE, "r") as f:
        return json.load(f)

def save_group_data(data):
    with open(GROUP_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# === Telegram Application ===
application = Application.builder().token(TOKEN).build()

# === /coffee ===
async def coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    chat = update.effective_chat
    user = update.effective_user
    chat_id = str(chat.id)
    user_id = str(user.id)

    group_data = load_group_data()
    group = group_data.get(chat_id, {})

    if chat.type != "private" and not group.get("enabled", True):
        await update.message.reply_text("🛑 CoffeeBot is currently off in this group.")
        return

    last_used = group.get("last_used", {}).get(user_id, 0)
    if time.time() - last_used < 15:
        await update.message.reply_text("⏳ Whoa there, barista! Wait before brewing again.")
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

# === Admin commands: Enable/Disable Bot ===
async def enable_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    chat_id = str(chat.id)
    if chat.type == "private":
        return await update.message.reply_text("Bruk denne kommandoen i en gruppe.")

    member = await context.bot.get_chat_member(chat.id, update.effective_user.id)
    if member.status not in ["creator", "administrator"]:
        return await update.message.reply_text("Only group admins can enable the bot.")

    data = load_group_data()
    data[chat_id] = {"enabled": True, "title": chat.title, "last_used": {}}
    save_group_data(data)
    await update.message.reply_text("✅ CoffeeBot enabled!")

async def disable_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    chat_id = str(chat.id)
    if chat.type == "private":
        return await update.message.reply_text("Bruk denne kommandoen i en gruppe.")

    member = await context.bot.get_chat_member(chat.id, update.effective_user.id)
    if member.status not in ["creator", "administrator"]:
        return await update.message.reply_text("Only group admins can disable the bot.")

    data = load_group_data()
    data[chat_id] = {"enabled": False, "title": chat.title, "last_used": {}}
    save_group_data(data)
    await update.message.reply_text("☕ CoffeeBot disabled!")

# === Registrering av Kommando-Handlers ===
application.add_handler(CommandHandler("coffee", coffee))
application.add_handler(CommandHandler("coffeeon", enable_bot))
application.add_handler(CommandHandler("coffeeoff", disable_bot))
application.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("☕ Type /coffee to brew!")))
application.add_handler(CommandHandler("help", lambda u, c: u.message.reply_text("Use /coffee, /coffeeon, /coffeeoff, etc.")))

# === Flask Webhook Route ===
@app.route(f"/webhook/<secret>", methods=["POST"])
def webhook(secret):
    if secret != WEBHOOK_SECRET:
        return "Unauthorized", 403

    update = Update.de_json(request.get_json(force=True), application.bot)
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.create_task(application.process_update(update))
    return "ok", 200

@app.route("/")
def index():
    return "CoffeeBot is live ☕", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
