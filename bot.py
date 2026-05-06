import asyncio
import logging
import math
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import BOT_TOKEN
import database

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

ITEMS_PER_PAGE = 5

def get_pagination_keyboard(query: str, current_page: int, total_pages: int):
    builder = InlineKeyboardBuilder()
    
    # Store query in callback, but truncate to 30 chars to avoid 64-byte limit
    q_safe = query[:30]
    
    if current_page > 1:
        builder.button(text="⬅️ Aldınǵı", callback_data=f"page:{current_page-1}:{q_safe}")
        
    builder.button(text=f"{current_page} / {total_pages}", callback_data="ignore")
    
    if current_page < total_pages:
        builder.button(text="Keyingi ➡️", callback_data=f"page:{current_page+1}:{q_safe}")
        
    builder.adjust(3 if current_page > 1 and current_page < total_pages else 2)
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        "👋 <b>Xosh keldińiz!</b>\n\n"
        "Bul bot arqalı siz shólkemlerdi izlewińiz múmkin.\n"
        "İzlew ushın shólkemniń <b>nomerin</b>, <b>INN nomerin</b> yamasa <b>atamasınıń bir bólegin</b> jiberiń."
    )
    await message.answer(welcome_text)

@dp.callback_query(F.data.startswith("page:"))
async def page_handler(callback: types.CallbackQuery):
    _, page_str, query = callback.data.split(":", 2)
    page = int(page_str)
    
    await process_search(callback.message, query, page, is_callback=True)
    await callback.answer()

@dp.callback_query(F.data == "ignore")
async def ignore_callback(callback: types.CallbackQuery):
    await callback.answer()

@dp.message()
async def search_handler(message: types.Message):
    query = message.text
    if not query:
        return
    await process_search(message, query, 1)

async def process_search(message: types.Message, query: str, page: int, is_callback: bool = False):
    if not is_callback:
        processing_msg = await message.answer("🔍 İzlenbekte...")
    
    # Fetch up to 50 results
    results = database.search_organizations(query, limit=50)
    
    if not results:
        text = "❌ Hesh nárse tabılmadı. Iltimas, qaytadan izlep kóriń."
        if is_callback:
            await message.edit_text(text)
        else:
            await processing_msg.edit_text(text)
        return

    total_results = len(results)
    total_pages = math.ceil(total_results / ITEMS_PER_PAGE)
    
    if page > total_pages:
        page = total_pages
        
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    page_results = results[start_idx:end_idx]

    # Format the results
    response_lines = []
    response_lines.append(f"✅ <b>Tabılǵan nátiyjeler ({total_results} dana):</b>\n")
    
    for org in page_results:
        name = org.get('name', "Belgisiz")
        inn = org.get('inn', "Belgisiz")
        similarity = org.get('similarity', 0)
        
        org_text = (
            f"🏢 <b>Ataması:</b> {name}\n"
            f"🆔 <b>INN:</b> <code>{inn}</code>\n"
            f"🎯 <b>Anıqlıq:</b> {similarity}%\n"
            "➖➖➖➖➖➖➖➖➖➖"
        )
        response_lines.append(org_text)
        
    final_text = "\n".join(response_lines)
    markup = get_pagination_keyboard(query, page, total_pages) if total_pages > 1 else None
    
    # Telegram max message length is 4096 characters
    if len(final_text) > 4000:
        final_text = final_text[:4000] + "...\n(Xabar júdá uzın, iltimas anıǵıraq izleń)"
    
    if is_callback:
        await message.edit_text(final_text, reply_markup=markup)
    else:
        await processing_msg.edit_text(final_text, reply_markup=markup)

async def main():
    # Run the bot
    print("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if not BOT_TOKEN or BOT_TOKEN == "your_telegram_bot_token_here":
        print("ERROR: Please set a valid BOT_TOKEN in the .env file!")
        exit(1)
    asyncio.run(main())
