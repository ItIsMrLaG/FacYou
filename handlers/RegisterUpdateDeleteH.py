from typing import Any, Tuple

from CFG.UICfg import COMMANDS as cmds
from returns.result import Result, Success, Failure
from utils import render_list_of_groups, render_categories_buttons, render_group

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.db_requests import DatabaseManager
from Interface import Group, Category, User

router = Router()


# ============================ REGISTER EVENT ============================ #


class Register(StatesGroup):
    PRIVATE = "🔒 Приватная"
    PUBLIC = "Публичная"
    choosing_name = State()
    choosing_category = State()
    choosing_privacy = State()
    choosing_link = State()


@router.message(F.text, Command(cmds["register_cmd"][0]))
async def register_cmd(message: types.Message, state: FSMContext):
    await message.answer("Введите название вашей группы:")
    await state.set_state(Register.choosing_name)


@router.message(Register.choosing_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    buttons = [[
        InlineKeyboardButton(text=Register.PRIVATE, callback_data="access:private"),
        InlineKeyboardButton(text=Register.PUBLIC, callback_data="access:public"),
    ]]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        text="<b>Выберите доступность группы:</b> \n(<i>Уровень приватности контролируете Вы сами. В случае приватной группы, Ваша ссылка должна быть приватной. </i>)",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(Register.choosing_privacy)


@router.callback_query(Register.choosing_privacy)
async def process_privacy(callback_query: types.CallbackQuery, state: FSMContext, db: DatabaseManager):
    access = callback_query.data.split("access:")[1]
    if access == "private":
        await state.update_data(is_private=True)
        await callback_query.message.edit_text(text=f"Вы выбрали тип группы: <b>{Register.PRIVATE}</b>",
                                               parse_mode="HTML")
    else:
        await state.update_data(is_private=False)
        await callback_query.message.edit_text(text=f"Вы выбрали тип группы: <b>{Register.PUBLIC}</b>",
                                               parse_mode="HTML")

    cats = await db.get_categories()
    keyboard = InlineKeyboardMarkup(inline_keyboard=render_categories_buttons(cats, "category"))

    await callback_query.message.answer(text="Выберите категорию группы:", reply_markup=keyboard)
    await callback_query.answer()
    await state.set_state(Register.choosing_category)


@router.callback_query(Register.choosing_category)
async def process_categories(callback_query: types.CallbackQuery, state: FSMContext, db: DatabaseManager):
    cat_id = callback_query.data.split("category:")[1]
    category = await db.get_category(cat_id)

    if isinstance(category, Failure):
        await callback_query.answer(category._inner_value)
        await state.clear()
        return

    cat_name = category.unwrap().name

    if cat_name.find("Другое") != -1:
        await state.update_data(category=Category(id=int(cat_id), name=cat_name))
        await callback_query.message.edit_text(f"Похоже, для вашей группы еще нет подходящей категории",
                                               parse_mode="HTML")
    else:
        await state.update_data(category=Category(id=int(cat_id), name=cat_name))
        await callback_query.message.edit_text(f"Вы выбрали категорию: <b>{cat_name}</b>", parse_mode="HTML")

    await callback_query.message.answer("Введите ссылку на группу:")
    await callback_query.answer()
    await state.set_state(Register.choosing_link)


@router.message(Register.choosing_link)
async def process_link(message: types.Message, state: FSMContext, db: DatabaseManager):
    await state.update_data(link=message.text)

    data = await state.get_data()

    name: str = data["name"]
    category: Category = data["category"]
    link: str = data["link"]
    is_private: bool = data["is_private"]

    new_group: Group = Group(
        name=name,
        link=link,
        holder=User(id=message.from_user.id, nick=message.from_user.username),
        is_private=is_private,
        category=category
    )

    res = await db.add_unvalidated_group(new_group)

    if isinstance(res, Failure):
        await message.answer(res._inner_value)
        await state.clear()
        return
    else:
        await message.answer(
            f"Группа отправлена на проверку администратору\n\n" + render_group(new_group),
            parse_mode="HTML"
        )
    await state.clear()


# ============================ LIST EVENT ============================ #


async def get_group_list(
        message: types.Message,
        db: DatabaseManager) -> bool:
    res = await db.get_user_groups(message.from_user.id)
    if isinstance(res, Failure):
        await message.answer(res._inner_value)
        return False
    else:
        [validated, unvalidated] = res.unwrap()
        await message.answer(
            f"{render_list_of_groups([g.name for g in validated], [g.name for g in unvalidated])}",
            parse_mode="HTML"
        )
    return True


@router.message(F.text, Command(cmds["my_groups_cmd"][0]))
async def update_cmd(message: types.Message, state: FSMContext, db: DatabaseManager):
    await get_group_list(message, db)


# ============================ GROUP UPDATE EVENT ============================ #


class Update(StatesGroup):
    UPDATE_KEY = "CHANGE"
    UPDATE = "ИЗМЕНИТЬ"
    choosing_group = State()
    choosing_parameter = State()
    update_title = State()
    update_privacy = State()
    update_link = State()
    update_category = State()


async def update_group(message: types.Message, old_id: int, group: Group, db: DatabaseManager):
    res_name = await db.update_group_title(old_id, group.name)
    if isinstance(res_name, Failure):
        await message.answer(res_name._inner_value)
        return

    res_privacy = await db.update_group_privacy(old_id, group.is_private)
    if isinstance(res_privacy, Failure):
        await message.answer(res_privacy._inner_value)
        return

    # TODO: Update Category and link
    await message.answer("Группа {group.name} успешно обновлена")


@router.message(F.text, Command(cmds["update_cmd"][0]))
async def update_cmd(message: types.Message, state: FSMContext, db: DatabaseManager):
    res = await get_group_list(message, db)
    if res:
        await message.answer("Введите название группы для редактирования:")
        await state.set_state(Update.choosing_group)
    else:
        await state.clear()


async def show_fields_keypad(message_run, text: str):
    buttons = [
        [
            InlineKeyboardButton(text="Имя", callback_data="update:title"),
            InlineKeyboardButton(text="Приватность", callback_data="update:privacy")
        ],
        [
            InlineKeyboardButton(text="Ссылку", callback_data="update:link"),
            InlineKeyboardButton(text="Категорию", callback_data="update:category")
        ],
        [InlineKeyboardButton(text=Update.UPDATE, callback_data=f"update:{Update.UPDATE_KEY}")]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message_run(text, reply_markup=keyboard, parse_mode="HTML")


@router.message(Update.choosing_group)
async def process_choosing_group(message: types.Message, state: FSMContext, db: DatabaseManager):
    await state.update_data(group_name=message.text)
    group_name = (await state.get_data())["group_name"]

    group: Result[Group, str] = await db.get_group_by_name(group_name)
    if isinstance(group, Failure):
        await message.answer(text=group._inner_value)
        await state.clear()
        return

    # TODO group.unwrap().category fail with error !!!

    await state.update_data(
        group_id=group.unwrap().id,
        handlers=[],
        group_info=group.unwrap()
    )

    await show_fields_keypad(
        message.answer,
        f"Выберите поля для редактирования ✏️\n"
        f"<i>Чтоб прекратить редактирование, нажмите {Update.UPDATE}, не выбирая групп</i>"
    )
    await state.set_state(Update.choosing_parameter)


async def title_first_stage(message: types.Message, data: dict, db: DatabaseManager):
    await message.answer(
        f"Введите новое имя группы: \n<i>Старое имя: {data['group_info'].name}</i>",
        parse_mode="HTML"
    )


async def privacy_first_stage(message: types.Message, data: dict, db: DatabaseManager):
    buttons = [[
        InlineKeyboardButton(text=Register.PRIVATE, callback_data="access_update:private"),
        InlineKeyboardButton(text=Register.PUBLIC, callback_data="access_update:public"),
    ]]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        f"Выберите уровень приватности: \n<i>Старый уровень: {'🔒 Приватная' if data['group_info'].is_private else 'Публичная'}</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def link_first_stage(message: types.Message, data: dict, db: DatabaseManager):
    await message.answer(
        f"Введите новую ссылку группы: \n<i>Старая ссылка: {data['group_info'].link}</i>",
        parse_mode="HTML"
    )


async def category_first_stage(message: types.Message, data: dict, db: DatabaseManager):
    cats = await db.get_categories()
    keyboard = InlineKeyboardMarkup(inline_keyboard=render_categories_buttons(cats, "category1"))

    await message.answer(
        text=f"Выберите категорию группы: \n<i>(Категория до этого: {data['group_info'].category.name})</i>",
        reply_markup=keyboard, parse_mode="HTML")


def translate(tp_: str) -> tuple:
    if tp_ == "title":
        return "Имя", Update.update_title, title_first_stage
    elif tp_ == "privacy":
        return "Приватность", Update.update_privacy, privacy_first_stage
    elif tp_ == "category":
        return "Категорию", Update.update_category, category_first_stage
    elif tp_ == "link":
        return "Ссылку", Update.update_link, link_first_stage


async def next_field_update(message: types.Message, data: dict, state: FSMContext, db: DatabaseManager):
    if len(data["handlers"]) == 0:
        await update_group(message, data["group_id"], data['group_info'], db)
        await state.clear()
    else:
        _, st, user_event = translate(data["handlers"][0])
        await user_event(message, data, db)
        await state.set_state(st)
        await state.update_data(handlers=data["handlers"][1:])


@router.callback_query(F.data.startswith("update"), Update.choosing_parameter)
async def process_choosing(callback_query: types.CallbackQuery, state: FSMContext, db: DatabaseManager):
    tp = callback_query.data.split("update:")[1]
    data: dict[str: Any] = await state.get_data()

    if tp == Update.UPDATE_KEY:
        if len(data["handlers"]) == 0:
            await callback_query.message.edit_text("Редактирование прекращено")
            await state.clear()
        else:
            fields = "<b>" + " - " + '\n - '.join([translate(el)[0] for el in data["handlers"]]) + "</b>"

            await callback_query.message.edit_text(
                "Выбранные для редактирования поля: \n" + fields,
                parse_mode="HTML"
            )
            _, st, user_event = translate(data["handlers"][0])
            await user_event(callback_query.message, data, db)
            await state.set_state(st)
            await state.update_data(handlers=data["handlers"][1:])

    elif tp not in data["handlers"]:
        data["handlers"].append(tp)
        fields = "<i>" + " - " + '\n - '.join([translate(el)[0] for el in data["handlers"]]) + "</i>"
        await show_fields_keypad(callback_query.message.edit_text, "Выберите поля для редактирования ✏️\n" + fields)

    await callback_query.answer()


@router.message(Update.update_title)
async def update_title_second_stage(message: types.Message, state: FSMContext, db: DatabaseManager):
    data: dict[str: Any] = await state.get_data()
    data['group_info'].name = message.text

    await next_field_update(message, data, state, db)


@router.callback_query(Update.update_privacy)
async def update_privacy_second_stage(callback_query: types.CallbackQuery, state: FSMContext, db: DatabaseManager):
    access = callback_query.data.split("access_update:")[1]
    data: dict[str: Any] = await state.get_data()

    if access == "private":
        data['group_info'].is_private = True
        await callback_query.message.edit_text(text=f"Вы выбрали тип группы: <b>{Register.PRIVATE}</b>",
                                               parse_mode="HTML")
    else:
        data['group_info'].is_private = False
        await callback_query.message.edit_text(text=f"Вы выбрали тип группы: <b>{Register.PUBLIC}</b>",
                                               parse_mode="HTML")

    await next_field_update(callback_query.message, data, state, db)
    await callback_query.answer()


@router.callback_query(Update.update_category)
async def update_category_next_stage(callback_query: types.CallbackQuery, state: FSMContext, db: DatabaseManager):
    data: dict[str: Any] = await state.get_data()
    cat_id = callback_query.data.split("category1:")[1]
    category = await db.get_category(cat_id)

    if isinstance(category, Failure):
        await callback_query.answer(category._inner_value)
        await state.clear()
        return

    cat_name = category.unwrap().name
    data['group_info'].category = Category(id=int(cat_id), name=cat_name)
    await callback_query.message.edit_text(f"Вы выбрали категорию: <b>{cat_name}</b>", parse_mode="HTML")

    await next_field_update(callback_query.message, data, state, db)
    await callback_query.answer()


@router.message(Update.update_link)
async def update_link_second_stage(message: types.Message, state: FSMContext, db: DatabaseManager):
    data: dict[str: Any] = await state.get_data()
    data['group_info'].link = message.text

    await next_field_update(message, data, state, db)


# ============================ DELETE EVENT ============================ #


class Delete(StatesGroup):
    enter_name = State()


@router.message(F.text, Command(cmds["delete_cmd"][0]))
async def delete_cmd(message: types.Message, db: DatabaseManager, state: FSMContext):
    res = await db.get_user_groups(message.from_user.id)

    if isinstance(res, Failure):
        await message.answer(res._inner_value)
        await state.clear()
        return
    else:
        [validated, unvalidated] = res.unwrap()
        await message.answer(
            f"{render_list_of_groups([g.name for g in validated], [g.name for g in unvalidated])}",
            parse_mode="HTML"
        )
        await message.answer("Выберите группу для удаления:")
        await state.set_state(Delete.enter_name)


@router.message(Delete.enter_name)
async def process_name(message: types.Message, state: FSMContext, db: DatabaseManager):
    await state.update_data(group_name=message.text)

    data = await state.get_data()
    group_name = data["group_name"]
    user_id = message.from_user.id
    res = await db.delete_group(group_name, user_id)
    if isinstance(res, Success):
        await message.answer(res.unwrap())

    await state.clear()
