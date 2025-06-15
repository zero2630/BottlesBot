import asyncio  # noqa: F401
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import insert, select, update

from keyboards import reply, inline
from bot import bot
from other import states
from other.database import async_session_maker
from other.models import User, Bottle, Viewed, Report
from other import button_text
from other import settings
from other import utils


router = Router()


@router.message(F.text.casefold() == button_text.main_but2)
async def get_bottle(message: Message):
    async with async_session_maker() as session:
        stmt = select(User.p_bad_mode).where(User.tg_id == message.from_user.id)
        mode = (await session.execute(stmt)).first()[0]
        stmt = utils.get_find_stmt(message.from_user.id, mode)
        res = (await session.execute(stmt)).first()
        if res:
            bottle = res[0]
            stmt = (
                update(Bottle)
                .where(Bottle.id == bottle.id)
                .values(views=bottle.views + 1)
            )
            await session.execute(stmt)
            stmt = insert(Viewed).values(person=message.from_user.id, bottle=bottle.id)
            await session.execute(stmt)
            await session.commit()

            await utils.increment_user_value(
                message.from_user.id, find_amount=User.find_amount + 1
            )
            date = datetime.strptime(str(bottle.created_at)[:16], "%Y-%m-%d %H:%M")
            date = date + timedelta(hours=3)
            str_date = date.strftime("%Y-%m-%d %H:%M")
            await utils.send_bottle_multitype(
                bottle,
                message.from_user.id,
                inline.action_bottle(
                    bottle.id,
                    True,
                    True,
                    (not mode),
                    message.from_user.id,
                    bottle.likes,
                    bottle.dislikes,
                ),
                f"<b>Твое послание</b>:\n<i>{str_date} МСК</i>\n\n",
            )
        else:
            await message.answer(
                "<b>Новых посланий нет</b> 😭", reply_markup=reply.main
            )


@router.callback_query(inline.Reaction.filter(F.action == "like"))
async def tap_like(call: CallbackQuery, callback_data: inline.Reaction):
    async with async_session_maker() as session:
        stmt = select(Bottle.author).where(Bottle.id == callback_data.bottle_id)
        bottle_author = (await session.execute(stmt)).first()[0]
        stmt = (
            update(Bottle)
            .where(Bottle.id == callback_data.bottle_id)
            .values(rating=Bottle.rating + 10, likes=Bottle.likes + 1)
        )
        await session.execute(stmt)
        await session.commit()

    await utils.increment_user_value(bottle_author, likes=User.likes + 1)
    await utils.increment_user_value(bottle_author, likes_amount=User.likes_amount + 1)
    await call.message.edit_reply_markup(
        reply_markup=inline.action_bottle(
            callback_data.bottle_id,
            False,
            callback_data.answ_enabled,
            callback_data.rep_enabled,
            callback_data.tg_id,
        )
    )
    await call.message.answer("❤️", reply_markup=reply.main)

    await bot.send_message(bottle_author, "Вам отправили ❤️")


@router.callback_query(inline.Reaction.filter(F.action == "dislike"))
async def tap_dislike(call: CallbackQuery, callback_data: inline.Reaction):
    async with async_session_maker() as session:
        stmt = (
            update(Bottle)
            .where(Bottle.id == callback_data.bottle_id)
            .values(rating=Bottle.rating - 15, dislikes=Bottle.dislikes + 1)
        )
        await session.execute(stmt)
        await session.commit()

    await call.message.edit_reply_markup(
        reply_markup=inline.action_bottle(
            callback_data.bottle_id,
            False,
            callback_data.answ_enabled,
            callback_data.rep_enabled,
            callback_data.tg_id,
        )
    )
    await call.message.answer("🤮", reply_markup=reply.main)


@router.callback_query(inline.Reaction.filter(F.action == "answ"))
async def tap_answ(
    call: CallbackQuery, callback_data: inline.Reaction, state: FSMContext
):
    async with async_session_maker() as session:
        stmt = select(Bottle).where(Bottle.id == callback_data.bottle_id)
        bottle = (await session.execute(stmt)).first()[0]
    await state.set_state(states.SendAnswer.answ)
    await state.update_data(answ=callback_data)
    await call.message.edit_reply_markup(
        reply_markup=inline.action_bottle(
            callback_data.bottle_id,
            callback_data.react_enabled,
            False,
            callback_data.rep_enabled,
            callback_data.tg_id,
            bottle.likes,
            bottle.dislikes,
        )
    )
    await call.message.answer("Напиши свой ответ на послание:", reply_markup=reply.main)


@router.message(states.SendAnswer.answ, F.text | F.photo | F.animation | F.video_note | F.sticker | F.video)
async def send_answer_success(message: Message, state: FSMContext):
    data = (await state.get_data())["answ"]
    if message.text:
        msg_text = message.text
    elif message.caption:
        msg_text = message.caption
    else:
        msg_text = ""

    async with async_session_maker() as session:
        stmt = select(Bottle).where(Bottle.id == data.bottle_id)
        bottle = (await session.execute(stmt)).first()[0]
        stmt = (
            update(Bottle)
            .where(Bottle.id == data.bottle_id)
            .values(rating=Bottle.rating + 30)
        )
        await session.execute(stmt)

        if message.text:
            msg_type = "text"
            msg_file = ""
        elif message.photo:
            msg_type = "img"
            msg_file = message.photo[-1].file_id
        elif message.animation:
            msg_type = "anim"
            msg_file = message.animation.file_id
        elif message.video_note:
            msg_type = "note"
            msg_file = message.video_note.file_id
        elif message.sticker:
            msg_type = "sticker"
            msg_file = message.sticker.file_id
        elif message.video:
            msg_type = "video"
            msg_file = message.video.file_id


        stmt = insert(Bottle).values(
            text=msg_text, author=message.from_user.id, type=msg_type, bad=bottle.bad, is_active=False, related_bottle=bottle.id, file_id=msg_file
        ).returning(Bottle)
        answ = (await session.execute(stmt)).first()[0]
        stmt = select(User.p_watch_answ_type).where(User.tg_id == bottle.author)
        watch_type = (await session.execute(stmt)).first()[0]
        await session.commit()

    await utils.increment_user_value(bottle.author, receive_amount=User.receive_amount + 1)
    await state.clear()
    await message.answer("Ваш ответ был отправлен автору ✅", reply_markup=reply.main)

    if watch_type == "new":
        await utils.send_bottle_multitype(answ, bottle.author, inline.watch_answ_bottle(
                bottle.id, answ.id, bottle.author, True
            ),
            "<b>На твою бутылочку ответили:</b>\n"
        )
        # await bot.send_message(
        #     text=f"<b>На твою бутылочку ответили:</b>\n" f"{msg_text}",
        #     chat_id=bottle.author,
        #     reply_markup=inline.watch_answ_bottle(
        #         bottle.id, answ.id, bottle.author, True
        #     ),
        # )
    else:
        await bot.send_message(
            text="<b>Тебе пришел ответ!</b>\n", chat_id=bottle.author
        )
        await utils.send_bottle_multitype(bottle, bottle.author, None, "")
        await utils.send_bottle_multitype(answ, bottle.author, None,"<b>Тебе ответили:</b>\n")
        # await bot.send_message(
        #     text=f"<b>Тебе ответили:</b>\n" f"{msg_text}", chat_id=bottle.author
        # )


@router.callback_query(inline.WatchBottle.filter(F.is_answ == False))
async def watch_bottle(
    call: CallbackQuery, callback_data: inline.WatchBottle, state: FSMContext
):
    async with async_session_maker() as session:
        stmt = select(Bottle).where(Bottle.id == callback_data.bottle_id)
        bottle = (await session.execute(stmt)).first()[0]
        await utils.send_bottle_multitype(
            bottle,
            callback_data.tg_id,
            inline.watch_answ_bottle(
                bottle.id, callback_data.answ_id, callback_data.tg_id, False
            ),
            "",
        )

        await call.message.delete()


@router.callback_query(inline.WatchBottle.filter(F.is_answ == True))
async def watch_answ(
    call: CallbackQuery, callback_data: inline.WatchBottle, state: FSMContext
):
    async with async_session_maker() as session:
        stmt = select(Bottle).where(Bottle.id == callback_data.answ_id)
        answ = (await session.execute(stmt)).first()[0]
        # await call.message.answer(
        #     text=f"<b>На твою бутылочку ответили:</b>\n{answ.text}",
        #     reply_markup=inline.watch_answ_bottle(
        #         callback_data.bottle_id,
        #         callback_data.answ_id,
        #         callback_data.tg_id,
        #         True,
        #     ),
        # )
        await utils.send_bottle_multitype(
                answ,
                callback_data.tg_id,
                inline.watch_answ_bottle(
                    callback_data.bottle_id,
                    callback_data.answ_id,
                    callback_data.tg_id,
                    True,
                ),
        "<b>На твою бутылочку ответили:</b>\n"
        )

        await call.message.delete()


@router.callback_query(inline.Reaction.filter(F.action == "report"))
async def report_bottle(
    call: CallbackQuery, callback_data: inline.Reaction, state: FSMContext
):
    async with async_session_maker() as session:
        stmt = select(Bottle).where(Bottle.id == callback_data.bottle_id)
        bottle = (await session.execute(stmt)).first()[0]
        stmt = insert(Report).values(
            bottle=bottle.id, report_author=callback_data.tg_id
        )
        await session.execute(stmt)
        await session.commit()
        for i in range(len(settings.MODERATORS)):
            await utils.send_bottle_multitype(
                bottle,
                settings.MODERATORS[i],
                inline.ban_usr(bottle.id, callback_data.tg_id),
                "<b>⚠️Поступила новая жалоба⚠️\nсодержание бутылочки</b>:\n",
            )

    await call.message.delete_reply_markup()
    await call.message.answer(
        "Жалоба была направлена модераторам ⚠️", reply_markup=reply.main
    )


@router.callback_query(inline.BanUsr.filter(F.action == "warn_usr"))
async def ban_usr_callback(call: CallbackQuery, callback_data: inline.BanUsr):
    async with async_session_maker() as session:
        stmt = (
            select(Report)
            .where(Report.report_author == callback_data.rep_author_id)
            .where(Report.bottle == callback_data.bottle_id)
        )
        res = (await session.execute(stmt)).first()[0]
        if not res.is_closed:
            stmt = select(Bottle).where(Bottle.id == callback_data.bottle_id)
            bottle = (await session.execute(stmt)).first()[0]
            usr = bottle.author
            stmt = (
                update(Bottle)
                .where(Bottle.id == callback_data.bottle_id)
                .values(is_active=False)
            )
            await session.execute(stmt)

            await utils.increment_user_value(usr, warns=User.warns + 1)

            await utils.send_bottle_multitype(
                bottle,
                usr,
                None,
                "<b>Вы получили предупреждение за данную бутылочку</b>:\n",
            )

            await call.message.answer(text=f"Пользователь {usr} получил предупреждение")

            stmt = update(Report).where(Report.id == res.id).values(is_closed=True)
            await session.execute(stmt)
            await session.commit()
        else:
            await call.message.answer(text="Другой модератор уже обработал жалобу")

    await call.message.delete()


@router.callback_query(inline.BanUsr.filter(F.action == "not_ban_usr"))
async def not_ban_usr_callback(call: CallbackQuery, callback_data: inline.BanUsr):
    async with async_session_maker() as session:
        stmt = (
            select(Report)
            .where(Report.report_author == callback_data.rep_author_id)
            .where(Report.bottle == callback_data.bottle_id)
        )
        res = (await session.execute(stmt)).first()[0]
        stmt = update(Report).where(Report.id == res.id).values(is_closed=True)
        await session.execute(stmt)
        await session.commit()
    await call.message.delete()
