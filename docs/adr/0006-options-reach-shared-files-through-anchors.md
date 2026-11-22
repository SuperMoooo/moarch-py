# Options reach shared files only through anchor snippets

An option can be ticked at `init` or added a year later with `create`, by
which time `main.py`, `config.py` and `docker-compose.yml` are the project
owner's, edited and never to be re-rendered. So no shared template branches
on an option that can be added later (`{% if options.auth %}`); each option
owns its own files and adds lines to shared files above `# moarch:` anchors,
and one planner (`scaffold.plan_options`) applies the same snippets at `init`
and at `create`. What depends on two options (auth with email, auth with the
audit log) is a snippet whose condition needs both, applied by whichever
`create` makes it true.

The cost is more anchors in generated files, and optional sign-in parts
written as protocols set in `build_auth_parts` rather than inline `if`s. The
gain is that `tests/test_options.py` can prove, for every option, that adding
it later leaves the same project as ticking it at `init`, and that an edited
shared file is only ever appended to, never overwritten.
