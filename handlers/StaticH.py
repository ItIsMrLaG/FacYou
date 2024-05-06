from CFG.ConfigHandler import config as cfg
from CFG.UICfg import commands as cmds
from CFG.SupportCFG import contacts
from utils import render_template

from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(F.text, Command(cmds["help_cmd"][0]))
async def help_cmd(message: types.Message):
    fields: dict = {
        "bot_name": "FacYou_bot",
        "search_cmd": cmds["search_cmd"][0],
        "register_cmd": cmds["register_cmd"][0],
    }
    rendered_text: str = render_template(cfg.static_folder.joinpath("guide.template"), fields)

    await message.answer(rendered_text, parse_mode="HTML")


@router.message(F.text, Command(cmds["support_cmd"][0]))
async def support_cmd(message: types.Message):
    path = cfg.static_folder.joinpath("support.template")
    fields: dict = {}
    for i in range(len(contacts)):
        fields["id"+str(i)] = contacts[i]
    rendered_text: str = render_template(path, fields)

    await message.answer(rendered_text, parse_mode="HTML")


@router.message(F.text, Command(cmds["start_cmd"][0]))
async def start_cmd(message: Message):
    path = cfg.static_folder.joinpath("hello.template")
    fields: dict = {
        "user_name": message.from_user.full_name,
        "bot_name": "FacYou_bot",
        "search_cmd": cmds["search_cmd"][0],
        "register_cmd": cmds["register_cmd"][0],
    }
    rendered_text: str = render_template(path, fields)

    await message.answer(rendered_text, parse_mode="HTML")


@router.message(F.text)
async def message_with_text(message: Message):
    await message.answer(f"Я не знаю, что с этим делать, попробуйте воспользоваться командой /{cmds['help_cmd'][0]}.")
