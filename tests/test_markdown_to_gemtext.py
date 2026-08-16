"""Tests for the Markdown to Gemtext converter."""

##############################################################################
# Pytest imports.
from pytest import mark

##############################################################################
# Local imports.
from md2gemtext import Options, markdown_to_gemtext
from md2gemtext._converter import get_marker, to_superscript_number


##############################################################################
def test_marker_generation() -> None:
    """Test the base-26 marker generation logic."""
    assert get_marker(0) == "{a}"
    assert get_marker(25) == "{z}"
    assert get_marker(26) == "{aa}"
    assert get_marker(27) == "{ab}"
    assert get_marker(51) == "{az}"
    assert get_marker(52) == "{ba}"
    assert get_marker(701) == "{zz}"
    assert get_marker(702) == "{aaa}"


##############################################################################
def test_to_superscript_number() -> None:
    """Test number to UTF-8 superscript conversion."""
    assert to_superscript_number(1) == "¹"
    assert to_superscript_number(2) == "²"
    assert to_superscript_number(10) == "¹⁰"
    assert to_superscript_number(25) == "²⁵"
    assert to_superscript_number(100) == "¹⁰⁰"


##############################################################################
@mark.parametrize(
    "markdown, gemtext",
    [
        ("", ""),
        ("         ", ""),
        ("Hello, world!", "Hello, world!\n"),
        ("Hello, world!\n\nAgain!", "Hello, world!\n\nAgain!\n"),
        ("Paragraph line 1\nand line 2.", "Paragraph line 1 and line 2.\n"),
        ("# Heading 1", "# Heading 1"),
        ("## Heading 2", "## Heading 2"),
        ("### Heading 3", "### Heading 3"),
        ("#### Heading 4", "### Heading 4"),
        ("##### Heading 5", "### Heading 5"),
        ("###### Heading 6", "### Heading 6"),
        ("- Item 1\n- Item 2", "* Item 1\n* Item 2\n"),
        ("* Item 1\n* Item 2", "* Item 1\n* Item 2\n"),
        ("+ Item 1\n+ Item 2", "* Item 1\n* Item 2\n"),
        ("1. First item\n2. Second item", "1. First item\n\n2. Second item\n"),
        ("```\nPreformatted\n```", "```\nPreformatted\n```\n"),
        ("```python\nprint('hello')\n```", "```python\nprint('hello')\n```\n"),
        ("    indented code block", "```\nindented code block\n```\n"),
        ("> Quote", "> Quote\n"),
        ("> Line 1\n> Line 2", "> Line 1 Line 2\n"),
        ("> Quote 1\n\n> Quote 2", "> Quote 1\n>\n> Quote 2\n"),
        ("---", "---"),
        ("***", "---"),
        (
            "| A | B |\n| --- | --- |\n| 1 | 2 |",
            "```table\n| A   | B   |\n| :-- | :-- |\n| 1   | 2   |\n```\n",
        ),
        (
            "Here is a note[^1].\n\n[^1]: The footnote text.",
            "Here is a note¹.\n\n¹ The footnote text.\n",
        ),
    ],
)
def test_basic_conversion(markdown: str, gemtext: str) -> None:
    """Test basic Markdown to Gemtext conversion.

    Args:
        markdown: The Markdown to convert.
        gemtext: The expected Gemtext output.
    """
    assert markdown_to_gemtext(markdown) == gemtext


##############################################################################
def test_paragraph_inline_links() -> None:
    """Test paragraph inline links extraction and formatting."""
    md = "Here is [a link](https://example.com) in a paragraph."
    expected = (
        "Here is a link{a} in a paragraph.\n\n=> https://example.com {a} a link\n"
    )
    assert markdown_to_gemtext(md) == expected


##############################################################################
def test_linkify_bare_urls() -> None:
    """Test automatic linkification of raw URLs."""
    md = "So if you visit https://example.com/ you will see example text"
    expected = (
        "So if you visit https://example.com/{a} you will see example text\n\n"
        "=> https://example.com/ {a} https://example.com/\n"
    )
    assert markdown_to_gemtext(md) == expected


##############################################################################
def test_linkify_gemini_protocol() -> None:
    """Test automatic linkification of gemini:// URLs by default."""
    md = "Visit gemini://geminiprotocol.net/ for the specification."
    expected = (
        "Visit gemini://geminiprotocol.net/{a} for the specification.\n\n"
        "=> gemini://geminiprotocol.net/ {a} gemini://geminiprotocol.net/\n"
    )
    assert markdown_to_gemtext(md) == expected


##############################################################################
def test_extra_linkable_protocols() -> None:
    """Test custom protocols configured via extra_linkable_protocols."""
    md = "Check spartan://example.org/ and nex://nightfall.city/ now."
    options = Options(extra_linkable_protocols=["spartan", "nex"])
    expected = (
        "Check spartan://example.org/{a} and nex://nightfall.city/{b} now.\n\n"
        "=> spartan://example.org/ {a} spartan://example.org/\n"
        "=> nex://nightfall.city/ {b} nex://nightfall.city/\n"
    )
    assert markdown_to_gemtext(md, options=options) == expected


##############################################################################
def test_multiple_inline_links_and_marker_reset() -> None:
    """Test multiple links in a paragraph and marker resetting in subsequent paragraphs."""
    md = (
        "First [one](https://1.com) and [two](https://2.com).\n\n"
        "Second [three](https://3.com)."
    )
    expected = (
        "First one{a} and two{b}.\n\n"
        "=> https://1.com {a} one\n"
        "=> https://2.com {b} two\n\n"
        "Second three{a}.\n\n"
        "=> https://3.com {a} three\n"
    )
    assert markdown_to_gemtext(md) == expected


##############################################################################
def test_more_than_26_links_in_paragraph() -> None:
    """Test that 27+ links in a single paragraph use {aa} markers."""
    links_md = " ".join(f"[{i}](https://{i}.com)" for i in range(28))
    gemtext = markdown_to_gemtext(links_md)
    assert "25{z}" in gemtext
    assert "26{aa}" in gemtext
    assert "27{ab}" in gemtext
    assert "=> https://26.com {aa} 26" in gemtext
    assert "=> https://27.com {ab} 27" in gemtext


##############################################################################
def test_heading_with_link() -> None:
    """Test that links in headings are treated like links in paragraphs."""
    md = "## Heading with [Documentation](https://docs.example.com)"
    expected = (
        "## Heading with Documentation{a}\n"
        "=> https://docs.example.com {a} Documentation"
    )
    assert markdown_to_gemtext(md) == expected


##############################################################################
def test_list_items_with_links() -> None:
    """Test links in unordered list items."""
    # Solo link list items convert directly
    solo_md = "- [Python](https://python.org)\n- [Gemini](https://geminiprotocol.net)"
    assert markdown_to_gemtext(solo_md) == (
        "=> https://python.org Python\n=> https://geminiprotocol.net Gemini\n"
    )

    # List items with mixed text convert with {a} markers
    mixed_md = "- Check out [Python](https://python.org) today"
    assert markdown_to_gemtext(mixed_md) == (
        "* Check out Python{a} today\n=> https://python.org {a} Python\n"
    )


##############################################################################
def test_blockquote_with_links() -> None:
    """Test blockquotes containing inline links."""
    md = "> Quote mentioning [Python](https://python.org)."
    expected = "> Quote mentioning Python{a}.\n=> https://python.org {a} Python\n"
    assert markdown_to_gemtext(md) == expected


##############################################################################
def test_ordered_list_with_links() -> None:
    """Test that ordered list items are treated as paragraphs."""
    md = "1. Visit [Python](https://python.org) site\n2. Download code"
    expected = (
        "1. Visit Python{a} site\n\n"
        "=> https://python.org {a} Python\n\n"
        "2. Download code\n"
    )
    assert markdown_to_gemtext(md) == expected


##############################################################################
def test_footnote_with_links() -> None:
    """Test that links inside footnote definitions follow paragraph rules."""
    md = (
        "See the reference[^1].\n\n"
        "[^1]: Refer to the [Python Docs](https://docs.python.org) for details."
    )
    expected = (
        "See the reference¹.\n\n"
        "¹ Refer to the Python Docs{a} for details.\n\n"
        "=> https://docs.python.org {a} Python Docs\n"
    )
    assert markdown_to_gemtext(md) == expected


##############################################################################
def test_multiple_footnotes() -> None:
    """Test multiple footnotes rendered separately."""
    md = "Point one[^first] and point two[^second].\n\n[^first]: First note.\n[^second]: Second note."
    expected = "Point one¹ and point two².\n\n¹ First note.\n\n² Second note.\n"
    assert markdown_to_gemtext(md) == expected


##############################################################################
def test_named_and_double_digit_footnotes() -> None:
    """Test footnote labels with arbitrary names and numbering up to 10+."""
    refs = " ".join(f"note[^{i}]" for i in range(1, 12))
    defs = "\n\n".join(f"[^{i}]: Note {i}." for i in range(1, 12))
    md = f"{refs}\n\n{defs}"
    gemtext = markdown_to_gemtext(md)
    assert "note¹" in gemtext
    assert "note¹⁰" in gemtext
    assert "note¹¹" in gemtext
    assert "¹⁰ Note 10." in gemtext
    assert "¹¹ Note 11." in gemtext


##############################################################################
def test_front_matter_options() -> None:
    """Test front matter filtering and preformatted output."""
    md = "---\ntitle: Document Title\nauthor: Author Name\n---\n# Main Heading"

    expected_with_fm = (
        "```frontmatter\n"
        "title: Document Title\n"
        "author: Author Name\n"
        "```\n\n"
        "# Main Heading"
    )

    # Default: emitted as preformatted text (hide_front_matter=False)
    assert markdown_to_gemtext(md) == expected_with_fm

    # hide_front_matter=True: filtered out
    assert markdown_to_gemtext(md, Options(hide_front_matter=True)) == "# Main Heading"


##############################################################################
def test_image_conversion() -> None:
    """Test image conversion to Gemtext links."""
    # Standalone image (default space_after_paragraphs=True)
    assert markdown_to_gemtext("![Alt text](https://example.com/pic.png)") == (
        "=> https://example.com/pic.png Alt text\n"
    )
    # Standalone image (space_after_paragraphs=False)
    assert (
        markdown_to_gemtext(
            "![Alt text](https://example.com/pic.png)",
            Options(space_after_paragraphs=False),
        )
        == "=> https://example.com/pic.png Alt text"
    )


##############################################################################
def test_code_block_internal_backticks_escaping() -> None:
    """Test that lines inside code blocks starting with ``` are space-prefixed."""
    md = "````markdown\nSome text\n```embedded fence\ncode\n```\n````"
    expected = "```markdown\nSome text\n ```embedded fence\ncode\n ```\n```\n"
    assert markdown_to_gemtext(md) == expected


##############################################################################
@mark.parametrize(
    "markdown, retain, gemtext",
    [
        (
            "Text with **bold**, *italic*, ~~strike~~, and `code`.",
            True,
            "Text with **bold**, *italic*, ~~strike~~, and `code`.\n",
        ),
        (
            "Text with **bold**, *italic*, ~~strike~~, and `code`.",
            False,
            "Text with bold, italic, strike, and code.\n",
        ),
        (
            "Link with [**bold link**](https://example.com).",
            True,
            "Link with **bold link**{a}.\n\n=> https://example.com {a} **bold link**\n",
        ),
        (
            "Link with [**bold link**](https://example.com).",
            False,
            "Link with bold link{a}.\n\n=> https://example.com {a} bold link\n",
        ),
    ],
)
def test_retain_inline_markup_option(markdown: str, retain: bool, gemtext: str) -> None:
    """Test the retain_inline_markup option."""
    assert (
        markdown_to_gemtext(markdown, Options(retain_inline_markup=retain)) == gemtext
    )


##############################################################################
@mark.parametrize(
    "markdown, space, gemtext",
    [
        ("Hello, world!", True, "Hello, world!\n"),
        ("Hello, world!", False, "Hello, world!"),
        ("Hello, world!\n\nAgain!", True, "Hello, world!\n\nAgain!\n"),
        ("Hello, world!\n\nAgain!", False, "Hello, world!\nAgain!"),
    ],
)
def test_space_after_paragraphs_option(
    markdown: str, space: bool, gemtext: str
) -> None:
    """Test the space_after_paragraphs option."""
    assert (
        markdown_to_gemtext(markdown, Options(space_after_paragraphs=space)) == gemtext
    )


##############################################################################
@mark.parametrize(
    "markdown, space, gemtext",
    [
        ("> A quote", True, "> A quote\n"),
        ("> A quote", False, "> A quote"),
        ("> A quote\n\n> Second", True, "> A quote\n>\n> Second\n"),
        ("> A quote\n\n> Second", False, "> A quote\n>\n> Second"),
    ],
)
def test_space_after_blockquotes_option(
    markdown: str, space: bool, gemtext: str
) -> None:
    """Test the space_after_blockquotes option."""
    assert (
        markdown_to_gemtext(markdown, Options(space_after_blockquotes=space)) == gemtext
    )


##############################################################################
@mark.parametrize(
    "markdown, space, gemtext",
    [
        ("- Item 1\n- Item 2", True, "* Item 1\n* Item 2\n"),
        ("- Item 1\n- Item 2", False, "* Item 1\n* Item 2"),
        (
            "- Item 1\n- Item 2\n\nParagraph",
            True,
            "* Item 1\n* Item 2\n\nParagraph\n",
        ),
        (
            "- Item 1\n- Item 2\n\nParagraph",
            False,
            "* Item 1\n* Item 2\nParagraph\n",
        ),
    ],
)
def test_space_after_lists_option(markdown: str, space: bool, gemtext: str) -> None:
    """Test the space_after_lists option."""
    assert markdown_to_gemtext(markdown, Options(space_after_lists=space)) == gemtext


##############################################################################
def test_table_formatting() -> None:
    """Test table alignment, preformatting, and link extraction."""
    md = (
        "| Protocol | Port | Transport |\n"
        "| :--- | ---: | :---: |\n"
        "| [Gemini](gemini://geminiprotocol.net) | 1965 | TLS |\n"
        "| HTTP | 80 | TCP |"
    )

    # Default (preformat_tables=True)
    expected_preformatted = (
        "```table\n"
        "| Protocol  | Port | Transport |\n"
        "| :-------- | ---: | :-------: |\n"
        "| Gemini{a} | 1965 |    TLS    |\n"
        "| HTTP      |   80 |    TCP    |\n"
        "```\n\n"
        "=> gemini://geminiprotocol.net {a} Gemini\n"
    )
    assert markdown_to_gemtext(md) == expected_preformatted

    # Plain aligned table (preformat_tables=False)
    expected_plain = (
        "| Protocol  | Port | Transport |\n"
        "| :-------- | ---: | :-------: |\n"
        "| Gemini{a} | 1965 |    TLS    |\n"
        "| HTTP      |   80 |    TCP    |\n\n"
        "=> gemini://geminiprotocol.net {a} Gemini\n"
    )
    assert markdown_to_gemtext(md, Options(preformat_tables=False)) == expected_plain


##############################################################################
def test_html_block_handling_options() -> None:
    """Test the html_block_handling option (convert, preformat, striptags)."""
    html_block_md = (
        "<section>\n"
        "  <h2>Embedded Header</h2>\n"
        '  <p>Some text with <a href="https://example.com">a link</a>.</p>\n'
        "</section>"
    )

    # 1. convert (default)
    converted = markdown_to_gemtext(html_block_md)
    assert "## Embedded Header" in converted
    assert "Some text with a link" in converted
    assert "=> https://example.com" in converted

    # 2. preformat
    preformatted = markdown_to_gemtext(
        html_block_md, Options(html_block_handling="preformat")
    )
    assert "```html" in preformatted
    assert "<section>" in preformatted
    assert "```" in preformatted

    # 3. striptags
    stripped = markdown_to_gemtext(
        html_block_md, Options(html_block_handling="striptags")
    )
    assert "<" not in stripped
    assert ">" not in stripped
    assert "Embedded Header" in stripped
    assert "Some text with a link." in stripped


##############################################################################
def test_html_inline_handling_options() -> None:
    """Test the html_inline_handling option (striptags, keep)."""
    md = "Press <kbd>Ctrl</kbd> + <kbd>C</kbd> to copy."

    # default (striptags) strips inline tags
    assert markdown_to_gemtext(md) == "Press Ctrl + C to copy.\n"

    # keep retains inline tags
    assert (
        markdown_to_gemtext(md, Options(html_inline_handling="keep"))
        == "Press <kbd>Ctrl</kbd> + <kbd>C</kbd> to copy.\n"
    )


### test_markdown_to_gemtext.py ends here
