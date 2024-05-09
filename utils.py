from pathlib import Path
from jinja2 import Template
from Interface import Category
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Interface import Group



def render_template(path: Path, fields: dict) -> str:
    with open(path, 'r', encoding='utf-8') as file:
        template_text = file.read()
        template = Template(template_text)
        rendered_text = template.render(fields)
    return rendered_text

def render_list_of_groups(validated: list[str], unvalidated: list[str]) -> str:
    response = "Ваши провалидированные группы:\n"
    if validated:
        response += "\n".join(f"   * {group}" for group in validated)
    else:
        response += "   Нет провалидированных групп"

    response += "\n\nВаши непровалидированные группы:\n"
    if unvalidated:
        response += "\n".join(f"   * {group}" for group in unvalidated)
    else:
        response += "   Нет непровалидированных групп"

    return response

def render_categories_buttons(categories: list[Category]) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(text=c.name, callback_data=f"category:{c.id}") for c in categories
    ]
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
    
    return keyboard

def render_group_links(groups: list[Group]) -> str:
    response = "Доступные группы в данной категории:\n"
    response += "\n".join(f'<a href="{g.link}">{g.name}</a>' for g in groups)

    return response