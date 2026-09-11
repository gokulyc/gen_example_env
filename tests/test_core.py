import pytest

from gen_example_env.core import (
    Mode,
    generate_example,
    looks_secret,
    parse_env_lines,
    render_example,
)

SAMPLE = """\
# Database
DB_HOST=localhost
DB_PORT=5432

export DEBUG=true
API_KEY="abc123" # inline comment
PASSWORD='p@ss word'
URL=https://example.com/path#anchor
NOT AN ASSIGNMENT
EMPTY=
"""


def test_parse_preserves_order_and_line_types():
    lines = parse_env_lines(SAMPLE)
    assert [line.raw for line in lines] == SAMPLE.splitlines()
    assert [line.key for line in lines] == [
        None, "DB_HOST", "DB_PORT", None, "DEBUG", "API_KEY", "PASSWORD", "URL", None, "EMPTY",
    ]


def test_parse_export_quotes_and_inline_comments():
    by_key = {line.key: line for line in parse_env_lines(SAMPLE) if line.key}
    assert by_key["DEBUG"].export is True
    assert by_key["DEBUG"].value == "true"
    assert by_key["API_KEY"].quoted is True
    assert by_key["API_KEY"].value == "abc123"
    assert by_key["API_KEY"].comment == "# inline comment"
    assert by_key["PASSWORD"].value == "p@ss word"
    # A '#' with no leading whitespace is part of the value, not a comment.
    assert by_key["URL"].value == "https://example.com/path#anchor"
    assert by_key["URL"].comment == ""
    assert by_key["EMPTY"].value == ""


def test_render_placeholder_mode_is_default():
    expected = """\
# Database
DB_HOST=<DB_HOST>
DB_PORT=<DB_PORT>

export DEBUG=<DEBUG>
API_KEY=<API_KEY>  # inline comment
PASSWORD=<PASSWORD>
URL=<URL>
NOT AN ASSIGNMENT
EMPTY=<EMPTY>
"""
    assert generate_example(SAMPLE) == expected
    assert generate_example(SAMPLE, mode=Mode.PLACEHOLDER) == expected


def test_render_blank_mode():
    assert generate_example(SAMPLE, mode=Mode.BLANK) == """\
# Database
DB_HOST=
DB_PORT=

export DEBUG=
API_KEY=  # inline comment
PASSWORD=
URL=
NOT AN ASSIGNMENT
EMPTY=
"""


def test_render_keep_safe_mode():
    # Secret-looking keys (API_KEY, PASSWORD) and quoted values are blanked; the rest is kept.
    assert generate_example(SAMPLE, mode=Mode.KEEP_SAFE) == """\
# Database
DB_HOST=localhost
DB_PORT=5432

export DEBUG=true
API_KEY=  # inline comment
PASSWORD=
URL=https://example.com/path#anchor
NOT AN ASSIGNMENT
EMPTY=
"""


@pytest.mark.parametrize(
    "key",
    ["SECRET", "MY_SECRET", "TOKEN", "ACCESS_TOKEN", "PASSWORD", "DB_PASSWD", "PRIVATE_PEM",
     "AWS_CREDENTIALS", "AUTH_URL", "API_BASE", "KEY_ID", "stripe_api_key"],
)
def test_looks_secret_matches_secret_like_keys(key):
    (line,) = parse_env_lines(f"{key}=value")
    assert looks_secret(line) is True


@pytest.mark.parametrize("key", ["DB_HOST", "PORT", "DEBUG", "LOG_LEVEL", "REGION"])
def test_looks_secret_ignores_plain_keys(key):
    (line,) = parse_env_lines(f"{key}=value")
    assert looks_secret(line) is False


def test_looks_secret_treats_quoted_values_as_secret():
    (line,) = parse_env_lines('DB_HOST="localhost"')
    assert looks_secret(line) is True
    assert generate_example('DB_HOST="localhost"', mode=Mode.KEEP_SAFE) == "DB_HOST=\n"


def test_mode_values_match_cli_strings():
    assert {m.value for m in Mode} == {"blank", "placeholder", "keep-safe"}


def test_render_empty_input():
    assert render_example([]) == ""
    assert generate_example("") == ""
