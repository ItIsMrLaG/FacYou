from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from CFG.UICfg import ADMIN_COMMANDS as ad_cmds
from CFG.UICfg import COMMANDS as cmds

from returns.result import Success, Result, Failure
from aiogram import types, F, Router
from aiogram.filters import Command

from Interface import Group
from database.db_requests import DatabaseManager
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from CFG.ConfigHandler import config as cfg
from utils import render_group_link, render_template, render_group


class Admin(StatesGroup):
    validate = State()


router = Router()


async def send_validate_item(message: Message, g: Group):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"validate:accept"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"validate:reject")
        ]
    ])

    await message.answer(
        render_group(g),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(F.text, Command(cmds["admin_cmd"][0]))
async def admin_cmd(message: types.Message):
    user_id: int = message.from_user.id
    if user_id not in cfg.admins:
        await message.answer("Вы не являетесь администратором данного бота")
        return

    path = cfg.static_folder.joinpath("admin.template")
    fields: dict = {
        "validate_cmd": ad_cmds["validate_cmd"][0]
    }

    rendered_text: str = render_template(path, fields)

    await message.answer(rendered_text, parse_mode="HTML")


@router.message(F.text, Command(ad_cmds["validate_cmd"][0]))
async def validate_cmd(message: types.Message, state: FSMContext, db: DatabaseManager):
    user_id: int = message.from_user.id
    if user_id not in cfg.admins:
        await message.answer("Вы не являетесь администратором данного бота")
        return

    groups: list[Group] = await db.get_unvalidated_groups()
    if len(groups) == 0:
        await message.answer("Нет групп, ожидающих валидации :)")
        return

    g: Group = groups[0]
    await send_validate_item(message, g)
    await state.set_state(Admin.validate)

    await state.update_data(
        groups=groups[1:],
        group_on_validate=g,
    )


@router.callback_query(Admin.validate, F.data.startswith("validate:"))
async def handle_validation(callback_query: types.CallbackQuery, state: FSMContext, db: DatabaseManager):
    q_data: str = callback_query.data.split("validate:")[1]
    ans: str = q_data.split(":")[0]
    data: dict[str: Any] = await state.get_data()
    group_on_validate: Group = data["group_on_validate"]

    if ans == "accept":
        result: Result[bool, str] = await db.update_group_set_validate_status(str(group_on_validate.id))
        if isinstance(result, Failure):
            await callback_query.message.edit_text(
                text=f"‼️Не удалось добавить группу {render_group_link(data['group_on_validate'])}.",
                parse_mode="HTML"
            )
            # TODO: handle the case result.unwrap()

        await callback_query.message.edit_text(
            text=f"✅ Группа {render_group_link(data['group_on_validate'])} добавлена. (автор запроса: @{data['group_on_validate'].holder.nick})",
            parse_mode="HTML",
        )
    else:
        group_name = group_on_validate.name
        res = await db.delete_group(group_name, callback_query.from_user.id)
        await callback_query.message.edit_text(
            "❌" + res._inner_value + f"\n(группа: {render_group_link(data['group_on_validate'])}, автор запроса: @{data['group_on_validate'].holder.nick})",
            parse_mode="HTML",
        )

    if len(data["groups"]) == 0:
        await callback_query.message.answer("‼️Нет групп, ожидающих валидации :)")
        await callback_query.answer()
        await state.clear()
        return

    g: Group = data["groups"][0]
    await send_validate_item(callback_query.message, g)

    await state.update_data(
        groups=data["groups"][1:],
        group_on_validate=g,
    )


@router.callback_query(Admin.validate, F.data)
async def strange_behaviour(callback_query: types.CallbackQuery, state: FSMContext, db: DatabaseManager):
    await callback_query.message.edit_text(
        "🥺 Используйте встроенную клавиатуру, а не ручной ввод. (Для возобновления процесса валидации: /validate)")
    await callback_query.answer()
    await state.clear()
