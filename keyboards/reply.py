from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from other.button_text import *

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=main_but1)],
        [KeyboardButton(text=main_but2)],
        [KeyboardButton(text=main_but3), KeyboardButton(text=main_but4)],
    ],
    resize_keyboard=True,
)

find_bottle = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=main_but1)],
        [KeyboardButton(text=main_but2)],
        [KeyboardButton(text=main_but3), KeyboardButton(text=main_but4)],
    ],
    resize_keyboard=True,
)

bottle_history_type = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=type_but1)],
        [KeyboardButton(text=type_but2)],
        [KeyboardButton(text=cancel_but)],
    ],
    resize_keyboard=True,
)

cancel = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=cancel_but)]], resize_keyboard=True
)


def find_bottle(find_lim, bottles):
    builder = ReplyKeyboardBuilder()

    builder.row(KeyboardButton(text=f"{find_lim}/5 🔎"), KeyboardButton(text=f"{bottles} 🍾"))
    builder.row(KeyboardButton(text="отмена"))

    return builder.as_markup(resize_keyboard=True)