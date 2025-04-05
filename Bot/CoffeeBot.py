import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import random

# Coffee results by d20 roll
coffee_results = {
    1: "Burnt battery acid",
    2: "Cold and sour",
    3: "Instant regret",
    4: "Overbrewed sludge",
    5: "Watery disappointment",
    6: "Smells better than it tastes",
    7: "Vending machine sadness",
    8: "Bitter but tolerable",
    9: "Average brew",
    10: "Solid morning fuel",
    11: "Coffee shop standard",
    12: "Fair trade, full body",
    13: "Cold brew from Elven woods",
    14: "Magical morning blend",
    15: "Sipped with eyes closed",
    16: "Barista sang while making it",
    17: "Tastes like victory",
    18: "Masterwork espresso",
    19: "Divine roast",
    20: "COFFEE OF THE GODS"
}

async def coffee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    roll = random.randint(1, 20)
    result = coffee_results[roll]
    caption = f"🎲 You rolled a *{roll}*\n☕ Result: _{result}_"
    
    # Full path to image
    image_path = os.path.join("dice", f"{roll}.png")

    # Send image + caption
    with open(image_path, "rb") as img:
        await update.message.reply_photo(photo=img, caption=caption, parse_mode="Markdown")

if __name__ == '__main__':
    app = ApplicationBuilder().token("8147366493:AAHwb0k607j8nFx1W_Z4dTvbgyrNhTMOGmQ").build()

    app.add_handler(CommandHandler("coffee", coffee))

    print("🤖 Bot is running... Press Ctrl+C to stop.")
    app.run_polling()
