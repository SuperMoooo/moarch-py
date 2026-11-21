"""Renders the Jinja templates shipped inside the package (`moarch_py/templates/`)."""

from __future__ import annotations

from functools import cache
from typing import Any

from jinja2 import Environment, PackageLoader, StrictUndefined


def yaml_quote(value: str) -> str:
    """[value] as a double-quoted YAML scalar.

    A skill description holds `: ` and backticks, which a plain scalar cannot,
    and an agent that fails to parse the frontmatter drops the skill silently.
    """
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


@cache
def _environment() -> Environment:
    environment = Environment(
        loader=PackageLoader("moarch_py", "templates"),
        # StrictUndefined: a misspelt variable fails the render instead of
        # silently writing an empty string into someone's project.
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        # trim/lstrip: `{% if %}` lines leave no blank line or indent behind,
        # so a template reads like the file it produces.
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )
    environment.filters["yaml_quote"] = yaml_quote
    return environment


def render(template_name: str, context: dict[str, Any]) -> str:
    """Renders `templates/<template_name>` with [context]."""
    return _environment().get_template(template_name).render(**context)
