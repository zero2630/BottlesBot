from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from other import button_text

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=button_text.main_but1)],
        [KeyboardButton(text=button_text.main_but2)],
        [
            KeyboardButton(text=button_text.main_but3),
            KeyboardButton(text=button_text.main_but4),
        ],
    ],
    resize_keyboard=True,
)

find_bottle = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=button_text.main_but1)],
        [KeyboardButton(text=button_text.main_but2)],
        [
            KeyboardButton(text=button_text.main_but3),
            KeyboardButton(text=button_text.main_but4),
        ],
    ],
    resize_keyboard=True,
)

bottle_history_type = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=button_text.type_but1)],
        [KeyboardButton(text=button_text.type_but2)],
        [KeyboardButton(text=button_text.cancel_but)],
    ],
    resize_keyboard=True,
)

cancel = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=button_text.cancel_but)]], resize_keyboard=True
)
