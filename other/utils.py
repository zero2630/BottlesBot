import asyncio  # noqa: F401
import random
from datetime import datetime, timedelta

from sqlalchemy import insert, select, update, not_

from keyboards import inline
from bot import bot
from other.database import async_session_maker
from other.models import User, Bottle, Viewed


async def increment_user_value(tg_id, **kwargs):
    async with async_session_maker() as session:
        stmt = update(User).where(User.tg_id == tg_id).values(**kwargs)
        await session.execute(stmt)
        await session.commit()


def get_find_stmt(tg_id, mode):
    if random.randint(1, 2) == 1:
        stmt = (
            select(Bottle)
            .order_by(Bottle.views)
            .order_by(Bottle.rating.desc())
            .where(
                not_(Bottle.id.in_(select(Viewed.bottle).where(Viewed.person == tg_id)))
            )
            .where(not_(Bottle.id.in_(select(Bottle.id).where(Bottle.author == tg_id))))
            .where(Bottle.is_active == True)
            .where(Bottle.bad == mode)
        )
    else:
        stmt = (
            select(Bottle)
            .order_by(Bottle.rating.desc())
            .where(
                not_(Bottle.id.in_(select(Viewed.bottle).where(Viewed.person == tg_id)))
            )
            .where(not_(Bottle.id.in_(select(Bottle.id).where(Bottle.author == tg_id))))
            .where(Bottle.is_active == True)
            .where(Bottle.bad == mode)
        )

    return stmt


async def send_bottle_multitype(bottle, tg_id, markup, add_text):
    if bottle.type == "text":
        return await bot.send_message(
            chat_id=tg_id, text=add_text + bottle.text, reply_markup=markup
        )
    elif bottle.type == "img":
        return await bot.send_photo(
            chat_id=tg_id,
            photo=bottle.file_id,
            caption=add_text + bottle.text,
            reply_markup=markup,
        )
    elif bottle.type == "anim":
        return await bot.send_animation(
            chat_id=tg_id, animation=bottle.file_id, reply_markup=markup
        )
    elif bottle.type == "note":
        return await bot.send_video_note(
            chat_id=tg_id, video_note=bottle.file_id, reply_markup=markup
        )
    elif bottle.type == "sticker":
        return await bot.send_sticker(
            chat_id=tg_id, sticker=bottle.file_id, reply_markup=markup
        )
    elif bottle.type == "video":
        return await bot.send_video(
            chat_id=tg_id, video=bottle.file_id, caption=add_text+bottle.text, reply_markup=markup
        )
    return None


async def get_rand_bottle(tg_id):
    async with async_session_maker() as session:
        stmt = select(User.p_bad_mode).where(User.tg_id == tg_id)
        mode = (await session.execute(stmt)).first()[0]
        stmt = get_find_stmt(tg_id, mode)
        res = (await session.execute(stmt)).first()
        if res:
            bottle = res[0]
            stmt = (
                update(Bottle)
                .where(Bottle.id == bottle.id)
                .values(views=bottle.views + 1)
            )
            await session.execute(stmt)
            stmt = insert(Viewed).values(person=tg_id, bottle=bottle.id)
            await session.execute(stmt)
            await session.commit()

            await increment_user_value(tg_id, find_amount=User.find_amount + 1)
            date = datetime.strptime(str(bottle.created_at)[:16], "%Y-%m-%d %H:%M")
            date = date + timedelta(hours=3)
            str_date = date.strftime("%Y-%m-%d %H:%M")
            await send_bottle_multitype(
                bottle,
                tg_id,
                inline.action_bottle(
                    bottle.id,
                    True,
                    True,
                    (not mode),
                    tg_id,
                    bottle.likes,
                    bottle.dislikes,
                ),
                f"<b>Твое послание</b>:\n<i>{str_date} МСК</i>\n\n",
            )
