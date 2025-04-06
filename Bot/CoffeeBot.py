import os
import json
import random
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# === Miljøvariabler ===
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = os.environ.get("BASE_URL")  # eks: https://coffeebot.onrender.com
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

if not BOT_TOKEN or not BASE_URL:
    raise RuntimeError("BOT_TOKEN og BASE_URL må være satt")

# === Telegram bot init ===
application = Application.builder().token(BOT_TOKEN).build()

# === Flask app init ===
app = Flask(__name__)

# === Automatisk webhook setup ===
async def set_webhook():
    webhook_url = f"{BASE_URL}/webhook"
    bot = Bot(BOT_TOKEN)
    await bot.set_webhook(url=webhook_url, secret_token=WEBHOOK_SECRET)

import asyncio
asyncio.run(set_webhook())

# === Dice-resultater ===
coffee_results = {
    1: "Terrible", 2: "Weak", 3: "Sour", 4: "Bitter", 5: "Flat",
    6: "Ok", 7: "Mild", 8: "Passable", 9: "Drinkable", 10: "Good",
    11: "Nice", 12: "Smooth", 13: "Pleasant", 14: "Strong",
    15: "Bold", 16: "Tasty", 17: "Excellent", 18: "Perfect",
    19: "Godlike", 20: "COFFEE OF THE GODS"
}

# === Kommando: /coffee ===
async def coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    roll = random.randint(1, 20)
    result = coffee_results[roll]
    caption = f"🎲 You rolled a *{roll}*\n☕ Result: _{result}_"
    image_path = os.path.join("Bot", "Dice", f"{roll}.png")

    with open(image_path, "rb") as img:
        await update.message.reply_photo(photo=img, caption=caption, parse_mode="Markdown")

application.add_handler(CommandHandler("coffee", coffee))

# === Flask webhook-endepunkt ===
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.create_task(application.process_update(update))
    return "ok", 200

@app.route("/")
def home():
    return "CoffeeBot is alive ☕", 200
