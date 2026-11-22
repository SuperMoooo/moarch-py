"""The interactive questions `moarch-py init` asks when it is not given `--all`."""

from __future__ import annotations

import questionary

from moarch_py.options import (
    CHECKLISTS,
    OPTIONS_BY_KEY,
    Broker,
    Checklist,
    Database,
    default_keys,
    resolve_needs,
)
from moarch_py.presets import PRESETS, InitPreset
from moarch_py.terminal import console


class WizardCancelledError(Exception):
    """Raised when the user presses Ctrl+C or Esc in a question."""


def _answered[AnswerT](answer: AnswerT | None) -> AnswerT:
    # questionary returns None when the question is cancelled.
    if answer is None:
        raise WizardCancelledError
    return answer


def ask_preset() -> InitPreset | None:
    """Asks what is being built; None for "Let me decide" (the usual defaults)."""
    choices = [questionary.Choice("Let me decide", value="")]
    choices += [
        questionary.Choice(f"{preset.name} — {preset.description}", value=preset.slug)
        for preset in PRESETS
    ]
    slug = _answered(questionary.select("What are you building?", choices=choices).ask())
    return next((preset for preset in PRESETS if preset.slug == slug), None)


def ask_database() -> Database:
    """Asks which database engine the project runs on."""
    answer = questionary.select(
        "Database:",
        choices=[questionary.Choice(database.label, value=database) for database in Database],
        default=Database.POSTGRES,
    ).ask()
    return Database(_answered(answer))


def ask_broker(default: Broker) -> Broker:
    """Asks which broker carries background tasks; "none" means no worker."""
    answer = questionary.select(
        "Background tasks broker:",
        choices=[questionary.Choice(broker.label, value=broker) for broker in Broker],
        default=default,
    ).ask()
    return Broker(_answered(answer))


def ask_checklists(
    preset: InitPreset | None, fixed_broker: Broker | None = None
) -> tuple[set[str], Broker]:
    """Asks every checklist, pre-ticked from [preset]; returns the ticked keys and the broker.

    [fixed_broker] (from `--broker`) skips the broker question.

    A preset's required options are shown ticked and cannot be unticked.
    Options another ticked one needs are added afterwards and listed.
    """
    ticked = preset.ticked if preset else default_keys()
    required = set(preset.required) if preset else set()
    broker = preset.broker if preset else Broker.NONE
    answers: set[str] = set()
    for checklist in CHECKLISTS:
        if checklist.title == "Background & realtime":
            broker = fixed_broker or ask_broker(broker)
        answers |= _ask_checklist(checklist, ticked, required, preset, broker)
    resolved, needed_by = resolve_needs(answers)
    for key, by in sorted(needed_by.items()):
        reasons = ", ".join(OPTIONS_BY_KEY[option].label for option in by)
        console.print(f"  + {OPTIONS_BY_KEY[key].label} (needed by {reasons})")
    return resolved, broker


def _ask_checklist(
    checklist: Checklist,
    ticked: set[str],
    required: set[str],
    preset: InitPreset | None,
    broker: Broker,
) -> set[str]:
    """One checklist's answers. With a lead option, it is asked first as yes/no."""
    options = list(checklist.options)
    answers: set[str] = set()
    if checklist.lead is not None:
        lead = OPTIONS_BY_KEY[checklist.lead]
        if checklist.lead in required:
            answers.add(checklist.lead)
        elif not _answered(
            questionary.confirm(f"{lead.label}?", default=checklist.lead in ticked).ask()
        ):
            return set()
        else:
            answers.add(checklist.lead)
        options = [option for option in options if option.key != checklist.lead]
    if broker is Broker.NONE:
        # The scheduler hands tasks to a broker; without one there is nothing to schedule on.
        options = [option for option in options if option.key != "scheduler"]
    choices = []
    for option in options:
        if option.key in required:
            assert preset is not None
            choices.append(
                questionary.Choice(
                    option.label,
                    value=option.key,
                    checked=True,
                    disabled=f"required by {preset.slug}",
                )
            )
        else:
            choices.append(
                questionary.Choice(option.label, value=option.key, checked=option.key in ticked)
            )
    picked = _answered(
        questionary.checkbox(
            f"{checklist.title} (space to toggle, enter to confirm):", choices=choices
        ).ask()
    )
    # Disabled choices are never part of the answer, so the locked ones are added back.
    return answers | set(picked) | {option.key for option in options if option.key in required}
