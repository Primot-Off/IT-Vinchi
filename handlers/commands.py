import aiomysql

from aiogram import Router, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

from utils.states import Menu

from keyboards.reply import rmk, start
from keyboards.builders import builder_buttons

from database.db import *

from handlers.actions import view_likes

router = Router()

@router.message(CommandStart())
async def start_command(message: Message, bot: Bot, state: FSMContext):
    await message.bot.send_chat_action(message.chat.id, "typing")
    pool = await create_db_pool()

    if await user_exists(pool, message.from_user.id):
        await state.set_state(Menu.main)
        user_data = await get_user_data(pool, message.from_user.id)
        if user_data.get('liked_it'):
            liked_it = user_data['liked_it'].split(", ")
            if len(liked_it) > 0:
                return await message.answer(f"1. Показать людей, которые оценили мою анкету.\n2. Моя анкета\n3. {'Отключить поиск' if user_data['included'] == 1 else 'Включить поиск' }", reply_markup = builder_buttons(["1👍", "2", "3"]))
        return await message.answer(f"1. Смотреть анкеты\n2. Моя анкета\n3. {'Отключить поиск' if user_data['included'] == 1 else 'Включить поиск' }", reply_markup = builder_buttons(["1", "2", "3"]))

    photo = FSInputFile("assets/start.jpg")
    await message.answer_photo(photo, caption = f"""👋 Привет, программист!
\nЭтот бот создан, чтобы соединять разработчиков: для общения, совместных проектов, нетворкинга 🐞
\n📌 Хочешь найти интересных людей из мира IT? Тогда начнём с твоей анкеты — расскажи немного о себе.
\nНажми кнопку ниже, чтобы создать анкету 👇""", reply_markup = start)