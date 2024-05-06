import asyncio
import logging
import sys

from CFG.ConfigHandler import config as cfg
from CFG.UICfg import commands as cmds
from handlers import StaticH, AdminH, RegisterUpdateDeleteH, SearchH

from aiogram import Bot, Dispatcher, types


async def main():
    BOT = Bot(cfg.token.get_secret_value())
    dp = Dispatcher()

    dp.include_routers(
        SearchH.router,
        RegisterUpdateDeleteH.router,
        AdminH.router,
        StaticH.router,
    )

    bot_commands = [
        types.BotCommand(command=name, description=descr) for (name, descr) in cmds.values()
    ]
    await BOT.set_my_commands(bot_commands)
    await BOT.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(BOT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
