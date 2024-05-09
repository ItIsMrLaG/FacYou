from CFG.ConfigHandler import config as cfg
from CFG.UICfg import commands as cmds
from utils import render_template

from returns.result import Success
from aiogram import types, F, Router
from aiogram.filters import Command
from database.db_requests import DatabaseManager
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup



router = Router()

admin_ids = {1236245459}    

@router.message(F.text, Command(cmds["admin_cmd"][0]))
async def admin_cmd(message: types.Message):
    pass  # TODO

@router.message(F.text, Command(cmds["validate_cmd"][0]))
async def validate_cmd(message: types.Message, db: DatabaseManager):
    user_id = message.from_user.id
    if user_id not in admin_ids:
        await message.answer("Вы не являетесь администратором данного бота")
        return
    
    groups = await db.get_unvalidated_groups()
    for g in groups:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"validate:accept:{g.name}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"validate:reject:{g.name}")
            ]
        ])

        await message.answer(
            f"Название: {g.name}\n"
            f"Ссылка: {g.link}\n"
            f"Категория: {g.category.name}\n"
            f"{'🔒 Приватная' if g.is_private else 'Публичная'}\n",
            reply_markup=keyboard
        )

@router.callback_query(F.data)
async def handle_validation(callback_query: types.CallbackQuery, db: DatabaseManager):
    data = callback_query.data.split("validate:")[1]
    ans = data.split(":")[0]

    if ans == "accept":
        group_name = data.split(":")[1]
        group_id = await db.get_group_id_by_name(group_name)
        if isinstance(group_id, Success):
            await db.update_group_set_validate_status(group_id.unwrap())
            await callback_query.message.answer("Группа принята")
    else:
        group_name = data.split(":")[1]
        res = await db.delete_group(group_name, callback_query.from_user.id)
        await callback_query.message.answer(res._inner_value)
