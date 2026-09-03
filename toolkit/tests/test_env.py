"""load_dotenv — including the quote-stripping bug this consolidation fixed."""

import pytest

from truehand.core.env import load_dotenv, require_env
from truehand.errors import UserError


def _write(tmp_path, body):
    p = tmp_path / ".env"
    p.write_text(body, encoding="utf-8")
    return p


def test_plain_value(tmp_path, monkeypatch):
    monkeypatch.delenv("T_KEY", raising=False)
    load_dotenv(_write(tmp_path, "T_KEY=abc\n"))
    import os
    assert os.environ["T_KEY"] == "abc"


@pytest.mark.parametrize("quote", ['"', "'"])
def test_surrounding_quotes_are_stripped(tmp_path, monkeypatch, quote):
    """generate-character-references.py's copy did NOT do this, so a quoted
    key yielded a value with literal quote marks."""
    monkeypatch.delenv("T_KEY", raising=False)
    load_dotenv(_write(tmp_path, f"T_KEY={quote}abc{quote}\n"))
    import os
    assert os.environ["T_KEY"] == "abc"


def test_comments_and_blank_lines_are_skipped(tmp_path, monkeypatch):
    monkeypatch.delenv("T_KEY", raising=False)
    load_dotenv(_write(tmp_path, "# a comment\n\nT_KEY=abc\n"))
    import os
    assert os.environ["T_KEY"] == "abc"


def test_a_value_containing_equals_is_preserved(tmp_path, monkeypatch):
    monkeypatch.delenv("T_KEY", raising=False)
    load_dotenv(_write(tmp_path, "T_KEY=a=b=c\n"))
    import os
    assert os.environ["T_KEY"] == "a=b=c"


def test_the_real_environment_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("T_KEY", "from-env")
    load_dotenv(_write(tmp_path, "T_KEY=from-file\n"))
    import os
    assert os.environ["T_KEY"] == "from-env"


def test_a_missing_file_is_not_an_error(tmp_path):
    load_dotenv(tmp_path / "nope.env")


def test_require_env_raises_with_a_usable_message(monkeypatch):
    monkeypatch.delenv("T_MISSING", raising=False)
    with pytest.raises(UserError, match="T_MISSING"):
        require_env("T_MISSING", why="Testing")
