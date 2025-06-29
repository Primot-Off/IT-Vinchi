from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup

def builder_buttons(text: str | list[str]) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    if isinstance(text, str):
        text = [text]

    for txt in text:
        builder.button(text=txt)
    if type(text) == list and len(text) > 4:
        if len(text) % 3 == 0:
            builder.adjust(3)
        elif len(text) % 5 == 0:
            builder.adjust(5)
        else:
            builder.adjust(4)

    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)