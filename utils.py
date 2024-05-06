from pathlib import Path
from jinja2 import Template


def render_template(path: Path, fields: dict) -> str:
    with open(path, 'r', encoding='utf-8') as file:
        template_text = file.read()
        template = Template(template_text)
        rendered_text = template.render(fields)
    return rendered_text
