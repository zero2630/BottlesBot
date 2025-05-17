from aiogram.fsm.state import StatesGroup, State


class SendAnswer(StatesGroup):
    answ = State()


class SendBottle(StatesGroup):
    bottle_text = State()
    bottle_text_lim = State()


class BuyBottle(StatesGroup):
    buy_bottle = State()