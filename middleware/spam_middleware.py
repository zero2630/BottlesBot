from typing import Callable, Any, Dict, Awaitable
import asyncio  # noqa: F401

from aiogram.types import TelegramObject, Message
from aiogram.enums.content_type import ContentType

import html


class SpamMiddleware:
    def __init__(self, storage):
        self.storage = storage

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ):
        user = event.from_user.id
        new_event = event

        text = ""
        if event.content_type == ContentType.TEXT:
            new_event = event.model_copy(update={"text": html.escape(event.text)})
            text = new_event.text
        elif event.content_type == ContentType.PHOTO:
            if event.caption:
                new_event = event.model_copy(
                    update={"caption": html.escape(event.caption)}
                )
                text = new_event.caption

        if len(text) > 1000:
            await event.answer("Слишком большой текст сообщения")
            return None

        check_user = await self.storage.redis.get(name=user)

        if check_user:
            if int(check_user.decode()) == 2:
                await self.storage.redis.set(name=user, value=1, ex=1)
                return await handler(new_event, data)
            elif int(check_user.decode()) == 1:
                await self.storage.redis.set(name=user, value=0, ex=5)
                await event.answer(
                    "Слишком частые сообщения. Бот приостановлен на 5 секунд"
                )
            return None
        await self.storage.redis.set(name=user, value=2, ex=1)

        return await handler(new_event, data)
