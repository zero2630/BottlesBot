import asyncio

from aiogram.fsm.storage.redis import RedisStorage
from sqlalchemy import update, delete

from handlers import user, commands
from bot import bot, dp
from middleware.spam_middleware import SpamMiddleware
from other.database import async_session_maker
from other.models import User


async def update_find_lim():
    while True:
        async with async_session_maker() as session:
            stmt = update(User).where(User.find_lim < 5).values(find_lim = User.find_lim + 1)
            await session.execute(stmt)
            await session.commit()
        await asyncio.sleep(30)


async def main():
    loop = asyncio.get_event_loop()
    loop.create_task(update_find_lim())
    storage = RedisStorage.from_url("redis://localhost:6379/0")
    dp.include_routers(
        commands.router, user.router
    )
    dp.message.middleware.register(SpamMiddleware(storage))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
