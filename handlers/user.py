import asyncio
import random
from random import choice

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage
from sqlalchemy import insert, select, update, not_, delete

from keyboards import reply, inline
from bot import bot
from other import states
from other.database import async_session_maker
from other.models import User, Bottle, Answer, Viewed, ReportMsg
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
            ).where(not_(Bottle.id.in_(select(Bottle.id).where(Bottle.author == tg_id))))
    else:
        stmt = select(Bottle).order_by(Bottle.rating.desc()
            ).where(not_(Bottle.id.in_(select(Viewed.bottle).where(Viewed.person == tg_id)))
            ).where(not_(Bottle.id.in_(select(Bottle.id).where(Bottle.author == tg_id))))

    return stmt


async def send_bottle_multitype(bottle, tg_id, markup, add_text):
    if bottle.type == "text":
        return await bot.send_message(chat_id=tg_id, text=add_text+bottle.text, reply_markup=markup)
    elif bottle.type == "img":
        return await bot.send_photo(chat_id=tg_id, photo=bottle.file_id, caption=add_text+bottle.text, reply_markup=markup)
    elif bottle.type == "voice":
        return await bot.send_voice(chat_id=tg_id, voice=bottle.file_id, reply_markup=markup)


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
            await state.update_data(bottle_text='send_lim')
            await message.answer(f"Напиши свое послание:", reply_markup=reply.cancel)

        elif bottles>0:
            await message.answer(
                f"Лимит отправки посланий исчерпан.\nОн обновляется каждые 5 минут.\n<b>Имеется {bottles} доп. бутылок\nИспользовать?</b>",
                reply_markup=inline.use_bottles(message.from_user.id, "use_send"))

        else:
            await message.answer(f"Лимит отправки посланий исчерпан.\nОн обновляется каждые 5 минут.", reply_markup=reply.main)


@router.callback_query(inline.UseBottles.filter(F.action == "use_send"))
async def use_bottle_send(call: CallbackQuery, callback_data: inline.UseBottles, state:FSMContext):
    await state.set_state(states.SendBottle.bottle_text)
    await state.update_data(bottle_text='bottles')
    await call.message.answer(f"Напиши свое послание:", reply_markup=reply.cancel)


@router.message(states.SendBottle.bottle_text, F.text)
async def send_bottle_success(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = insert(Bottle).values(text=message.text, author=message.from_user.id, type="text")
        await session.execute(stmt)
        await session.commit()
    if (await state.get_data())["bottle_text"] == "send_lim":
        await increment_user_value(message.from_user.id, send_amount=User.send_amount+1, send_lim=User.send_lim-1)
    else:
        await increment_user_value(message.from_user.id, send_amount=User.send_amount + 1, bottles=User.bottles - 1)

    await message.answer("Бутылочка с посланием отправлена ✅", reply_markup=reply.main)
    await state.clear()


@router.message(states.SendBottle.bottle_text, F.photo)
async def send_bottle_success(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        photo_caption = ""
        if message.caption:
            photo_caption = message.caption
        stmt = insert(Bottle).values(text=photo_caption, author=message.from_user.id, type="img", file_id=message.photo[-1].file_id)
        await session.execute(stmt)
        await session.commit()
    if (await state.get_data())["bottle_text"] == "send_lim":
        await increment_user_value(message.from_user.id, send_amount=User.send_amount+1, send_lim=User.send_lim-1)
    else:
        await increment_user_value(message.from_user.id, send_amount=User.send_amount + 1, bottles=User.bottles - 1)

    await message.answer("Бутылочка с посланием отправлена ✅", reply_markup=reply.main)
    await state.clear()

#--------------------------------------------------------------------------------------------------------------


@router.message(F.text.casefold() == main_but2)
async def get_bottle(message: Message):
    async with async_session_maker() as session:
        stmt = select(User.find_lim).where(User.tg_id == message.from_user.id)
        find_lim = (await session.execute(stmt)).first()[0]
        stmt = select(User.bottles).where(User.tg_id == message.from_user.id)
        bottles = (await session.execute(stmt)).first()[0]
        if find_lim > 0:
            stmt = get_find_stmt(message.from_user.id)
            res = (await session.execute(stmt)).first()
            if res:
                bottle = res[0]
                stmt = update(Bottle).where(Bottle.id == bottle.id).values(views=bottle.views+1)
                await session.execute(stmt)
                stmt = insert(Viewed).values(person=message.from_user.id, bottle=bottle.id)
                await session.execute(stmt)
                await session.commit()

                await increment_user_value(message.from_user.id, find_amount=User.find_amount + 1, find_lim = User.find_lim - 1)
                await send_bottle_multitype(bottle, message.from_user.id,
                                            inline.action_bottle(bottle.id, True, True),
                                            f"<b>Твое послание</b>:\n<i>{str(bottle.created_at)[:16]}</i>\n\n")
            else:
                await message.answer(f"<b>Новых посланий нет</b> 😭", reply_markup=reply.main)
        else:
            if bottles>0:
                await message.answer(f"Лимит поиска посланий исчерпан.\nОн обновляется каждые 60 секунд.\n<b>Имеется {bottles} доп. бутылок\nИспользовать?</b>",
                                     reply_markup=inline.use_bottles(message.from_user.id, "use_find"))
            else:
                await message.answer(
                    f"Лимит поиска посланий исчерпан.\nОн обновляется каждые 60 секунд.",
                    reply_markup=reply.main)


@router.callback_query(inline.UseBottles.filter(F.action == "use_find"))
async def use_bottle(call: CallbackQuery, callback_data: inline.UseBottles):
    async with async_session_maker() as session:
        stmt = get_find_stmt(callback_data.tg_id)

        res = (await session.execute(stmt)).first()
        if res:
            bottle = res[0]
            stmt = update(Bottle).where(Bottle.id == bottle.id).values(views=bottle.views + 1)
            await session.execute(stmt)
            stmt = insert(Viewed).values(person=callback_data.tg_id, bottle=bottle.id)
            await session.execute(stmt)
            await session.commit()

            await increment_user_value(callback_data.tg_id, bottles=User.bottles-1, find_amount=User.find_amount + 1)
            await send_bottle_multitype(bottle, callback_data.tg_id,
                                        inline.action_bottle(bottle.id, True, True),
                                        f"<b>Твое послание</b>:\n<i>{str(bottle.created_at)[:16]}</i>\n\n")
        else:
            await call.message.answer(f"<b>Новых посланий нет</b> 😭", reply_markup=reply.main)


@router.callback_query(inline.Reaction.filter(F.action == "like"))
async def tap_like(call: CallbackQuery, callback_data: inline.Reaction):
    async with async_session_maker() as session:
        stmt = select(Bottle.author).where(Bottle.id == callback_data.bottle_id)
        bottle_author = (await session.execute(stmt)).first()[0]
        stmt = update(Bottle).where(Bottle.id == callback_data.bottle_id).values(rating=Bottle.rating+10)
        await session.execute(stmt)
        await session.commit()

    await increment_user_value(bottle_author, likes=User.likes + 1)
    await increment_user_value(bottle_author, likes_amount=User.likes_amount + 1)
    await call.message.edit_reply_markup(reply_markup=inline.action_bottle(callback_data.bottle_id, False, callback_data.answ_enabled))
    await call.message.answer("❤️", reply_markup=reply.main)
    await bot.send_message(bottle_author, "Вам отправили ❤️")


@router.callback_query(inline.Reaction.filter(F.action == "dislike"))
async def tap_dislike(call: CallbackQuery, callback_data: inline.Reaction):
    async with async_session_maker() as session:
        stmt = update(Bottle).where(Bottle.id == callback_data.bottle_id).values(rating=Bottle.rating-15)
        await session.execute(stmt)
        await session.commit()

    await call.message.edit_reply_markup(reply_markup=inline.action_bottle(callback_data.bottle_id, False, callback_data.answ_enabled))
    await call.message.answer("🤮", reply_markup=reply.main)


@router.callback_query(inline.Reaction.filter(F.action == "answ"))
async def tap_answ(call: CallbackQuery, callback_data: inline.Reaction, state: FSMContext):
    await state.set_state(states.SendAnswer.answ)
    await state.update_data(answ=callback_data)
    await call.message.edit_reply_markup(reply_markup=inline.action_bottle(callback_data.bottle_id, callback_data.react_enabled, False))
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
        await session.commit()

    await increment_user_value(bottle.author, receive_amount=User.receive_amount + 1)
    await state.clear()
    await message.answer("Ваш ответ был отправлен автору ✅", reply_markup=reply.main)
    await bot.send_message(text=f"<b>Тебе пришел ответ!</b>\n"
                           f"на бутылочку\n",
                           chat_id=bottle.author)
    await send_bottle_multitype(bottle, bottle.author, None, "")

    await bot.send_message(text=f"<b>Тебе ответили:</b>\n"
                           f"{message.text}", chat_id=bottle.author)


@router.callback_query(inline.Reaction.filter(F.action == "report"))
async def report_bottle(call: CallbackQuery, callback_data: inline.Reaction, state: FSMContext):
    async with async_session_maker() as session:
        stmt = select(Bottle).where(Bottle.id == callback_data.bottle_id)
        bottle = (await session.execute(stmt)).first()[0]
        messages = {}
        for i in range(len(settings.MODERATORS)):
            msg = (await send_bottle_multitype(bottle, settings.MODERATORS[i], inline.ban_usr(bottle.id), "<b>⚠️Поступила новая жалоба⚠️\nсодержание бутылочки</b>:\n"))
            # msg = (await bot.send_message(chat_id=settings.MODERATORS[i],
            #                        text=f"<b>⚠️Поступила новая жалоба⚠️\n"
            #                         f"содержание бутылочки</b>:\n"
            #                         f"<blockquote>{call.message.text}</blockquote>",
            #                        reply_markup=inline.ban_usr(callback_data.bottle_id)))
            messages[msg.message_id] = msg.chat.id

        for msg_id, chat_id in messages.items():
            stmt = insert(ReportMsg).values(msg_id=msg_id, chat_id=chat_id, report_id=callback_data.bottle_id)
            await session.execute(stmt)
        await session.commit()


    await call.message.answer("Жалоба была направлена модераторам ⚠️", reply_markup=reply.main)


@router.callback_query(inline.BanUsr.filter(F.action == "warn_usr"))
async def ban_usr_callback(call: CallbackQuery, callback_data: inline.BanUsr):
    async with async_session_maker() as session:
        stmt = select(Bottle).where(Bottle.id == callback_data.bottle_id)
        bottle = (await session.execute(stmt)).first()[0]
        usr = bottle.author
        stmt = delete(Bottle).where(Bottle.id == callback_data.bottle_id)
        await session.execute(stmt)
        await session.commit()

        await increment_user_value(usr, warns=User.warns+1)

        # await bot.send_message(chat_id=usr, text=f"<b>Вы получили предупреждение за данную бутылочку</b>:<blockquote>{bottle.text}</blockquote>")
        await send_bottle_multitype(bottle, usr, None, "<b>Вы получили предупреждение за данную бутылочку</b>:\n")

        stmt = select(ReportMsg).where(ReportMsg.report_id == callback_data.bottle_id)
        res = (await session.execute(stmt)).all()
        for el in res:
            await bot.send_message(chat_id=el[0].chat_id, text=f"Пользователь {usr} получил предупреждение")
            await bot.delete_message(chat_id=el[0].chat_id, message_id=el[0].msg_id)
        stmt = delete(ReportMsg).where(ReportMsg.report_id == callback_data.bottle_id)


@router.callback_query(inline.BanUsr.filter(F.action == "not_ban_usr"))
async def ban_usr_callback(call: CallbackQuery, callback_data: inline.BanUsr):
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
                         f"<b>на балансе</b>: {usr.likes} ❤️\n"
                         f"<b>на балансе</b>: {usr.bottles} 🍾\n",
                         reply_markup=reply.main)


#--------------------------------------------------------------------------------------------------------------

@router.message(F.text.casefold() == main_but4)
async def buy_menu(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = select(User.likes).where(User.tg_id == message.from_user.id)
        likes = (await session.execute(stmt)).first()[0]

    await message.answer(f"<b>За полученные ❤️ можно приобрести дополнительные открытия бутылок\n"
                         f"1 🍾 = 1 ❤️\n"
                         f"На балансе: {likes} ❤️</b>",
                         reply_markup=inline.buy_bottles(message.from_user.id))


@router.callback_query(inline.BuyBottles.filter(F.action == "buy_1"))
async def buy_bottles(call: CallbackQuery, callback_data: inline.Reaction):
    async with async_session_maker() as session:
        stmt = select(User.likes).where(User.tg_id == callback_data.tg_id)
        likes = (await session.execute(stmt)).first()[0]
        if likes>=callback_data.amount:
            await increment_user_value(callback_data.tg_id, bottles=User.bottles+callback_data.amount)
            await increment_user_value(callback_data.tg_id, likes=User.likes - callback_data.amount)
            await session.commit()

            await call.message.answer("💸", reply_markup=reply.main)

        else:
            await call.message.answer("Не хватает ❤️", reply_markup=reply.main)

#--------------------------------------------------------------------------------------------------------------
