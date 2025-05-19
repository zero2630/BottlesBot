import asyncio

from aiogram.fsm.storage.redis import RedisStorage
from sqlalchemy import update, delete, select

from handlers import user, commands
from bot import bot, dp
from middleware.spam_middleware import SpamMiddleware
from middleware.ban_middleware import BanMiddleware
from other.database import async_session_maker
from other.models import User


async def update_lim():
    while True:
        async with async_session_maker() as session:
            stmt = update(User).where(User.find_lim < 5).values(find_lim = User.find_lim + 1)
            await session.execute(stmt)
            stmt = update(User).where(User.send_lim < 3).values(send_lim=User.send_lim + 1)
            await session.execute(stmt)
            await session.commit()
        await asyncio.sleep(60)


async def update_rating():
    while True:
        async with async_session_maker() as session:
            stmt = select(User).order_by(User.likes_amount.desc())
            users = (await session.execute(stmt)).all()
            tasks = [asyncio.create_task(session.execute(update(User).where(User.id == users[i][0].id).values(rating_place=i+1))) for i in range(len(users))]
            for task in asyncio.as_completed(tasks):
                await task

            await session.commit()
        await asyncio.sleep(600)


async def main():
    loop = asyncio.get_event_loop()
    loop.create_task(update_lim())
    loop.create_task(update_rating())
    storage = RedisStorage.from_url("redis://localhost:6379/0")
    banned_storage = RedisStorage.from_url("redis://localhost:6379/1")
    dp.include_routers(
        commands.router, user.router
    )
    dp.message.middleware.register(SpamMiddleware(storage))
    dp.message.middleware.register(BanMiddleware(banned_storage))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
