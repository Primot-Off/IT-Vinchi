from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def link_button(text:str, url:str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=text, url=url)]
            ]
        )