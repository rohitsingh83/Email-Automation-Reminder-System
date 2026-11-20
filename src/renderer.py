"""Jinja2 email template renderer."""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def render_email(templates_dir: Path, template_name: str, context: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    template = env.get_template(template_name)
    return template.render(**context)
