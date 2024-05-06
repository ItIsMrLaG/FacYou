from CFG.UICfg import commands as cmds

from aiogram import types, F, Router
from aiogram.filters import Command

router = Router()


@router.message(F.text, Command(cmds["register_cmd"][0]))
async def register_cmd(message: types.Message):
    pass  # TODO


@router.message(F.text, Command(cmds["update_cmd"][0]))
async def update_cmd(message: types.Message):
    pass  # TODO


@router.message(F.text, Command(cmds["delete_cmd"][0]))
async def delete_cmd(message: types.Message):
    pass  # TODO
