from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData


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



def action_bottle(bottle_id, react_enabled, answ_enabled):
    if not react_enabled and not answ_enabled:
        return None

    builder = InlineKeyboardBuilder()
    if react_enabled:
        builder.button(
            text=f"❤️",
            callback_data=Reaction(action="like", bottle_id=bottle_id, react_enabled=react_enabled, answ_enabled=answ_enabled)
        )
        builder.button(
            text=f"🤮",
            callback_data=Reaction(action="dislike", bottle_id=bottle_id, react_enabled=react_enabled, answ_enabled=answ_enabled)
        )

    if answ_enabled:
        builder.button(
            text=f"✉️ ответить",
            callback_data=Reaction(action="answ", bottle_id=bottle_id, react_enabled=react_enabled, answ_enabled=answ_enabled)
        )

    builder.adjust(2, 1)

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


def use_bottles(tg_id, action):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"Да",
        callback_data=UseBottles(action=action, tg_id=tg_id),
    )
    return builder.as_markup(resize_keyboard=True)
