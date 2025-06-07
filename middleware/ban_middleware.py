from typing import Callable, Any, Dict, Awaitable
import asyncio
import datetime

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from sqlalchemy import select, insert

from other.database import async_session_maker
from other.models import User

class BanMiddleware():
    def __init__(self, storage):
        self.storage = storage

    async def __call__(self,
                 handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                 event: Message,
                 data: Dict[str, Any]
                 ):
        user = event.from_user.id
        check_user = await self.storage.redis.get(name=user)

        if check_user:
            if int(check_user.decode()) == 1:
                return None
            return await handler(event, data)
        else:
            async with async_session_maker() as session:
                stmt = select(User.is_banned).where(User.tg_id == user)
                res = (await session.execute(stmt)).first()
                if res:
                    is_banned = int(res[0])
                    await self.storage.redis.set(name=user, value=is_banned, ex=10)
                    if is_banned:
                        return None

                else:
                    stmt = insert(User).values(tg_id=user)
                    await session.execute(stmt)
                    await session.commit()
        return await handler(event, data)
