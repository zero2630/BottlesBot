import asyncio  # noqa: F401

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, update

from keyboards import reply, inline
from other.database import async_session_maker
from other.models import User
from other import button_text


router = Router()


@router.message(F.text == button_text.cancel_but)
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("действие отменено", reply_markup=reply.main)


@router.message(F.text.casefold() == button_text.main_but3)
async def bottle_history(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == message.from_user.id)
        usr = (await session.execute(stmt)).first()[0]

    await message.answer(
        f"<b>Статистика</b>\n\n"
        f"<b>бутылок отправлено</b>: {usr.send_amount}\n"
        f"<b>бутылок найдено</b>: {usr.find_amount}\n"
        f"<b>ответов получено</b>: {usr.receive_amount}\n"
        f"<b>всего</b>: {usr.likes_amount} ❤️\n"
        f"<b>место в рейтинге</b>: {usr.rating_place} 🏆\n",
        reply_markup=reply.main,
    )


@router.message(F.text.casefold() == button_text.main_but4)
async def buy_menu(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == message.from_user.id)
        usr = (await session.execute(stmt)).first()[0]
        await session.commit()

    await message.answer(
        "<b>Твои настройки:</b>",
        reply_markup=inline.settings(
            message.from_user.id, usr.p_watch_answ_type, usr.p_bad_mode
        ),
    )


@router.callback_query(inline.Settings.filter(F.action == "answ_format"))
async def answ_format_callback(call: CallbackQuery, callback_data: inline.Settings):
    if callback_data.par1 == "new":
        new_par = "old"
    else:
        new_par = "new"

    async with async_session_maker() as session:
        stmt = (
            update(User)
            .where(User.tg_id == callback_data.tg_id)
            .values(p_watch_answ_type=new_par)
        )
        await session.execute(stmt)
        await session.commit()

        await call.message.edit_reply_markup(
            reply_markup=inline.settings(
                callback_data.tg_id, new_par, callback_data.par2
            )
        )


@router.callback_query(inline.Settings.filter(F.action == "bot_mode"))
async def bot_mode_callback(call: CallbackQuery, callback_data: inline.Settings):
    new_par2 = not callback_data.par2
    if new_par2:
        await call.message.answer(
            "<b>Внимание</b>\n"
            "Был выбран щитпост режим бота\n"
            "В этом режиме почти полностью <b>отсутствует модерация</b>"
        )

    async with async_session_maker() as session:
        stmt = (
            update(User)
            .where(User.tg_id == callback_data.tg_id)
            .values(p_bad_mode=new_par2)
        )
        await session.execute(stmt)
        await session.commit()

        await call.message.edit_reply_markup(
            reply_markup=inline.settings(
                callback_data.tg_id, callback_data.par1, new_par2
            )
        )
