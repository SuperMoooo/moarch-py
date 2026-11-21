"""The `moarch-py` command line. Same grammar as the Flutter moarch: init, create <thing>, ..."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from moarch_py import __version__
from moarch_py.commands import (
    CreateModelRequest,
    CreateModuleRequest,
    InitRequest,
    UsageError,
    run_create_model,
    run_create_module,
    run_init,
)
from moarch_py.file_plan import AnchorNotFoundError, FileConflictError
from moarch_py.naming import InvalidNameError
from moarch_py.options import Database
from moarch_py.scaffold import ModelExistsError, NotAMoarchProjectError, UnknownModuleError
from moarch_py.terminal import FAILED, error_console, make_output_safe
from moarch_py.uv_runner import ToolMissingError
from moarch_py.wizard import WizardCancelledError

app = typer.Typer(
    name="moarch-py",
    help="Scaffold and grow modular-monolith FastAPI projects on uv.",
    no_args_is_help=True,
    add_completion=False,
)
create_app = typer.Typer(help="Add a piece to an existing moarch-py project.", no_args_is_help=True)
app.add_typer(create_app, name="create")

# Errors that mean "the command could not do what was asked", shown as one
# message rather than a traceback.
_EXPECTED_ERRORS = (
    UsageError,
    InvalidNameError,
    FileConflictError,
    AnchorNotFoundError,
    NotAMoarchProjectError,
    UnknownModuleError,
    ModelExistsError,
    ToolMissingError,
)


def _show_version(requested: bool) -> None:
    if requested:
        typer.echo(f"moarch-py {__version__}")
        raise typer.Exit


@app.callback()
def _root(
    version: Annotated[
        bool,
        typer.Option("--version", callback=_show_version, is_eager=True, help="Show the version."),
    ] = False,
) -> None:
    """Scaffold and grow modular-monolith FastAPI projects on uv."""


@app.command()
def init(
    name: Annotated[
        str | None,
        typer.Argument(help="Create this folder. Leave out to scaffold the current folder."),
    ] = None,
    take_defaults: Annotated[
        bool, typer.Option("--all", help="Generate the default structure without prompts.")
    ] = False,
    database: Annotated[
        Database | None, typer.Option("--db", help="Database engine, skipping that question.")
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="List what would be written; write nothing.")
    ] = False,
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing files.")] = False,
    install: Annotated[
        bool,
        typer.Option("--install/--no-install", help="Install packages with uv after writing."),
    ] = True,
) -> None:
    """Scaffold a FastAPI project: app, database, tests, Docker, CI and the AI agent guide."""
    _run(
        lambda: run_init(
            InitRequest(
                name=name,
                take_defaults=take_defaults,
                database=database,
                dry_run=dry_run,
                force=force,
                install=install,
            )
        )
    )


@create_app.command("module")
def create_module(
    name: Annotated[
        str, typer.Argument(help="The business area, as a plural: orders, order_items.")
    ],
    project: Annotated[Path, typer.Option("--project", "-p", help="The project folder.")] = Path(
        "."
    ),
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="List what would be written; write nothing.")
    ] = False,
    force: Annotated[
        bool, typer.Option("--force", help="Overwrite the module's files if they exist.")
    ] = False,
) -> None:
    """A module: public.py for other modules, plus model, schemas, repository, service, router."""
    _run(
        lambda: run_create_module(
            CreateModuleRequest(name=name, project_root=project, dry_run=dry_run, force=force)
        )
    )


# `feature` was this command's name in 0.1.0 and is still the Flutter moarch's
# word; kept as a hidden alias so existing scripts and habits keep working.
create_app.command("feature", hidden=True)(create_module)


@create_app.command("model")
def create_model(
    module: Annotated[str, typer.Argument(help="The existing module it belongs to: orders.")],
    name: Annotated[str, typer.Argument(help="The new model, as a plural: order_lines.")],
    project: Annotated[Path, typer.Option("--project", "-p", help="The project folder.")] = Path(
        "."
    ),
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="List what would be written; write nothing.")
    ] = False,
) -> None:
    """Another model inside an existing module: its class, schemas, repository and a test."""
    _run(
        lambda: run_create_model(
            CreateModelRequest(module=module, name=name, project_root=project, dry_run=dry_run)
        )
    )


def _run(command: Callable[[], None]) -> None:
    """Runs [command], turning an expected failure into a message and exit code 1."""
    try:
        command()
    except _EXPECTED_ERRORS as error:
        error_console.print(f"{FAILED} {error}")
        raise typer.Exit(code=1) from error
    except WizardCancelledError:
        error_console.print("Cancelled; nothing was written.")
        raise typer.Exit(code=1) from None


def main() -> None:
    """The `moarch-py` console script."""
    make_output_safe()
    app()
