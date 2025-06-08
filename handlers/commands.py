import asyncio
import hashlib

from aiogram.filters import Command, CommandStart
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.utils.deep_linking import create_start_link, decode_payload
from sqlalchemy import insert, select, delete, update

from keyboards import reply
from other import states
from other import settings
from other.models import User, RefLink, UserSettings
from other.database import async_session_maker
from keyboards import inline
from bot import bot


router = Router()


@router.message(CommandStart(deep_link=True))
async def command_start(message: Message, command: Command):
    text = ("<b>Отправляй</b> послания в бутылке и вылавливай чужие\n"
            "<b>Пиши</b> ответы на найденные послания и читай ответы к своим\n"
            "Все послания <b>анонимны</b>\n"
            "Напиши /rules чтобы узнать правила")

    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == message.from_user.id)
        res = (await session.execute(stmt)).first()
        if not res:
            reflink_uid = command.args
            stmt = update(RefLink).where(RefLink.uid == reflink_uid).values(count=RefLink.count + 1)
            await session.execute(stmt)
            stmt = insert(User).values(tg_id=message.from_user.id)
            await session.execute(stmt)
            await session.commit()
            stmt = insert(UserSettings).values(usr=message.from_user.id)
            await session.execute(stmt)
        await session.commit()

    await message.answer(text, reply_markup=reply.main)


@router.message(CommandStart())
async def command_start(message: Message, command: Command):
    text = ("<b>Отправляй</b> послания в бутылке и вылавливай чужие\n"
            "<b>Пиши</b> ответы на найденные послания и читай ответы к своим\n"
            "Все послания <b>анонимны</b>\n"
            "Напиши /rules чтобы узнать правила")

    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == message.from_user.id)
        res = (await session.execute(stmt)).first()
        if not res:
            stmt = insert(User).values(tg_id=message.from_user.id)
            await session.execute(stmt)
            await session.commit()
            stmt = insert(UserSettings).values(usr=message.from_user.id)
            await session.execute(stmt)
        await session.commit()

    await message.answer(text, reply_markup=reply.main)


@router.message(Command("deluser"))
async def command_deluser(message: Message):
    if str(message.from_user.id) in settings.ADMINS:
        async with async_session_maker() as session:
            stmt = delete(User).where(User.tg_id == int(message.text.split()[1]))
            await session.execute(stmt)
            await session.commit()
        await message.answer(f"user {message.text.split()[1]} deleted")


@router.message(Command("unban"))
async def command_unban(message: Message):
    if str(message.from_user.id) in settings.ADMINS:
        async with async_session_maker() as session:
            usr_id = int(message.text.split()[1])
            stmt = update(User).where(User.tg_id == usr_id).values(is_banned=False)
            await session.execute(stmt)
            await session.commit()

        banned_storage = RedisStorage.from_url("redis://localhost:6379/1")
        await banned_storage.redis.set(name=usr_id, value=0, ex=300)
        await message.answer(f"user {usr_id} unbanned")
        await bot.send_message(chat_id=usr_id, text="Вас разбанили")


@router.message(Command("send_all"))
async def command_sendall(message: Message):
    if str(message.from_user.id) in settings.ADMINS:
        async with async_session_maker() as session:
            stmt = select(User.tg_id)
            ids = (await session.execute(stmt)).all()
            await session.commit()

            send_text = " ".join(message.text.split(" ")[1:])
            tasks = [asyncio.create_task(bot.send_message(chat_id=usr[0], text=send_text, reply_markup=inline.answ_admin())) for usr in ids]
            for task in asyncio.as_completed(tasks):
                try:
                    await task
                except:
                    None


@router.callback_query(inline.AnswAdmin.filter(F.action == "answ_admin"))
async def tap_answ_admin(call: CallbackQuery, callback_data: inline.AnswAdmin, state: FSMContext):
    await state.set_state(states.AnswAdmin.answ)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("Напиши свой ответ:", reply_markup=reply.main)


@router.message(states.AnswAdmin.answ)
async def send_answer_admin_success(message: Message, state: FSMContext):
    await state.clear()

    await message.answer("Ответ был направлен админу")

    await bot.send_message(chat_id=settings.ADMINS[0], text=f"Вам написал пользователь:\n<blockquote>{message.text}</blockquote>")


@router.message(Command("ban"))
async def command_ban(message: Message):
    if str(message.from_user.id) in settings.ADMINS:
        async with async_session_maker() as session:
            usr = int(message.text.split()[1])
            stmt = update(User).where(User.tg_id == usr).values(is_banned=True)
            await session.execute(stmt)
            await session.commit()

        banned_storage = RedisStorage.from_url("redis://localhost:6379/1")
        await banned_storage.redis.set(name=usr, value=1, ex=300)
        await bot.send_message(chat_id=usr, text="Вас забанили")
        await message.answer(f"Пользователь {usr} забанен️", reply_markup=reply.main)


@router.message(Command("isadmin"))
async def command_isadmin(message: Message):
    if str(message.from_user.id) in settings.ADMINS:
        await message.answer(f"true")


@router.message(Command("create_invite"))
async def command_create_invite(message: Message, command: Command):
    if str(message.from_user.id) in settings.ADMINS:
        reflink_name = command.args
        reflink_hash = hashlib.md5(reflink_name.encode("utf-8")).hexdigest()
    async with async_session_maker() as session:
        stmt = insert(RefLink).values(uid=reflink_hash, name=reflink_name)
        await session.execute(stmt)
        await session.commit()

    link = await create_start_link(bot, reflink_hash)
    await message.answer(f"link: {link}")


@router.message(Command("online"))
async def check_online(message: Message):
    banned_storage = RedisStorage.from_url("redis://localhost:6379/1")
    val = await banned_storage.redis.get(name="online")
    await message.answer(f"<b>Текущий онлайн</b>: {int(val)} человек")


@router.message(Command("rules"))
async def check_online(message: Message):
    await message.answer("<b>Общие правила</b>:\n"
                         "1. Порнография в открытом виде запрещена.\n"
                         "2. Никакой расчлененки.\n"
                         "3. Маты допускаются в умеренном количестве.\n"
                         "4. Не писать оскорбления в чей-либо адрес.\n"
                         "5. Никакой рекламы, это не рекламная биржа.\n"
                         "6. Обсуждение политики под БОЛЬШИМ вопросом. Лучше не стоит.\n"
                         "За нарушения будете получать предупреждения. За 1, 2, 5 пункты можно сразу отлететь в бан")
