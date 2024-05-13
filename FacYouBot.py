import asyncio
import logging
import sys

from CFG.ConfigHandler import config as cfg
from CFG.UICfg import COMMANDS as cmds
from handlers import StaticH, AdminH, RegisterUpdateDeleteH, SearchH

from aiogram import Bot, Dispatcher, types
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from db_middleware import DatabaseMiddleware
from database.models import async_main


async def main():
    engine = create_async_engine(cfg.db_url, echo=True)
    await async_main(engine)
    session = async_sessionmaker(engine, expire_on_commit=False)

    BOT = Bot(cfg.token.get_secret_value())
    dp = Dispatcher()

    dp.include_routers(
        SearchH.router,
        RegisterUpdateDeleteH.router,
        AdminH.router,
        StaticH.router,
    )
    dp.update.middleware(DatabaseMiddleware(session=session))

    bot_commands = [
        types.BotCommand(command=name, description=descr) for (name, descr) in cmds.values()
    ]
    await BOT.set_my_commands(bot_commands)
    await BOT.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(BOT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
