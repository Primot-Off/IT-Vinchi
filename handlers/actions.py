from datetime import datetime
import pytz

from utils.states import Questionnaire, Menu

from keyboards.builders import builder_buttons
from keyboards.reply import rmk

from database.db import *

moscow_tz = pytz.timezone('Europe/Moscow')

async def state_menu_profile_edit(message, state):
    await state.set_state(Menu.profile_edit)
    return await message.answer("1. Изменить описание\n2. Изменить языки\n3. Изменить фото\n4. Назад", reply_markup = builder_buttons(["1", "2", "3", "4"]))

async def state_menu_profile(message, pool, bot, state):
    await message.answer(f"Твоя анкета:")
    user_profile = await get_profile(pool, message.from_user.id)
    if user_profile.get("media"):
        await bot.send_media_group(chat_id = message.chat.id, media = user_profile["media"])
    elif user_profile.get("message"):
        await message.answer(user_profile["message"])
    await state.set_state(Menu.profile)
    return await message.answer("1. Смотреть анкеты\n2. Заполнить анкету заново\n3. Изменить анкету", reply_markup = builder_buttons(["1", "2", "3"]))


async def download_photo(message, time_now):
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_path = file.file_path
    folder = Path(f"database/users/{message.from_user.id}/photos/{time_now}")
    folder.mkdir(parents=True, exist_ok=True)
    filename = folder / f"{photo.file_unique_id}.jpg"
    await message.bot.download_file(file_path, filename)


async def view_questionnaires(pool, user_id, message, bot, state):
    main_user = await get_user_data(pool, user_id)
    looked = []
    if main_user.get('looked'):
        looked = main_user['looked'].split(",") if main_user.get('looked') else []
        looked = [int(x) for x in looked if x.strip().isdigit()]
    looked.append(user_id)
    time_now = int(datetime.now(moscow_tz).timestamp())
    if main_user.get("when_looked"):
        if time_now - main_user["when_looked"] > 43200:
            looked = [user_id]
            await looked_clear(pool, user_id)
    if main_user.get("liked_who"):
        liked_who = main_user["liked_who"].split(", ")
        looked = looked + liked_who
    random_user_id = await get_random_user(pool, looked)
    if random_user_id:
        await when_looked_update(pool, user_id, time_now)
        await looked_update(pool, user_id, random_user_id)
        await state.set_state(Menu.view)
        await state.update_data(view = random_user_id)
        await message.answer("👀", reply_markup = builder_buttons(["❤️", "👎", "💤"]))
        random_user = await get_profile(pool, random_user_id)
        if random_user.get("media"):
            return await bot.send_media_group(chat_id = message.chat.id, media = random_user["media"])
        elif random_user.get("message"):
            return await message.answer(random_user["message"])
    await message.answer("😓 На сегодня анкеты кончились")
    await state.set_state(Menu.main)
    return await message.answer(f"1. Смотреть анкеты\n2. Моя анкета\n3. {'Отключить поиск' if main_user['included'] == 1 else 'Включить поиск' }", reply_markup = builder_buttons(["1", "2", "3"]))


async def view_likes(pool, message, user_id: int, bot, state):
    user = await get_user_data(pool, user_id)
    if user.get("liked_it"):
        liked_it = [int(id) for id in user["liked_it"].split(", ")]
        if len(liked_it) > 0:
            await like_remove(pool, liked_it[0], user_id)
            user_like = await get_profile(pool, liked_it[0])
            await state.set_state(Menu.feedback_likes)
            await state.update_data(feedback_likes = liked_it[0])
            await message.answer(f"Кому-то понравилась твоя анкета{f' (и ещё {len(liked_it) - 1})' if len(liked_it) > 1 else ''}", reply_markup = builder_buttons(["❤️", "👎", "💤"]))
            if user_like.get("media"):
                return await bot.send_media_group(chat_id = message.chat.id, media = user_like["media"])
            elif user_like.get("message"):
                return await message.answer(user_like["message"])
    await message.answer("😓 Анкеты кончились")
    await state.set_state(Menu.main)
    return await message.answer(f"1. Смотреть анкеты\n2. Моя анкета\n3. {'Отключить поиск' if user['included'] == 1 else 'Включить поиск' }", reply_markup = builder_buttons(["1", "2", "3"]))