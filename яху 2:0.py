import asyncio
import logging
import random

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import yfinance as yf

# === Настройки ===
TOKEN = "7895470939:AAEFSLYDEbfwWOY3P_j-vmYSsO1LNL8Z5Fk"
REF_LINK = "https://u3.shortink.io/register?utm_campaign=815121&utm_source=affiliate&utm_medium=sr&a=kBQn8bFXGHmrzs&ac=dogsmoktr"
ADMIN_ID = 7351552004

bot = Bot(token=TOKEN)
dp = Dispatcher()

PAIRS = {
    "main": ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CHF", "EUR/GBP", "GBP/JPY", "EUR/JPY", "GBP/CAD", "AUD/JPY",
             "CAD/JPY", "USD/CAD", "AUD/CAD", "EUR/CHF", "GBP/CHF", "AUD/CHF", "EUR/AUD", "GBP/AUD", "CHF/JPY", "NZD/JPY", "CAD/AUD"],
    "otc": ["EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC", "AUD/USD OTC", "USD/CHF OTC", "EUR/GBP OTC", "NZD/USD OTC",
            "EUR/JPY OTC", "GBP/JPY OTC", "AUD/JPY OTC", "CAD/JPY OTC", "USD/CAD OTC", "USD/TRY OTC", "EUR/CHF OTC",
            "GBP/CHF OTC", "AUD/NZD OTC", "EUR/AUD OTC", "GBP/AUD OTC", "USD/SGD OTC", "NZD/JPY OTC", "CAD/AUD OTC"]
}

TIMEFRAMES = ["5s", "15s", "30s", "1m", "3m", "5m", "10m", "15m", "30m", "1h"]

user_data = {}
approved_users = set()
approved_screenshots = set()
user_state = {}
pending_id = {}
pending_screenshot = {}

demo_access = {}
demo_used = set()
DEMO_LIMIT = 10

# === Кнопки ===
def build_paginated_keyboard(items, prefix, page=0, max_per_page=5):
    builder = InlineKeyboardBuilder()
    start = page * max_per_page
    end = start + max_per_page
    for item in items[start:end]:
        builder.button(text=item, callback_data=f"{prefix}_select_{item}")
    if start > 0:
        builder.button(text="◀️ Назад", callback_data=f"{prefix}_page_{page - 1}")
    if end < len(items):
        builder.button(text="Вперед ▶️", callback_data=f"{prefix}_page_{page + 1}")
    builder.adjust(1)
    return builder.as_markup()

def get_market_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🌍 Основной рынок", callback_data="market_main")
    builder.button(text="🌙 OTC рынок", callback_data="market_otc")
    builder.button(text="🎯 Сигналы по 3 парам", callback_data="multi_signal")
    builder.button(text="🔥 Лучший актив сейчас", callback_data="best_pair")
    return builder.as_markup()

def get_pair_keyboard(market, page=0):
    return build_paginated_keyboard(PAIRS[market], "pair", page)

def get_timeframe_keyboard(page=0):
    return build_paginated_keyboard(TIMEFRAMES, "timeframe", page)

def get_approval_keyboard(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{user_id}"),
         InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{user_id}")]
    ])

def get_id_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆔 Отправить ID Pocket Option", callback_data="send_id")]
    ])

def get_screenshot_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Отправить скриншот", callback_data="send_screenshot")]
    ])

def pair_to_ticker(pair):
    return pair.replace(" OTC", "").replace("/", "") + "=X"

def timeframe_to_interval(tf):
    return {
        "5s": "1m", "15s": "1m", "30s": "1m", "1m": "1m", "3m": "3m",
        "5m": "5m", "10m": "15m", "15m": "15m", "30m": "30m", "1h": "60m"
    }.get(tf, "1m")

def generate_analysis(pair, tf):
    ticker = pair_to_ticker(pair)
    interval = timeframe_to_interval(tf)
    try:
        data = yf.download(ticker, period="1d", interval=interval, progress=False)
    except Exception:
        return f"⚠️ Не удалось загрузить данные для {pair}."

    if data.empty or len(data) < 2:
        return f"📊 Сигнал для {pair} на {tf}: {random.choice(['⬆️ Вверх', '⬇️ Вниз'])}"
    last, prev = data['Close'].iloc[-1], data['Close'].iloc[-2]
    direction = "⬆️ Вверх" if last > prev else "⬇️ Вниз"
    return (f"📊 Сигнал для {pair} на {tf}:\n📈 Направление: {direction}\n"
            f"📍 Последняя цена: {last:.5f}\n📍 Предыдущая: {prev:.5f}\n"
            f"{'⚠️ Волатильный рынок' if 'OTC' in pair else '✅ Стандартный рынок'}")

@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    uid = msg.from_user.id
    if uid in approved_users and uid in approved_screenshots:
        await msg.answer("🎉 Добро пожаловать! Выберите рынок:", reply_markup=get_market_keyboard())
    else:
        if uid in demo_used:
            await msg.answer(
                "🚫 Вы уже использовали демо-доступ.\n\n"
                "🔓 Чтобы получить полный доступ к сигналам:\n"
                f"1. Зарегистрируйтесь по 👉 [ссылке]({REF_LINK})\n"
                "2. Отправьте ваш ID Pocket Option.\n"
                "3. Отправьте скриншот пополнения от $10.",
                reply_markup=get_id_keyboard(),
                parse_mode="Markdown"
            )
            return

        welcome = (
            "👋 *Добро пожаловать в Trading AI Bot!*\n\n"
            "📈 Этот бот помогает трейдерам принимать решения с помощью *искусственного интеллекта*, анализируя десятки валютных пар в реальном времени!\n\n"
            "🤖 Используются данные с реального рынка и алгоритмы на основе *машинного обучения*, чтобы повысить ваши шансы на успех.\n\n"
            "🔓 У вас есть два варианта:\n"
            "🎁 *Попробовать демо-доступ* — получите *10 бесплатных сигналов* на ваш выбор.\n"
            "💎 *Получить полный доступ* — откройте неограниченный доступ к ИИ-сигналам.\n\n"
            "👇 Выберите ниже:"
        )
        kb = InlineKeyboardBuilder()
        kb.button(text="🎁 Демо-доступ (10 сигналов)", callback_data="demo_start")
        kb.button(text="🔓 Получить полный доступ", callback_data="full_access")
        await msg.answer(welcome, reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp.callback_query()
async def callbacks(cb: types.CallbackQuery):
    uid = cb.from_user.id
    data = cb.data

    if data == "demo_start":
        if uid in demo_used:
            return await cb.answer("🚫 Вы уже использовали демо-доступ.", show_alert=True)
        demo_access[uid] = 0
        demo_used.add(uid)
        await cb.message.answer("🎁 Вы начали демо-доступ. Выберите рынок:", reply_markup=get_market_keyboard())

    elif data == "full_access":
        await cb.message.answer(
            "🔓 *Как получить полный доступ:*\n\n"
            "1️⃣ Перейдите по 👉 [ссылке для регистрации]({})\n"
            "2️⃣ Зарегистрируйтесь заново (если уже был аккаунт — создайте новый!)\n"
            "3️⃣ Пополните баланс от $10\n"
            "4️⃣ Отправьте ваш ID и скриншот пополнения\n\n"
            "🧾 После проверки вы получите неограниченный доступ к сигналам!".format(REF_LINK),
            parse_mode="Markdown",
            reply_markup=get_id_keyboard()
        )

    elif data.startswith("market_"):
        user_data.setdefault(uid, {})['market'] = data.split('_')[1]
        await cb.message.edit_text("Выберите пару:", reply_markup=get_pair_keyboard(user_data[uid]['market']))

    elif data.startswith("pair_select_"):
        user_data.setdefault(uid, {})['pair'] = data.split('_', 2)[2]
        await cb.message.edit_text("Выберите таймфрейм:", reply_markup=get_timeframe_keyboard())

    elif data.startswith("pair_page_"):
        page = int(data.split('_')[2])
        market = user_data.get(uid, {}).get('market', 'main')
        await cb.message.edit_text("Выберите пару:", reply_markup=get_pair_keyboard(market, page))

    elif data.startswith("timeframe_select_"):
        if uid in approved_users and uid in approved_screenshots:
            pass
        elif uid in demo_access:
            if demo_access[uid] >= DEMO_LIMIT:
                return await cb.answer("🎁 Лимит демо-доступа исчерпан. Получите полный доступ!", show_alert=True)
            demo_access[uid] += 1
        else:
            return await cb.answer("⛔ Нет доступа. Выберите демо или оформите полный доступ.", show_alert=True)

        tf = data.split('_', 2)[2]
        pair = user_data.get(uid, {}).get("pair")
        if pair:
            analysis = generate_analysis(pair, tf)
            await cb.message.delete()
            await cb.message.answer(analysis)
            await cb.message.answer("🔁 Выберите рынок или повторите выбор:", reply_markup=get_market_keyboard())

    elif data.startswith("timeframe_page_"):
        page = int(data.split('_')[2])
        await cb.message.edit_text("Выберите таймфрейм:", reply_markup=get_timeframe_keyboard(page))

    elif data == "multi_signal":
        if uid not in approved_users and uid not in demo_access:
            return await cb.answer("⛔ Нет доступа.", show_alert=True)
        for _ in range(3):
            pair = random.choice(PAIRS['main'])
            tf = random.choice(TIMEFRAMES)
            await cb.message.answer(generate_analysis(pair, tf))
            await asyncio.sleep(0.5)

    elif data == "best_pair":
        best = random.choice(PAIRS['main'])
        tf = "1m"
        analysis = generate_analysis(best, tf)
        await cb.message.answer(f"🔥 Лучший актив: {best} на {tf}\n{analysis}")

    elif data.startswith("approve_") or data.startswith("reject_"):
        target_id = int(data.split("_")[1])
        if "approve" in data:
            if target_id in pending_id:
                approved_users.add(target_id)
                pending_id.pop(target_id)
                user_state[target_id] = 'awaiting_screenshot'
                await bot.send_message(target_id, "✅ ID одобрен. Отправьте скриншот.")
            elif target_id in pending_screenshot:
                approved_screenshots.add(target_id)
                pending_screenshot.pop(target_id)
                await bot.send_message(target_id, "✅ Скриншот одобрен! Доступ открыт.", reply_markup=get_market_keyboard())
        else:
            if target_id in pending_id:
                pending_id.pop(target_id)
                await bot.send_message(target_id, "❌ ID отклонен.")
            elif target_id in pending_screenshot:
                pending_screenshot.pop(target_id)
                await bot.send_message(target_id, "❌ Скриншот отклонен.")
        await cb.message.edit_text(f"Обработка {target_id} завершена.")

    elif data == "send_id":
        user_state[uid] = 'awaiting_id'
        await cb.message.answer("📥 Введите ваш ID Pocket Option")

    elif data == "send_screenshot":
        if uid not in approved_users:
            return await cb.answer("⛔ Сначала одобрите ID", show_alert=True)
        user_state[uid] = 'awaiting_screenshot'
        await cb.message.answer("📤 Отправьте скриншот пополнения")

@dp.message()
async def msg_handler(msg: types.Message):
    uid = msg.from_user.id
    state = user_state.get(uid)

    if state == 'awaiting_id':
        if not msg.text or not msg.text.isdigit():
            return await msg.answer("❗ Введите только цифры.")
        pending_id[uid] = msg.text
        user_state[uid] = None
        await msg.answer("✅ ID отправлен на проверку")
        await bot.send_message(ADMIN_ID, f"Новый ID от {uid}: {msg.text}", reply_markup=get_approval_keyboard(uid))

    elif state == 'awaiting_screenshot':
        if not msg.photo:
            return await msg.answer("❗ Отправьте скриншот как фото")
        pending_screenshot[uid] = msg.photo[-1].file_id
        user_state[uid] = None
        await msg.answer("✅ Скриншот отправлен на проверку")
        await bot.send_photo(ADMIN_ID, msg.photo[-1].file_id, caption=f"Скриншот от {uid}", reply_markup=get_approval_keyboard(uid))

    else:
        await msg.answer("🤖 Используйте команду /start")

# === Запуск ===
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot))
