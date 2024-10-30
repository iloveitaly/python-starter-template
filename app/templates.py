from jinja2 import Environment, FileSystemLoader, select_autoescape

import app


def render_template(template_path: str, context: dict):
    env = Environment(
        loader=FileSystemLoader(app.root / "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )

    template = env.get_template(template_path)
    return template.render(context)
