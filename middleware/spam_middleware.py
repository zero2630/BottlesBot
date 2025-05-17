from typing import Callable, Any, Dict, Awaitable
import asyncio
import datetime

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

class SpamMiddleware():
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
            if int(check_user.decode()) == 2:
                await self.storage.redis.set(name=user, value=1, ex=1)
                return await handler(event, data)
            elif int(check_user.decode()) == 1:
                await self.storage.redis.set(name=user, value=0, ex=5)
                await event.answer("Слишком частые сообщения. Бот приостановлен на 5 секунд")
            return None
        await self.storage.redis.set(name=user, value=2, ex=1)

        return await handler(event, data)