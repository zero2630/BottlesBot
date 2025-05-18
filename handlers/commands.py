import asyncio

from aiogram.filters import Command, CommandStart
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.redis import RedisStorage
from sqlalchemy import insert, select, delete, update

from keyboards import reply
from other import states
from other import settings
from other.models import User
from other.database import async_session_maker
from bot import bot


router = Router()


@router.message(CommandStart())
async def command_start(message: Message):
    print(message.from_user.id)
    text = ("<b>Отправляй</b> послания в бутылке и вылавливай чужие\n"
            "<b>Пиши</b> ответы на найденные послания и читай ответы к своим\n"
            "Все послания <b>анонимны</b>")

    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == message.from_user.id)
        res = (await session.execute(stmt)).first()
        if not res:
            stmt = insert(User).values(tg_id=message.from_user.id)
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
            tasks = [asyncio.create_task(bot.send_message(chat_id=usr[0], text=send_text)) for usr in ids]
            for task in asyncio.as_completed(tasks):
                try:
                    await task
                except:
                    None


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
