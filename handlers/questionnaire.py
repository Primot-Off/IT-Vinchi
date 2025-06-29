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

storage = MemoryStorage()

moscow_tz = pytz.timezone('Europe/Moscow') # Московское время

# ------ Анкета ------

@router.message(F.text.lower() == "✍ создать анкету")
async def create_profile(message: Message, state: FSMContext):
    pool = await create_db_pool()
    if await user_exists(pool, message.from_user.id) is False:
        await state.set_state(Questionnaire.name)
        await message.answer(
            "🤩 Давай начнем с твоего имени. Как тебя зовут?",
            reply_markup=builder_buttons(message.from_user.first_name) # Здесь можно добавить клавиатуру, если нужно
        )

@router.message(Questionnaire.name)
async def questionnaire_name(message: Message, state: FSMContext):
    if len(message.text) < 3:
        return await message.answer("❗️Пожалуйста, введи корректное имя (минимум 3 символа).")
    await state.update_data(name=message.text)
    await state.set_state(Questionnaire.age)
    await message.answer("🗓 Сколько тебе лет?", reply_markup=rmk)

@router.message(Questionnaire.age)
async def questionnaire_age(message: Message, state: FSMContext):
    try:
        if message.text.isdigit() and int(message.text) > 0 and int(message.text) < 150:
            await state.update_data(age=int(message.text))
            await state.set_state(Questionnaire.github)
            await message.answer(
                "💻 Укажи свой GitHub профиль (если есть)\n\nПример:\n<i>https://github.com/Primot-Off</i>",
                reply_markup=builder_buttons("Нет")
                )
        else:
            await message.answer("❗️Пожалуйста, введи корректный возраст (число).")
    except Exception as e:
        await message.answer(f"❗️Пожалуйста, введи корректный возраст (число).\n\nОшибка: {e}")


@router.message(Questionnaire.github)
async def questionnaire_github(message: Message, state: FSMContext):
    if message.text.lower() == "нет":
        await state.update_data(github=None)
        await state.set_state(Questionnaire.about)
        await message.answer("👤 Расскажи о себе\n\n💼 Чем ты занимаешься? (фронтенд, бэкенд, дизайн, ML и т.д.)\n🛠 Какие технологии или языки знаешь?\n🎯 Что ищешь: общение, партнёров, идеи, проекты?\n🌍 Из какого ты города или часового пояса?\n🎮 Чем увлекаешься вне кодинга?", reply_markup=rmk)
    elif await is_valid_github_url(message.text):
        await state.update_data(github=message.text)
        await state.set_state(Questionnaire.about)
        await message.answer("👤 Расскажи о себе\n\n💼 Чем ты занимаешься? (фронтенд, бэкенд, дизайн, ML и т.д.)\n🛠 Какие технологии или языки знаешь?\n🎯 Что ищешь: общение, партнёров, идеи, проекты?\n🌍 Из какого ты города или часового пояса?\n🎮 Чем увлекаешься вне кодинга?", reply_markup=rmk)
    else:
        await message.answer(
            "❗️ Недействительная ссылка\n\nПример:\n<i>https://github.com/Primot-Off</i>",
            reply_markup=builder_buttons("Нет")
            )

@router.message(Questionnaire.about)
async def questionnaire_about(message: Message, state: FSMContext):
    if len(message.text) < 5:
        return await message.answer("❗️ Пожалуйста, введи более подробное описание о себе (минимум 5 символов).")
    if len(message.text) > 500:
        return await message.answer("❗️ Пожалуйста, введи описание не более 500 символов.")
    await state.update_data(about=message.text)
    await state.set_state(Questionnaire.languages)
    await message.answer(
        "✏️ Выпиши списком языки программирования, языки разметки и т.п., с которыми ты работаешь через запятую\n\nПример:\n<i>Python, HTML, Java</i>",
        reply_markup=builder_buttons("Пропустить")
        )
    
@router.message(Questionnaire.languages)
async def questionnaire_languages(message: Message, state: FSMContext):
    if message.text.lower() == "продолжить":
        await state.set_state(Questionnaire.photos)
        return await message.answer("📸 Теперь можешь загрузить свои фотографии", reply_markup=builder_buttons("Пропустить"))
    elif message.text.lower() == "пропустить":
        await state.update_data(languages=[])
        await state.set_state(Questionnaire.photos)
        return await message.answer("📸 Теперь можешь загрузить свои фотографии", reply_markup=builder_buttons("Пропустить"))
    languages = [lang.strip() for lang in message.text.split(",")]
    languages_are_not_valid = []
    for lang in languages:
        if await is_valid_language(lang.lower()) is False:
            languages_are_not_valid.append(lang)
    await state.update_data(languages=languages)
    if len(languages_are_not_valid) > 0:
        return await message.answer(
            f"❗️Некоторые языки не распознаны: {', '.join(languages_are_not_valid)}\n\nПожалуйста, проверь и введи корректные языки заново или напишите в <a href='https://t.me/PrimotOff/'>поддержку</a>.",
            reply_markup=builder_buttons("Пропустить")
            )
    await state.set_state(Questionnaire.photos)
    await message.answer(
        "📸 Теперь можешь загрузить свои фотографии",
        reply_markup=builder_buttons("Пропустить")
    )

@router.message(Questionnaire.photos, F.photo)
async def questionnaire_photos(message: Message, state: FSMContext, bot: Bot):
    await asyncio.sleep(1)
    await message.bot.send_chat_action(message.chat.id, "typing")
    time_now = int(datetime.now(moscow_tz).timestamp())
    await state.update_data(photos=time_now)
    data = await state.get_data()
    await state.clear()
    await asyncio.sleep(1) # чтобы файл успел сохраниться
    if data.get("name") is None: # если пользователь кидает несколько фото сразу, то функция почему-то несколько раз вызывается, если кто-то знает как это по-другому пофиксить, то в тг @PrimotOff
        return
    await download_photo(message, time_now)
    
    pool = await create_db_pool()
    await create_user(
        pool,
        user_id = message.from_user.id,
        name = data["name"],
        age = data["age"],
        github = data.get("github"),
        about = data["about"],
        languages = data["languages"],
        photos = data["photos"]
    )
    languages = data.get('languages') or []
    languages_str = f"Языки:\n{', '.join(languages)}\n" if languages else ""
    folder = Path(f"database/users/{message.from_user.id}/photos/{time_now}")
    photos = [p for p in folder.iterdir() if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
    media = []
    for idx, photo in enumerate(photos):
        file = FSInputFile(photo)
        if idx == 0:
            if data.get("github") is not None:
                media.append(InputMediaPhoto(media=file, caption=f"""
<b>{data['name']}</b>, {data['age']} лет
{languages_str}{f"\n- {data['about']}\n" if data.get('about') else ""}
📂 <a href='{data["github"]}'>GitHub</a>"""))
            else:
                media.append(InputMediaPhoto(media=file, caption=f"""
<b>{data['name']}</b>, {data['age']} лет
{languages_str}{f"\n- {data['about']}" if data.get('about') else ""}"""))
        else:
            media.append(InputMediaPhoto(media=file))
    await message.answer("Твоя анкета:", reply_markup=rmk)
    await bot.send_media_group(chat_id = message.chat.id, media=media)
    await state.set_state(Menu.profile)
    user_data = await get_user_data(pool, message.from_user.id)
    if user_data.get('liked_it'):
        liked_it = user_data['liked_it'].split(", ")
        if len(liked_it) > 0:
            return await message.answer(f"1. Показать людей, которые оценили мою анкету.\n2. Заполнить анкету заново\n3. Изменить анкету", reply_markup = builder_buttons(["1👍", "2", "3"]))
    return await message.answer("1. Смотреть анкеты\n2. Заполнить анкету заново\n3. Изменить анкету", reply_markup = builder_buttons(["1", "2", "3"]))

@router.message(Questionnaire.photos)
async def questionnaire_photos_not_photo(message: Message, state: FSMContext, bot: Bot):
    if not message.photo:
        if message.text.lower() == "пропустить":
            await message.bot.send_chat_action(message.chat.id, "typing")
            pool = await create_db_pool()
            await state.update_data(photos=None)
            data = await state.get_data()
            await create_user(
                pool,
                user_id = message.from_user.id,
                name = data["name"],
                age = data["age"],
                github = data.get("github"),
                about = data["about"],
                languages = data["languages"],
                photos = data["photos"]
            )
            await state.clear()
            await message.answer("Твоя анкета:")
            languages = data.get('languages') or []
            languages_str = f"Языки:\n{', '.join(languages)}\n" if languages else ""
            if data.get("github") is not None:
                return await message.answer(f"""
<b>{data['name']}</b>, {data['age']} лет
{languages_str}{f"\n- {data['about']}\n" if data.get('about') else ""}
📂 <a href='{data["github"]}'>GitHub</a>
""", reply_markup=rmk)
            else:
                await message.answer(f"""
<b>{data['name']}</b>, {data['age']} лет
{languages_str}{f"\n- {data['about']}" if data.get('about') else ""}
""", reply_markup=rmk
            )
            await state.set_state(Menu.profile)
            user_data = await get_user_data(pool, message.from_user.id)
            if user_data.get('liked_it'):
                liked_it = user_data['liked_it'].split(", ")
                if len(liked_it) > 0:
                    return await message.answer(f"1. Показать людей, которые оценили мою анкету.\n2. Заполнить анкету заново\n3. Изменить анкету", reply_markup = builder_buttons(["1👍", "2", "3"]))
            return await message.answer("1. Смотреть анкеты\n2. Заполнить анкету заново\n3. Изменить анкету", reply_markup = builder_buttons(["1", "2", "3"]))
        await message.answer(
            "📸 Отправь свои фотографии для анкеты",
            reply_markup=builder_buttons("Пропустить")
        )

# ------ Меню ------

@router.message(Menu.main)
async def menu_main(message: Message, state: FSMContext, bot: Bot):
    await message.bot.send_chat_action(message.chat.id, "typing")
    pool = await create_db_pool()
    text = message.text
    if text == "1":
        return await view_questionnaires(pool, message.from_user.id, message, bot, state)
    if text == "2":
        return await state_menu_profile(message, pool, bot, state)
    if text == "3":
        await included_update(pool, message.from_user.id)
        user_data = await get_user_data(pool, message.from_user.id)
        if user_data.get('liked_it'):
            liked_it = user_data['liked_it'].split(", ")
            if len(liked_it) > 0:
                return await message.answer(f"1. Показать людей, которые оценили мою анкету.\n2. Моя анкета\n3. {'Отключить поиск' if user_data['included'] == 1 else 'Включить поиск' }", reply_markup = builder_buttons(["1👍", "2", "3"]))
        return await message.answer(f"1. Смотреть анкеты\n2. Моя анкета\n3. {'Отключить поиск' if user_data['included'] == 1 else 'Включить поиск' }", reply_markup = builder_buttons(["1", "2", "3"]))
    
@router.message(Menu.profile)
async def menu_profile(message: Message, state: FSMContext, bot: Bot):
    await message.bot.send_chat_action(message.chat.id, "typing")
    text = message.text
    if text == "1":
        pool = await create_db_pool()
        return await view_questionnaires(pool, message.from_user.id, message, bot, state)
    if text == "2":
        await state.set_state(Questionnaire.name)
        return await message.answer(
            "🤩 Давай начнем с твоего имени. Как тебя зовут?",
            reply_markup=builder_buttons(message.from_user.first_name)
        )
    if text == "3":
        return await state_menu_profile_edit(message, state)


@router.message(Menu.profile_edit)
async def menu_profile_edit(message: Message, state: FSMContext, bot: Bot):
    text = message.text
    if text == "1":
        await state.set_state(Menu.profile_edit_about)
        return await message.answer("👤 Расскажи о себе\n\n💼 Чем ты занимаешься? (фронтенд, бэкенд, дизайн, ML и т.д.)\n🛠 Какие технологии или языки знаешь?\n🎯 Что ищешь: общение, партнёров, идеи, проекты?\n🌍 Из какого ты города или часового пояса?\n🎮 Чем увлекаешься вне кодинга?", reply_markup=builder_buttons(["Отмена", "Удалить"]))
    if text == "2":
        await state.set_state(Menu.profile_edit_languages)
        return await message.answer(
            "✏️ Выпиши списком языки программирования, языки разметки и т.п., с которыми ты работаешь через запятую\n\nПример:\n<i>Python, HTML, Java</i>",
            reply_markup=builder_buttons(["Отмена", "Удалить"])
        )
    if text == "3":
        await state.set_state(Menu.profile_edit_photos)
        return await message.answer("📸 Загрузи свои фотографии", reply_markup=builder_buttons(["Отмена", "Удалить"]))
    if text == "4":
        pool = await create_db_pool()
        return await state_menu_profile(message, pool, bot, state)

@router.message(Menu.profile_edit_about)
async def menu_profile_edit_about(message: Message, state: FSMContext, bot: Bot):
    await message.bot.send_chat_action(message.chat.id, "typing")
    text = message.text
    if text.lower() == "отмена":
        return await state_menu_profile_edit(message, state)
    if len(message.text) < 5:
        return await message.answer("❗️ Пожалуйста, введи более подробное описание о себе (минимум 5 символов).")
    if len(message.text) > 500:
        return await message.answer("❗️ Пожалуйста, введи описание не более 500 символов.")
    pool = await create_db_pool()
    await about_update(pool, message.from_user.id, text)
    return await state_menu_profile(message, pool, bot, state)


@router.message(Menu.profile_edit_languages)
async def menu_profile_edit_languages(message: Message, state: FSMContext, bot: Bot):
    await message.bot.send_chat_action(message.chat.id, "typing")
    text = message.text
    if text.lower() == "отмена":
        return await state_menu_profile_edit(message, state)
    languages = [lang.strip() for lang in text.split(",")]
    if text == "Удалить":
        languages = []
    languages_are_not_valid = []
    for lang in languages:
        if await is_valid_language(lang.lower()) is False:
            languages_are_not_valid.append(lang)
    if len(languages_are_not_valid) > 0:
        return await message.answer(
            f"❗️Некоторые языки не распознаны: {', '.join(languages_are_not_valid)}\n\nПожалуйста, проверь и введи корректные языки заново или напишите в <a href='https://t.me/PrimotOff/'>поддержку</a>.",
            reply_markup=builder_buttons(["Отмена", "Удалить"])
            )
    pool = await create_db_pool()
    await languages_update(pool, message.from_user.id, languages)
    return await state_menu_profile(message, pool, bot, state)

@router.message(Menu.profile_edit_photos, F.photo)
async def menu_profile_edit_photos(message: Message, state: FSMContext, bot: Bot):
    await message.bot.send_chat_action(message.chat.id, "typing")
    time_now = int(datetime.now(moscow_tz).timestamp())
    await download_photo(message, time_now)
    data = await state.get_data()
    if time_now != data.get("profile_edit_photos"):
        await state.update_data(profile_edit_photos=time_now)
        pool = await create_db_pool()
        await photos_update(pool, message.from_user.id, time_now)
        return await state_menu_profile(message, pool, bot, state)
    pass

@router.message(Menu.profile_edit_photos)
async def menu_profile_edit_photos_not(message: Message, state: FSMContext, bot: Bot):
    await message.bot.send_chat_action(message.chat.id, "typing")
    text = message.text
    if text.lower() == "отмена":
        return await state_menu_profile_edit(message, state)
    if text.lower() == "удалить":
        time_now = int(datetime.now(moscow_tz).timestamp())
        folder = Path(f"database/users/{message.from_user.id}/photos/{time_now}")
        folder.mkdir(parents=True, exist_ok=True)
        pool = await create_db_pool()
        await photos_update(pool, message.from_user.id, text)
        return await state_menu_profile(message, pool, bot, state)
    return await message.answer(
            "📸 Отправь свои фотографии для анкеты",
            reply_markup=builder_buttons(["Отмена", "Удалить"])
        )


@router.message(Menu.view)
async def menu_view(message: Message, state: FSMContext, bot: Bot):
    await message.bot.send_chat_action(message.chat.id, "typing")
    text = message.text 
    pool = await create_db_pool()
    if text == "❤️":
        data = await state.get_data()
        await like_the_profile(pool, message.from_user.id, data['view'])
        like_user = await get_user_data(pool, data['view'])
        try:
            await bot.send_message(data['view'], f"Твою анкету лайкнули {len(like_user['liked_it'].split(", "))} {await plural_raz(len(like_user['liked_it'].split(", ")))}.\n\n1. Посмотреть\n2. Назад", reply_markup = builder_buttons(["1👍", "2❌"]))
        except Exception as e:
            await message.answer(f"Ошибка: {e}")
            print(e)
        return await view_questionnaires(pool, message.from_user.id, message, bot, state)
    if text == "👎":
        return await view_questionnaires(pool, message.from_user.id, message, bot, state)
    if text == "💤":
        await state.set_state(Menu.main)
        user_data = await get_user_data(pool, message.from_user.id)
        if user_data.get('liked_it'):
            liked_it = user_data['liked_it'].split(", ")
            if len(liked_it) > 0:
                return await message.answer(f"1. Показать людей, которые оценили мою анкету.\n2. Моя анкета\n3. {'Отключить поиск' if user_data['included'] == 1 else 'Включить поиск' }", reply_markup = builder_buttons(["1👍", "2", "3"]))
        return await message.answer(f"1. Смотреть анкеты\n2. Моя анкета\n3. {'Отключить поиск' if user_data['included'] == 1 else 'Включить поиск' }", reply_markup = builder_buttons(["1", "2", "3"]))
    

@router.message(Menu.feedback_likes)
async def feedback_likes(message: Message, state: FSMContext, bot: Bot):
    await message.bot.send_chat_action(message.chat.id, "typing")
    text = message.text
    if text == "❤️":
        data = await state.get_data()
        if data.get('feedback_likes'):
            user = await bot.get_chat(int(data['feedback_likes']))
            await message.answer(f"Начни общаться с <a href='t.me/{user.username}'>{user.first_name}</a>")
            try:
                await bot.send_message(int(data['feedback_likes']), f"🎉 Твою заявку приняли\nНачни общаться с <a href='t.me/{message.from_user.username}'>{message.from_user.first_name}</a>")
            except Exception as e:
                await message.answer(f"Ошибка: {e}")
    pool = await create_db_pool()
    if text == "💤":
        await state.set_state(Menu.main)
        user_data = await get_user_data(pool, message.from_user.id)
        if user_data.get('liked_it'):
            liked_it = user_data['liked_it'].split(", ")
            if len(liked_it) > 0:
                return await message.answer(f"1. Показать людей, которые оценили мою анкету.\n2. Моя анкета\n3. {'Отключить поиск' if user_data['included'] == 1 else 'Включить поиск' }", reply_markup = builder_buttons(["1👍", "2", "3"]))
        return await message.answer(f"1. Смотреть анкеты\n2. Моя анкета\n3. {'Отключить поиск' if user_data['included'] == 1 else 'Включить поиск' }", reply_markup = builder_buttons(["1", "2", "3"]))
    return await view_likes(pool, message, message.from_user.id, bot, state)