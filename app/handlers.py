from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.text_decorations import markdown_decoration as md
from app.database.models import User
from app.database.models import async_session
from app.database.system import admins_id, password, owners_id
from sqlalchemy import select
from logger import logger

import re
import logging
import app.keyboards as kb
import app.database.requests as rq

router = Router()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AddUser(StatesGroup):
    fio = State()
    number = State()
    email = State()
    adres = State()
    dr = State()
    info = State()

class SearchFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        user_state = await rq.get_user_state(message.from_user.id)
        return user_state in ["input_number", "input_fio"]

class UserActions(StatesGroup):
    input_password = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await rq.set_user(message.from_user.id, message.from_user.username)
    await rq.set_user_state(message.from_user.id, "start_bot")
    user_id = message.from_user.id
    logger.info(f"\n\nКористувач @{message.from_user.username}\nID: {message.from_user.id}\nІм'я: {message.from_user.first_name}\nПрізвище: {message.from_user.last_name}\nВикористав команду /start\n")
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == user_id))
        if not user:
            user = User(tg_id=user_id, attempts=3)
            session.add(user)
            await session.commit()
        if user.attempts <= 0:
            await message.answer("Доступ заборонено. Спроби закінчилися.")
            return
    if await rq.banned_user(user_id):
        logger.warning(f"\nКористувач @{message.from_user.username} ID: {message.from_user.id} спробував використати бот у бані.\n")
    elif message.from_user.id in admins_id:
        await message.answer('Вітаю Вас у нашій команді.', reply_markup=kb.admin_menu)
    else:
        await message.answer("Введіть пароль для доступу к боту:")
        await rq.set_user_state(message.from_user.id, 'login')
        await state.set_state(UserActions.input_password)


@router.message(UserActions.input_password)
async def check_password(message: Message, state: FSMContext):
    user_id = message.from_user.id
    logger.info(f"\n\nКористувач @{message.from_user.username} ID: {message.from_user.id} ввів пароль: {message.text}\n")
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == user_id))
        attempts = user.attempts
        if message.text == password:
            await message.answer("Пароль вірний. Ласкаво просимо!", reply_markup=kb.menu)
            user.attempts = 3
            await session.commit()
            await state.clear()
            await rq.set_user_state(message.from_user.id, 'good_login')
        else:
            attempts -= 1
            if attempts > 0:
                await message.answer(f"Неправильний пароль. Залишилось спроб: {attempts}.")
                user.attempts = attempts
                await session.commit()
            elif attempts <= 0:
                await message.answer("Спроби закінчились. Доступ закрито. ")
                await session.commit()
                await state.clear


@router.message(Command("unbanme"))
async def unban_me(message: Message):
    if message.from_user.id in owners_id:
        success = await rq.unban_user(message.from_user.id)
        if success:
            await message.answer("Ви успішно розблокували себе!")
        else:
            await message.answer("Ви не заблоковані.")

@router.message(SearchFilter())
async def handle_search_message(message: Message):
    user_state = await rq.get_user_state(message.from_user.id)
    await handle_search(message, user_state)

async def handle_search(message: Message, user_state: str):
    await rq.set_user(message.from_user.id, message.from_user.username)
    if await rq.banned_user(message.from_user.id):
        logger.warning(f"\nКористувач @{message.from_user.username} ID: {message.from_user.id} спробував використати бот у бані.\n")
    else:
        if user_state == "input_number":
            number = message.text.replace(" ", "").replace("+", "").replace("-", "").replace("(", "").replace(")", "")
            if number.startswith("0") and len(number) == 10:
                number = "38" + number
            elif number.startswith("38") and len(number) == 12:
                pass

            username = message.from_user.username
            logger.info(f"\nКористувач @{username} ID: {message.from_user.id} шукав: {number}\n")

            if re.fullmatch(r"38\d{10}", number):
                users_info = await rq.search_by_number(number)
                if users_info:
                    response = "Знайдено таку інформацію:\n\n"
                    for user in users_info:
                        if user.number != None:
                            user.number = "+" + str(user.number)
                        response += (
                            f"ПІБ: {user.fio}\n"
                            f"Номер: {user.number}\n"
                            f"Email: {user.email}\n"
                            f"Адреса: {user.adres}\n"
                            f"Дата народження: {user.dr}\n"
                            f"Інша інформація: {user.info}\n\n\n")
                    await message.answer(response, reply_markup=kb.back_keyboard)
                else:
                    await message.answer("Інформацію не знайдено.", reply_markup=kb.back_keyboard)
            else:
                await message.answer("Неправильний формат, спробуйте знову.")

        elif user_state == "input_fio":
            looking_fio = message.text.strip()
            username = message.from_user.username
            logger.info(f"\n\nКористувач @{username} ID: {message.from_user.id} шукав: {looking_fio}\n")
            users = await rq.search_by_fio(looking_fio)
            if users:
                response = "Знайдено таку інформацію:\n\n"
                for user in users:
                    if user.number != None:
                        user.number = "+" + str(user.number)
                    response += (
                        f"ПІБ: {user.fio}\n"
                        f"Номер: {user.number}\n"
                        f"Email: {user.email}\n"
                        f"Адреса: {user.adres}\n"
                        f"Дата народження: {user.dr}\n"
                        f"Інша інформація: {user.info}\n\n\n")
                await message.answer(response, reply_markup=kb.back_keyboard)
            else:
                await message.answer("Інформацію не знайдено.", reply_markup=kb.back_keyboard)

@router.callback_query(F.data == "search_number")
async def search_number(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_state = await rq.get_user_state(callback.from_user.id)
    if await rq.banned_user(user_id):
        logger.warning(f"\n\nУвага! Користувач: @{callback.from_user.username} ID: {callback.from_user.id}\nСпробував використати бот у бані.\n")
    elif user_state == "login":
        await callback.answer("Введіть пароль для доступу!")
        logger.warning(f"\n\nУвага! Користувач: @{callback.from_user.username} ID: {callback.from_user.id}\nСпробував обійти пароль.\n")
    else:
        await callback.answer('')
        await callback.message.answer("Введіть номер телефону: 380ХХХХХХХХХ")
        await rq.set_user_state(callback.from_user.id, "input_number")

@router.callback_query(F.data == "search_fio")
async def search_fio(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_state = await rq.get_user_state(callback.from_user.id)
    if await rq.banned_user(user_id):
        logger.warning(f"\n\nУвага! Користувач: @{callback.from_user.username} ID: {callback.from_user.id}\nСпробував використати бот у бані.\n")
    elif user_state == "login":
        await callback.answer("Введіть пароль для доступу!")
        logger.warning(f"\n\nУвага! Користувач: @{callback.from_user.username} ID: {callback.from_user.id}\nСпробував обійти пароль.\n")
    else:
        await callback.answer('')
        await callback.message.answer("Введіть ПІБ або Прізвище:")
        await rq.set_user_state(callback.from_user.id, "input_fio")

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    if await rq.banned_user(user_id):
        await callback.answer('')
        logger.warning(f"\n\nУвага! Користувач: @{callback.from_user.username} ID: {callback.from_user.id}\nСпробував використати бот у бані.\n")
    else:
        await callback.answer('')
        await rq.set_user_state(callback.from_user.id, "menu")
        if user_id in admins_id:
            await callback.message.delete()
            await callback.message.answer("---------- Головне меню ----------\n\nВиберіть дію:", reply_markup=kb.admin_menu)
        else:
            await callback.message.delete()
            await callback.message.answer("---------- Головне меню ----------\n\nВиберіть дію:", reply_markup=kb.menu)


@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery, state: FSMContext):
    await rq.set_user_state(callback.from_user.id, "admin_panel")
    await state.clear()
    if await rq.banned_user(callback.from_user.id):
        logger.warning(f"\n\nУвага! Адмін @{callback.from_user.username} ID: {callback.from_user.id}\nСпробував використати бот у бані.\n")
    else:
        await callback.answer('')
        await callback.message.delete()
        await callback.message.answer("Панель адміністратора", reply_markup=kb.admin_panel)

@router.callback_query(F.data == "add_user")
async def add_user_start(callback: CallbackQuery, state: FSMContext):
    await rq.set_user_state(callback.from_user.id, "add_users")
    await state.clear()
    if await rq.banned_user(callback.from_user.id):
        logger.warning(f"\n\nУвага! Адмін @{callback.from_user.username} ID: {callback.from_user.id}\nСпробував використати бот у бані.\n")
    else:
        await callback.answer('')
        await callback.message.answer("Введіть ПІБ:")
        await state.set_state(AddUser.fio)

@router.message(AddUser.fio)
async def add_user_fio(message: Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await message.answer("Введіть номер телефону:\nФормат: 380123456789")
    await state.set_state(AddUser.number)

@router.message(AddUser.number)
async def add_user_phone(message: Message, state: FSMContext):
    await state.update_data(number=message.text)
    await message.answer("Введіть email:")
    await state.set_state(AddUser.email)

@router.message(AddUser.email)
async def add_user_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer("Введіть адресу:")
    await state.set_state(AddUser.adres)

@router.message(AddUser.adres)
async def add_user_address(message: Message, state: FSMContext):
    await state.update_data(adres=message.text)
    await message.answer("Введіть дату народження:\nФормат: ДД.ММ.РРРР")
    await state.set_state(AddUser.dr)

@router.message(AddUser.dr)
async def add_user_birthdate(message: Message, state: FSMContext):
    await state.update_data(dr=message.text)
    await message.answer("Введіть додаткову інформацію:")
    await state.set_state(AddUser.info)

@router.message(AddUser.info)
async def add_user_info(message: Message, state: FSMContext):
    await state.update_data(info=message.text)
    data = await state.get_data()
    admin_username = message.from_user.username
    admin_id = message.from_user.id
    logger.info(f"\n\nАдміністратор @{admin_username} ID: {admin_id} добавив користувача: {data}\n")
    await rq.add_user_info(data)
    await message.answer("Інформація успішно додана!", reply_markup=kb.admin_panel)
    await state.clear()


class AdminActions(StatesGroup):
    ban_user = State()
    unban_user = State()

@router.callback_query(F.data == "ban_user")
async def ban_user_start(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback.from_user.id
    if await rq.banned_user(user_id):
        logger.warning(f"\n\nУвага! Адмін @{callback.from_user.username} ID: {callback.from_user.id}\nСпробував використати бот у бані.\n")
    else:
        await callback.answer('')
        await rq.set_user_state(callback.from_user.id, "ban_user")
        unbanned_users = await rq.get_unbanned_users()
        user_list = []
        for tg_id, tg_name in unbanned_users:
            safe_name = md.quote(tg_name) if tg_name else "Юзернейм відсутній"
            user_list.append(f"ID: `{tg_id}`, Юзернейм: {safe_name}")
        await callback.message.answer("Список незаблокованих користувачів:\n" + "\n".join(user_list) + "\n\nВведіть ID користувача для блокування:", reply_markup=kb.back_to_admin_menu, parse_mode="MarkdownV2")
        await state.set_state(AdminActions.ban_user)

@router.callback_query(F.data == "unban_user")
async def unban_user_start(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback.from_user.id
    if await rq.banned_user(user_id):
        logger.warning(f"\n\nУвага! Адмін @{callback.from_user.username} ID: {callback.from_user.id}\nСпробував використати бот у бані.\n")
    else:
        await callback.answer('')
        await rq.set_user_state(callback.from_user.id, "unban_user")
        banned_users = await rq.get_banned_users()
        user_list = []
        for tg_id, tg_name in banned_users:
            safe_name = md.quote(tg_name) if tg_name else "Юзернейм відсутній"
            user_list.append(f"ID: `{tg_id}`, Юзернейм: {safe_name}")
        await callback.message.answer("Список заблокованих користувачів:\n" + "\n".join(user_list) + "\n\nВведіть ID користувача для розблокування:", reply_markup=kb.back_to_admin_menu, parse_mode="MarkdownV2")
        await state.set_state(AdminActions.unban_user)

@router.message(AdminActions.ban_user)
async def ban_user_by_id(message: Message):
    if message.from_user.id not in admins_id:
        logger.warning(f"\n\nКористувач @{message.from_user.username} ID: {message.from_user.id}\nСпробував використати команду адміністратора.\n")
        return
    try:
        user_id_to_ban = int(message.text)
        admin_username = message.from_user.username
        admin_id = message.from_user.id
        already = await rq.banned_user(user_id_to_ban)
        if user_id_to_ban in owners_id and admin_id not in owners_id:
            await message.answer("У Вас не вистачає прав для цієї дії!", reply_markup=kb.back_to_admin_menu)
            logger.warning(f"\n\n!!!!!Увага!!!!!\nАдмиіністратор @{admin_username} ID: {admin_id} спробував заблокувати ВЛАСНИКА з ID: {user_id_to_ban}\n")
        elif user_id_to_ban in owners_id and admin_id in owners_id:
            success = await rq.ban_user(user_id_to_ban)
            if already:
                await message.answer(f"ВЛАСНИК `{user_id_to_ban}` вже заблокован", reply_markup=kb.back_to_admin_menu, parse_mode="MarkdownV2")
                logger.info(f"\n\nВЛАСНИК @{admin_username} ID: {admin_id} спробував заблокувати вже заблокованого ВЛАСНИКА з ID: {user_id_to_ban}\n")
            elif success:
                await message.answer(f"Увага\\! Ви заблокували одного з ВЛАСНИКІВ бота\nID: `{user_id_to_ban}`", reply_markup=kb.back_to_admin_menu, parse_mode="MarkdownV2")
                logger.info(f"\n\nВЛАСНИК @{admin_username} ID: {admin_id} заблокував ВЛАСНИКА з ID: {user_id_to_ban}\n")
            else:
                await message.answer(f"Користувач `{user_id_to_ban}` не знайдено у базі даних", reply_markup=kb.back_to_admin_menu, parse_mode="MarkdownV2")
                logger.info(f"\n\nВЛАСНИК @{admin_username} ID: {admin_id} спробував заблокувати ВЛАСНИКА з ID: {user_id_to_ban}\n")
        else:
            success = await rq.ban_user(user_id_to_ban)
            if already:
                await message.answer(f"Користувач `{user_id_to_ban}` вже заблокован", reply_markup=kb.back_to_admin_menu, parse_mode="MarkdownV2")
                logger.info(f"\n\nАдміністратор @{admin_username} ID: {admin_id} спробував заблокувати вже заблокованого користувача з ID: {user_id_to_ban}\n")
            elif success:
                await message.answer(f"Користувач `{user_id_to_ban}` успішно заблокован", reply_markup=kb.back_to_admin_menu, parse_mode="MarkdownV2")
                logger.info(f"\n\nАдміністратор @{admin_username} ID: {admin_id} заблокував користувача з ID: {user_id_to_ban}\n")
            else:
                await message.answer(f"Користувач `{user_id_to_ban}` не знайденно у базі даних", reply_markup=kb.back_to_admin_menu, parse_mode="MarkdownV2")
                logger.info(f"\n\nАдміністратор @{admin_username} ID: {admin_id} спробував заблокувати користувача з ID: {user_id_to_ban}\n")
    except ValueError:
        await message.answer("Неправильний формат. Введіть числовий ID:", reply_markup=kb.back_to_admin_menu)

@router.message(AdminActions.unban_user)
async def unban_user_by_id(message: Message):
    if message.from_user.id not in admins_id:
        logger.warning(f"\n\nКористувач @{message.from_user.username} ID: {message.from_user.id}\nСпробував використати команду адміністратора.\n")
        return
    try:
        user_id_to_unban = int(message.text)
        admin_username = message.from_user.username
        admin_id = message.from_user.id
        already = await rq.banned_user(user_id_to_unban)
        success = await rq.unban_user(user_id_to_unban)
        if not already:
            await message.answer(f"Користувач `{user_id_to_unban}` вже розблоковано", reply_markup=kb.back_to_admin_menu, parse_mode="MarkdownV2")
            logger.info(f"\n\nАдміністратор @{admin_username} ID: {admin_id} спробував розблокував вже розблокованого користувача з ID: {user_id_to_unban}\n")
        elif success:
            await message.answer(f"Користувач `{user_id_to_unban}` успішно разблокован", reply_markup=kb.back_to_admin_menu, parse_mode="MarkdownV2")
            logger.info(f"\n\nАдміністратор @{admin_username} ID: {admin_id} розблокував користувача з ID: {user_id_to_unban}\n")
        else:
            await message.answer(f"Користувач `{user_id_to_unban}` не знайденно у базі даних", reply_markup=kb.back_to_admin_menu, parse_mode="MarkdownV2")
            logger.info(f"\n\nАдміністратор @{admin_username} ID: {admin_id} спробував розблокувати користувача з ID: {user_id_to_unban}\n")
    except ValueError:
        await message.answer("Неправильний формат. Введіть числовий ID:", reply_markup=kb.back_to_admin_menu)

