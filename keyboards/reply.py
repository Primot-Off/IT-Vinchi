from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

start = ReplyKeyboardMarkup(
    keyboard = [
        [
            KeyboardButton(text="✍ Создать анкету")
        ]
    ],
    resize_keyboard = True,
    one_time_keyboard = True,
    input_field_placeholder = "Выберите действие",
    selective = True
)
rmk = ReplyKeyboardRemove()