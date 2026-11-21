"""Turns options into the files of a project or a feature. No disk writes, no subprocesses.

Keeping generation pure is what lets `--dry-run` show exactly what a real run
writes, and lets the tests check every option combination in milliseconds.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from moarch_py import __version__
from moarch_py.catalog import PROJECT_SKILLS, ScaffoldSpec, specs_for
from moarch_py.file_plan import FilePlan, insert_at_anchor
from moarch_py.manifest import MANIFEST_FILE, ProjectManifest
from moarch_py.naming import FeatureName, ProjectName
from moarch_py.options import Database, ProjectOptions
from moarch_py.render import render

# The version generated projects target. 3.12 is the most widely used Python
# in production (JetBrains/PSF Python Developers Survey 2025); a newer
# interpreter still runs these projects, since requires-python is a floor.
PYTHON_VERSION = "3.12"

# Used in the Dockerfile when uv's version cannot be detected.
FALLBACK_UV_IMAGE_TAG = "latest"


def project_context(options: ProjectOptions, *, uv_version: str | None) -> dict[str, Any]:
    """The variables every project template can read."""
    return {
        "name": options.name,
        "options": options,
        "database": options.database,
        "python_version": PYTHON_VERSION,
        "uv_version": uv_version or FALLBACK_UV_IMAGE_TAG,
        "moarch_version": __version__,
        "skills": PROJECT_SKILLS,
    }


def render_spec(spec: ScaffoldSpec, context: dict[str, Any]) -> str:
    """One catalog entry's file content."""
    return render(spec.template, {**context, **spec.extra})


def plan_project(
    root: Path, options: ProjectOptions, *, uv_version: str | None
) -> tuple[FilePlan, ProjectManifest]:
    """Every file `init` writes for [options] (pyproject.toml excepted), and its manifest."""
    context = project_context(options, uv_version=uv_version)
    plan = FilePlan(root)
    for spec in specs_for(options):
        plan.add(spec.path_for(options.name.package), render_spec(spec, context))
    manifest = ProjectManifest.new(
        package=options.name.package,
        database=options.database.value,
        stack=options.enabled,
    )
    manifest.record(plan.files)
    return plan, manifest


# The files `moarch-py create feature` writes, relative to the feature folder,
# with the template that renders each.
_FEATURE_FILES: tuple[tuple[str, str], ...] = (
    ("__init__.py", "feature/package_init.py.j2"),
    ("models.py", "feature/models.py.j2"),
    ("schemas.py", "feature/schemas.py.j2"),
    ("repository.py", "feature/repository.py.j2"),
    ("service.py", "feature/service.py.j2"),
    ("dependencies.py", "feature/dependencies.py.j2"),
    ("router.py", "feature/router.py.j2"),
)


class NotAMoarchProjectError(Exception):
    """Raised when a command that needs `.moarch-py.yaml` runs outside a moarch-py project."""


def load_manifest(root: Path) -> ProjectManifest:
    """The project's manifest, or NotAMoarchProjectError with what to do instead."""
    manifest = ProjectManifest.load(root)
    if manifest is None:
        raise NotAMoarchProjectError(
            f"No {MANIFEST_FILE} in {root}. Run this inside a project made by "
            "`moarch-py init`, or run `moarch-py init` here first."
        )
    return manifest


def plan_feature(root: Path, manifest: ProjectManifest, feature: FeatureName) -> FilePlan:
    """The feature's six files and test, plus its registration at the two anchors."""
    project = ProjectName.parse(manifest.package)
    context = {
        "name": project,
        "feature": feature,
        "database": Database(manifest.database),
    }
    package_dir = f"src/{project.package}"
    feature_dir = f"{package_dir}/features/{feature.module}"

    plan = FilePlan(root)
    for file_name, template in _FEATURE_FILES:
        plan.add(f"{feature_dir}/{file_name}", render(template, context))
    plan.add(
        f"tests/features/{feature.module}/test_{feature.module}_api.py",
        render("feature/test_api.py.j2", context),
    )

    router_path = f"{package_dir}/api/v1/router.py"
    router_source = (root / router_path).read_text(encoding="utf-8")
    feature_module = f"{project.package}.features.{feature.module}"
    router_alias = f"{feature.module}_router"
    router_source = insert_at_anchor(
        router_source,
        "router-imports",
        f"from {feature_module}.router import router as {router_alias}",
        relative_path=router_path,
    )
    router_source = insert_at_anchor(
        router_source,
        "routers",
        f"api_router.include_router({router_alias})",
        relative_path=router_path,
    )
    plan.edit(router_path, router_source)

    models_path = f"{package_dir}/db/models.py"
    models_source = (root / models_path).read_text(encoding="utf-8")
    models_source = insert_at_anchor(
        models_source,
        "models",
        # Imported only so Base.metadata registers the table, hence the noqa.
        f"from {feature_module}.models import {feature.model_class}  # noqa: F401",
        relative_path=models_path,
    )
    plan.edit(models_path, models_source)
    return plan
