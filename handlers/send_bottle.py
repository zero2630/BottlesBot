import asyncio  # noqa: F401

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import insert, select

from keyboards import reply
from other import states
from other.database import async_session_maker
from other.models import User, Bottle
from other import button_text
from other import utils

router = Router()


@router.message(F.text.casefold() == button_text.main_but1)
async def send_bottle(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = select(User.send_lim).where(User.tg_id == message.from_user.id)
        send_lim = (await session.execute(stmt)).first()[0]
        if send_lim > 0:
            await state.set_state(states.SendBottle.bottle_text)
            await message.answer("Напиши свое послание:", reply_markup=reply.cancel)
        else:
            await message.answer(
                "Лимит отправки посланий исчерпан.\nОн обновляется каждые 60 секунд.",
                reply_markup=reply.main,
            )


# случай с текстом
@router.message(states.SendBottle.bottle_text, F.text)
async def send_bottle_success_text(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = select(User.p_bad_mode).where(User.tg_id == message.from_user.id)
        mode = (await session.execute(stmt)).first()[0]
        stmt = insert(Bottle).values(
            text=message.text, author=message.from_user.id, type="text", bad=mode
        )
        await session.execute(stmt)
        await session.commit()
        await utils.increment_user_value(
            message.from_user.id,
            send_amount=User.send_amount + 1,
            send_lim=User.send_lim - 1,
        )

    await message.answer("Бутылочка с посланием отправлена ✅", reply_markup=reply.main)
    await state.clear()


# случай с фото
@router.message(states.SendBottle.bottle_text, F.photo)
async def send_bottle_success_photo(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        photo_caption = ""
        if message.caption:
            photo_caption = message.caption
        stmt = select(User.p_bad_mode).where(User.tg_id == message.from_user.id)
        mode = (await session.execute(stmt)).first()[0]
        stmt = insert(Bottle).values(
            text=photo_caption,
            author=message.from_user.id,
            type="img",
            file_id=message.photo[-1].file_id,
            bad=mode,
        )
        await session.execute(stmt)
        await session.commit()
        await utils.increment_user_value(
            message.from_user.id,
            send_amount=User.send_amount + 1,
            send_lim=User.send_lim - 1,
        )

    await message.answer("Бутылочка с посланием отправлена ✅", reply_markup=reply.main)
    await state.clear()


# случай с gif
@router.message(states.SendBottle.bottle_text, F.animation)
async def send_bottle_success_gif(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = select(User.p_bad_mode).where(User.tg_id == message.from_user.id)
        mode = (await session.execute(stmt)).first()[0]
        stmt = insert(Bottle).values(
            text="",
            author=message.from_user.id,
            type="anim",
            file_id=message.animation.file_id,
            bad=mode,
        )
        await session.execute(stmt)
        await session.commit()
        await utils.increment_user_value(
            message.from_user.id,
            send_amount=User.send_amount + 1,
            send_lim=User.send_lim - 1,
        )

    await message.answer("Бутылочка с посланием отправлена ✅", reply_markup=reply.main)
    await state.clear()


# случай с кружочком
@router.message(states.SendBottle.bottle_text, F.video_note)
async def send_bottle_success_note(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        stmt = select(User.p_bad_mode).where(User.tg_id == message.from_user.id)
        mode = (await session.execute(stmt)).first()[0]
        stmt = insert(Bottle).values(
            text="",
            author=message.from_user.id,
            type="note",
            file_id=message.video_note.file_id,
            bad=mode,
        )
        await session.execute(stmt)
        await session.commit()
        await utils.increment_user_value(
            message.from_user.id,
            send_amount=User.send_amount + 1,
            send_lim=User.send_lim - 1,
        )

    await message.answer("Бутылочка с посланием отправлена ✅", reply_markup=reply.main)
    await state.clear()
