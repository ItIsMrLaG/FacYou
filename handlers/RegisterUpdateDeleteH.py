from CFG.UICfg import commands as cmds
from returns.result import Result, Success, Failure
from utils import render_list_of_groups, render_categories_buttons

from aiogram import types, F, Router, types
from aiogram.filters import Command
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.db_requests import DatabaseManager
from Interface import Group, Category, User

router = Router()

class Register(StatesGroup):
    choosing_name = State()
    choosing_category = State()
    choosing_privacy = State()
    choosing_link = State()

@router.message(F.text, Command(cmds["register_cmd"][0]))
async def register_cmd(message: types.Message, db: DatabaseManager, state: FSMContext):
    await message.answer("Введите название вашей группы:")
    await state.set_state(Register.choosing_name)

@router.message(Register.choosing_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    private = InlineKeyboardButton(text="🔒 Приватная", callback_data="access:private")
    public = InlineKeyboardButton(text="Публичная", callback_data="access:public")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[private, public]])
    await message.answer(text="Выберите доступность группы:", reply_markup=keyboard)
    await state.set_state(Register.choosing_privacy)


@router.callback_query(Register.choosing_privacy)
async def process_privacy(callback_query: types.CallbackQuery, state: FSMContext, db: DatabaseManager):
    access = callback_query.data.split("access:")[1]
    if access == "private":
        await state.update_data(is_private=True)
    else:
        await state.update_data(is_private=False)
    
    cats = await db.get_categories()
    keyboard = render_categories_buttons(cats)

    await callback_query.message.answer(text="Выберите категорию группы:", reply_markup=keyboard)
    await state.set_state(Register.choosing_category)


@router.callback_query(Register.choosing_category)
async def process_categories(callback_query: types.CallbackQuery, state: FSMContext, db: DatabaseManager):
    cat_id = callback_query.data.split("category:")[1]
    category = await db.get_category(cat_id)

    if isinstance(category, Failure):
        await callback_query.answer(category._inner_value)
        state.clear()
        return
    
    cat_name = category.unwrap().name
    
    if cat_name.find("Другое") != -1:
        await state.update_data(category=Category(id = cat_id, name=cat_name))
        await callback_query.answer(f"Похоже, для вашей группы еще нет подходящей категории")
    else:
        await state.update_data(category=Category(id = cat_id, name=cat_name))
        await callback_query.answer(f"Вы выбрали категорию: {cat_name}")
        
    await callback_query.message.answer("Введите ссылку на группу")
    await state.set_state(Register.choosing_link)

@router.message(Register.choosing_link)
async def process_link(message: types.Message, state: FSMContext, db: DatabaseManager):
    await state.update_data(link=message.text)

    data = await state.get_data()

    name = data["name"]
    category = data["category"]
    link = data["link"]
    is_private=data["is_private"]

    res = await db.add_unvalidated_group(
        Group(
            name=name, 
            link=link,
            holder=User(id=message.from_user.id, nick=message.from_user.username),
            is_private=is_private,
            category=category
            ))
    
    if (isinstance(res, Failure)):
        await message.answer(res._inner_value)
        state.clear()
        return
    else:
        await message.answer("Группа отправлена на проверку администратору")

    await state.clear()

class Update(StatesGroup):
    choosing_group = State()
    choosing_parameter = State()
    update_title = State()
    update_privacy = State()


@router.message(F.text, Command(cmds["update_cmd"][0]))
async def update_cmd(message: types.Message, state: FSMContext, db: DatabaseManager):
    res = await db.get_user_groups(message.from_user.id)
    if isinstance(res, Failure):
        message.answer(res._inner_value)
        state.clear()
        return
    else:
        [validated, unvalidated] = res.unwrap()
        await message.answer(f"{render_list_of_groups([g.name for g in validated], [g.name for g in unvalidated])}")  
        await message.answer("Введите название группы для редактирования:")
    await state.set_state(Update.choosing_group)

@router.message(Update.choosing_group)
async def process_choosing_group(message: types.Message, state: FSMContext, db: DatabaseManager):
    await state.update_data(group_name = message.text)
    group_name = (await state.get_data())["group_name"]

    group_id = await db.get_group_id_by_name(group_name)
    if isinstance(group_id, Failure):
        await message.answer(text = group_id._inner_value)
        state.clear()
        return
    
    await state.update_data(group_id = group_id.unwrap())

    title = InlineKeyboardButton(text="Название", callback_data="update:title")
    privacy = InlineKeyboardButton(text="Приватность", callback_data="update:privacy")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[title, privacy]])
    await message.answer("Выберите параметр для редактирования", reply_markup=keyboard)
    await state.set_state(Update.choosing_parameter)

@router.callback_query(Update.choosing_parameter)
async def process_choosing(callback_query: types.CallbackQuery, state: FSMContext):
    type = callback_query.data.split("update:")[1]
    if type == "title":
        await callback_query.message.answer("Введите новое название")
        await state.set_state(Update.update_title)
    elif type == "privacy":
        await state.set_state(Update.update_privacy)
    

@router.message(Update.update_title)
async def update_title(message: types.Message, state: FSMContext, db: DatabaseManager):
    await state.update_data(title=message.text)

    data = await state.get_data()
    title = data["title"]
    group_id = data["group_id"]

    res = await db.update_group_title(group_id, title)
    if isinstance(res, Failure):
        await message.answer(res._inner_value)
        state.clear()
    else:
        await message.answer("Группа успешно обновлена")

    await state.clear()

@router.message(Update.update_privacy)
async def update_privacy(message: types.Message, state: FSMContext, db: DatabaseManager):
    data = await state.get_data()
    group_id = data["group_id"]

    res = await db.update_group_privacy(group_id)
    if isinstance(res, Failure):
        await message.answer(res._inner_value)
        state.clear()
    else:
        await message.answer("Группа успешно обновлена")
    await state.clear()

class Delete(StatesGroup):
    enter_name = State()

@router.message(F.text, Command(cmds["delete_cmd"][0]))
async def delete_cmd(message: types.Message, db: DatabaseManager, state: FSMContext):
    res = await db.get_user_groups(message.from_user.id)

    if isinstance(res, Failure):
        await message.answer(res._inner_value)
        state.clear()
        return
    else:
        [validated, unvalidated] = res.unwrap()
        await message.answer(f"{render_list_of_groups([g.name for g in validated], [g.name for g in unvalidated])}")
        await message.answer("Выберите группу для удаления:")
        await state.set_state(Delete.enter_name)

@router.message(Delete.enter_name)
async def process_name(message: types.Message, state: FSMContext, db: DatabaseManager):
    await state.update_data(group_name = message.text)

    data = await state.get_data()
    group_name = data["group_name"]
    user_id = message.from_user.id
    res = await db.delete_group(group_name, user_id)
    if isinstance(res, Success):
        await message.answer(res.unwrap())
    
    await state.clear()


