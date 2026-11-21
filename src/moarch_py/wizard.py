"""The interactive questions `moarch-py init` asks when it is not given `--all`."""

from __future__ import annotations

import questionary

from moarch_py.options import CHECKLIST, Database


class WizardCancelledError(Exception):
    """Raised when the user presses Ctrl+C or Esc in a question."""


def ask_database() -> Database:
    """Asks which database engine the project runs on."""
    answer = questionary.select(
        "Database:",
        choices=[questionary.Choice(database.label, value=database) for database in Database],
        default=Database.POSTGRES,
    ).ask()
    # questionary returns None when the question is cancelled.
    if answer is None:
        raise WizardCancelledError
    return Database(answer)


def ask_checklist() -> set[str]:
    """Asks what to generate; returns the ticked checklist keys."""
    answer = questionary.checkbox(
        "What to generate (space to toggle, enter to confirm):",
        choices=[
            questionary.Choice(option.label, value=option.key, checked=option.default)
            for option in CHECKLIST
        ],
    ).ask()
    if answer is None:
        raise WizardCancelledError
    return set(answer)
