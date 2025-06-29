import asyncio, logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config_reader import config

from handlers import commands, questionnaire, echo

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(
        config.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher()

    dp.include_routers(
        commands.router,
        echo.router,
        questionnaire.router
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())