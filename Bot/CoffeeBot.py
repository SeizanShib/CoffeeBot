import os
import json
import logging
import random
import time
import asyncio
from flask import Flask, request, Response, abort
from telegram import Update, constants
from telegram.ext import Application, CommandHandler, ContextTypes

# --- Logging configuration ---
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("CoffeeBot")

# --- Environment Variables ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_URL = os.getenv("BASE_URL")  # For example, "https://yourapp.onrender.com"

if not BOT_TOKEN or not WEBHOOK_SECRET or not WEBHOOK_URL:
    raise ValueError("BOT_TOKEN, WEBHOOK_SECRET, and WEBHOOK_URL must be set in environment variables.")

# --- Flask App Setup ---
app = Flask(__name__)

# --- File paths for persistent data ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DICE_PATH = os.path.join(BASE_DIR, "Dice")
GROUP_DATA_FILE = os.path.join(BASE_DIR, "group_data.json")

if not os.path.exists(GROUP_DATA_FILE) or os.path.getsize(GROUP_DATA_FILE) == 0:
    with open(GROUP_DATA_FILE, "w") as f:
        json.dump({}, f)

def load_group_data():
    with open(GROUP_DATA_FILE, "r") as f:
        return json.load(f)

def save_group_data(data):
    with open(GROUP_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# --- Build Telegram Application (PTB v20+) ---
application = Application.builder().token(BOT_TOKEN).build()

# --- Bot Handlers ---
async def coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("Received /coffee command.")
    if not update.message:
        logger.debug("No message found in update.")
        return

    chat = update.effective_chat
    user = update.effective_user
    chat_id = str(chat.id)
    user_id = str(user.id)

    group_data = load_group_data()
    group = group_data.get(chat_id, {})

    # For group chats, bot may be disabled
    if chat.type != "private" and not group.get("enabled", True):
        await update.message.reply_text("🛑 CoffeeBot is currently off in this group.")
        return

    # Rate limit: 15 seconds per user
    last_used = group.get("last_used", {}).get(user_id, 0)
    if time.time() - last_used < 15:
        await update.message.reply_text("⏳ Whoa there, barista! Wait before brewing again.")
        return

    roll = random.randint(1, 20)
    image_path = os.path.join(DICE_PATH, f"{roll}.png")
    logger.debug(f"Rolled: {roll} ; Image path: {image_path}")

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
        logger.error(f"Image not found: {image_path}")
        await update.message.reply_text("⚠️ Coffee image missing!")
        return

    caption = f"🎲 You rolled a *{roll}*\n_{captions[roll]}_"
    try:
        with open(image_path, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=caption,
                parse_mode=constants.ParseMode.MARKDOWN
            )
        logger.debug("Sent coffee photo.")
    except Exception as e:
        logger.exception("Error sending photo:")
        await update.message.reply_text(caption)

    # Update rate limiting info
    group.setdefault("last_used", {})[user_id] = time.time()
    group_data[chat_id] = group
    save_group_data(group_data)

async def enable_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("Received /coffeeon command.")
    chat = update.effective_chat
    chat_id = str(chat.id)
    if chat.type == "private":
        await update.message.reply_text("Please use this command in a group.")
        return
    try:
        member = await context.bot.get_chat_member(chat.id, update.effective_user.id)
    except Exception:
        logger.exception("Error fetching chat member.")
        await update.message.reply_text("Could not verify admin status.")
        return

    if member.status not in ["creator", "administrator"]:
        await update.message.reply_text("Only group admins can enable the bot.")
        return

    data = load_group_data()
    data[chat_id] = {"enabled": True, "title": chat.title, "last_used": {}}
    save_group_data(data)
    await update.message.reply_text("✅ CoffeeBot enabled!")
    logger.debug(f"Enabled bot in chat {chat_id}")

async def disable_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("Received /coffeeoff command.")
    chat = update.effective_chat
    chat_id = str(chat.id)
    if chat.type == "private":
        await update.message.reply_text("Please use this command in a group.")
        return
    try:
        member = await context.bot.get_chat_member(chat.id, update.effective_user.id)
    except Exception:
        logger.exception("Error fetching chat member.")
        await update.message.reply_text("Could not verify admin status.")
        return

    if member.status not in ["creator", "administrator"]:
        await update.message.reply_text("Only group admins can disable the bot.")
        return

    data = load_group_data()
    data[chat_id] = {"enabled": False, "title": chat.title, "last_used": {}}
    save_group_data(data)
    await update.message.reply_text("☕ CoffeeBot disabled!")
    logger.debug(f"Disabled bot in chat {chat_id}")

# --- Register command handlers ---
application.add_handler(CommandHandler("coffee", coffee))
application.add_handler(CommandHandler("coffeeon", enable_bot))
application.add_handler(CommandHandler("coffeeoff", disable_bot))
application.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("☕ Type /coffee to brew!")))
application.add_handler(CommandHandler("help", lambda update, context: update.message.reply_text("Commands: /coffee, /coffeeon, /coffeeoff")))

# --- Flask Webhook Endpoint ---
# Using an async route (Flask 2.3+ required)
@app.route("/telegram/<secret>", methods=["POST"])
async def telegram_webhook(secret):
    if secret != WEBHOOK_SECRET:
        logger.warning("Received webhook with incorrect secret.")
        return Response("Unauthorized", status=403)
    
    if request.headers.get("Content-Type") != "application/json":
        return Response("Bad Request: JSON expected", status=400)
    
    update_data = await request.get_json()
    update = Update.de_json(update_data, application.bot)
    logger.debug("Received update: " + str(update))
    
    # Enqueue update for processing by PTB's dispatcher
    await application.update_queue.put(update)
    return Response("ok", status=200)

@app.route("/")
def home():
    return "CoffeeBot is alive ☕", 200

# --- ASGI Server Runner ---
# We convert our Flask app to ASGI using WsgiToAsgi and run it with Uvicorn
import uvicorn
from asgiref.wsgi import WsgiToAsgi

async def main():
    # Set webhook with Telegram to point to our public URL + secret
    full_webhook_url = f"{WEBHOOK_URL}/telegram/{WEBHOOK_SECRET}"
    await application.bot.set_webhook(full_webhook_url)
    logger.info("Webhook set to: " + full_webhook_url)
    
    # Run the Telegram bot and the web server concurrently
    # Using a single asyncio event loop for both components:
    async with application:
        # Convert Flask app to ASGI app
        asgi_app = WsgiToAsgi(app)
        port = int(os.environ.get("PORT", 5000))
        config = uvicorn.Config(asgi_app, host="0.0.0.0", port=port, log_level="info")
        server = uvicorn.Server(config)
        logger.info("Starting ASGI server...")
        await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
