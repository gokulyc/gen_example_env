from gen_example_env.core import Mode, generate_example, parse_env_lines, render_example

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


def test_render_blank_mode():
    assert generate_example(SAMPLE) == """\
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


def test_render_placeholder_mode():
    out = generate_example(SAMPLE, mode=Mode.PLACEHOLDER)
    assert "DB_HOST=<DB_HOST>" in out
    assert "export DEBUG=<DEBUG>" in out
    assert "API_KEY=<API_KEY>  # inline comment" in out


def test_render_keep_safe_mode():
    out = generate_example(SAMPLE, mode=Mode.KEEP_SAFE)
    assert "DB_HOST=localhost" in out
    assert "DB_PORT=5432" in out
    assert "export DEBUG=true" in out
    assert "URL=https://example.com/path#anchor" in out
    # secret-looking key and quoted value are both blanked
    assert "API_KEY=  # inline comment" in out
    assert "PASSWORD=\n" in out


def test_render_empty_input():
    assert render_example([]) == ""
    assert generate_example("") == ""
