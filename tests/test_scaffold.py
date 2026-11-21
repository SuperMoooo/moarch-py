"""What `init` and `create feature` generate, for each option, without touching uv."""

import ast
import itertools
import json
from pathlib import Path

import pytest
import yaml

from moarch_py.catalog import CATALOG, PROJECT_SKILLS
from moarch_py.naming import FeatureName, ProjectName
from moarch_py.options import CHECKLIST, Database, ProjectOptions
from moarch_py.scaffold import plan_feature, plan_project

NAME = ProjectName.parse("shop-api")


def _plan(tmp_path: Path, **overrides: object) -> dict[str, str]:
    options = ProjectOptions.with_defaults(NAME, Database.POSTGRES)
    options = ProjectOptions(**{**options.__dict__, **overrides})  # type: ignore[arg-type]
    plan, _ = plan_project(tmp_path, options, uv_version="0.12.11")
    return plan.files


def test_catalog_slugs_are_unique() -> None:
    slugs = [spec.slug for spec in CATALOG]
    assert len(slugs) == len(set(slugs))


# Every combination of database and checklist: 3 x 2^5 = 96 projects.
_COMBINATIONS = [
    (database, ticked)
    for database in Database
    for count in range(len(CHECKLIST) + 1)
    for ticked in itertools.combinations([o.key for o in CHECKLIST], count)
]


@pytest.mark.parametrize(("database", "ticked"), _COMBINATIONS)
def test_every_combination_renders_valid_python_yaml_and_json(
    tmp_path: Path, database: Database, ticked: tuple[str, ...]
) -> None:
    options = ProjectOptions.from_checklist(NAME, database, set(ticked))
    plan, _ = plan_project(tmp_path, options, uv_version=None)

    for path, content in plan.files.items():
        if path.endswith(".py"):
            ast.parse(content, filename=path)
        elif path.endswith((".yml", ".yaml")):
            yaml.safe_load(content)
        elif path.endswith(".json"):
            # VS Code's files are JSONC: drop the `//` comment lines first.
            lines = [line for line in content.splitlines() if not line.strip().startswith("//")]
            json.loads("\n".join(lines))
        if path.endswith("SKILL.md"):
            frontmatter = content.split("---")[1]
            assert yaml.safe_load(frontmatter)["name"].startswith("moarch-")


def test_switched_off_options_leave_no_files(tmp_path: Path) -> None:
    files = _plan(tmp_path, migrations=False, docker=False, ci=False, pre_commit=False, ai=False)

    unexpected = [
        path
        for path in files
        if path.startswith(("migrations/", ".github/", ".agents/", ".claude/"))
        or path in {"alembic.ini", "Dockerfile", "docker-compose.yml", "AGENTS.md", "CLAUDE.md"}
    ]
    assert unexpected == []


def test_the_ai_guide_ships_every_skill_for_both_agent_folders(tmp_path: Path) -> None:
    files = _plan(tmp_path)

    for slug, _ in PROJECT_SKILLS:
        assert f".agents/skills/moarch-{slug}/SKILL.md" in files
        pointer = files[f".claude/skills/moarch-{slug}/SKILL.md"]
        assert f".agents/skills/moarch-{slug}/SKILL.md" in pointer
    assert "@AGENTS.md" in files["CLAUDE.md"]
    assert "moarch-make-readable" in files["AGENTS.md"]
    assert "moarch-explain" in files["AGENTS.md"]


def test_ruff_is_the_editor_formatter_and_linter(tmp_path: Path) -> None:
    settings = _plan(tmp_path)[".vscode/settings.json"]

    assert '"editor.defaultFormatter": "charliermarsh.ruff"' in settings
    assert '"source.fixAll.ruff"' in settings
    assert "charliermarsh.ruff" in _plan(tmp_path)[".vscode/extensions.json"]


def test_the_dockerfile_targets_the_project_python_and_uv(tmp_path: Path) -> None:
    dockerfile = _plan(tmp_path)["Dockerfile"]

    assert "FROM python:3.12-slim AS builder" in dockerfile
    assert "ghcr.io/astral-sh/uv:0.12.11" in dockerfile
    assert '"shop_api.main:app"' in dockerfile
    assert "USER app" in dockerfile


def test_sqlite_projects_get_no_database_service(tmp_path: Path) -> None:
    compose = yaml.safe_load(_plan(tmp_path, database=Database.SQLITE)["docker-compose.yml"])

    assert set(compose["services"]) == {"api"}


def test_postgres_compose_waits_for_a_healthy_database(tmp_path: Path) -> None:
    compose = yaml.safe_load(_plan(tmp_path)["docker-compose.yml"])

    assert compose["services"]["api"]["depends_on"]["db"]["condition"] == "service_healthy"
    assert "@db:5432/shop_api" in compose["services"]["api"]["environment"]["DATABASE_URL"]


def _write_project(root: Path) -> None:
    from moarch_py.manifest import ProjectManifest

    options = ProjectOptions.with_defaults(NAME, Database.POSTGRES)
    plan, manifest = plan_project(root, options, uv_version=None)
    plan.write()
    (root / ".moarch-py.yaml").write_text(manifest.render(), encoding="utf-8")
    assert ProjectManifest.load(root) is not None


def test_a_feature_writes_every_layer_and_registers_at_both_anchors(tmp_path: Path) -> None:
    from moarch_py.manifest import ProjectManifest

    _write_project(tmp_path)
    manifest = ProjectManifest.load(tmp_path)
    assert manifest is not None

    plan = plan_feature(tmp_path, manifest, FeatureName.parse("order_items"))

    feature_dir = "src/shop_api/features/order_items"
    for layer in ("models", "schemas", "repository", "service", "dependencies", "router"):
        ast.parse(plan.files[f"{feature_dir}/{layer}.py"])
    assert "tests/features/order_items/test_order_items_api.py" in plan.files
    router = plan.files["src/shop_api/api/v1/router.py"]
    assert "api_router.include_router(order_items_router)" in router
    models = plan.files["src/shop_api/db/models.py"]
    assert "from shop_api.features.order_items.models import OrderItem" in models
    assert '@router.get("/{order_item_id}")' in plan.files[f"{feature_dir}/router.py"]
