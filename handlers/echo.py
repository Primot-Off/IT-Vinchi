from pathlib import Path
from datetime import datetime
import pytz, asyncio

from aiogram import Router, F, Bot
from aiogram.types import Message, InputMediaPhoto, FSInputFile
from aiogram.fsm.context import FSMContext, StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from utils.states import Questionnaire, Menu

from keyboards.builders import builder_buttons
from keyboards.reply import rmk

from database.db import *

from handlers.checks import is_valid_github_url, is_valid_language
from handlers.actions import *


router = Router()


@router.message(F.text.in_(["1👍", "2❌"]))
async def echo(message: Message, state: FSMContext, bot: Bot):
    await message.bot.send_chat_action(message.chat.id, "typing")
    text = message.text
    pool = await create_db_pool()
    if text == "1👍":
        return await view_likes(pool, message, message.from_user.id, bot, state)
    if text == "2❌":
        user = await get_user_data(pool, message.from_user.id)
        await state.set_state(Menu.main)
        if user.get('liked_it'):
            liked_it = user['liked_it'].split(", ")
            if len(liked_it) > 0:
                return await message.answer(f"1. Показать людей, которые оценили мою анкету.\n2. Моя анкета\n3. {'Отключить поиск' if user['included'] == 1 else 'Включить поиск' }", reply_markup = builder_buttons(["1👍", "2", "3"]))
        return await message.answer(f"1. Смотреть анкеты\n2. Моя анкета\n3. {'Отключить поиск' if user['included'] == 1 else 'Включить поиск' }", reply_markup = builder_buttons(["1", "2", "3"]))