import asyncio
from random import choice

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import insert, select, update, not_

from keyboards import reply, inline
from bot import bot
from other import states
from other.database import async_session_maker
from other.models import User, Bottle, ReportBottle, Answer, Viewed
from other.button_text import *


router = Router()


async def increment_user_value(tg_id, **kwargs):
    async with async_session_maker() as session:
        stmt = update(User).where(User.tg_id == tg_id).values(**kwargs)
        await session.execute(stmt)
        await session.commit()


@router.message(F.text == cancel_but)
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("действие отменено", reply_markup=reply.main)


@router.message(F.text.casefold() == main_but1)
async def send_bottle(message: Message, state: FSMContext):
    await state.set_state(states.SendBottle.bottle_text)
    await message.answer(f"Напиши свое послание:", reply_markup=reply.cancel)


@router.message(states.SendBottle.bottle_text)
async def send_bottle_success(message: Message, state: FSMContext):
    await state.clear()
    async with async_session_maker() as session:
        stmt = insert(Bottle).values(text=message.text, author=message.from_user.id)
        await session.execute(stmt)
        await session.commit()

    await increment_user_value(message.from_user.id, send_amount=User.send_amount + 1)
    await message.answer("Бутылочка с посланием отправлена ✅", reply_markup=reply.main)


#--------------------------------------------------------------------------------------------------------------


@router.message(F.text.casefold() == main_but2)
async def get_bottle(message: Message):
    async with async_session_maker() as session:
        stmt = select(User.find_lim).where(User.tg_id == message.from_user.id)
        find_lim = (await session.execute(stmt)).first()[0]
        stmt = select(User.bottles).where(User.tg_id == message.from_user.id)
        bottles = (await session.execute(stmt)).first()[0]
        if find_lim > 0:
            stmt = select(Bottle).order_by(Bottle.views).order_by(Bottle.rating.desc())
            # ).where(not_(Bottle.id.in_(select(Viewed.bottle).where(Viewed.person == message.from_user.id)))
            # ).where(not_(Bottle.id.in_(select(Bottle.id).where(Bottle.author == message.from_user.id))))
            res = (await session.execute(stmt)).first()
            if res:
                bottle = res[0]
                stmt = update(Bottle).where(Bottle.id == bottle.id).values(views=bottle.views+1)
                await session.execute(stmt)
                stmt = insert(Viewed).values(person=message.from_user.id, bottle=bottle.id)
                await session.execute(stmt)
                await session.commit()

                await increment_user_value(message.from_user.id, find_amount=User.find_amount + 1, find_lim = User.find_lim - 1)
                await message.answer(f"<b>Ищу подходящую бутылочку...</b>", reply_markup=reply.main)
                await bot.send_message(message.from_user.id, f"<b>Твое послание</b>:\n{bottle.text}", reply_markup=inline.action_bottle(bottle.id, True, True))
            else:
                await message.answer(f"<b>Новых посланий нет</b> 😭", reply_markup=reply.main)
        else:
            if bottles>0:
                await message.answer(f"Лимит поиска посланий исчерпан.\nОн обновляется каждый час.\nИмеется {bottles} доп. бутылок\nИспользовать?",
                                     reply_markup=inline.use_bottles(message.from_user.id))
            else:
                await message.answer(
                    f"Лимит поиска посланий исчерпан.\nОн обновляется каждый час.\nИмеется {bottles} доп. бутылок",
                    reply_markup=reply.main)


@router.callback_query(inline.UseBottles.filter(F.action == "use_1"))
async def use_bottle(call: CallbackQuery, callback_data: inline.UseBottles):
    async with async_session_maker() as session:
        stmt = select(Bottle).order_by(Bottle.views).order_by(Bottle.rating.desc()
        ).where(not_(Bottle.id.in_(select(Viewed.bottle).where(Viewed.person == callback_data.tg_id)))
        ).where(not_(Bottle.id.in_(select(Bottle.id).where(Bottle.author == callback_data.tg_id))))
        res = (await session.execute(stmt)).first()
        if res:
            bottle = res[0]
            stmt = update(Bottle).where(Bottle.id == bottle.id).values(views=bottle.views + 1)
            await session.execute(stmt)
            stmt = insert(Viewed).values(person=callback_data.tg_id, bottle=bottle.id)
            await session.execute(stmt)
            await session.commit()

            await increment_user_value(callback_data.tg_id, bottles=User.bottles-1, find_amount=User.find_amount + 1)
            await call.message.answer(f"<b>Ищу подходящую бутылочку...</b>", reply_markup=reply.main)
            await bot.send_message(callback_data.tg_id, f"<b>Твое послание</b>:\n{bottle.text}",
                                   reply_markup=inline.action_bottle(bottle.id, True, True))
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
                           f"на бутылочку\n"
                           f"<blockquote>{bottle.text}</blockquote>\n",
                           chat_id=bottle.author)

    await bot.send_message(text=f"<b>Тебе ответили:</b>\n"
                           f"{message.text}", chat_id=bottle.author)

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
                         f"1 🍾 = 5 ❤️\n"
                         f"На балансе: {likes} ❤️</b>",
                         reply_markup=inline.buy_bottles(message.from_user.id))


@router.callback_query(inline.BuyBottles.filter(F.action == "buy_1"))
async def buy_bottles(call: CallbackQuery, callback_data: inline.Reaction):
    async with async_session_maker() as session:
        stmt = select(User.likes).where(User.tg_id == callback_data.tg_id)
        likes = (await session.execute(stmt)).first()[0]
        if likes>=5*callback_data.amount:
            await increment_user_value(callback_data.tg_id, bottles=User.bottles+callback_data.amount)
            await increment_user_value(callback_data.tg_id, likes=User.likes - 5*callback_data.amount)
            await session.commit()

            await call.message.answer("💸", reply_markup=reply.main)

        else:
            await call.message.answer("Не хватает ❤️", reply_markup=reply.main)

#--------------------------------------------------------------------------------------------------------------
