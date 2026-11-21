"""moarch: scaffold modular-monolith FastAPI projects on uv."""

from importlib.metadata import version

# Read from the installed package, so `version` in pyproject.toml is the only
# place a release bumps.
__version__ = version("moarch-py")
