"""The options beyond "What to generate": each renders, combines, and adds later the same."""

import ast
import json
from pathlib import Path

import pytest
import yaml

from moarch_py.catalog import INSERTS
from moarch_py.commands import CREATE_TARGETS, keys_for
from moarch_py.manifest import ProjectManifest
from moarch_py.naming import ProjectName
from moarch_py.options import (
    CHECKLIST,
    CHECKLISTS,
    Broker,
    Database,
    OptionsError,
    ProjectOptions,
    default_keys,
    option_field_names,
    resolve_needs,
)
from moarch_py.presets import PRESETS, InitPreset
from moarch_py.scaffold import options_from_manifest, plan_options, plan_project

NAME = ProjectName.parse("shop-api")
_CORE_KEYS = {option.key for option in CHECKLISTS[0].options}
_EXTRA_KEYS = sorted(option.key for option in CHECKLIST if option.key not in _CORE_KEYS)


def _options(
    keys: set[str], *, database: Database = Database.POSTGRES, broker: Broker = Broker.NONE
) -> ProjectOptions:
    return ProjectOptions.from_checklist(NAME, database, _CORE_KEYS | keys, broker=broker)


def _assert_files_parse(files: dict[str, str]) -> None:
    for path, content in files.items():
        if path.endswith(".py"):
            ast.parse(content, filename=path)
        elif path.endswith((".yml", ".yaml")):
            yaml.safe_load(content)
        elif path.endswith(".json"):
            lines = [line for line in content.splitlines() if not line.strip().startswith("//")]
            json.loads("\n".join(lines))


def test_every_checklist_option_is_a_field_and_back() -> None:
    assert {option.key for option in CHECKLIST} == option_field_names()


def test_insert_slugs_are_unique() -> None:
    slugs = [insert.slug for insert in INSERTS]
    assert len(slugs) == len(set(slugs))


def test_all_takes_no_extra_option_and_no_broker() -> None:
    options = ProjectOptions.with_defaults(NAME, Database.POSTGRES)

    assert set(options.enabled) == _CORE_KEYS
    assert default_keys() == _CORE_KEYS
    assert options.broker is Broker.NONE


def test_an_option_ticks_what_it_needs_and_says_why() -> None:
    ticked, needed_by = resolve_needs({"lockout", "push"})

    assert "auth" in ticked
    assert sorted(needed_by["auth"]) == ["lockout", "push"]


def test_a_scheduler_without_a_broker_is_refused() -> None:
    with pytest.raises(OptionsError, match="broker"):
        _options({"scheduler"})


@pytest.mark.parametrize("key", _EXTRA_KEYS)
def test_each_option_alone_renders_valid_files(tmp_path: Path, key: str) -> None:
    broker = Broker.REDIS if key == "scheduler" else Broker.NONE
    plan, _ = plan_project(tmp_path, _options({key}, broker=broker), uv_version=None)

    _assert_files_parse(plan.files)


@pytest.mark.parametrize("database", list(Database))
@pytest.mark.parametrize("broker", [Broker.RABBITMQ, Broker.REDIS])
def test_everything_on_renders_valid_files(
    tmp_path: Path, database: Database, broker: Broker
) -> None:
    options = _options(set(_EXTRA_KEYS), database=database, broker=broker)
    plan, _ = plan_project(tmp_path, options, uv_version=None)

    _assert_files_parse(plan.files)
    compose = yaml.safe_load(plan.files["docker-compose.yml"])
    assert {"redis", "worker", "scheduler", "mailpit", "minio"} <= set(compose["services"])
    assert compose["services"]["worker"]["environment"]["BROKER_URL"] == broker.compose_url


@pytest.mark.parametrize("preset", PRESETS, ids=lambda preset: preset.slug)
def test_each_preset_renders_valid_files(tmp_path: Path, preset: InitPreset) -> None:
    options = ProjectOptions.from_checklist(
        NAME, Database.POSTGRES, preset.ticked, broker=preset.broker
    )
    plan, _ = plan_project(tmp_path, options, uv_version=None)

    _assert_files_parse(plan.files)
    assert preset.required <= set(options.enabled)


def test_a_preset_requires_only_options_that_exist() -> None:
    keys = {option.key for option in CHECKLIST}
    for preset in PRESETS:
        assert preset.required | preset.selected <= keys, preset.slug


def _lines_by_file(files: dict[str, str]) -> dict[str, list[str]]:
    # Order between snippets at one anchor follows the order options were
    # added in; ruff sorts imports anyway. What must match is every line.
    return {path: sorted(content.splitlines()) for path, content in files.items()}


def _added_later(root: Path, keys: set[str], broker: Broker) -> dict[str, str]:
    """A base project written to disk, then [keys] added the way `create` adds them."""
    base = _options(set())
    plan, _ = plan_project(root, base, uv_version=None)
    plan.write()
    later = base.with_added(keys, broker=broker)
    plan_options(root, later, previous=base, uv_version=None).write()
    return {
        path: (root / path).read_text(encoding="utf-8")
        for path in plan_project(root, later, uv_version=None)[0].files
    }


_LATER_CASES = [
    *[({key}, Broker.REDIS if key == "scheduler" else Broker.NONE) for key in _EXTRA_KEYS],
    ({"auth", "email", "audit_log", "lockout", "auth_refresh"}, Broker.NONE),
    (set(_EXTRA_KEYS), Broker.RABBITMQ),
]


@pytest.mark.parametrize(("keys", "broker"), _LATER_CASES, ids=lambda case: str(case))
def test_adding_options_later_ends_like_ticking_them_at_init(
    tmp_path: Path, keys: set[str], broker: Broker
) -> None:
    at_init, _ = plan_project(tmp_path / "init", _options(keys, broker=broker), uv_version=None)

    later = _added_later(tmp_path / "later", keys, broker)

    assert _lines_by_file(later) == _lines_by_file(at_init.files)


def test_options_added_one_by_one_end_like_all_at_once(tmp_path: Path) -> None:
    # Auth after email and the audit log: its combination snippets
    # (verification emails, auth events in the audit log) must still appear.
    root = tmp_path / "steps"
    base = _options(set())
    plan_project(root, base, uv_version=None)[0].write()
    current = base
    for step in ({"email"}, {"audit_log"}, {"auth"}, {"lockout"}):
        updated = current.with_added(step)
        plan_options(root, updated, previous=current, uv_version=None).write()
        current = updated
    at_once, _ = plan_project(tmp_path / "once", current, uv_version=None)

    on_disk = {path: (root / path).read_text(encoding="utf-8") for path in at_once.files}
    assert _lines_by_file(on_disk) == _lines_by_file(at_once.files)
    dependencies = on_disk["src/shop_api/modules/users/dependencies.py"]
    assert "parts.events.append(AuditLogRecorder(session))" in dependencies
    assert "parts.verification = EmailVerification(" in dependencies


def test_without_docker_the_compose_snippets_are_skipped(tmp_path: Path) -> None:
    options = ProjectOptions.from_checklist(NAME, Database.POSTGRES, {"cache", "email"})

    plan, _ = plan_project(tmp_path, options, uv_version=None)

    assert "docker-compose.yml" not in plan.files
    assert "REDIS_URL=" in plan.files[".env.example"]


def test_the_manifest_records_the_options_and_the_broker(tmp_path: Path) -> None:
    options = _options({"auth", "scheduler"}, broker=Broker.RABBITMQ)
    _, manifest = plan_project(tmp_path, options, uv_version=None)
    (tmp_path / ".moarch-py.yaml").write_text(manifest.render(), encoding="utf-8")

    loaded = ProjectManifest.load(tmp_path)

    assert loaded is not None
    assert options_from_manifest(loaded) == options


def test_create_names_map_to_options() -> None:
    assert keys_for("service", ["observability"]) == {"tracing", "sentry", "metrics"}
    assert keys_for("security", ["headers", "lockout"]) == {"security_headers", "lockout"}
    for targets in CREATE_TARGETS.values():
        for keys in targets.values():
            assert set(keys) <= option_field_names()


def test_auth_matches_the_flutter_client_paths(tmp_path: Path) -> None:
    files = plan_project(
        tmp_path, _options({"auth", "auth_refresh", "auth_apple", "email"}), uv_version=None
    )[0].files
    users = "src/shop_api/modules/users"
    routes = "".join(
        files[f"{users}/{name}"]
        for name in ("router.py", "refresh_router.py", "apple_sign_in.py", "email_router.py")
    )

    for path in (
        "/register",
        "/login",
        "/logout",
        "/me",
        "/device-token",
        "/refresh",
        "/apple",
        "/password/forgot",
        "/password/reset",
        "/email/resend",
    ):
        assert f'"{path}"' in routes, path
    assert 'prefix="/auth"' in files[f"{users}/router.py"]
