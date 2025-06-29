import aiomysql, logging
from pathlib import Path

from aiogram.types import FSInputFile, InputMediaPhoto

from handlers.checks import *

from config_reader import config

logging.basicConfig(level=logging.INFO)

db_password = config.db_password.get_secret_value()

# Конфигурация для подключения к базе данных пользователей
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': config.db_password.get_secret_value(),
    'db': 'it_vinchi',
    'port': 3306
}

async def create_db_pool():
    return await aiomysql.create_pool(**DB_CONFIG)


async def user_exists(pool, user_id: int) -> bool: # Проверка существования пользователя
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT EXISTS(SELECT 1 FROM users WHERE id = %s)", (user_id))
            result = await cur.fetchone()
            return result[0] == 1


async def create_user(
        pool, user_id: int, name: str, age: int, 
        github: str, about: str, languages: list, photos: int
        ):  # Создание пользователя в базе данных
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO users (id, name, age, github, about, languages, photos, included)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) AS new
                ON DUPLICATE KEY UPDATE
                    name = new.name,
                    age = new.age,
                    github = new.github,
                    about = new.about,
                    languages = new.languages,
                    photos = new.photos,
                    included = new.included
            """, (user_id, name, age, github, about, ", ".join(languages), photos, True))
            await conn.commit()


async def get_user_data(pool, user_id: int): # Получение данных пользователя по ID
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            return await cur.fetchone()


async def get_profile(pool, user_id: int):
    user_data = await get_user_data(pool, user_id)
    languages = user_data.get('languages') or []
    languages_str = f"Языки:\n{languages}\n" if languages else ""
    if user_data.get("photos"):
        folder = Path(f"database/users/{user_id}/photos/{user_data["photos"]}")
        photos = [p for p in folder.iterdir() if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
        media = []
        for idx, photo in enumerate(photos):
            file = FSInputFile(photo)
            if idx == 0:
                if user_data.get("github"):
                    media.append(InputMediaPhoto(media=file, caption=f"""
<b>{user_data['name']}</b>, {user_data['age']} {await plural_age(user_data['age'])}
{languages_str}{f"\n- {user_data['about']}\n" if user_data.get('about') else ""}
📂 <a href='{user_data["github"]}'>GitHub</a>
                                                """))
                else:
                    media.append(InputMediaPhoto(media=file, caption=f"""
<b>{user_data['name']}</b>, {user_data['age']} {await plural_age(user_data['age'])}
{languages_str}{f"\n- {user_data['about']}" if user_data.get('about') else ""}
                                                """))
            else:
                media.append(InputMediaPhoto(media=file))
        return {
            "media": media,
        }
    else:
        if user_data.get("github") is not None:
            return {
                "message": f"""
<b>{user_data['name']}</b>, {user_data['age']} {await plural_age(user_data['age'])}
{languages_str}{f"\n- {user_data['about']}\n" if user_data.get('about') else ""}
📂 <a href='{user_data["github"]}'>GitHub</a>
"""
            }
        return {
            "message": f"""
<b>{user_data['name']}</b>, {user_data['age']} {await plural_age(user_data['age'])}
{languages_str}{f"\n- {user_data['about']}" if user_data.get('about') else ""}"""
        }


async def github_update(pool, user_id: int, url: str):
    if await is_valid_github_url(url) is False:
        url = None
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "UPDATE users SET github = %s WHERE id = %s",
                (url, user_id)
            )
            await conn.commit()


async def about_update(pool, user_id: int, text: str):
    if text.strip().lower() == "удалить":
        text = None
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "UPDATE users SET about = %s WHERE id = %s",
                (text, user_id)
            )
            await conn.commit()


async def languages_update(pool, user_id: int, languages: list):
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "UPDATE users SET languages = %s WHERE id = %s",
                (", ".join(languages), user_id)
            )
            await conn.commit()


async def photos_update(pool, user_id: int, time_now):
    if str(time_now).lower() == "удалить":
        time_now = None
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "UPDATE users SET photos = %s WHERE id = %s",
                (time_now, user_id)
            )
            await conn.commit()

async def included_update(pool, user_id: int):
    status = 1
    user_data = await get_user_data(pool, user_id)
    if user_data['included'] == 1:
        status = 0
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "UPDATE users SET included = %s WHERE id = %s",
                (status, user_id)
            )
            await conn.commit()


async def get_random_user(pool, exclude_ids: list[int]) -> int | None:
    if not exclude_ids:
        exclude_ids = [-1]
    
    placeholders = ','.join(['%s'] * len(exclude_ids))
    query = f"""
        SELECT id FROM users
        WHERE included = 1 AND id not in ({placeholders})
        ORDER BY RAND()
        LIMIT 1
    """

    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, exclude_ids)
            result = await cur.fetchone()
            if result:
                return result[0]
            return None
        

async def when_looked_update(pool, user_id, time):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE users SET when_looked = %s WHERE id = %s",
                (time, user_id)
            )
            await conn.commit()

async def looked_update(pool, user_id, look_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT looked FROM users where id = %s", (user_id))
            result = await cur.fetchone()
            current = result[0] if result and result[0] else ""
            ids = current.split(", ") if current else []
            if str(look_id) not in ids:
                ids.append(str(look_id))
            updated_looked = str(", ".join(ids))
            await cur.execute(
                "UPDATE users SET looked = %s WHERE id = %s",
                (updated_looked, user_id)
            )
            await conn.commit()


async def looked_clear(pool, user_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE users SET looked = %s WHERE id = %s",
                ("", user_id)
            )
            await conn.commit()


async def like_the_profile(pool, from_like_id, to_like_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT liked_who FROM users where id = %s", (from_like_id)) # смотрит, кого лайкнул
            result = await cur.fetchone()
            current = result[0] if result and result[0] else ""
            ids = current.split(", ") if current else []
            if str(to_like_id) not in ids:
                ids.append(str(to_like_id))
            updated_like = str(", ".join(ids))
            await cur.execute(
                "UPDATE users SET liked_who = %s WHERE id = %s",
                (updated_like, from_like_id)
            )
            await cur.execute("SELECT liked_it FROM users where id = %s", (to_like_id)) # смотрит кто лайкнул
            result = await cur.fetchone()
            current = result[0] if result and result[0] else ""
            ids = current.split(", ") if current else []
            if str(from_like_id) not in ids:
                ids.append(str(from_like_id))
            updated_like = str(", ".join(ids))
            await cur.execute(
                "UPDATE users SET liked_it = %s WHERE id = %s",
                (updated_like, to_like_id)
            )
            await conn.commit()


async def like_remove(pool, from_like_id, to_like_id):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT liked_who FROM users where id = %s", (from_like_id)) # смотрит, кого лайкнул
            result = await cur.fetchone()
            current = result[0] if result and result[0] else ""
            ids = current.split(", ") if current else []
            if str(to_like_id) in ids:
                ids.remove(str(to_like_id))
            updated_like = str(", ".join(ids))
            await cur.execute(
                "UPDATE users SET liked_who = %s WHERE id = %s",
                (updated_like, from_like_id)
            )
            await cur.execute("SELECT liked_it FROM users where id = %s", (to_like_id)) # смотрит кто лайкнул
            result = await cur.fetchone()
            current = result[0] if result and result[0] else ""
            ids = current.split(", ") if current else []
            if str(from_like_id) in ids:
                ids.remove(str(from_like_id))
            updated_like = str(", ".join(ids))
            await cur.execute(
                "UPDATE users SET liked_it = %s WHERE id = %s",
                (updated_like, to_like_id)
            )
            await conn.commit()