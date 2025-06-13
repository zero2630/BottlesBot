import asyncio  # noqa: F401

from aiogram.filters import Command, CommandStart
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.storage.redis import RedisStorage
from sqlalchemy import insert, select, update

from keyboards import reply
from other.models import User, RefLink
from other.database import async_session_maker


router = Router()

start_text = (
    "<b>Отправляй</b> послания в бутылке и вылавливай чужие\n"
    "<b>Пиши</b> ответы на найденные послания и читай ответы к своим\n"
    "<b>Можно отправлять текст, gif, фото и кружочки</b>\n"
    "Все послания <b>анонимны</b>\n"
    "Напиши /rules чтобы узнать правила"
)


@router.message(CommandStart(deep_link=True))
async def command_start_deeplink(message: Message, command: Command):

    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == message.from_user.id)
        res = (await session.execute(stmt)).first()
        if not res:
            reflink_uid = command.args
            stmt = (
                update(RefLink)
                .where(RefLink.uid == reflink_uid)
                .values(count=RefLink.count + 1)
            )
            await session.execute(stmt)
            stmt = insert(User).values(tg_id=message.from_user.id)
            await session.execute(stmt)
            await session.commit()

    await message.answer(start_text, reply_markup=reply.main)


@router.message(CommandStart())
async def command_start(message: Message, command: Command):

    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == message.from_user.id)
        res = (await session.execute(stmt)).first()
        if not res:
            stmt = insert(User).values(tg_id=message.from_user.id)
            await session.execute(stmt)
            await session.commit()

    await message.answer(start_text, reply_markup=reply.main)


@router.message(Command("online"))
async def command_check_online(message: Message):
    banned_storage = RedisStorage.from_url("redis://localhost:6379/1")
    val = await banned_storage.redis.get(name="online")
    await message.answer(f"<b>Текущий онлайн</b>: {int(val)} человек")


@router.message(Command("rules"))
async def command_rules(message: Message):
    await message.answer(
        "<b>Общие правила</b>:\n"
        "1. Порнография в открытом виде запрещена.\n"
        "2. Никакой расчлененки.\n"
        "3. Маты допускаются в умеренном количестве.\n"
        "4. Не писать оскорбления в чей-либо адрес.\n"
        "5. Никакой рекламы, это не рекламная биржа.\n"
        "6. Обсуждение политики под БОЛЬШИМ вопросом. Лучше не стоит.\n"
        "За нарушения будете получать предупреждения."
        "За 1, 2, 5 пункты можно сразу отлететь в бан\n\n"
        "<b>Правила для щитпост режима</b>:\n"
        "1. Запрещена реклама\n"
        "2. Запрещены экстремистские высказывания, изображения\n"
        "3. Не допускаются картинки с жестоким обращением, особенно с детьми\n"
    )
