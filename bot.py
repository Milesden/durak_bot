
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from durak import DurakGame

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

user_games = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    game = DurakGame()
    user_games[user_id] = game
    trump = game.trump
    player_hand = ', '.join(map(str, game.player_hand))
    await update.message.reply_text(
        f"🎮 Игра началась!\nКозырь: {trump}\nТвои карты: {player_hand}\nНапиши карту (например: `7♠`) чтобы походить.",
        parse_mode='Markdown'
    )

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    game = user_games.get(user_id)
    if not game:
        await update.message.reply_text("Сначала напиши /start, чтобы начать игру.")
        return

    text = update.message.text.strip()
    if len(text) < 2:
        await update.message.reply_text("Неправильный формат карты. Например: `7♠`")
        return

    player_card = None
    for card in game.player_hand:
        if str(card) == text:
            player_card = card
            break

    if not player_card:
        await update.message.reply_text("У тебя нет такой карты.")
        return

    game.player_hand.remove(player_card)
    game.play_card(player_card)
    bot_response = game.bot_defend()

    if bot_response:
        msg = f"Ты сходил: {player_card}\nБот отбился: {bot_response}"
    else:
        msg = f"Ты сходил: {player_card}\nБот не смог отбиться и забрал карту!"

    player_hand = ', '.join(map(str, game.player_hand))
    msg += f"\n\nТвои карты: {player_hand}"

    await update.message.reply_text(msg)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, play))
    print("Durak bot запущен...")
    app.run_polling()
