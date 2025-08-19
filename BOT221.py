import asyncio
import logging
import json
import random
import yfinance as yf
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from config import TOKEN, ADMIN_ID, REF_LINK

bot = Bot(token=TOKEN)
dp = Dispatcher()

# === Функции для сигналов ===
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
    return f"📊 Сигнал для {pair} на {tf}\n📈 {direction}\nЦена: {last:.5f}"

# === Команды ===
@dp.message(Command("start"))
async def start_cmd(msg: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Открыть GPT DOG TRADE", web_app=WebAppInfo(url="https://yourdomain.com"))]
    ])
    await msg.answer(
        "👋 Добро пожаловать в GPT DOG TRADE!\n\n"
        "📌 Зарегистрируйтесь по ссылке и отправьте свой ID.\n"
        "После пополнения депозита мы одобрим ваш доступ.",
        reply_markup=kb
    )

# === WebApp данные ===
@dp.message()
async def handle_webapp(msg: types.Message):
    if msg.web_app_data:  
        payload = json.loads(msg.web_app_data.data)

        if payload["action"] == "send_id":
            await bot.send_message(ADMIN_ID, f"🆔 Новый ID от {msg.from_user.id}: {payload['value']}")
            await msg.answer("✅ ID отправлен на проверку")

        elif payload["action"] == "deposit":
            await bot.send_message(ADMIN_ID, f"💵 Пользователь {msg.from_user.id} пополнил депозит")
            await msg.answer("✅ Сообщение отправлено админу")

        elif payload["action"] == "signal":
            analysis = generate_analysis(payload["pair"], payload["tf"])
            await msg.answer(analysis)

        elif payload["action"] == "reset":
            await msg.answer("🔄 Сигнал сброшен")

        elif payload["action"] == "home":
            await msg.answer("🏠 Вы вернулись на главную")

# === Запуск ===
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(dp.start_polling(bot))
