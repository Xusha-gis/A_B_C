import asyncio
from datetime import datetime, timedelta
from database import get_all_users, remove_user
from config import CHANNEL_LINK
from aiogram import Bot
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)

async def check_subscriptions():
    while True:
        users = get_all_users()
        for user in users:
            user_id, _, end_date = user
            end = datetime.fromisoformat(end_date)
            days_left = (end - datetime.now()).days

            if days_left == 2:
                await bot.send_message(user_id, f"⏳ Obunangiz tugashiga 2 kun qoldi. Obunani uzaytirishni unutmang!")

            if datetime.now() > end:
                try:
                    await bot.send_message(user_id, "❌ Obunangiz muddati tugadi. Kanalga kirish uchun qayta to‘lov qiling.")
                    remove_user(user_id)
                except:
                    pass
        await asyncio.sleep(86400)  # 24 soatda bir tekshiradi

def start_scheduler():
    asyncio.create_task(check_subscriptions())
