from pathlib import Path
from jinja2 import Template

import CFG.VerifiedLinks
from Interface import Category
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Interface import Group


def render_template(path: Path, fields: dict) -> str:
    with open(path, 'r', encoding='utf-8') as file:
        template_text = file.read()
        template = Template(template_text)
        rendered_text = template.render(fields)
    return rendered_text


def render_categories_list(categories: list[str]) -> str:
    return "- " + "\n- ".join(categories)


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


def render_categories_buttons(categories: list[Category]) -> list[list[InlineKeyboardButton]]:
    buttons = [
        InlineKeyboardButton(text=c.name, callback_data=f"category:{c.id}") for c in categories
    ]

    return [buttons[i:i + 2] for i in range(0, len(buttons), 2)]


def render_group_link(group: Group) -> str:
    return f'<a href="{group.link}">{group.name}</a>'


def render_group_links(groups: list[Group]) -> str:
    return "\n".join(render_group_link(g) for g in groups)


def check_link(link: str) -> bool:
    for el in CFG.VerifiedLinks.GOOD_LINKS.values():
        print(link.find(el), el)
        if link.find(el) == 0:
            return True
    return False
