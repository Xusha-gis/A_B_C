import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import BOT_TOKEN, ADMIN_ID, CHANNEL_LINK, CARD_INFO
from database import init_db, add_user, get_user, get_all_users, remove_user
from keep_alive import keep_alive
from datetime import datetime, timedelta

# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Baza va Flask serverni ishga tushirish
init_db()
keep_alive()

# ✅ Obunani tekshiruvchi va eslatmalar yuboruvchi funksiyalar
async def check_subscriptions():
    while True:
        users = get_all_users()
        now = datetime.now()
        for user in users:
            user_id = user[0]
            end_date = datetime.fromisoformat(user[2])
            days_left = (end_date - now).days

            # ⚠️ 2 kun qolganda eslatma yuborish
            if days_left == 2:
                try:
                    await bot.send_message(
                        user_id,
                        "⏳ Obunangiz tugashiga 2 kun qoldi. Obunani yangilash uchun adminga to‘lovni yuboring."
                    )
                    print(f"📢 2 kun eslatmasi yuborildi: {user_id}")
                except Exception as e:
                    print(f"⚠️ Eslatma yuborib bo‘lmadi: {e}")

            # ❌ Obuna tugagan foydalanuvchilarni chiqarish
            if now > end_date:
                try:
                    await bot.ban_chat_member(CHANNEL_LINK, user_id)
                    await bot.unban_chat_member(CHANNEL_LINK, user_id)
                    await bot.send_message(
                        user_id,
                        "❌ Obunangiz muddati tugadi. Kanalga kirish huquqingiz o‘chirildi."
                    )
                    print(f"✅ Foydalanuvchi {user_id} obunadan chiqarildi.")
                except Exception as e:
                    print(f"⚠️ Kanal yoki xabar bilan xato: {e}")
                remove_user(user_id)
        await asyncio.sleep(3600)  # Har 1 soatda tekshiradi


# /start komandasi
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user = get_user(message.from_user.id)
    if user:
        end_date = datetime.fromisoformat(user[2]).strftime("%Y-%m-%d")
        await message.answer(
            f"✅ Siz premium obunachisiz!\n⏳ Obuna tugash sanasi: {end_date}"
        )
    else:
        await message.answer(
            f"""👋 Salom! Premium kanalga kirish uchun to‘lov qilishingiz kerak.

💳 Narx: 20 000 so‘m
💰 To‘lov uchun Humo karta: {CARD_INFO}

✅ To‘lov qilgan bo‘lsangiz, chekni shu yerga yuboring. Admin tekshiradi va tasdiqlasa sizga kanal linki keladi."""
        )


# Chek yuborilganda
@dp.message(lambda message: message.photo)
async def handle_photo(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await bot.send_photo(
            ADMIN_ID,
            message.photo[-1].file_id,
            caption=(
                f"📥 Yangi to‘lov cheki!\n"
                f"👤 Foydalanuvchi: {message.from_user.full_name}\n"
                f"🆔 ID: {message.from_user.id}"
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{message.from_user.id}"),
                        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{message.from_user.id}")
                    ]
                ]
            )
        )
        await message.reply("✅ Chekingiz adminga yuborildi. Tekshiruv jarayonida kuting...")
    else:
        await message.reply("⚠️ Admin siz chek yubora olmaysiz.")


# /stats komandasi (admin uchun)
@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ Siz admin emassiz!")
        return
    users = get_all_users()
    total_users = len(users)
    await message.reply(f"📊 Statistika:\n👥 Jami obunachilar: {total_users}")


# /users komandasi (admin uchun)
@dp.message(Command("users"))
async def users_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ Siz admin emassiz!")
        return
    users = get_all_users()
    if users:
        text = "📋 Obunachilar ro‘yxati:\n\n"
        for user in users:
            text += f"🆔 ID: {user[0]}\n📅 Tugash: {user[2]}\n---\n"
        await message.reply(text)
    else:
        await message.reply("📭 Obuna olgan foydalanuvchilar yo‘q.")


# /remove komandasi (admin uchun)
@dp.message(Command("remove"))
async def remove_user_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ Siz admin emassiz!")
        return
    try:
        user_id = int(message.text.split()[1])  # /remove 123456789

        # Foydalanuvchini bazadan o‘chirish
        remove_user(user_id)

        # Kanaldan chiqarish
        try:
            await bot.ban_chat_member(CHANNEL_LINK, user_id)
            await bot.unban_chat_member(CHANNEL_LINK, user_id)
        except Exception as e:
            await message.reply(f"⚠️ Kanalda foydalanuvchini chiqarib bo‘lmadi: {e}")

        # Foydalanuvchiga xabar yuborish
        try:
            await bot.send_message(
                user_id,
                "❌ Sizning premium obunangiz bekor qilindi. Kanalga kirish huquqingiz o‘chirildi."
            )
        except Exception as e:
            await message.reply(f"⚠️ Foydalanuvchiga xabar yuborib bo‘lmadi: {e}")

        await message.reply(f"✅ Foydalanuvchi {user_id} obunadan chiqarildi va xabar yuborildi.")
    except Exception as e:
        await message.reply("⚠️ Xatolik: /remove USER_ID formatida yozing.")


# Inline tugmalarni ishlovchi handler
@dp.callback_query()
async def callback_handler(callback_query: types.CallbackQuery):
    data = callback_query.data
    if data.startswith("approve_"):
        user_id = int(data.split("_")[1])
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)
        add_user(user_id, start_date.isoformat(), end_date.isoformat())
        try:
            await bot.send_message(
                user_id,
                f"✅ Obunangiz tasdiqlandi!\n"
                f"📎 Kanalga ulanish: {CHANNEL_LINK}\n"
                f"⏳ Tugash: {end_date.strftime('%Y-%m-%d')}"
            )
        except Exception as e:
            await callback_query.message.answer(f"❌ Xabar yuborib bo‘lmadi: {e}")
        await callback_query.message.edit_text(
            f"✅ Foydalanuvchi {user_id} obunaga qo‘shildi."
        )
    elif data.startswith("reject_"):
        user_id = int(data.split("_")[1])
        await bot.send_message(user_id, "❌ To‘lovingiz rad etildi. Qayta urinib ko‘ring.")
        await callback_query.message.edit_text(f"❌ Foydalanuvchi {user_id} rad etildi.")


# Botni ishga tushirish
async def main():
    print("✅ Bot ishga tushdi...")
    asyncio.create_task(check_subscriptions())  # Obunani tekshirish
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
