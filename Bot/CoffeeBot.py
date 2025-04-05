import os
import random
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Miljøvariabler for Render-oppsett
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = os.environ.get("BASE_URL")  # https://coffeebot.onrender.com

# Flask-app og Telegram-bot instans
app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

# Initier telegram-appen én gang på toppen
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("coffee", lambda u, c: coffee(u, c)))

# D20-resultater
coffee_results = {
    1: "Burnt battery acid", 2: "Cold and sour", 3: "Instant regret", 4: "Overbrewed sludge",
    5: "Watery disappointment", 6: "Smells better than it tastes", 7: "Vending machine sadness",
    8: "Bitter but tolerable", 9: "Average brew", 10: "Solid morning fuel",
    11: "Coffee shop standard", 12: "Fair trade, full body", 13: "Cold brew from Elven woods",
    14: "Magical morning blend", 15: "Sipped with eyes closed", 16: "Barista sang while making it",
    17: "Tastes like victory", 18: "Masterwork espresso", 19: "Divine roast", 20: "COFFEE OF THE GODS"
}

# Kommando: /coffee
async def coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    roll = random.randint(1, 20)
    result = coffee_results[roll]
    caption = f"🎲 You rolled a *{roll}*\n☕ Result: _{result}_"
    image_path = os.path.join("Bot", "Dice", f"{roll}.png")

    with open(image_path, "rb") as img:
        await update.message.reply_photo(photo=img, caption=caption, parse_mode="Markdown")

# Webhook-endepunkt som Telegram bruker
@app.route("/webhook", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    await application.process_update(update)
    return "ok", 200

# Test-endepunkt (valgfritt)
@app.route("/")
def root():
    return "CoffeeBot is alive and brewing ☕", 200

@app.before_first_request
def set_webhook():
    url = f"{BASE_URL}/webhook"
    bot.set_webhook(url=url)


