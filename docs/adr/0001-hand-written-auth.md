# Generated auth is hand-written on PyJWT and pwdlib

Generated projects get their own auth code (users module, argon2 hashing via
pwdlib, JWTs via PyJWT, refresh-token rotation) instead of depending on
fastapi-users or Authlib. fastapi-users is in maintenance mode and does not type
cleanly under `mypy --strict`; Authlib targets OAuth servers. Owning ~300
readable lines fits the generated project's own rules and lets people change it.
