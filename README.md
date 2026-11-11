# gen_example_env

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.txt)
![AI-assisted, human-reviewed](https://img.shields.io/badge/AI--assisted-human--reviewed-2ea44f)

> Built with the help of AI coding assistants; all code is human-reviewed and tested.

Generate a `.env.example` file from an existing `.env` file. Keys, comments, blank lines and
`export` prefixes are preserved; values are replaced with `<KEY>` placeholders (or blanked) so the
result is safe to commit.

## Install

Requires Python 3.12 or newer.

```bash
# a specific release
uv tool install git+https://github.com/gokulyc/gen_example_env@v0.1.0

# the latest release (newest v* tag)
repo=https://github.com/gokulyc/gen_example_env
tag=$(git ls-remote --tags --refs --sort=-v:refname "$repo" 'v*' | head -n1 | cut -d/ -f3)
uv tool install --force "git+$repo@$tag"

# unreleased code from main
uv tool install git+https://github.com/gokulyc/gen_example_env@main

# or, inside the repo:
uv tool install .          # installs the `gen_example_env` command globally
# or
uv sync && uv run gen_example_env --help
```

## Usage

```
gen_example_env [INPUT_FILE] [-o OUTPUT] [-m MODE] [-f] [--stdout]
```

| Option | Description |
| --- | --- |
| `INPUT_FILE` | The `.env` file to read. Defaults to `.env` in the current directory. |
| `-o, --output PATH` | Where to write the example. Defaults to `.env.example` next to the input. |
| `-m, --mode MODE` | `placeholder` (default), `blank`, or `keep-safe`. See below. |
| `-f, --force` | Overwrite the output file if it already exists. |
| `--stdout` | Print the result instead of writing a file. |
| `-V, --version` | Show the version and exit. |

### Modes

Given this `.env`:

```dotenv
# Database
DB_HOST=localhost
export DEBUG=true
API_KEY="abc123" # from the dashboard
```

| Mode | Output |
| --- | --- |
| `placeholder` (default) | `DB_HOST=<DB_HOST>` / `export DEBUG=<DEBUG>` / `API_KEY=<API_KEY>  # from the dashboard` |
| `blank` | `DB_HOST=` / `export DEBUG=` / `API_KEY=  # from the dashboard` |
| `keep-safe` | `DB_HOST=localhost` / `export DEBUG=true` / `API_KEY=  # from the dashboard` |

`keep-safe` blanks a value when the key name contains `SECRET`, `TOKEN`, `PASSWORD`, `PASSWD`,
`PRIVATE`, `CREDENTIAL`, `AUTH`, `API` or `KEY`, or when the value was quoted. Everything else is kept.

## Development

```bash
uv sync            # install runtime + dev dependencies
uv run pytest -q   # run the test suite
just               # list shortcuts (test, run, build, bump, ...)
```

## Releasing

The version lives only in `pyproject.toml`. Pushing a version change to `main` makes GitHub Actions
create tag `v<version>` (existing tags are never touched).

```bash
just bump minor    # or patch / major (uv version --bump ...)
git commit -am "Release $(just version)" && git push
```

To back out a bad version (e.g. 0.2.0): `just set-version 0.1.1`, commit and push, then `just untag 0.2.0`
to delete the tag locally and on GitHub. Prefer moving forward over reusing a number; PyPI never accepts
a version twice.

## License

MIT. See [LICENSE.txt](LICENSE.txt).
