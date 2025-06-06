from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from other.models import Bottle


class Reaction(CallbackData, prefix="reaction"):
    action: str
    bottle_id: int
    react_enabled: bool
    answ_enabled: bool


class BuyBottles(CallbackData, prefix="buy_bottles"):
    action: str
    amount: int
    tg_id: int


class UseBottles(CallbackData, prefix="use_bottles"):
    action: str
    tg_id: int


class BanUsr(CallbackData, prefix="ban_usr"):
    action: str
    bottle_id: int


class AnswAdmin(CallbackData, prefix="ban_usr"):
    action: str


class Settings(CallbackData, prefix="settings"):
    action: str
    tg_id: int
    par1: bool
    par2: bool


def action_bottle(bottle_id, react_enabled, answ_enabled, likes=0, dislikes=0):
    if not react_enabled and not answ_enabled:
        return None

    builder = InlineKeyboardBuilder()
    if react_enabled:
        builder.button(
            text=f"{likes} ❤️",
            callback_data=Reaction(action="like", bottle_id=bottle_id, react_enabled=react_enabled, answ_enabled=answ_enabled)
        )
        builder.button(
            text=f"{dislikes} 🤮",
            callback_data=Reaction(action="dislike", bottle_id=bottle_id, react_enabled=react_enabled, answ_enabled=answ_enabled)
        )

    if answ_enabled:
        builder.button(
            text=f"ответить",
            callback_data=Reaction(action="answ", bottle_id=bottle_id, react_enabled=react_enabled, answ_enabled=answ_enabled)
        )

    if answ_enabled:
        builder.button(
            text=f"кинуть жалобу",
            callback_data=Reaction(action="report", bottle_id=bottle_id, react_enabled=react_enabled, answ_enabled=answ_enabled)
        )

    builder.adjust(2, 1, 1)

    return builder.as_markup(resize_keyboard=True)


def answ_admin():
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"ответить",
        callback_data=AnswAdmin(action="answ_admin")
    )
    return builder.as_markup(resize_keyboard=True)


def buy_bottles(tg_id):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"1 🍾",
        callback_data=BuyBottles(action="buy_1", amount=1, tg_id=tg_id),
    )
    builder.button(
        text=f"5 🍾",
        callback_data=BuyBottles(action="buy_1", amount=5, tg_id=tg_id),
    )
    builder.button(
        text=f"10 🍾",
        callback_data=BuyBottles(action="buy_1", amount=10, tg_id=tg_id),
    )
    return builder.as_markup(resize_keyboard=True)


def settings(tg_id, par1, par2):
    vals = {
        True: "✅",
        False: "❌"
    }

    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"{vals[par1]} | присылать уведомления о ❤️",
        callback_data=Settings(action="like_notif", tg_id=tg_id, par1=par1, par2=par2),
    )
    builder.button(
        text=f"{vals[par2]} | присылать случайную бутылочку раз в день",
        callback_data=Settings(action="send_rand", tg_id=tg_id, par1=par1, par2=par2),
    )
    builder.adjust(1, 1)
    return builder.as_markup(resize_keyboard=True)


def use_bottles(tg_id, action):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"Да",
        callback_data=UseBottles(action=action, tg_id=tg_id),
    )
    return builder.as_markup(resize_keyboard=True)


def ban_usr(bottle_id):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"предупреждение",
        callback_data=BanUsr(action="warn_usr", bottle_id=bottle_id),
    )
    builder.button(
        text=f"пофиг",
        callback_data=BanUsr(action="not_ban_usr", bottle_id=bottle_id),
    )
    return builder.as_markup(resize_keyboard=True)
