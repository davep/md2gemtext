"""Tests for the md2gemtext CLI."""

##############################################################################
# Python imports.
from io import StringIO
from pathlib import Path

##############################################################################
# Pytest imports.
import pytest

##############################################################################
# Local imports.
from md2gemtext.__main__ import convert


##############################################################################
def test_cli_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test CLI reading from stdin."""
    monkeypatch.setattr(
        "sys.stdin",
        StringIO("# Test Title\n\nParagraph with [Link](https://example.com)"),
    )
    monkeypatch.setattr("sys.argv", ["md2gemtext"])

    convert()

    captured = capsys.readouterr()
    assert "# Test Title" in captured.out
    assert "Paragraph with Link{a}" in captured.out
    assert "=> https://example.com {a} Link" in captured.out


##############################################################################
def test_cli_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test CLI reading from a file."""
    md_file = tmp_path / "test.md"
    md_file.write_text("## File Heading\n\nSome text.", encoding="utf-8")

    monkeypatch.setattr("sys.argv", ["md2gemtext", str(md_file)])

    convert()

    captured = capsys.readouterr()
    assert "## File Heading" in captured.out
    assert "Some text." in captured.out


##############################################################################
def test_cli_strip_inline_markup_flag(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test CLI --strip-inline-markup flag."""
    monkeypatch.setattr("sys.stdin", StringIO("**Bold text** and `code`."))
    monkeypatch.setattr("sys.argv", ["md2gemtext", "--strip-inline-markup"])

    convert()

    captured = capsys.readouterr()
    assert "Bold text and code." in captured.out
    assert "**" not in captured.out


##############################################################################
def test_cli_hide_front_matter_flag(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test CLI --hide-front-matter flag."""
    monkeypatch.setattr(
        "sys.stdin",
        StringIO("---\ntitle: Doc\n---\n# Content"),
    )
    monkeypatch.setattr("sys.argv", ["md2gemtext", "--hide-front-matter"])

    convert()

    captured = capsys.readouterr()
    assert "```frontmatter" not in captured.out
    assert "title: Doc" not in captured.out
    assert "# Content" in captured.out


##############################################################################
def test_cli_no_space_flags(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test CLI --no-space-after-blockquotes and --no-space-after-lists flags."""
    monkeypatch.setattr(
        "sys.stdin",
        StringIO("> Quote\n\n- Item 1\n- Item 2"),
    )
    monkeypatch.setattr(
        "sys.argv",
        ["md2gemtext", "--no-space-after-blockquotes", "--no-space-after-lists"],
    )

    convert()

    captured = capsys.readouterr()
    assert "> Quote\n* Item 1\n* Item 2" in captured.out


##############################################################################
def test_cli_extra_protocol_flag(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test CLI --extra-protocol flag."""
    monkeypatch.setattr(
        "sys.stdin",
        StringIO("Visit spartan://example.org/ now."),
    )
    monkeypatch.setattr(
        "sys.argv",
        ["md2gemtext", "--extra-protocol", "spartan"],
    )

    convert()

    captured = capsys.readouterr()
    assert "Visit spartan://example.org/{a} now." in captured.out
    assert "=> spartan://example.org/ {a} spartan://example.org/" in captured.out


##############################################################################
def test_cli_no_preformat_tables_flag(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test CLI --no-preformat-tables flag."""
    monkeypatch.setattr(
        "sys.stdin",
        StringIO("| A | B |\n| --- | --- |\n| 1 | 2 |"),
    )
    monkeypatch.setattr(
        "sys.argv",
        ["md2gemtext", "--no-preformat-tables"],
    )

    convert()

    captured = capsys.readouterr()
    assert "```table" not in captured.out
    assert "| A   | B   |" in captured.out


##############################################################################
def test_cli_html_handling_flags(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test CLI --html-block-handling and --html-inline-handling flags."""
    html_input = "<div><p>Hello <kbd>World</kbd></p></div>"

    # --html-block-handling preformat
    monkeypatch.setattr("sys.stdin", StringIO(html_input))
    monkeypatch.setattr(
        "sys.argv", ["md2gemtext", "--html-block-handling", "preformat"]
    )
    convert()
    captured = capsys.readouterr()
    assert "```html" in captured.out
    assert "<div>" in captured.out

    # --html-block-handling striptags
    monkeypatch.setattr("sys.stdin", StringIO(html_input))
    monkeypatch.setattr(
        "sys.argv", ["md2gemtext", "--html-block-handling", "striptags"]
    )
    convert()
    captured = capsys.readouterr()
    assert "<" not in captured.out
    assert "Hello World" in captured.out

    # --html-inline-handling keep
    inline_input = "Press <kbd>Ctrl</kbd> to exit."
    monkeypatch.setattr("sys.stdin", StringIO(inline_input))
    monkeypatch.setattr("sys.argv", ["md2gemtext", "--html-inline-handling", "keep"])
    convert()
    captured = capsys.readouterr()
    assert "<kbd>Ctrl</kbd>" in captured.out


### test_cli.py ends here
