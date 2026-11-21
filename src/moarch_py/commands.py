"""What `moarch-py init` and `moarch-py create feature` do, step by step, including disk and uv."""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from moarch_py.dependencies import dependencies_for
from moarch_py.file_plan import FilePlan
from moarch_py.manifest import MANIFEST_FILE, ProjectManifest, hash_content
from moarch_py.naming import FeatureName, ProjectName
from moarch_py.options import Database, ProjectOptions
from moarch_py.pyproject_file import build_pyproject, read_project_name
from moarch_py.scaffold import PYTHON_VERSION, load_manifest, plan_feature, plan_project
from moarch_py.terminal import FAILED, OK, WARNING, console
from moarch_py.uv_runner import CommandFailedError, run, uv_version
from moarch_py.wizard import ask_checklist, ask_database

# `python -m ruff`, not the `.venv/Scripts/ruff.exe` launcher: antivirus
# heuristics (AVG/Avast Auto-Sandbox) treat every new launcher in a fresh venv
# as an unknown program and sandbox it, which can freeze a Windows machine.
# python.exe is a known, signed binary, so running tools through it is not flagged.
RUFF = ["uv", "run", "python", "-m", "ruff"]


class UsageError(Exception):
    """A problem with how the command was called; shown without a traceback."""


@dataclass(frozen=True)
class InitRequest:
    """Everything `moarch-py init` was called with."""

    name: str | None
    take_defaults: bool
    database: Database | None
    dry_run: bool
    force: bool
    install: bool


def resolve_project_root(name: str | None) -> tuple[Path, ProjectName]:
    """Where the project goes and what it is called.

    With a name, a new folder of that name. Without one, the current folder,
    named by its existing pyproject.toml (after `uv init`) or by the folder.
    """
    if name:
        project_name = ProjectName.parse(name)
        root = Path.cwd() / project_name.distribution
        if root.exists() and any(root.iterdir()):
            raise UsageError(
                f"{root} already exists and is not empty. Run `moarch-py init` inside it "
                "to scaffold it in place, or pick another name."
            )
        return root, project_name
    root = Path.cwd()
    if (root / MANIFEST_FILE).exists():
        raise UsageError(f"{root} is already a moarch-py project ({MANIFEST_FILE} exists).")
    existing_name = read_project_name(root)
    return root, ProjectName.parse(existing_name or root.name)


def collect_options(project_name: ProjectName, request: InitRequest) -> ProjectOptions:
    """The answers: from flags with `--all`, otherwise from the wizard."""
    if request.take_defaults:
        return ProjectOptions.with_defaults(project_name, request.database or Database.POSTGRES)
    if not sys.stdin.isatty():
        raise UsageError("No terminal to ask questions in. Pass --all to take the defaults.")
    database = request.database or ask_database()
    return ProjectOptions.from_checklist(project_name, database, ask_checklist())


def run_init(request: InitRequest) -> None:
    """`moarch-py init`: plans every file, writes them, installs, formats, records."""
    root, project_name = resolve_project_root(request.name)
    options = collect_options(project_name, request)
    detected_uv = uv_version()
    if request.install and detected_uv is None:
        raise UsageError(
            "uv is not installed: https://docs.astral.sh/uv/getting-started/installation/ "
            "(or pass --no-install to only write the files)."
        )

    plan, manifest = plan_project(root, options, uv_version=detected_uv)
    dependencies = dependencies_for(options)
    pyproject_path = root / "pyproject.toml"
    existing_pyproject = (
        pyproject_path.read_text(encoding="utf-8") if pyproject_path.exists() else None
    )
    plan.edit(
        "pyproject.toml",
        build_pyproject(
            existing_pyproject,
            options,
            python_version=PYTHON_VERSION,
            # Without `uv add`, list the names so the file still says what to install.
            unpinned_dependencies=None
            if request.install
            else (dependencies.runtime, dependencies.development),
        ),
    )
    if not (root / ".env").exists():
        plan.add(".env", plan.files[".env.example"])

    if request.dry_run:
        _print_plan(plan, title=f"Would create {project_name.distribution} in {root}")
        console.print(f"Runtime packages: {', '.join(dependencies.runtime)}")
        console.print(f"Dev packages:     {', '.join(dependencies.development)}")
        return

    root.mkdir(parents=True, exist_ok=True)
    plan.write(force=request.force)
    console.print(f"{OK} Wrote {len(plan.files)} files in {root}")

    if request.install:
        _install(root, dependencies.runtime, dependencies.development)
    _init_git(root)

    # Hash what is on disk *after* formatting, so `moarch-py update` does not
    # mistake ruff's reflow for a user's edit.
    on_disk = {path: (root / path).read_text(encoding="utf-8") for path in manifest.files}
    manifest.record(on_disk)
    (root / MANIFEST_FILE).write_text(manifest.render(), encoding="utf-8", newline="\n")
    _print_next_steps(root, options, installed=request.install, named=request.name is not None)


def _install(root: Path, runtime: list[str], development: list[str]) -> None:
    """Adds the packages with uv (newest compatible versions), then formats the code."""
    try:
        with console.status("Resolving and installing packages with uv..."):
            run(["uv", "add", *runtime], cwd=root)
            run(["uv", "add", "--dev", *development], cwd=root)
        console.print(f"{OK} Installed packages, wrote uv.lock")
        # Templates are readable at any line length; ruff makes them match
        # the project's own style, so `ruff format --check` passes from day one.
        run([*RUFF, "format", "."], cwd=root)
        run([*RUFF, "check", "--fix", "--quiet", "."], cwd=root)
        console.print(f"{OK} Formatted with ruff")
    except CommandFailedError as error:
        console.print(f"{FAILED} {error}")
        console.print(
            "The files are written. Fix the problem above, then run in the project:\n"
            f"  uv add {' '.join(runtime)}\n  uv add --dev {' '.join(development)}"
        )
        raise SystemExit(1) from error


def _init_git(root: Path) -> None:
    """Starts a git repository unless the folder is already inside one."""
    if shutil.which("git") is None:
        return
    try:
        run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root)
    except CommandFailedError:
        run(["git", "init", "--quiet"], cwd=root)
        console.print(f"{OK} Started a git repository")


def _print_plan(plan: FilePlan, *, title: str) -> None:
    console.print(f"[bold]{title}[/]")
    for path in sorted(plan.files):
        marker = "~" if path in plan.edits and (plan.root / path).exists() else "+"
        console.print(f"  {marker} {path}")


def _print_next_steps(root: Path, options: ProjectOptions, *, installed: bool, named: bool) -> None:
    steps = []
    if named:
        steps.append(f"cd {root.name}")
    if not installed:
        steps.append("uv sync")
    if options.migrations and options.database.runs_in_container:
        steps.append("docker compose up -d db        # or point DATABASE_URL in .env at yours")
    if options.migrations:
        steps.append("uv run alembic upgrade head")
    steps.append(f"uv run fastapi dev src/{options.name.package}/main.py")
    steps.append("moarch-py create feature orders   # your first feature")
    console.print("\n[bold]Next:[/]")
    for step in steps:
        console.print(f"  {step}")


@dataclass(frozen=True)
class CreateFeatureRequest:
    """Everything `moarch-py create feature` was called with."""

    name: str
    project_root: Path
    dry_run: bool
    force: bool


def run_create_feature(request: CreateFeatureRequest) -> None:
    """`moarch-py create feature <name>`: six layers and a test, registered at the anchors."""
    root = request.project_root.resolve()
    manifest = load_manifest(root)
    feature = FeatureName.parse(request.name)
    if feature.module in manifest.features and not request.force:
        raise UsageError(f"Feature '{feature.module}' already exists (--force to regenerate it).")

    plan = plan_feature(root, manifest, feature)
    if request.dry_run:
        _print_plan(plan, title=f"Would create feature {feature.module}")
        return
    # Decided before writing: an anchor file still exactly as moarch-py left it
    # stays "untouched" after this edit; one the user changed stays "edited".
    untouched_edits = {
        path
        for path in plan.edits
        if manifest.files.get(path) == hash_content((root / path).read_text(encoding="utf-8"))
    }
    plan.write(force=request.force)
    _format_if_possible(root, list(plan.files))

    _record_feature(root, manifest, feature, plan, untouched_edits)
    console.print(f"{OK} Created feature [bold]{feature.module}[/] ({len(plan.files)} files)")
    console.print(f"  route: /api/v1/{feature.url_path}   model: {feature.model_class}")
    console.print("\n[bold]Next:[/]")
    models_path = f"src/{manifest.package}/features/{feature.module}/models.py"
    console.print(f"  edit the columns in {models_path}")
    if "migrations" in manifest.stack:
        console.print(f'  uv run alembic revision --autogenerate -m "create {feature.table}"')
        console.print("  uv run alembic upgrade head")
    console.print("  uv run pytest")


def _format_if_possible(root: Path, paths: list[str]) -> None:
    """Formats [paths] with the project's ruff when its environment exists."""
    if not (root / ".venv").exists():
        return
    try:
        run([*RUFF, "format", *paths], cwd=root)
        run([*RUFF, "check", "--fix", "--quiet", *paths], cwd=root)
    except CommandFailedError as error:
        console.print(f"{WARNING} Could not format the new files: {error}")


def _record_feature(
    root: Path,
    manifest: ProjectManifest,
    feature: FeatureName,
    plan: FilePlan,
    untouched_edits: set[str],
) -> None:
    """Adds the feature and the hashes of what was written to `.moarch-py.yaml`."""
    if feature.module not in manifest.features:
        manifest.features.append(feature.module)
    recorded = [path for path in plan.files if path not in plan.edits or path in untouched_edits]
    manifest.record({path: (root / path).read_text(encoding="utf-8") for path in recorded})
    (root / MANIFEST_FILE).write_text(manifest.render(), encoding="utf-8", newline="\n")
