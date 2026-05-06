import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
import database

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        "👋 <b>Xush kelibsiz!</b>\n\n"
        "Bu bot orqali siz tashkilotlarni qidirishingiz mumkin.\n"
        "Qidirish uchun tashkilotning <b>raqamini</b>, <b>INN raqamini</b> yoki <b>nomining bir qismini</b> yuboring."
    )
    await message.answer(welcome_text)

@dp.message()
async def search_handler(message: types.Message):
    query = message.text
    if not query:
        return
        
    await message.answer("🔍 Qidirilmoqda...")
    
    results = database.search_organizations(query, limit=10)
    
    if not results:
        await message.answer("❌ Hech narsa topilmadi. Iltimos, boshqacha qidirib ko'ring.")
        return

    # Format the results
    response_lines = []
    response_lines.append(f"✅ <b>Topilgan natijalar ({len(results)} ta):</b>\n")
    
    for org in results:
        name = org.get('name', "Noma'lum")
        inn = org.get('inn', "Noma'lum")
        # phone = org.get('phone', "Mavjud emas")
        
        org_text = (
            f"🏢 <b>Nomi:</b> {name}\n"
            f"🆔 <b>INN:</b> <code>{inn}</code>\n"
            # f"📞 <b>Telefon:</b> {phone}\n"
            "➖➖➖➖➖➖➖➖➖➖"
        )
        response_lines.append(org_text)
        
    final_text = "\n".join(response_lines)
    
    # Telegram max message length is 4096 characters
    if len(final_text) > 4000:
        final_text = final_text[:4000] + "...\n(Xabar juda uzun, iltimos aniqroq qidiring)"
        
    await message.answer(final_text)

async def main():
    # Run the bot
    print("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if not BOT_TOKEN or BOT_TOKEN == "your_telegram_bot_token_here":
        print("ERROR: Please set a valid BOT_TOKEN in the .env file!")
        exit(1)
    asyncio.run(main())
