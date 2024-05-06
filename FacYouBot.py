import asyncio
import logging
import sys

from CFG.config_handler import config as cfg
from CFG.ui_cfg import commands as cmds
from utils import render_template

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

BOT = Bot(cfg.token.get_secret_value(), parse_mode=ParseMode.HTML)
dp = Dispatcher()


@dp.message(F.text, Command(cfg["search_cmd"][0]))
async def search_cmd(message: types.Message):
    pass  # TODO


@dp.message(F.text, Command(cfg["register_cmd"][0]))
async def register_cmd(message: types.Message):
    pass  # TODO


@dp.message(F.text, Command(cfg["update_cmd"][0]))
async def update_cmd(message: types.Message):
    pass  # TODO


@dp.message(F.text, Command(cfg["delete_cmd"][0]))
async def delete_cmd(message: types.Message):
    pass  # TODO


@dp.message(F.text, Command(cfg["support_cmd"][0]))
async def support_cmd(message: types.Message):
    pass  # TODO


@dp.message(F.text, Command(cfg["admin_cmd"][0]))
async def admin_cmd(message: types.Message):
    pass  # TODO


@dp.message(F.text, Command(cfg["help_cmd"][0]))
async def help_cmd(message: types.Message):
    fields: dict = {
        "bot_name": "FacYou_bot",
        "search_cmd": cmds["search_cmd"][0],
        "register_cmd": cmds["register_cmd"][0],
    }
    rendered_text: str = render_template(cfg.static_folder.joinpath("guide.template"), fields)

    await message.answer(
        rendered_text, parse_mode="HTML"
    )


@dp.message(F.text, CommandStart)
async def start_cmd(message: Message):
    path = cfg.static_folder.joinpath("hello.template")
    fields: dict = {
        "user_name": message.from_user.full_name,
        "bot_name": "FacYou_bot",
        "search_cmd": cmds["search_cmd"][0],
        "register_cmd": cmds["register_cmd"][0],
    }
    rendered_text: str = render_template(path, fields)

    await message.answer(
        rendered_text, parse_mode="HTML"
    )


async def main():
    bot_commands = [
        types.BotCommand(command=name, description=descr) for (name, descr) in cmds.values()
    ]
    await BOT.set_my_commands(bot_commands)
    await dp.start_polling(BOT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
