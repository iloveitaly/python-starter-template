from jinja2 import Environment, FileSystemLoader, select_autoescape

import app
from app.environments import is_development


def render_template(template_path: str, context: dict):
    env = Environment(
        loader=FileSystemLoader(app.root / "app/templates"),
        autoescape=select_autoescape(["html", "xml"]),
        auto_reload=is_development(),
    )

    template = env.get_template(template_path)
    return template.render(context)
