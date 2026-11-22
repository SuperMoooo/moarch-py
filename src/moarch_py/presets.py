"""Kinds of app `moarch-py init` can start from, as in the Flutter moarch.

A preset only fills in the checklists: which options are ticked when they
open, and which of those cannot be unticked. Nothing records the preset, so a
project is never "a fintech project" afterwards; every later command reads
the options alone (docs/adr/0003).
"""

from __future__ import annotations

from dataclasses import dataclass

from moarch_py.options import Broker

# The five "What to generate" options every preset keeps on.
_PROJECT_BASICS = frozenset({"migrations", "docker", "ci", "pre_commit", "ai"})
_OBSERVABILITY = frozenset({"tracing", "sentry", "metrics"})


@dataclass(frozen=True)
class InitPreset:
    """One kind of app: what it pre-ticks, what it locks on, and its broker."""

    slug: str
    """What `--preset` takes."""

    name: str
    """What the "What are you building?" question shows."""

    description: str
    """One line under [name], saying what the preset is for."""

    required: frozenset[str]
    """Options this kind of app cannot do without; ticked and locked."""

    selected: frozenset[str]
    """Further options ticked to begin with, still free to untick."""

    broker: Broker = Broker.NONE
    """The broker chosen to begin with; Broker.NONE means no worker."""

    @property
    def ticked(self) -> set[str]:
        """Every option ticked when the checklists open."""
        return set(_PROJECT_BASICS | self.required | self.selected)


PRESETS: tuple[InitPreset, ...] = (
    InitPreset(
        "fintech",
        "FinTech / banking",
        "Money moves: locked-down auth, audit trail, idempotent writes, full observability.",
        required=frozenset(
            {
                "auth",
                "auth_refresh",
                "lockout",
                "rate_limit",
                "audit_log",
                "idempotency",
                "security_headers",
            }
        ),
        selected=frozenset({"auth_google", "auth_apple", "email", "scheduler"} | _OBSERVABILITY),
        broker=Broker.RABBITMQ,
    ),
    InitPreset(
        "ecommerce",
        "E-commerce / marketplace",
        "Orders and payments that must not double, with a cache and files for products.",
        required=frozenset({"auth", "idempotency", "email"}),
        selected=frozenset(
            {
                "auth_refresh",
                "auth_google",
                "auth_apple",
                "rate_limit",
                "security_headers",
                "cache",
                "storage",
                "push",
            }
            | _OBSERVABILITY
        ),
        broker=Broker.REDIS,
    ),
    InitPreset(
        "social",
        "Social / community",
        "People, media and live updates.",
        required=frozenset({"auth", "storage", "websockets"}),
        selected=frozenset(
            {"auth_refresh", "auth_google", "auth_apple", "email", "push", "cache", "rate_limit"}
        ),
        broker=Broker.REDIS,
    ),
    InitPreset(
        "health",
        "Health / fitness",
        "Sensitive personal data: an audit trail and a locked-down sign-in.",
        required=frozenset({"auth", "auth_refresh", "audit_log", "security_headers", "lockout"}),
        selected=frozenset({"email", "push", "scheduler"} | _OBSERVABILITY),
        broker=Broker.REDIS,
    ),
    InitPreset(
        "field",
        "Field service / delivery",
        "Crews on the move: photos and signatures, jobs pushed and streamed to them.",
        required=frozenset({"auth", "storage"}),
        selected=frozenset({"auth_refresh", "push", "sse"}),
        broker=Broker.REDIS,
    ),
    InitPreset(
        "content",
        "News / media / content",
        "Reading at scale: a cache in front, files for media, live updates.",
        required=frozenset({"auth", "cache"}),
        selected=frozenset(
            {"auth_refresh", "auth_google", "auth_apple", "email", "storage", "push", "sse"}
        ),
    ),
    InitPreset(
        "mvp",
        "MVP",
        "The smallest backend a first app needs: sign-in and email.",
        required=frozenset({"auth"}),
        selected=frozenset({"auth_refresh", "auth_google", "auth_apple", "email"}),
    ),
)

PRESETS_BY_SLUG: dict[str, InitPreset] = {preset.slug: preset for preset in PRESETS}
