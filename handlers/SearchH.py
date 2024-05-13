from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from CFG.UICfg import commands as cmds

from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from Interface import Group, Category
from database.db_requests import DatabaseManager
from utils import render_categories_buttons, render_group_links, render_categories_list

router = Router()


class Search(StatesGroup):
    SUBMIT_KEY = "SUBMIT"
    SUBMIT_NAME = "ВЫБРАТЬ"
    choosing = State()


@router.message(F.text, Command(cmds["search_cmd"][0]))
async def search_cmd(message: types.Message, state: FSMContext, db: DatabaseManager):
    cats: list[Category] = await db.get_categories()
    cats_dict: dict[str: Category] = dict([(cat.id, cat.name) for cat in cats])
    print(cats_dict)

    cat_buttons = render_categories_buttons(cats)
    submit_button = [InlineKeyboardButton(text=Search.SUBMIT_NAME, callback_data=f"category:{Search.SUBMIT_KEY}")]
    cat_buttons.append(submit_button)

    keyboard = InlineKeyboardMarkup(inline_keyboard=cat_buttons)

    await message.answer(text="Выберите категорию группы:", reply_markup=keyboard)
    await state.set_state(Search.choosing)

    await state.update_data(
        user_cat_ids=set(),
        user_keyboard=keyboard,
        available_cats=cats_dict
    )


@router.callback_query(Search.choosing)
async def process_category(callback_query: types.CallbackQuery, state: FSMContext, db: DatabaseManager):
    key: str = callback_query.data.split("category:")[1]
    data: dict[str: Any] = await state.get_data()

    if key == Search.SUBMIT_KEY:
        user_cat_ids: set[str] = data["user_cat_ids"]
        cat_names: list[str] = [data["available_cats"][int(c_id)] for c_id in data["user_cat_ids"]]

        groups: list[Group] = []

        for cat_id in user_cat_ids:
            groups.extend(await db.get_validated_groups_by_category(cat_id))

        msg = f"<b>Выбранные категории:</b>\n{render_categories_list(cat_names)} \n\n<b>Доступные группы:</b>\n{render_group_links(groups)}"

        await callback_query.message.edit_text(msg, parse_mode='HTML')
        await callback_query.answer()
        await state.clear()

    else:
        cat_id: str = key
        if cat_id not in data["user_cat_ids"]:
            data["user_cat_ids"].add(cat_id)

            # TODO: Make it more efficient (pass a string of group names through the state)
            cat_names: list[str] = [data["available_cats"][int(c_id)] for c_id in data["user_cat_ids"]]

            main_info: str = "Выберите категорию группы: \n"
            info: str = "<i>" + f"Выбранные {len(data['user_cat_ids'])} категории:\n" + render_categories_list(
                cat_names) + "</i>"

            await callback_query.message.edit_text(
                text=main_info + info,
                reply_markup=data["user_keyboard"],
                parse_mode='HTML'
            )

        await callback_query.answer()
