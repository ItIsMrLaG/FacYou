from CFG.UICfg import commands as cmds

from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from database.db_requests import DatabaseManager
from utils import render_categories_buttons, render_group_links

router = Router()

class Search(StatesGroup):
    choosing_category = State()

@router.message(F.text, Command(cmds["search_cmd"][0]))
async def search_cmd(message: types.Message, state: FSMContext, db: DatabaseManager): 
    cats = await db.get_categories()
    keyboard = render_categories_buttons(cats)

    await message.answer(text="Выберите категорию группы:", reply_markup=keyboard)
    await state.set_state(Search.choosing_category)


@router.callback_query(Search.choosing_category)
async def process_category(callback_query: types.CallbackQuery, state: FSMContext, db: DatabaseManager):
    cat_id = callback_query.data.split("category:")[1]
    groups = await db.get_validated_groups_by_category(cat_id)

    msg = render_group_links(groups)
    await callback_query.message.answer(msg, parse_mode='HTML')

    await state.clear()





