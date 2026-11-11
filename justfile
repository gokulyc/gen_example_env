default:
    @just --list

sync:
    uv sync

test:
    uv run pytest -q

run *args:
    uv run gen_example_env {{args}}

build:
    uv build

version:
    @uv version --short

# just bump patch|minor|major
bump part="patch":
    uv version --bump {{part}}

# just set-version 0.1.0
set-version v:
    uv version {{v}}

# delete a tag locally and on GitHub, e.g. just untag 0.2.0
untag v:
    git tag -d v{{v}}
    git push origin :refs/tags/v{{v}}
