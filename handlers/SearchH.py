from CFG.UICfg import commands as cmds

from aiogram import types, F, Router
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from Interface import Category

# TODO: REWRITE IT
categories = [Category("спорт", "0"), Category("что-то", "1")]
# TODO

CATEGORY_PREFIX = "cat_"
FINISH_POSTFIX = "end"

router = Router()
user_data: dict[int: set[str]] = {}


def get_categories_keyboard(cat: list[Category]) -> InlineKeyboardMarkup:
    buttons = [
        [types.InlineKeyboardButton(
            text=f"{el.name}", callback_data=CATEGORY_PREFIX + el.id
        )] for el in cat
    ]
    buttons.append([
        types.InlineKeyboardButton(
            text="НАЙТИ",
            callback_data=CATEGORY_PREFIX + FINISH_POSTFIX
        ),
    ])
    print(buttons[0][0].callback_data)
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_categories_from_id(cat: list[Category], id_set: set[str]) -> list[categories]:
    ans: list[Category] = []
    for ct in cat:
        if ct.id in id_set:
            ans.append(ct)
    return ans


@router.message(F.text, Command(cmds["search_cmd"][0]))
async def search_cmd(message: types.Message):
    # TODO
    # await message.answer(
    #     "<i>Выбранные категории\n...</i>\n\nДобавьте категорию: ",
    #     parse_mode="HTML",
    #     reply_markup=get_categories_keyboard(categories)
    # )
    # print("here")
    ...


async def add_category(message: types.Message, user_set: set[str]):
    user_categories: list[Category] = get_categories_from_id(categories, user_set)
    user_categories_str: str = " ".join([el.name for el in user_categories])
    await message.edit_text(
        f"<i>Выбранные категории\n{user_categories_str}</i>\n\nДобавьте категорию: ",
        parse_mode="HTML",
        reply_markup=get_categories_keyboard(categories),
    )


@router.callback_query(F.data.startswith("CATEGORY_PREFIX"))
async def callbacks_num(callback: types.CallbackQuery):
    user_set: set[str] = user_data.get(callback.from_user.id, set())
    action = callback.data.split("_")[1]

    print("Here")

    if action == FINISH_POSTFIX:
        user_categories: list[Category] = get_categories_from_id(categories, user_set)
        # TODO: REWRITE IT:
        ans = "\n⏩".join([el.name for el in user_categories])
        user_data.pop(callback.from_user.id)
        await callback.message.edit_text(f"Ваши категории: \n{ans}")
    else:
        user_set.add(action)
        user_data[callback.from_user.id] = user_set
        await add_category(callback.message, user_set)

    await callback.answer()
