"""The names a project or a feature is known by in each place it appears.

One input (`my-api`, `orders`) becomes a distribution name for `pyproject.toml`,
a Python package name for `src/`, a class name, a table name and a URL path.
Deriving all of them in one place keeps a feature called `order_items` from
being `OrderItem` in the model but `Orderitems` in the router.
"""

from __future__ import annotations

import keyword
import re
from dataclasses import dataclass

# A name must start with a letter and may then mix letters, digits, `-`, `_`
# and spaces; anything else (a dot, a slash) would make an invalid package.
_VALID_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9 _-]*$")
_WORD_SEPARATORS = re.compile(r"[ _-]+")
# Splits `OrderItems` and `orderItems` into words before they are re-joined.
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
# Written in capitals in a human title: "Shop API", not "Shop Api".
_ACRONYMS = frozenset(
    {"ai", "api", "crm", "db", "erp", "http", "id", "io", "sdk", "sql", "ui", "url"}
)


def _title_word(word: str) -> str:
    return word.upper() if word in _ACRONYMS else word.capitalize()


class InvalidNameError(ValueError):
    """Raised when a project or feature name cannot become a Python identifier."""


def _words(raw_name: str) -> list[str]:
    """Splits `my-api`, `my_api`, `My Api` and `myApi` into `["my", "api"]`."""
    name = raw_name.strip()
    if not _VALID_NAME.match(name):
        raise InvalidNameError(
            f"'{raw_name}' is not a valid name: start with a letter and use only "
            "letters, digits, '-', '_' or spaces."
        )
    spaced = _CAMEL_BOUNDARY.sub(" ", name)
    return [word.lower() for word in _WORD_SEPARATORS.split(spaced) if word]


def singular(word: str) -> str:
    """Returns the English singular of a plural noun, for the common cases.

    `orders` → `order`, `categories` → `category`, `addresses` → `address`.
    Irregular plurals (`people`) stay as they are; the user can pass the
    singular explicitly where that matters.
    """
    if word.endswith("ies") and len(word) > 3:
        return word[:-3] + "y"
    if word.endswith(("sses", "xes", "ches", "shes")):
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _ensure_identifier(identifier: str, raw_name: str) -> str:
    """Rejects a name that is a Python keyword (`class`, `import`) once joined."""
    if keyword.iskeyword(identifier):
        raise InvalidNameError(f"'{raw_name}' is a Python keyword and cannot name a package.")
    return identifier


@dataclass(frozen=True)
class ProjectName:
    """A project's name in each form `pyproject.toml`, `src/` and docs need."""

    distribution: str
    """`my-api`: the name in `pyproject.toml` and on PyPI."""

    package: str
    """`my_api`: the import name, and the folder under `src/`."""

    title: str
    """`My API`: the human name in the README and the OpenAPI docs."""

    @classmethod
    def parse(cls, raw_name: str) -> ProjectName:
        """Builds every form of the project name from what the user typed."""
        words = _words(raw_name)
        package = _ensure_identifier("_".join(words), raw_name)
        return cls(
            distribution="-".join(words),
            package=package,
            title=" ".join(_title_word(word) for word in words),
        )


@dataclass(frozen=True)
class FeatureName:
    """A feature's name in each form its six files and its route need.

    A feature is named by its plural (`orders`), the way its URL and table
    read; the model class is the singular (`Order`).
    """

    module: str
    """`order_items`: the folder under `features/`."""

    url_path: str
    """`order-items`: the route prefix, `/api/v1/order-items`."""

    table: str
    """`order_items`: the database table."""

    model_class: str
    """`OrderItem`: the SQLAlchemy model class."""

    singular_snake: str
    """`order_item`: a variable holding one row, `order_item_id` in a path."""

    plural_title: str
    """`Order Items`: the OpenAPI tag."""

    @classmethod
    def parse(cls, raw_name: str) -> FeatureName:
        """Builds every form of the feature name from what the user typed."""
        words = _words(raw_name)
        singular_words = [*words[:-1], singular(words[-1])]
        module = _ensure_identifier("_".join(words), raw_name)
        return cls(
            module=module,
            url_path="-".join(words),
            table=module,
            model_class="".join(word.capitalize() for word in singular_words),
            singular_snake="_".join(singular_words),
            plural_title=" ".join(word.capitalize() for word in words),
        )
