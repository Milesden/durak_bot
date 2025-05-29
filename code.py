
import os
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Карты и масти для колоды 36 карт
ranks = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
suits = ['♣️', '♦️', '♥️', '♠️']

def create_deck():
    return [r + s for s in suits for r in ranks]

# Хранение состояний игроков: колода, руки, козырь, ход, карты на столе
games = {}

# Главное меню
main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(
    KeyboardButton("🃏 Начать игру"),
    KeyboardButton("📋 Показать карты"),
    KeyboardButton("🚪 Сдаться")
)

def get_cards_kb(cards):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    kb.add(*[KeyboardButton(card) for card in cards])
    kb.add(KeyboardButton("🚪 Сдаться"))
    return kb

def card_value(card):
    # Для упрощения — возвращаем индекс ранга
    return ranks.index(card[:-2]) if card[:-2] in ranks else ranks.index(card[:-1])

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Привет! Готов сыграть в 'Дурака'? Нажми кнопку ниже.", reply_markup=main_kb)

@dp.message_handler(lambda msg: msg.text == "🃏 Начать игру")
async def start_game(message: types.Message):
    user_id = message.from_user.id
    deck = create_deck()
    random.shuffle(deck)

    # Козырь - последняя карта в колоде
    trump = deck[-1]
    trump_suit = trump[-2:] if len(trump) == 3 else trump[-1]

    # Раздаем по 6 карт игроку и боту
    player_hand = [deck.pop() for _ in range(6)]
    bot_hand = [deck.pop() for _ in range(6)]

    games[user_id] = {
        "deck": deck,
        "trump": trump,
        "trump_suit": trump_suit,
        "player_hand": player_hand,
        "bot_hand": bot_hand,
        "table": [],  # пары карт (атакующая, отбивающая)
        "player_turn": True,
        "attacking_card": None,
        "defending_card": None,
        "game_over": False
    }

    await message.answer(
        f"Игра началась! Козырь: {trump}\nВаши карты:",
        reply_markup=get_cards_kb(player_hand)
    )

@dp.message_handler(lambda msg: msg.text == "📋 Показать карты")
async def show_cards(message: types.Message):
    user_id = message.from_user.id
    if user_id not in games or games[user_id]["game_over"]:
        await message.answer("Вы не в игре. Нажмите '🃏 Начать игру'.", reply_markup=main_kb)
        return
    hand = games[user_id]["player_hand"]
    await message.answer(f"Ваши карты: {', '.join(hand)}", reply_markup=get_cards_kb(hand))

@dp.message_handler(lambda msg: msg.text == "🚪 Сдаться")
async def surrender(message: types.Message):
    user_id = message.from_user.id
    if user_id in games and not games[user_id]["game_over"]:
        games[user_id]["game_over"] = True
        await message.answer("Вы сдались. Игра окончена.", reply_markup=main_kb)
    else:
        await message.answer("Вы сейчас не в игре.", reply_markup=main_kb)

def can_beat(attack_card, defense_card, trump_suit):
    # Можно отбить, если:
    # 1. Карты одной масти и карта защиты старше
    # 2. Карта защиты козырь, а атаки не козырь
    attack_rank = ranks.index(attack_card[:-2]) if len(attack_card) == 3 else ranks.index(attack_card[:-1])
    defense_rank = ranks.index(defense_card[:-2]) if len(defense_card) == 3 else ranks.index(defense_card[:-1])
    attack_suit = attack_card[-2:] if len(attack_card) == 3 else attack_card[-1]
    defense_suit = defense_card[-2:] if len(defense_card) == 3 else defense_card[-1]

    if defense_suit == attack_suit and defense_rank > attack_rank:
        return True
    if defense_suit == trump_suit and attack_suit != trump_suit:
        return True
    return False

async def bot_defend(user_id):
    game = games[user_id]
    attack_card = game["attacking_card"]
    trump_suit = game["trump_suit"]
    bot_hand = game["bot_hand"]

    # Ищем карту, которой можно отбиться
    for card in bot_hand:
        if can_beat(attack_card, card, trump_suit):
            # Отбился
            game["defending_card"] = card
            bot_hand.remove(card)
            game["bot_hand"] = bot_hand
            game["table"].append((attack_card, card))
            game["attacking_card"] = None
            return True
    # Не смог отбиться
    return False

@dp.message_handler()
async def game_handler(message: types.Message):
    user_id = message.from_user.id
    text = message.text

    if user_id not in games or games[user_id]["game_over"]:
        await message.answer("Вы не в игре. Нажмите '🃏 Начать игру'.", reply_markup=main_kb)
        return

    game = games[user_id]

    if text == "🚪 Сдаться":
        game["game_over"] = True
        await message.answer("Вы сдались. Игра окончена.", reply_markup=main_kb)
        return

    if text not in game["player_hand"]:
        await message.answer("Выберите карту из вашей руки.", reply_markup=get_cards_kb(game["player_hand"]))
        return

    if not game["player_turn"]:
        await message.answer("Сейчас ходит бот, подождите...")
        return

    # Игрок атакует
    attack_card = text
    game["player_hand"].remove(attack_card)
    game["attacking_card"] = attack_card
    game["table"] = [(attack_card, None)]
    game["player_turn"] = False

    await message.answer(f"Вы ходите картой {attack_card}. Бот пытается отбиться...")

    # Ход бота: пытается отбиться
    if await bot_defend(user_id):
        await message.answer(f"Бот отбился картой {game['defending_card']}.\nВаши карты: {', '.join(game['player_hand'])}", reply_markup=get_cards_kb(game["player_hand"]))
        game["player_turn"] = True
        game["attacking_card"] = None
        game["defending_card"] = None
        game["table"] = []
    else:
        # Бот не отбился, берет карты
        game["bot_hand"].extend([attack_card])
        game["attacking_card"] = None
        game["table"] = []
        game["player_turn"] = True
        await message.answer("Бот не смог отбиться и забирает карты. Ваш ход снова, выберите карту.", reply_markup=get_cards_kb(game["player_hand"]))

    # Проверка окончания игры
    if len(game["player_hand"]) == 0:
        game["game_over"] = True
        await message.answer("Поздравляем! Вы выиграли!", reply_markup=main_kb)
    elif len(game["bot_hand"]) == 0:
        game["game_over"] = True
        await message.answer("Бот выиграл. Попробуйте еще раз!", reply_markup=main_kb)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
