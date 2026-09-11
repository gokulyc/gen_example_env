from pathlib import Path

from typer.testing import CliRunner

from gen_example_env import __version__
from gen_example_env.cli import app

runner = CliRunner()

ENV = "DB_HOST=localhost\n# secret\nAPI_KEY=\"abc123\" # inline\nexport DEBUG=true\n"
PLACEHOLDER_OUT = "DB_HOST=<DB_HOST>\n# secret\nAPI_KEY=<API_KEY>  # inline\nexport DEBUG=<DEBUG>\n"
BLANK_OUT = "DB_HOST=\n# secret\nAPI_KEY=  # inline\nexport DEBUG=\n"
KEEP_SAFE_OUT = "DB_HOST=localhost\n# secret\nAPI_KEY=  # inline\nexport DEBUG=true\n"


def write_env(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(ENV)
    return env


def test_writes_default_output_next_to_input(tmp_path: Path):
    env = write_env(tmp_path)
    result = runner.invoke(app, [str(env)])
    assert result.exit_code == 0, result.output
    out = tmp_path / ".env.example"
    assert out.read_text() == PLACEHOLDER_OUT
    assert "3 variables" in result.output
    assert "mode=placeholder" in result.output


def test_stdout_does_not_write_file(tmp_path: Path):
    env = write_env(tmp_path)
    result = runner.invoke(app, [str(env), "--stdout"])
    assert result.exit_code == 0
    assert result.output == PLACEHOLDER_OUT
    assert not (tmp_path / ".env.example").exists()


def test_refuses_to_overwrite_without_force(tmp_path: Path):
    env = write_env(tmp_path)
    out = tmp_path / ".env.example"
    out.write_text("KEEP=me\n")
    result = runner.invoke(app, [str(env)])
    assert result.exit_code == 1
    assert "already exists" in result.output
    assert out.read_text() == "KEEP=me\n"


def test_force_overwrites_and_custom_output_and_mode(tmp_path: Path):
    env = write_env(tmp_path)
    out = tmp_path / "custom.example"
    out.write_text("old\n")
    result = runner.invoke(app, [str(env), "-o", str(out), "--force", "--mode", "blank"])
    assert result.exit_code == 0, result.output
    assert out.read_text() == BLANK_OUT


def test_keep_safe_mode_via_short_flag(tmp_path: Path):
    env = write_env(tmp_path)
    result = runner.invoke(app, [str(env), "--stdout", "-m", "keep-safe"])
    assert result.exit_code == 0, result.output
    assert result.output == KEEP_SAFE_OUT


def test_placeholder_mode_explicit(tmp_path: Path):
    env = write_env(tmp_path)
    result = runner.invoke(app, [str(env), "--stdout", "--mode", "placeholder"])
    assert result.exit_code == 0, result.output
    assert result.output == PLACEHOLDER_OUT


def test_mode_is_case_insensitive(tmp_path: Path):
    env = write_env(tmp_path)
    result = runner.invoke(app, [str(env), "--stdout", "--mode", "BLANK"])
    assert result.exit_code == 0, result.output
    assert result.output == BLANK_OUT


def test_invalid_mode_is_rejected(tmp_path: Path):
    env = write_env(tmp_path)
    result = runner.invoke(app, [str(env), "--stdout", "--mode", "nope"])
    assert result.exit_code == 2
    assert not (tmp_path / ".env.example").exists()


def test_missing_input_exits_1(tmp_path: Path):
    result = runner.invoke(app, [str(tmp_path / "nope.env")])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.strip() == f"gen_example_env {__version__}"
