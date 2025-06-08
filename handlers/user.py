import asyncio
import random
from pyexpat.errors import messages
from random import choice
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage
from sqlalchemy import insert, select, update, not_, delete

from keyboards import reply, inline
from bot import bot
from other import states
from other.database import async_session_maker
from other.models import User, Bottle, Answer, Viewed, Report
from other.button_text import *
from other import settings


router = Router()


async def increment_user_value(tg_id, **kwargs):
    async with async_session_maker() as session:
        stmt = update(User).where(User.tg_id == tg_id).values(**kwargs)
        await session.execute(stmt)
        await session.commit()


def get_find_stmt(tg_id):
    if random.randint(1, 2) == 1:
        stmt = select(Bottle).order_by(Bottle.views).order_by(Bottle.rating.desc()
            ).where(not_(Bottle.id.in_(select(Viewed.bottle).where(Viewed.person == tg_id)))
            ).where(not_(Bottle.id.in_(select(Bottle.id).where(Bottle.author == tg_id)))
            ).where(Bottle.is_active == True)
    else:
        stmt = select(Bottle).order_by(Bottle.rating.desc()
            ).where(not_(Bottle.id.in_(select(Viewed.bottle).where(Viewed.person == tg_id)))
            ).where(not_(Bottle.id.in_(select(Bottle.id).where(Bottle.author == tg_id)))
            ).where(Bottle.is_active == True)

    return stmt


async def send_bottle_multitype(bottle, tg_id, markup, add_text):
    if bottle.type == "text":
        return await bot.send_message(chat_id=tg_id, text=add_text+bottle.text, reply_markup=markup)
    elif bottle.type == "img":
        return await bot.send_photo(chat_id=tg_id, photo=bottle.file_id, caption=add_text+bottle.text, reply_markup=markup)
    elif bottle.type == "voice":
        return await bot.send_voice(chat_id=tg_id, voice=bottle.file_id, reply_markup=markup)


async def get_rand_bottle(tg_id):
    async with async_session_maker() as session:
        stmt = get_find_stmt(tg_id)
        res = (await session.execute(stmt)).first()
        if res:
            bottle = res[0]
            stmt = update(Bottle).where(Bottle.id == bottle.id).values(views=bottle.views+1)
            await session.execute(stmt)
            stmt = insert(Viewed).values(person=tg_id, bottle=bottle.id)
            await session.execute(stmt)
            await session.commit()

            await increment_user_value(tg_id, find_amount=User.find_amount + 1)
            date = datetime.strptime(str(bottle.created_at)[:16], "%Y-%m-%d %H:%M")
            date = date + timedelta(hours=3)
            str_date = date.strftime("%Y-%m-%d %H:%M")
            await send_bottle_multitype(bottle, tg_id,
                                        inline.action_bottle(bottle.id, True, True, message.from_user.id, bottle.likes, bottle.dislikes),
                                        f"<b>Твое послание</b>:\n<i>{str_date} МСК</i>\n\n")


@router.message(F.text == cancel_but)
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("действие отменено", reply_markup=reply.main)


@router.message(F.text.casefold() == main_but1)
async def send_bottle(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = select(User.send_lim).where(User.tg_id == message.from_user.id)
        send_lim = (await session.execute(stmt)).first()[0]
        stmt = select(User.bottles).where(User.tg_id == message.from_user.id)
        bottles = (await session.execute(stmt)).first()[0]
        if send_lim > 0:
            await state.set_state(states.SendBottle.bottle_text)
            await message.answer(f"Напиши свое послание:", reply_markup=reply.cancel)
        else:
            await message.answer(f"Лимит отправки посланий исчерпан.\nОн обновляется каждые 60 секунд.", reply_markup=reply.main)


# @router.callback_query(inline.UseBottles.filter(F.action == "use_send"))
# async def use_bottle_send(call: CallbackQuery, callback_data: inline.UseBottles, state:FSMContext):
#     await state.set_state(states.SendBottle.bottle_text)
#     await state.update_data(bottle_text='bottles')
#     await call.message.answer(f"Напиши свое послание:", reply_markup=reply.cancel)


# случай с текстом
@router.message(states.SendBottle.bottle_text, F.text)
async def send_bottle_success(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = insert(Bottle).values(text=message.text, author=message.from_user.id, type="text")
        await session.execute(stmt)
        await session.commit()
        await increment_user_value(message.from_user.id, send_amount=User.send_amount+1, send_lim=User.send_lim-1)

    await message.answer("Бутылочка с посланием отправлена ✅", reply_markup=reply.main)
    await state.clear()


# случай с фото
@router.message(states.SendBottle.bottle_text, F.photo)
async def send_bottle_success(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        photo_caption = ""
        if message.caption:
            photo_caption = message.caption
        stmt = insert(Bottle).values(text=photo_caption, author=message.from_user.id, type="img", file_id=message.photo[-1].file_id)
        await session.execute(stmt)
        await session.commit()
        await increment_user_value(message.from_user.id, send_amount=User.send_amount+1, send_lim=User.send_lim-1)

    await message.answer("Бутылочка с посланием отправлена ✅", reply_markup=reply.main)
    await state.clear()

#--------------------------------------------------------------------------------------------------------------


@router.message(F.text.casefold() == main_but2)
async def get_bottle(message: Message):
    async with async_session_maker() as session:
        stmt = get_find_stmt(message.from_user.id)
        res = (await session.execute(stmt)).first()
        if res:
            bottle = res[0]
            stmt = update(Bottle).where(Bottle.id == bottle.id).values(views=bottle.views+1)
            await session.execute(stmt)
            stmt = insert(Viewed).values(person=message.from_user.id, bottle=bottle.id)
            await session.execute(stmt)
            await session.commit()

            await increment_user_value(message.from_user.id, find_amount=User.find_amount + 1)
            date = datetime.strptime(str(bottle.created_at)[:16], "%Y-%m-%d %H:%M")
            date = date + timedelta(hours=3)
            str_date = date.strftime("%Y-%m-%d %H:%M")
            await send_bottle_multitype(bottle, message.from_user.id,
                                        inline.action_bottle(bottle.id, True, True, message.from_user.id, bottle.likes, bottle.dislikes),
                                        f"<b>Твое послание</b>:\n<i>{str_date} МСК</i>\n\n")
        else:
            await message.answer(f"<b>Новых посланий нет</b> 😭", reply_markup=reply.main)


# @router.callback_query(inline.UseBottles.filter(F.action == "use_find"))
# async def use_bottle(call: CallbackQuery, callback_data: inline.UseBottles):
#     async with async_session_maker() as session:
#         stmt = get_find_stmt(callback_data.tg_id)
#
#         res = (await session.execute(stmt)).first()
#         if res:
#             bottle = res[0]
#             stmt = update(Bottle).where(Bottle.id == bottle.id).values(views=bottle.views + 1)
#             await session.execute(stmt)
#             stmt = insert(Viewed).values(person=callback_data.tg_id, bottle=bottle.id)
#             await session.execute(stmt)
#             await session.commit()
#
#             await increment_user_value(callback_data.tg_id, bottles=User.bottles-1, find_amount=User.find_amount + 1)
#             date = datetime.strptime(str(bottle.created_at)[:16], "%Y-%m-%d %H:%M")
#             date = date + timedelta(hours=3)
#             str_date = date.strftime("%Y-%m-%d %H:%M")
#             await send_bottle_multitype(bottle, callback_data.tg_id,
#                                         inline.action_bottle(bottle.id, True, True, bottle.likes, bottle.dislikes),
#                                         f"<b>Твое послание</b>:\n<i>{str_date} МСК</i>\n\n")
#         else:
#             await call.message.answer(f"<b>Новых посланий нет</b> 😭", reply_markup=reply.main)


@router.callback_query(inline.Reaction.filter(F.action == "like"))
async def tap_like(call: CallbackQuery, callback_data: inline.Reaction):
    async with async_session_maker() as session:
        stmt = select(Bottle.author).where(Bottle.id == callback_data.bottle_id)
        bottle_author = (await session.execute(stmt)).first()[0]
        stmt = update(Bottle).where(Bottle.id == callback_data.bottle_id).values(rating=Bottle.rating+10, likes=Bottle.likes+1)
        await session.execute(stmt)
        await session.commit()

    await increment_user_value(bottle_author, likes=User.likes + 1)
    await increment_user_value(bottle_author, likes_amount=User.likes_amount + 1)
    await call.message.edit_reply_markup(reply_markup=inline.action_bottle(callback_data.bottle_id, False, callback_data.answ_enabled, callback_data.tg_id, ))
    await call.message.answer("❤️", reply_markup=reply.main)

    # if send_notif:
    await bot.send_message(bottle_author, "Вам отправили ❤️")


@router.callback_query(inline.Reaction.filter(F.action == "dislike"))
async def tap_dislike(call: CallbackQuery, callback_data: inline.Reaction):
    async with async_session_maker() as session:
        stmt = update(Bottle).where(Bottle.id == callback_data.bottle_id).values(rating=Bottle.rating-15, dislikes=Bottle.dislikes+1)
        await session.execute(stmt)
        await session.commit()

    await call.message.edit_reply_markup(reply_markup=inline.action_bottle(callback_data.bottle_id, False, callback_data.answ_enabled, callback_data.tg_id, ))
    await call.message.answer("🤮", reply_markup=reply.main)


@router.callback_query(inline.Reaction.filter(F.action == "answ"))
async def tap_answ(call: CallbackQuery, callback_data: inline.Reaction, state: FSMContext):
    async with async_session_maker() as session:
        stmt = select(Bottle).where(Bottle.id == callback_data.bottle_id)
        bottle = (await session.execute(stmt)).first()[0]
    await state.set_state(states.SendAnswer.answ)
    await state.update_data(answ=callback_data)
    await call.message.edit_reply_markup(reply_markup=inline.action_bottle(callback_data.bottle_id, callback_data.react_enabled, False, callback_data.tg_id, bottle.likes, bottle.dislikes))
    await call.message.answer("Напиши свой ответ на послание:", reply_markup=reply.main)


@router.message(states.SendAnswer.answ)
async def send_answer_success(message: Message, state: FSMContext):
    data = (await state.get_data())["answ"]
    async with async_session_maker() as session:
        stmt = select(Bottle).where(Bottle.id == data.bottle_id)
        bottle = (await session.execute(stmt)).first()[0]
        stmt = update(Bottle).where(Bottle.id == data.bottle_id).values(rating=Bottle.rating + 30)
        await session.execute(stmt)
        stmt = insert(Answer).values(text=message.text, author=message.from_user.id, bottle=bottle.id)
        await session.execute(stmt)
        stmt = select(User.p_watch_answ_type).where(User.tg_id == bottle.author)
        watch_type = (await session.execute(stmt)).first()[0]
        await session.commit()

        stmt = select(Answer.id).where(Answer.author == message.from_user.id).where(Answer.bottle == bottle.id)
        answ_id = (await session.execute(stmt)).first()[0]
        await session.commit()

    await increment_user_value(bottle.author, receive_amount=User.receive_amount + 1)
    await state.clear()
    await message.answer("Ваш ответ был отправлен автору ✅", reply_markup=reply.main)

    if watch_type == "new":
        await bot.send_message(text=f"<b>На твою бутылочку ответили:</b>\n"
                                    f"{message.text}", chat_id=bottle.author,
                               reply_markup=inline.watch_answ_bottle(bottle.id, answ_id, bottle.author, True))
    else:
        await bot.send_message(text=f"<b>Тебе пришел ответ!</b>\n"
                               f"на бутылочку\n",
                               chat_id=bottle.author)
        await send_bottle_multitype(bottle, bottle.author, None, "")
        await bot.send_message(text=f"<b>Тебе ответили:</b>\n"
                               f"{message.text}", chat_id=bottle.author)


@router.callback_query(inline.WatchBottle.filter(F.is_answ == False))
async def watch_bottle(call: CallbackQuery, callback_data: inline.WatchBottle, state: FSMContext):
    async with async_session_maker() as session:
        stmt = select(Bottle).where(Bottle.id == callback_data.bottle_id)
        bottle = (await session.execute(stmt)).first()[0]
        await send_bottle_multitype(bottle, callback_data.tg_id,
                                    inline.watch_answ_bottle(bottle.id, callback_data.answ_id, callback_data.tg_id, False), "")

        await call.message.delete()


@router.callback_query(inline.WatchBottle.filter(F.is_answ == True))
async def watch_bottle(call: CallbackQuery, callback_data: inline.WatchBottle, state: FSMContext):
    async with async_session_maker() as session:
        stmt = select(Answer).where(Answer.id == callback_data.answ_id)
        answ = (await session.execute(stmt)).first()[0]
        await call.message.answer(text=f"<b>На твою бутылочку ответили:</b>\n{answ.text}",
                                  reply_markup=inline.watch_answ_bottle(callback_data.bottle_id, callback_data.answ_id, callback_data.tg_id, True))

        await call.message.delete()




@router.callback_query(inline.Reaction.filter(F.action == "report"))
async def report_bottle(call: CallbackQuery, callback_data: inline.Reaction, state: FSMContext):
    async with async_session_maker() as session:
        stmt = select(Bottle).where(Bottle.id == callback_data.bottle_id)
        bottle = (await session.execute(stmt)).first()[0]
        stmt = insert(Report).values(bottle=bottle.id, report_author=callback_data.tg_id)
        await session.execute(stmt)
        await session.commit()
        for i in range(len(settings.MODERATORS)):
            msg = (await send_bottle_multitype(bottle, settings.MODERATORS[i], inline.ban_usr(bottle.id, callback_data.tg_id), "<b>⚠️Поступила новая жалоба⚠️\nсодержание бутылочки</b>:\n"))

    await call.message.delete_reply_markup()
    await call.message.answer("Жалоба была направлена модераторам ⚠️", reply_markup=reply.main)


@router.callback_query(inline.BanUsr.filter(F.action == "warn_usr"))
async def ban_usr_callback(call: CallbackQuery, callback_data: inline.BanUsr):
    async with async_session_maker() as session:
        stmt = select(Report).where(Report.report_author == callback_data.rep_author_id).where(Report.bottle == callback_data.bottle_id)
        res = (await session.execute(stmt)).first()[0]
        if not res.is_closed:
            stmt = select(Bottle).where(Bottle.id == callback_data.bottle_id)
            bottle = (await session.execute(stmt)).first()[0]
            usr = bottle.author
            stmt = update(Bottle).where(Bottle.id == callback_data.bottle_id).values(is_active=False)
            await session.execute(stmt)

            await increment_user_value(usr, warns=User.warns+1)

            await send_bottle_multitype(bottle, usr, None, "<b>Вы получили предупреждение за данную бутылочку</b>:\n")

            await call.message.answer(text=f"Пользователь {usr} получил предупреждение")

            stmt = update(Report).where(Report.id == res.id).values(is_closed=True)
            await session.execute(stmt)
            await session.commit()
        else:
            await call.message.answer(text=f"Другой модератор уже обработал жалобу")

    await call.message.delete()



@router.callback_query(inline.BanUsr.filter(F.action == "not_ban_usr"))
async def ban_usr_callback(call: CallbackQuery, callback_data: inline.BanUsr):
    async with async_session_maker() as session:
        stmt = select(Report).where(Report.report_author == callback_data.rep_author_id).where(Report.bottle == callback_data.bottle_id)
        res = (await session.execute(stmt)).first()[0]
        stmt = update(Report).where(Report.id == res.id).values(is_closed=True)
        await session.execute(stmt)
        await session.commit()
    await call.message.delete()

#--------------------------------------------------------------------------------------------------------------


@router.message(F.text.casefold() == main_but3)
async def bottle_history(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == message.from_user.id)
        usr = (await session.execute(stmt)).first()[0]

    await message.answer(f"<b>Статистика</b>\n\n"
                         f"<b>бутылок отправлено</b>: {usr.send_amount}\n"
                         f"<b>бутылок найдено</b>: {usr.find_amount}\n"
                         f"<b>ответов получено</b>: {usr.receive_amount}\n"
                         f"<b>всего</b>: {usr.likes_amount} ❤️\n"
                         f"<b>место в рейтинге</b>: {usr.rating_place} 🏆\n",
                         reply_markup=reply.main)


#--------------------------------------------------------------------------------------------------------------

@router.message(F.text.casefold() == main_but4)
async def buy_menu(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == message.from_user.id)
        usr = (await session.execute(stmt)).first()[0]
        await session.commit()

    await message.answer(f"<b>Твои настройки:</b>",
                         reply_markup=inline.settings(message.from_user.id, usr.p_watch_answ_type))


@router.callback_query(inline.Settings.filter(F.action == "answ_format"))
async def answ_format_callback(call: CallbackQuery, callback_data: inline.Settings):
    if callback_data.par1 == "new":
        new_par = "old"
    else:
        new_par = "new"

    async with async_session_maker() as session:
        stmt = update(User).where(User.tg_id == callback_data.tg_id).values(p_watch_answ_type=new_par)
        await session.execute(stmt)
        await session.commit()

        await call.message.edit_reply_markup(reply_markup=inline.settings(callback_data.tg_id, new_par))



# @router.callback_query(inline.Settings.filter(F.action == "send_rand"))
# async def send_rand_callback(call: CallbackQuery, callback_data: inline.Settings):
#     async with async_session_maker() as session:
#         stmt = update(UserSettings).where(UserSettings.usr == callback_data.tg_id).values(p_send_rand=(not callback_data.par2))
#         await session.execute(stmt)
#         await session.commit()
#
#         await call.message.edit_reply_markup(reply_markup=inline.settings(callback_data.tg_id, callback_data.par1, (not callback_data.par2)))


# @router.callback_query(inline.Settings.filter(F.action == "like_notif"))
# async def like_notif_callback(call: CallbackQuery, callback_data: inline.Settings):
#     async with async_session_maker() as session:
#         stmt = update(UserSettings).where(UserSettings.usr == callback_data.tg_id).values(p_like_notif=(not callback_data.par1))
#         await session.execute(stmt)
#         await session.commit()
#
#         await call.message.edit_reply_markup(reply_markup=inline.settings(callback_data.tg_id, (not callback_data.par1), callback_data.par2))

#--------------------------------------------------------------------------------------------------------------
