from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from other.models import Bottle


class Reaction(CallbackData, prefix="reaction"):
    action: str
    bottle_id: int
    react_enabled: bool
    answ_enabled: bool
    rep_enabled: bool
    tg_id: int


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
    rep_author_id: int


class AnswAdmin(CallbackData, prefix="ban_usr"):
    action: str


class Settings(CallbackData, prefix="settings"):
    action: str
    tg_id: int
    par1: str
    par2: bool


class WatchBottle(CallbackData, prefix="watch_bottle"):
    is_answ: bool
    tg_id: int
    bottle_id: int
    answ_id: int


def action_bottle(bottle_id, react_enabled, answ_enabled, rep_enabled, tg_id, likes=0, dislikes=0):
    if not react_enabled and not answ_enabled:
        return None

    builder = InlineKeyboardBuilder()
    if react_enabled:
        builder.button(
            text=f"{likes} ❤️",
            callback_data=Reaction(action="like", bottle_id=bottle_id, react_enabled=react_enabled, answ_enabled=answ_enabled, rep_enabled=rep_enabled, tg_id=tg_id)
        )
        builder.button(
            text=f"{dislikes} 🤮",
            callback_data=Reaction(action="dislike", bottle_id=bottle_id, react_enabled=react_enabled, answ_enabled=answ_enabled, rep_enabled=rep_enabled, tg_id=tg_id)
        )

    if answ_enabled:
        builder.button(
            text=f"ответить",
            callback_data=Reaction(action="answ", bottle_id=bottle_id, react_enabled=react_enabled, answ_enabled=answ_enabled, rep_enabled=rep_enabled, tg_id=tg_id)
        )

    if rep_enabled:
        builder.button(
            text=f"кинуть жалобу",
            callback_data=Reaction(action="report", bottle_id=bottle_id, react_enabled=react_enabled, answ_enabled=answ_enabled, rep_enabled=rep_enabled, tg_id=tg_id)
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
    vals_type = {
        "new": "1️⃣",
        "old": "2️⃣"
    }
    vals_mode = {
        True: "😈",
        False: "😇"
    }

    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"{vals_type[par1]} | формат отображения ответа",
        callback_data=Settings(action="answ_format", tg_id=tg_id, par1=par1, par2=par2),
    )
    builder.button(
        text=f"{vals_mode[par2]} | режим бота",
        callback_data=Settings(action="bot_mode", tg_id=tg_id, par1=par1, par2=par2),
    )
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def use_bottles(tg_id, action):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"Да",
        callback_data=UseBottles(action=action, tg_id=tg_id),
    )
    return builder.as_markup(resize_keyboard=True)


def ban_usr(bottle_id, rep_author_id):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"предупреждение",
        callback_data=BanUsr(action="warn_usr", bottle_id=bottle_id, rep_author_id=rep_author_id),
    )
    builder.button(
        text=f"пофиг",
        callback_data=BanUsr(action="not_ban_usr", bottle_id=bottle_id, rep_author_id=rep_author_id),
    )
    return builder.as_markup(resize_keyboard=True)


def watch_answ_bottle(bottle_id, answ_id, tg_id, is_answ):
    builder = InlineKeyboardBuilder()
    if is_answ:
        text = "посмотреть свою бутылочку"
    else:
        text = "посмотреть ответ"

    builder.button(
        text=text,
        callback_data=WatchBottle(bottle_id=bottle_id, answ_id=answ_id, tg_id=tg_id, is_answ=(not is_answ)),
    )

    return builder.as_markup(resize_keyboard=True)


