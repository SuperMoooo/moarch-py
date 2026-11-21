"""The business modules of this modular monolith: one package per business area.

    modules/recipes/
        public.py        what other modules may import; nothing else in here is theirs
        models.py        SQLAlchemy tables
        schemas.py       Pydantic request and response bodies
        repository.py    database calls, nothing else
        service.py       business rules and transactions
        router.py        HTTP: parse the request, call the service, return a schema
        dependencies.py  wires session → repository → service for the router

A module is a business area (recipes, billing, users), not a single table: it
can hold several models that always change together. Modules talk to each
other only through `public.py`; `uv run lint-imports` (import-linter, set up in
pyproject.toml) fails the build when one reaches into another's internals.

Create one with `moarch-py create module <name>`.
"""
