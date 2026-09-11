# gen_example_env

Generate a `.env.example` file from an existing `.env` file. Keys, comments, blank lines and
`export` prefixes are preserved; values are replaced with `<KEY>` placeholders (or blanked) so the
result is safe to commit.

## Install

```bash
uv tool install .          # installs the `gen_example_env` command globally
# or, inside the repo:
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
```
