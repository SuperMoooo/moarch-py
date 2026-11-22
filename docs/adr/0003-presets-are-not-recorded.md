# Presets only pre-tick options and are never recorded

As in the Flutter moarch, a preset (`--preset fintech`) only pre-ticks and locks
checklist options; `.moarch-py.yaml` stores the options, not the preset, and no
preset brings code of its own. A project is never "a fintech project" afterwards,
so later commands reason about options alone and a preset can change between
versions without breaking existing projects.
