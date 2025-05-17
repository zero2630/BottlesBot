from aiogram.filters import Command, CommandStart
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import insert, select, delete

from keyboards import reply
from other import states
from other import settings
from other.models import User
from other.database import async_session_maker


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
async def command_admin(message: Message):
    if str(message.from_user.id) in settings.ADMINS:
        async with async_session_maker() as session:
            stmt = delete(User).where(User.tg_id == int(message.text.split()[1]))
            await session.execute(stmt)
            await session.commit()
        await message.answer(f"user {message.text.split()[1]} deleted")


@router.message(Command("isadmin"))
async def command_admin(message: Message):
    if str(message.from_user.id) in settings.ADMINS:
        await message.answer(f"true")
