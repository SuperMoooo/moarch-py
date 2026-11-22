"""The two kinds of catalog entry: a whole generated file, and a snippet added at an anchor.

Shared files (main.py, config.py, docker-compose.yml…) are written once by
`init` and edited by their owners afterwards, so an option added later can
never re-render them. Instead every option reaches a shared file through an
`AnchorInsert`: the same snippet at the same `# moarch:` line, whether `init`
adds the option or `create` adds it a year later (docs/adr/0006).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from moarch_py.options import ProjectOptions


def always(_: ProjectOptions) -> bool:
    """The `when` of a file or snippet every project has."""
    return True


@dataclass(frozen=True)
class ScaffoldSpec:
    """One generated file: where it goes, what renders it, and when it exists."""

    slug: str
    """The name `moarch-py update <slug>` takes; unique across the catalog."""

    path: str
    """The project-relative path; `{package}` is replaced by the package name."""

    template: str
    """The template under `moarch_py/templates/`."""

    group: str
    """The group `moarch-py update <group>` refreshes together."""

    when: Callable[[ProjectOptions], bool] = always

    extra: dict[str, str] = field(default_factory=dict)
    """Template variables only this file needs (a skill's name and description)."""

    def path_for(self, package: str) -> str:
        """The path in a project whose package is [package]."""
        return self.path.format(package=package)


@dataclass(frozen=True)
class AnchorInsert:
    """A snippet an option adds to a file above its `# moarch:<anchor>` line.

    Exactly one of [template] (a file under `templates/`) or [text] (a short
    inline Jinja snippet, such as an import line) gives the content.
    """

    slug: str
    path: str
    """The target file, as in ScaffoldSpec.path."""

    anchor: str
    when: Callable[[ProjectOptions], bool]
    template: str | None = None
    text: str | None = None

    def path_for(self, package: str) -> str:
        """The target's path in a project whose package is [package]."""
        return self.path.format(package=package)
