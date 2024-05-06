from CFG.ConfigHandler import config as cfg
from CFG.UICfg import commands as cmds
from utils import render_template

from aiogram import types, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router()


@router.message(F.text, Command(cmds["admin_cmd"][0]))
async def admin_cmd(message: types.Message):
    pass  # TODO
