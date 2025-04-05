import os
import random
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Hent miljøvariabler
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = os.environ.get("BASE_URL")  # eks: https://coffeebot-vra9.onrender.com

# Flask webserver
app = Flask(__name__)

# Sett opp Telegram-bot
application = Application.builder().token(BOT_TOKEN).build()

# Resultater for kaffe-terningkast
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
    image_path = os.path.join("Bot", "Dice", f"{roll}.png")

    with open(image_path, "rb") as img:
        await update.message.reply_photo(photo=img, caption=caption, parse_mode="Markdown")

# Legg til handler
application.add_handler(CommandHandler("coffee", coffee))

# Webhook-endepunkt (Flask må kalle async via asyncio)
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        asyncio.run(application.process_update(update))  # Kjør async call i sync kontekst
        return "ok"
    except Exception as e:
        import traceback
        logging.error("Exception in webhook handler: %s", traceback.format_exc())
        return "error", 500

# Statussjekk
@app.get("/")
def home():
    return "CoffeeBot is alive ☕", 200
