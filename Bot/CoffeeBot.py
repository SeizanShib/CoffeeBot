import os
import random
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = os.environ.get("BASE_URL")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")

# Telegram bot application
application = Application.builder().token(BOT_TOKEN).build()

# Flask web server
app = Flask(__name__)

# Coffee roll results
coffee_results = {
    1: "Burnt battery acid", 2: "Cold and sour", 3: "Instant regret", 4: "Overbrewed sludge",
    5: "Watery disappointment", 6: "Smells better than it tastes", 7: "Vending machine sadness",
    8: "Bitter but tolerable", 9: "Average brew", 10: "Solid morning fuel",
    11: "Coffee shop standard", 12: "Fair trade, full body", 13: "Cold brew from Elven woods",
    14: "Magical morning blend", 15: "Sipped with eyes closed", 16: "Barista sang while making it",
    17: "Tastes like victory", 18: "Masterwork espresso", 19: "Divine roast", 20: "COFFEE OF THE GODS"
}

# /coffee command handler
async def coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    roll = random.randint(1, 20)
    result = coffee_results[roll]
    caption = f"🎲 You rolled a *{roll}*\n☕ Result: _{result}_"
    image_path = os.path.join("Bot", "Dice", f"{roll}.png")

    with open(image_path, "rb") as img:
        await update.message.reply_photo(photo=img, caption=caption, parse_mode="Markdown")

application.add_handler(CommandHandler("coffee", coffee))

# ✅ Riktig webhook-path, basert på din miljøvariabel
@app.route(f"/webhook/<secret>", methods=["POST"])
def webhook(secret):
    if secret != WEBHOOK_SECRET:
        return "Unauthorized", 403

    update = Update.de_json(request.get_json(force=True), application.bot)
    import asyncio
    asyncio.run(application.process_update(update))
    return "ok", 200


@app.route("/")
def home():
    return "CoffeeBot is alive ☕", 200
