import os
import random
import logging
import asyncio
from threading import Thread
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Aktiver logging
logging.basicConfig(level=logging.DEBUG)

# Miljøvariabler
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = os.environ.get("BASE_URL")  # Eks: https://coffeebot-abc123.onrender.com

# Flask server
app = Flask(__name__)

# Telegram-bot
application = Application.builder().token(BOT_TOKEN).build()

# 🎲 Kaffe-resultater
coffee_results = {
    1: "Burnt battery acid", 2: "Cold and sour", 3: "Instant regret", 4: "Overbrewed sludge",
    5: "Watery disappointment", 6: "Smells better than it tastes", 7: "Vending machine sadness",
    8: "Bitter but tolerable", 9: "Average brew", 10: "Solid morning fuel",
    11: "Coffee shop standard", 12: "Fair trade, full body", 13: "Cold brew from Elven woods",
    14: "Magical morning blend", 15: "Sipped with eyes closed", 16: "Barista sang while making it",
    17: "Tastes like victory", 18: "Masterwork espresso", 19: "Divine roast", 20: "COFFEE OF THE GODS"
}

# 🎯 /coffee-kommando
async def coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.debug("🚀 coffee()-kommando trigget")

    try:
        roll = random.randint(1, 20)
        result = coffee_results[roll]
        caption = f"🎲 You rolled a *{roll}*\n☕ Result: _{result}_"

        image_path = os.path.join(os.getcwd(), "Bot", "Dice", f"{roll}.png")
        logging.debug(f"📁 current working dir: {os.getcwd()}")
        logging.debug(f"🔍 forventet bilde: {image_path}")

        if not os.path.exists(image_path):
            await update.message.reply_text("⚠️ Bilde ikke funnet!")
            return

        with open(image_path, "rb") as img:
            await update.message.reply_photo(photo=img, caption=caption, parse_mode="Markdown")

        logging.debug(f"✅ Sendte bilde for roll {roll}")

    except Exception as e:
        logging.error(f"🔥 Feil i coffee-funksjonen: {e}")
        await update.message.reply_text("⚠️ Noe gikk galt med kaffen 😬")

# Legg til kommandohandler
application.add_handler(CommandHandler("coffee", coffee))

# 📡 Webhook-endepunkt med global event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        logging.debug("📥 Mottatt webhook-kall")
        data = request.get_json(force=True)
        logging.debug(f"📦 Webhook payload: {data}")
        update = Update.de_json(data, application.bot)
        logging.debug("✅ Opprettet Telegram Update-objekt")

        async def handle_update():
            if not application._initialized:
                logging.debug("🛠️ Initialiserer Telegram Application")
                await application.initialize()
            await application.process_update(update)
            logging.debug("🔁 Update prosessering ferdig")

        def run_task():
            asyncio.set_event_loop(loop)
            loop.run_until_complete(handle_update())

        Thread(target=run_task).start()

        return "ok"
    except Exception as e:
        import traceback
        logging.error("❌ Exception i webhook: %s", traceback.format_exc())
        return "error", 500

# Status-check
@app.get("/")
def home():
    return "CoffeeBot is alive ☕", 200
