import os
import random
import asyncio
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.DEBUG)

# Miljøvariabler
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = os.environ.get("BASE_URL")  # eks: https://coffeebot-vra9.onrender.com

# Flask
app = Flask(__name__)

# Telegram-bot
application = Application.builder().token(BOT_TOKEN).build()

coffee_results = {
    1: "Burnt battery acid", 2: "Cold and sour", 3: "Instant regret", 4: "Overbrewed sludge",
    5: "Watery disappointment", 6: "Smells better than it tastes", 7: "Vending machine sadness",
    8: "Bitter but tolerable", 9: "Average brew", 10: "Solid morning fuel",
    11: "Coffee shop standard", 12: "Fair trade, full body", 13: "Cold brew from Elven woods",
    14: "Magical morning blend", 15: "Sipped with eyes closed", 16: "Barista sang while making it",
    17: "Tastes like victory", 18: "Masterwork espresso", 19: "Divine roast", 20: "COFFEE OF THE GODS"
}

# /coffee-kommando
async def coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    roll = random.randint(1, 20)
    result = coffee_results[roll]
    caption = f"🎲 You rolled a *{roll}*\n☕ Result: _{result}_"
    image_path = os.path.join(os.getcwd(), "Bot", "Dice", f"{roll}.png")

    if not os.path.exists(image_path):
        await update.message.reply_text("⚠️ Bilde ikke funnet!")
        return

    with open(image_path, "rb") as img:
        await update.message.reply_photo(photo=img, caption=caption, parse_mode="Markdown")

application.add_handler(CommandHandler("coffee", coffee))

# Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        logging.debug("Mottatt webhook-kall")
        data = request.get_json(force=True)
        logging.debug(f"Webhook payload: {data}")
        update = Update.de_json(data, application.bot)
        logging.debug("Opprettet Telegram Update-objekt")

        loop = asyncio.get_event_loop()
        loop.create_task(application.process_update(update))
        logging.debug("Update prosessering startet")

        return "ok"
    except Exception as e:
        import traceback
        logging.error("Exception i webhook: %s", traceback.format_exc())
        return "error", 500

# Status
@app.get("/")
def home():
    return "CoffeeBot is alive ☕", 200
