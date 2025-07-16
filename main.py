import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from flask import Flask, request
import threading
import os

API_TOKEN = "8188119649:AAEC5lTlyPTTskGxO_d5APGKXE8iKmZKwbo"
WEBHOOK_HOST = "https://a-b-c-zon5.onrender.com"  # Render URL
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

ADMIN_ID = 5515940119
GROUP_ID = -1001356511143  # Guruh ID ni to'g'rilash kerak

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Foydalanuvchilar ro'yxati
users = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = {"subscribed": False}
    await message.answer("Salom! To'lov qilgan bo'lsangiz, chekni yuboring.")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        total_users = len(users)
        await message.answer(f"👥 Jami foydalanuvchilar: {total_users}")
    else:
        await message.answer("Siz admin emassiz.")

@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        user_list = "\n".join([str(uid) for uid in users.keys()])
        await message.answer(f"📄 Foydalanuvchilar ro'yxati:\n{user_list}")
    else:
        await message.answer("Siz admin emassiz.")

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        args = message.text.split()
        if len(args) == 2 and args[1].isdigit():
            user_id = int(args[1])
            if user_id in users:
                users.pop(user_id)
                await bot.send_message(user_id, "❌ Obunangiz bekor qilindi.")
                await message.answer(f"✅ Foydalanuvchi {user_id} o'chirildi.")
            else:
                await message.answer("⚠️ Bunday foydalanuvchi topilmadi.")
        else:
            await message.answer("⚠️ /cancel [user_id] shaklida yuboring.")
    else:
        await message.answer("Siz admin emassiz.")

@dp.message()
async def handle_payment(message: types.Message):
    if message.photo:
        user_id = message.from_user.id
        users[user_id] = {"subscribed": True}
        await message.answer("✅ To'lovingiz tasdiqlandi.")
        await bot.send_message(ADMIN_ID, f"💰 Yangi foydalanuvchi: {user_id}")
    else:
        await message.answer("📸 Iltimos, to'lov chekini rasm sifatida yuboring.")

# Flask app for webhook
app = Flask(__name__)

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = types.Update(**request.json)
    asyncio.run(dp.feed_update(bot, update))
    return {"ok": True}

def start_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

def set_webhook():
    asyncio.run(bot.set_webhook(WEBHOOK_URL))

if __name__ == "__main__":
    threading.Thread(target=start_flask).start()
    set_webhook()
