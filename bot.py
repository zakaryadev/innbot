import asyncio
import logging
import math
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import BOT_TOKEN, ADMIN_IDS
import database

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

ITEMS_PER_PAGE = 5


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# --- FSM States ---

class AddPhoneStates(StatesGroup):
    waiting_name = State()
    waiting_number = State()


class EditPhoneStates(StatesGroup):
    waiting_name = State()
    waiting_number = State()


class AddOrgStates(StatesGroup):
    waiting_name = State()
    waiting_inn = State()


class EditOrgStates(StatesGroup):
    waiting_name = State()
    waiting_inn = State()


# --- Keyboards ---

def get_org_menu_keyboard(org_id: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="📞 Telefon nomerleri", callback_data=f"phones:{org_id}")
    builder.button(text="✏️ Shólkemdi ózgertiw", callback_data=f"editorg:{org_id}")
    builder.button(text="🗑 Shólkemdi óshiriw", callback_data=f"delorg:{org_id}")
    builder.button(text="⬅️ Artqa", callback_data=f"closeorg")
    builder.adjust(1)
    return builder.as_markup()


def get_phones_keyboard(org_id: str, phones: list):
    builder = InlineKeyboardBuilder()

    for phone in phones:
        pid = phone['id']
        builder.button(text=f"✏️ {phone['phone_name']}", callback_data=f"editph:{pid}")
        builder.button(text="🗑", callback_data=f"delph:{pid}")

    builder.button(text="➕ Nomer qosıw", callback_data=f"addph:{org_id}")
    builder.button(text="⬅️ Artqa", callback_data=f"orgmenu:{org_id}")

    rows = [2] * len(phones) + [1, 1]
    builder.adjust(*rows)
    return builder.as_markup()


def get_delete_confirm_keyboard(phone_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Awa, óshir", callback_data=f"cdelph:{phone_id}")
    builder.button(text="❌ Yaq", callback_data=f"candelph:{phone_id}")
    builder.adjust(2)
    return builder.as_markup()


def get_org_delete_confirm_keyboard(org_id: str):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Awa, óshir", callback_data=f"cdelorg:{org_id}")
    builder.button(text="❌ Yaq", callback_data=f"candelorg:{org_id}")
    builder.adjust(2)
    return builder.as_markup()


# --- Format helpers ---

def format_org_result(org: dict, phones: list = None, index: int = None) -> str:
    name = org.get('name', "Belgisiz")
    inn = org.get('inn', "Belgisiz")
    similarity = org.get('similarity', 0)

    header = f"<b>{index}.</b> " if index else ""
    lines = [
        f"{header}🏢 <b>Ataması:</b> {name}",
        f"🆔 <b>INN:</b> <code>{inn}</code>",
        f"🎯 <b>Anıqlıq:</b> {similarity}%",
    ]

    if phones:
        for p in phones:
            lines.append(f"📞 <b>{p['phone_name']}:</b> {p['phone_number']}")

    lines.append("➖➖➖➖➖➖➖➖➖➖")
    return "\n".join(lines)


def format_phone_list(org: dict, phones: list) -> str:
    name = org.get('name', 'Belgisiz')
    lines = [f"📞 <b>{name}</b> — telefon nomerleri:\n"]

    if phones:
        for i, p in enumerate(phones, 1):
            lines.append(f"  {i}. <b>{p['phone_name']}</b>: {p['phone_number']}")
    else:
        lines.append("  <i>Hesh qanday nomer joq</i>")

    return "\n".join(lines)


# --- Handlers ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "👋 <b>Xosh keldińiz!</b>\n\n"
        "Bul bot arqalı siz shólkemlerdi izlewińiz múmkin.\n"
        "İzlew ushın shólkemniń <b>nomerin</b>, <b>INN nomerin</b> yamasa <b>atamasınıń bir bólegin</b> jiberiń."
    )
    if is_admin(message.from_user.id):
        welcome_text += (
            "\n\n🔑 <i>Siz admin sipatında tańıldıńız.</i>\n"
            "📋 Admin buyruqları:\n"
            "/addorg — Jaña shólkem qosıw"
        )
    await message.answer(welcome_text)


@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current = await state.get_state()
    if current:
        await state.clear()
        await message.answer("❌ Ámel biykar etildi.")
    else:
        await message.answer("Hesh qanday aktiv ámel joq.")


# --- Pagination ---

@dp.callback_query(F.data.startswith("page:"))
async def page_handler(callback: types.CallbackQuery):
    _, page_str, query = callback.data.split(":", 2)
    page = int(page_str)
    await process_search(callback.message, query, page, is_callback=True, user_id=callback.from_user.id)
    await callback.answer()


@dp.callback_query(F.data == "ignore")
async def ignore_callback(callback: types.CallbackQuery):
    await callback.answer()


# --- Org management menu ---

@dp.callback_query(F.data.startswith("orgmenu:"))
async def org_menu_handler(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizde admin huqıqı joq!", show_alert=True)
        return
    org_id = callback.data.split(":")[1]
    org = database.get_org_by_id(org_id)
    if not org:
        await callback.answer("❌ Shólkem tabılmadı", show_alert=True)
        return
    phones = database.get_phones_by_org(org_id)
    org['similarity'] = "—"
    text = format_org_result(org, phones)
    await callback.message.edit_text(text, reply_markup=get_org_menu_keyboard(org_id))
    await callback.answer()


@dp.callback_query(F.data == "closeorg")
async def close_org_menu(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer()


# --- Phone management callbacks ---

@dp.callback_query(F.data.startswith("phones:"))
async def phones_list_handler(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizde admin huqıqı joq!", show_alert=True)
        return
    org_id = callback.data.split(":")[1]
    org = database.get_org_by_id(org_id)
    if not org:
        await callback.answer("❌ Shólkem tabılmadı", show_alert=True)
        return
    phones = database.get_phones_by_org(org_id)
    text = format_phone_list(org, phones)
    markup = get_phones_keyboard(org_id, phones)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()


# --- Add Phone FSM ---

@dp.callback_query(F.data.startswith("addph:"))
async def add_phone_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizde admin huqıqı joq!", show_alert=True)
        return

    org_id = callback.data.split(":")[1]
    await state.set_state(AddPhoneStates.waiting_name)
    await state.update_data(org_id=org_id, msg_id=callback.message.message_id)
    await callback.message.edit_text(
        "📝 <b>Telefon nomeriniń atamasın jiberiń</b>\n"
        "<i>Mysalı: Direktór, Buxgalteriya, Qabıllaw bólimi</i>\n\n"
        "Biykar etiw ushın: /cancel"
    )
    await callback.answer()


@dp.message(AddPhoneStates.waiting_name)
async def add_phone_name(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Iltimas, tekst jiberiń.")
        return

    await state.update_data(phone_name=message.text.strip())
    await state.set_state(AddPhoneStates.waiting_number)
    await message.answer(
        "📱 <b>Endi telefon nomerin jiberiń</b>\n"
        "<i>Mysalı: +998 90 123 45 67</i>\n\n"
        "Biykar etiw ushın: /cancel"
    )


@dp.message(AddPhoneStates.waiting_number)
async def add_phone_number(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Iltimas, tekst jiberiń.")
        return

    data = await state.get_data()
    org_id = data['org_id']
    phone_name = data['phone_name']
    phone_number = message.text.strip()

    database.add_phone(org_id, phone_name, phone_number)
    await state.clear()

    org = database.get_org_by_id(org_id)
    phones = database.get_phones_by_org(org_id)
    text = f"✅ <b>Nomer qosıldı!</b>\n\n{format_phone_list(org, phones)}"
    markup = get_phones_keyboard(org_id, phones)
    await message.answer(text, reply_markup=markup)


# --- Edit Phone FSM ---

@dp.callback_query(F.data.startswith("editph:"))
async def edit_phone_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizde admin huqıqı joq!", show_alert=True)
        return

    phone_id = int(callback.data.split(":")[1])
    phone = database.get_phone_by_id(phone_id)
    if not phone:
        await callback.answer("❌ Nomer tabılmadı", show_alert=True)
        return

    await state.set_state(EditPhoneStates.waiting_name)
    await state.update_data(phone_id=phone_id, org_id=phone['org_id'],
                            old_name=phone['phone_name'], old_number=phone['phone_number'])
    await callback.message.edit_text(
        f"✏️ <b>Nomer atamasın ózgertiw</b>\n\n"
        f"Házirgi atama: <b>{phone['phone_name']}</b>\n\n"
        f"Jaña atamanı jiberiń yamasa /skip basıń (ózgertpew ushın)\n"
        f"Biykar etiw: /cancel"
    )
    await callback.answer()


@dp.message(EditPhoneStates.waiting_name)
async def edit_phone_name(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Iltimas, tekst jiberiń.")
        return

    data = await state.get_data()

    if message.text.strip() == "/skip":
        new_name = data['old_name']
    else:
        new_name = message.text.strip()

    await state.update_data(new_name=new_name)
    await state.set_state(EditPhoneStates.waiting_number)
    await message.answer(
        f"📱 <b>Telefon nomerin ózgertiw</b>\n\n"
        f"Házirgi nomer: <b>{data['old_number']}</b>\n\n"
        f"Jaña nomerin jiberiń yamasa /skip basıń (ózgertpew ushın)\n"
        f"Biykar etiw: /cancel"
    )


@dp.message(EditPhoneStates.waiting_number)
async def edit_phone_number(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Iltimas, tekst jiberiń.")
        return

    data = await state.get_data()

    if message.text.strip() == "/skip":
        new_number = data['old_number']
    else:
        new_number = message.text.strip()

    new_name = data['new_name']
    phone_id = data['phone_id']
    org_id = data['org_id']

    database.update_phone(phone_id, new_name, new_number)
    await state.clear()

    org = database.get_org_by_id(org_id)
    phones = database.get_phones_by_org(org_id)
    text = f"✅ <b>Nomer jańalandı!</b>\n\n{format_phone_list(org, phones)}"
    markup = get_phones_keyboard(org_id, phones)
    await message.answer(text, reply_markup=markup)


# --- Delete Phone ---

@dp.callback_query(F.data.startswith("delph:"))
async def delete_phone_confirm(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizde admin huqıqı joq!", show_alert=True)
        return

    phone_id = int(callback.data.split(":")[1])
    phone = database.get_phone_by_id(phone_id)
    if not phone:
        await callback.answer("❌ Nomer tabılmadı", show_alert=True)
        return

    await callback.message.edit_text(
        f"⚠️ <b>Bul nomerin óshiriwdi tastıyqlaysız ba?</b>\n\n"
        f"📞 <b>{phone['phone_name']}:</b> {phone['phone_number']}",
        reply_markup=get_delete_confirm_keyboard(phone_id)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("cdelph:"))
async def delete_phone_execute(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizde admin huqıqı joq!", show_alert=True)
        return

    phone_id = int(callback.data.split(":")[1])
    phone = database.get_phone_by_id(phone_id)
    if not phone:
        await callback.answer("❌ Nomer tabılmadı", show_alert=True)
        return

    org_id = phone['org_id']
    database.delete_phone(phone_id)

    org = database.get_org_by_id(org_id)
    phones = database.get_phones_by_org(org_id)
    text = f"🗑 <b>Nomer óshirildi!</b>\n\n{format_phone_list(org, phones)}"
    markup = get_phones_keyboard(org_id, phones)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()


@dp.callback_query(F.data.startswith("candelph:"))
async def delete_phone_cancel(callback: types.CallbackQuery):
    phone_id = int(callback.data.split(":")[1])
    phone = database.get_phone_by_id(phone_id)
    if not phone:
        await callback.answer("❌ Nomer tabılmadı", show_alert=True)
        return

    org_id = phone['org_id']
    org = database.get_org_by_id(org_id)
    phones = database.get_phones_by_org(org_id)
    text = format_phone_list(org, phones)
    markup = get_phones_keyboard(org_id, phones)
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()


# --- Add Organization FSM ---

@dp.message(Command("addorg"))
async def add_org_start(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizde admin huqıqı joq!")
        return
    await state.set_state(AddOrgStates.waiting_name)
    await message.answer(
        "🏢 <b>Jaña shólkemniń atamasın jiberiń</b>\n\n"
        "Biykar etiw: /cancel"
    )


@dp.message(AddOrgStates.waiting_name)
async def add_org_name(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Iltimas, tekst jiberiń.")
        return
    await state.update_data(org_name=message.text.strip())
    await state.set_state(AddOrgStates.waiting_inn)
    await message.answer(
        "🆔 <b>INN nomerin jiberiń</b>\n\n"
        "Biykar etiw: /cancel"
    )


@dp.message(AddOrgStates.waiting_inn)
async def add_org_inn(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Iltimas, tekst jiberiń.")
        return
    data = await state.get_data()
    org_name = data['org_name']
    inn = message.text.strip()
    new_id = database.add_organization(org_name, inn)
    await state.clear()
    await message.answer(
        f"✅ <b>Shólkem qosıldı!</b>\n\n"
        f"🏢 <b>Ataması:</b> {org_name}\n"
        f"🆔 <b>INN:</b> <code>{inn}</code>\n"
        f"🔢 <b>ID:</b> {new_id}"
    )


# --- Edit Organization FSM ---

@dp.callback_query(F.data.startswith("editorg:"))
async def edit_org_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizde admin huqıqı joq!", show_alert=True)
        return
    org_id = callback.data.split(":")[1]
    org = database.get_org_by_id(org_id)
    if not org:
        await callback.answer("❌ Shólkem tabılmadı", show_alert=True)
        return
    await state.set_state(EditOrgStates.waiting_name)
    await state.update_data(org_id=org_id, old_name=org['name'], old_inn=org['inn'])
    await callback.message.edit_text(
        f"✏️ <b>Shólkem atamasın ózgertiw</b>\n\n"
        f"Házirgi atama: <b>{org['name']}</b>\n\n"
        f"Jaña atamanı jiberiń yamasa /skip (ózgertpew ushın)\n"
        f"Biykar etiw: /cancel"
    )
    await callback.answer()


@dp.message(EditOrgStates.waiting_name)
async def edit_org_name(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Iltimas, tekst jiberiń.")
        return
    data = await state.get_data()
    new_name = data['old_name'] if message.text.strip() == "/skip" else message.text.strip()
    await state.update_data(new_name=new_name)
    await state.set_state(EditOrgStates.waiting_inn)
    await message.answer(
        f"🆔 <b>INN nomerin ózgertiw</b>\n\n"
        f"Házirgi INN: <b>{data['old_inn']}</b>\n\n"
        f"Jaña INN jiberiń yamasa /skip (ózgertpew ushın)\n"
        f"Biykar etiw: /cancel"
    )


@dp.message(EditOrgStates.waiting_inn)
async def edit_org_inn(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Iltimas, tekst jiberiń.")
        return
    data = await state.get_data()
    new_inn = data['old_inn'] if message.text.strip() == "/skip" else message.text.strip()
    database.update_organization(data['org_id'], data['new_name'], new_inn)
    await state.clear()
    org = database.get_org_by_id(data['org_id'])
    phones = database.get_phones_by_org(data['org_id'])
    org['similarity'] = "—"
    text = f"✅ <b>Shólkem jańalandı!</b>\n\n{format_org_result(org, phones)}"
    await message.answer(text, reply_markup=get_org_menu_keyboard(data['org_id']))


# --- Delete Organization ---

@dp.callback_query(F.data.startswith("delorg:"))
async def delete_org_confirm(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizde admin huqıqı joq!", show_alert=True)
        return
    org_id = callback.data.split(":")[1]
    org = database.get_org_by_id(org_id)
    if not org:
        await callback.answer("❌ Shólkem tabılmadı", show_alert=True)
        return
    phones = database.get_phones_by_org(org_id)
    phone_count = len(phones)
    warn = f"\n⚠️ <i>{phone_count} telefon nomer de óshiriledi!</i>" if phone_count else ""
    await callback.message.edit_text(
        f"⚠️ <b>Bul shólkemdi óshiriwdi tastıyqlaysız ba?</b>\n\n"
        f"🏢 {org['name']}\n"
        f"🆔 INN: {org['inn']}{warn}",
        reply_markup=get_org_delete_confirm_keyboard(org_id)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("cdelorg:"))
async def delete_org_execute(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizde admin huqıqı joq!", show_alert=True)
        return
    org_id = callback.data.split(":")[1]
    org = database.get_org_by_id(org_id)
    if not org:
        await callback.answer("❌ Shólkem tabılmadı", show_alert=True)
        return
    name = org['name']
    database.delete_organization(org_id)
    await callback.message.edit_text(f"🗑 <b>Shólkem óshirildi:</b> {name}")
    await callback.answer()


@dp.callback_query(F.data.startswith("candelorg:"))
async def delete_org_cancel(callback: types.CallbackQuery):
    org_id = callback.data.split(":")[1]
    org = database.get_org_by_id(org_id)
    if not org:
        await callback.answer("❌ Shólkem tabılmadı", show_alert=True)
        return
    phones = database.get_phones_by_org(org_id)
    org['similarity'] = "—"
    text = format_org_result(org, phones)
    await callback.message.edit_text(text, reply_markup=get_org_menu_keyboard(org_id))
    await callback.answer()


# --- Search ---

@dp.message()
async def search_handler(message: types.Message, state: FSMContext):
    # If user is in FSM state, skip search
    current = await state.get_state()
    if current:
        return

    query = message.text
    if not query:
        return
    await process_search(message, query, 1, user_id=message.from_user.id)


async def process_search(message: types.Message, query: str, page: int,
                          is_callback: bool = False, user_id: int = 0):
    if not is_callback:
        processing_msg = await message.answer("🔍 İzlenbekte...")

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

    response_lines = [f"✅ <b>Tabılǵan nátiyjeler ({total_results} dana):</b>\n"]

    admin = is_admin(user_id)
    org_ids_on_page = []

    for i, org in enumerate(page_results, 1):
        phones = database.get_phones_by_org(str(org.get('id', '')))
        response_lines.append(format_org_result(org, phones, index=i if admin else None))
        org_ids_on_page.append(str(org.get('id', '')))

    final_text = "\n".join(response_lines)

    if admin:
        response_lines.append("\n⚙️ <i>Basqarıw ushın tómendegi tuymelerni basıń:</i>")
        final_text = "\n".join(response_lines)

    # Build keyboard
    builder = InlineKeyboardBuilder()

    # Admin management buttons — compact numbered in one row
    if admin:
        for i, org in enumerate(page_results, 1):
            org_id = str(org.get('id', ''))
            builder.button(
                text=f"⚙️ {i}",
                callback_data=f"orgmenu:{org_id}"
            )

    # Pagination
    q_safe = query[:30]
    nav_count = 0
    if total_pages > 1:
        if page > 1:
            builder.button(text="⬅️ Aldınǵı", callback_data=f"page:{page-1}:{q_safe}")
            nav_count += 1
        builder.button(text=f"{page} / {total_pages}", callback_data="ignore")
        nav_count += 1
        if page < total_pages:
            builder.button(text="Keyingi ➡️", callback_data=f"page:{page+1}:{q_safe}")
            nav_count += 1

    # Layout: phone buttons in one row, then nav row
    rows = []
    if admin:
        rows.append(len(page_results))  # all phone buttons in one row
    if nav_count:
        rows.append(nav_count)

    if rows:
        builder.adjust(*rows)

    markup = builder.as_markup() if (admin or total_pages > 1) else None

    if len(final_text) > 4000:
        final_text = final_text[:4000] + "...\n(Xabar júdá uzın, iltimas anıǵıraq izleń)"

    if is_callback:
        await message.edit_text(final_text, reply_markup=markup)
    else:
        await processing_msg.edit_text(final_text, reply_markup=markup)


async def main():
    # Initialize phone_numbers table
    database.init_phone_table()
    print("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if not BOT_TOKEN or BOT_TOKEN == "your_telegram_bot_token_here":
        print("ERROR: Please set a valid BOT_TOKEN in the .env file!")
        exit(1)
    asyncio.run(main())
