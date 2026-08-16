"""Provides the core Markdown to Gemtext converter."""

##############################################################################
# Python imports.
import re
from html.parser import HTMLParser
from typing import Final

##############################################################################
# HTML to Gemtext imports.
from html2gemtext import Options as HTMLOptions
from html2gemtext import html_to_gemtext

##############################################################################
# Markdown-it imports.
from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

##############################################################################
# Local imports.
from .options import Options

##############################################################################
# Superscript conversion mapping for digits.
SUPERSCRIPT_DIGITS: Final[dict[str, str]] = {
    "0": "⁰",
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹",
}


##############################################################################
def to_superscript_number(num: int) -> str:
    """Convert an integer number to UTF-8 superscript digits.

    Args:
        num: The number to convert (e.g. 1, 10, 25).

    Returns:
        The superscript string representation (e.g. '¹', '¹⁰', '²⁵').
    """
    return "".join(SUPERSCRIPT_DIGITS.get(d, d) for d in str(num))


##############################################################################
def get_marker(index: int) -> str:
    """Generate a link marker string for the given 0-based index.

    Generates markers {a}, {b}, ..., {z}, {aa}, {ab}, etc.

    Args:
        index: The 0-based index of the link.

    Returns:
        The formatted marker string, e.g. '{a}'.
    """
    n = index + 1
    result: list[str] = []
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result.append(chr(ord("a") + rem))
    return f"{{{''.join(reversed(result))}}}"


##############################################################################
def _escape_code_lines(content: str) -> str:
    """Escape lines inside preformatted text that start with backticks.

    Prepends a space to any line whose first three characters are backticks
    to prevent Gemtext parsers from interpreting them as preformat toggles.

    Args:
        content: The code content.

    Returns:
        The escaped code content.
    """
    return "\n".join(
        f" {line}" if line.startswith("```") else line for line in content.splitlines()
    )


##############################################################################
class HTMLTagStripper(HTMLParser):
    """HTML parser to extract text content while stripping tags."""

    def __init__(self) -> None:
        """Initialise the tag stripper."""
        super().__init__()
        self._text_chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        """Collect text data.

        Args:
            data: Raw text data inside HTML elements.
        """
        self._text_chunks.append(data)

    def get_text(self) -> str:
        """Return the consolidated stripped text.

        Returns:
            The text content with HTML tags removed.
        """
        return "".join(self._text_chunks).strip()


##############################################################################
def strip_html_tags(html_content: str) -> str:
    """Strip HTML tags from HTML content, returning the raw text.

    Args:
        html_content: The HTML content to strip.

    Returns:
        The stripped plain text.
    """
    stripper = HTMLTagStripper()
    stripper.feed(html_content)
    stripper.close()
    return stripper.get_text()


##############################################################################
class ContentCapture:
    """Base class to capture Gemtext block content."""

    def __init__(self, options: Options) -> None:
        """Initialise the object.

        Args:
            options: The options for the converter.
        """
        self._options = options


##############################################################################
class Paragraph(ContentCapture):
    """A class to capture a paragraph."""

    def __init__(
        self,
        text: str,
        links: list[tuple[str, str, str]],
        options: Options,
    ) -> None:
        """Initialise the paragraph.

        Args:
            text: The paragraph text.
            links: List of (href, marker, text) tuples.
            options: Conversion options.
        """
        super().__init__(options)
        self._text = text
        self._links = links
        self._final_newline = options.space_after_paragraphs

    def __str__(self) -> str:
        """Return the paragraph as a Gemtext string."""
        parts: list[str] = [self._text]
        if self._links:
            parts.append("")
            for href, marker, text in self._links:
                parts.append(
                    f"=> {href} {marker} {text}" if text else f"=> {href} {marker}"
                )
        if self._final_newline:
            parts.append("")
        return "\n".join(parts)


##############################################################################
class Heading(ContentCapture):
    """A class to capture a heading."""

    def __init__(
        self,
        level: int,
        text: str,
        links: list[tuple[str, str, str]],
        options: Options,
    ) -> None:
        """Initialise the heading.

        Args:
            level: The heading level (1-6).
            text: The heading text.
            links: List of (href, marker, text) tuples.
            options: Conversion options.
        """
        super().__init__(options)
        self._level = min(level, 3)
        self._text = text
        self._links = links

    def __str__(self) -> str:
        """Return the heading as a Gemtext string."""
        prefix = "#" * self._level
        parts: list[str] = [f"{prefix} {self._text}".rstrip()]
        if self._links:
            for href, marker, text in self._links:
                parts.append(
                    f"=> {href} {marker} {text}" if text else f"=> {href} {marker}"
                )
        return "\n".join(parts)


##############################################################################
class ListItem(ContentCapture):
    """A class to capture an unordered list item."""

    def __init__(
        self,
        text: str,
        links: list[tuple[str, str, str]],
        is_solo_link: bool,
        options: Options,
        is_last_in_list: bool = False,
    ) -> None:
        """Initialise the list item.

        Args:
            text: The item text.
            links: List of (href, marker, text) tuples.
            is_solo_link: Whether the item consists solely of a link.
            options: Conversion options.
            is_last_in_list: Whether this is the last item in a run of list items.
        """
        super().__init__(options)
        self._text = text
        self._links = links
        self._is_solo_link = is_solo_link
        self._final_newline = is_last_in_list and options.space_after_lists

    def mark_last_in_list(self) -> None:
        """Mark this item as the last item in a run of list items."""
        self._final_newline = self._options.space_after_lists

    def __str__(self) -> str:
        """Return the list item as a Gemtext string."""
        if self._is_solo_link and self._links:
            href, _, text = self._links[0]
            line = f"=> {href} {text}".rstrip()
            return f"{line}\n" if self._final_newline else line

        parts: list[str] = [f"* {self._text}"]
        if self._links:
            for href, marker, text in self._links:
                parts.append(
                    f"=> {href} {marker} {text}" if text else f"=> {href} {marker}"
                )
        if self._final_newline:
            parts.append("")
        return "\n".join(parts)


##############################################################################
class NumberedListItem(ContentCapture):
    """A class to capture an ordered / numbered list item as a paragraph."""

    def __init__(
        self,
        prefix: str,
        text: str,
        links: list[tuple[str, str, str]],
        options: Options,
    ) -> None:
        """Initialise the numbered list item.

        Args:
            prefix: The numbering prefix (e.g. '1.').
            text: The item text.
            links: List of (href, marker, text) tuples.
            options: Conversion options.
        """
        super().__init__(options)
        self._prefix = prefix
        self._text = text
        self._links = links
        self._final_newline = options.space_after_paragraphs

    def __str__(self) -> str:
        """Return the numbered list item as a Gemtext string."""
        parts: list[str] = [f"{self._prefix} {self._text}".rstrip()]
        if self._links:
            parts.append("")
            for href, marker, text in self._links:
                parts.append(
                    f"=> {href} {marker} {text}" if text else f"=> {href} {marker}"
                )
        if self._final_newline:
            parts.append("")
        return "\n".join(parts)


##############################################################################
class Blockquote(ContentCapture):
    """A class to capture a blockquote."""

    def __init__(
        self,
        paragraphs: list[str],
        links: list[tuple[str, str, str]],
        options: Options,
    ) -> None:
        """Initialise the blockquote.

        Args:
            paragraphs: List of paragraph texts within the blockquote.
            links: List of (href, marker, text) tuples.
            options: Conversion options.
        """
        super().__init__(options)
        self._paragraphs = paragraphs
        self._links = links
        self._final_newline = options.space_after_blockquotes

    def __str__(self) -> str:
        """Return the blockquote as a Gemtext string."""
        all_lines: list[str] = []
        for idx, paragraph in enumerate(self._paragraphs):
            if idx > 0:
                all_lines.append("")
            all_lines.extend(paragraph.splitlines())

        parts: list[str] = [f"> {line}" if line else ">" for line in all_lines]
        if self._links:
            for href, marker, text in self._links:
                parts.append(
                    f"=> {href} {marker} {text}" if text else f"=> {href} {marker}"
                )
        if self._final_newline:
            parts.append("")
        return "\n".join(parts)


##############################################################################
class Preformatted(ContentCapture):
    """A class to capture preformatted text."""

    def __init__(
        self,
        info: str,
        content: str,
        options: Options,
    ) -> None:
        """Initialise the preformatted block.

        Args:
            info: The alt text / language identifier.
            content: The code content.
            options: Conversion options.
        """
        super().__init__(options)
        self._info = info
        self._content = content
        self._final_newline = options.space_after_paragraphs

    def __str__(self) -> str:
        """Return the preformatted block as a Gemtext string."""
        escaped = _escape_code_lines(self._content)
        parts = [
            f"```{self._info}".rstrip(),
            escaped,
            "```",
        ]
        if self._final_newline:
            parts.append("")
        return "\n".join(parts)


##############################################################################
class SoloLink(ContentCapture):
    """A class to capture a standalone link or image."""

    def __init__(self, href: str, text: str, options: Options) -> None:
        """Initialise the solo link.

        Args:
            href: The URL.
            text: The user-friendly link description.
            options: Conversion options.
        """
        super().__init__(options)
        self._href = href
        self._text = text
        self._final_newline = options.space_after_paragraphs

    def __str__(self) -> str:
        """Return the solo link as a Gemtext string."""
        line = f"=> {self._href} {self._text}".rstrip()
        return f"{line}\n" if self._final_newline else line


##############################################################################
class Table(ContentCapture):
    """A class to capture a formatted table."""

    def __init__(
        self,
        formatted_table: str,
        links: list[tuple[str, str, str]],
        options: Options,
    ) -> None:
        """Initialise the table.

        Args:
            formatted_table: The formatted table text.
            links: Extracted links from table cells.
            options: Conversion options.
        """
        super().__init__(options)
        self._table = formatted_table
        self._links = links
        self._preformat = options.preformat_tables
        self._final_newline = options.space_after_paragraphs

    def __str__(self) -> str:
        """Return the table as a Gemtext string."""
        parts: list[str] = []
        if self._preformat:
            escaped = _escape_code_lines(self._table)
            parts.extend(["```table", escaped, "```"])
        else:
            parts.append(self._table)

        if self._links:
            parts.append("")
            for href, marker, text in self._links:
                parts.append(
                    f"=> {href} {marker} {text}" if text else f"=> {href} {marker}"
                )

        if self._final_newline:
            parts.append("")
        return "\n".join(parts)


##############################################################################
class RawBlock(ContentCapture):
    """A class to capture raw content passed through as-is (e.g. tables, HRs)."""

    def __init__(self, content: str, options: Options) -> None:
        """Initialise the raw block.

        Args:
            content: The raw text content.
            options: Conversion options.
        """
        super().__init__(options)
        self._content = content

    def __str__(self) -> str:
        """Return the raw block content."""
        return self._content


##############################################################################
class MarkdownToGemtextConverter:
    """Converts Markdown documents to Gemtext using markdown-it-py."""

    def __init__(self, options: Options | None = None) -> None:
        """Initialise the converter.

        Args:
            options: Optional conversion options.
        """
        self._options = options or Options()
        md = MarkdownIt("gfm-like").use(footnote_plugin).use(front_matter_plugin)
        if md.linkify is not None:
            md.linkify.add("gemini:", "http:")
            for proto in self._options.extra_linkable_protocols:
                schema = proto if proto.endswith(":") else f"{proto}:"
                md.linkify.add(schema, "http:")
        self._md: Final[MarkdownIt] = md

    def _render_inline(
        self,
        inline_token: Token,
        with_markers: bool = True,
        start_marker_index: int = 0,
    ) -> tuple[str, list[tuple[str, str, str]]]:
        """Render an inline token into text and extracted links.

        Args:
            inline_token: The inline Token containing child tokens.
            with_markers: Whether to append {a-z} markers to links.
            start_marker_index: Starting index for link markers.

        Returns:
            A tuple of (rendered_text, list_of_links).
        """
        if not inline_token.children:
            return "", []

        tokens = inline_token.children
        result: list[str] = []
        links: list[tuple[str, str, str]] = []
        link_counter = start_marker_index

        i = 0
        while i < len(tokens):
            tok = tokens[i]

            if tok.type == "text":
                result.append(tok.content)
                i += 1
            elif tok.type == "code_inline":
                if self._options.retain_inline_markup:
                    result.append(f"`{tok.content}`")
                else:
                    result.append(tok.content)
                i += 1
            elif tok.type in (
                "em_open",
                "em_close",
                "strong_open",
                "strong_close",
                "s_open",
                "s_close",
            ):
                if self._options.retain_inline_markup:
                    result.append(tok.markup)
                i += 1
            elif tok.type == "softbreak":
                result.append(" ")
                i += 1
            elif tok.type == "hardbreak":
                result.append("\n")
                i += 1
            elif tok.type == "html_inline":
                if self._options.html_inline_handling == "keep":
                    result.append(tok.content)
                i += 1
            elif tok.type == "footnote_ref":
                fn_id = int(tok.meta.get("id", 0)) if tok.meta else 0
                result.append(to_superscript_number(fn_id + 1))
                i += 1
            elif tok.type == "footnote_anchor":
                # Suppress backlink anchor in Gemtext
                i += 1
            elif tok.type == "image":
                src = str(tok.attrs.get("src", "")) if tok.attrs else ""
                alt = str(
                    tok.content or (tok.attrs.get("alt", "") if tok.attrs else "")
                )
                links.append((src, "", alt))
                result.append(alt)
                i += 1
            elif tok.type == "link_open":
                href = str(tok.attrs.get("href", "")) if tok.attrs else ""
                inner_tokens: list[Token] = []
                i += 1
                depth = 1
                while i < len(tokens) and depth > 0:
                    if tokens[i].type == "link_open":
                        depth += 1
                    elif tokens[i].type == "link_close":
                        depth -= 1
                        if depth == 0:
                            break
                    inner_tokens.append(tokens[i])
                    i += 1
                i += 1  # Skip link_close

                inner_inline = Token(
                    type="inline", tag="", nesting=0, children=inner_tokens
                )
                link_text, _ = self._render_inline(inner_inline, with_markers=False)

                if with_markers:
                    marker = get_marker(link_counter)
                    link_counter += 1
                    links.append((href, marker, link_text))
                    result.append(f"{link_text}{marker}")
                else:
                    links.append((href, "", link_text))
                    result.append(link_text)
            else:
                if tok.content:
                    result.append(tok.content)
                i += 1

        full_text = "".join(result)
        cleaned_lines = [
            re.sub(r"[ \t]+", " ", line).strip() for line in full_text.split("\n")
        ]
        cleaned_text = "\n".join(line for line in cleaned_lines if line)
        return cleaned_text, links

    def _is_solo_link_inline(self, inline_token: Token) -> bool:
        """Check if an inline token consists solely of a single link.

        Args:
            inline_token: The inline token.

        Returns:
            True if the inline token is purely a link, False otherwise.
        """
        if not inline_token.children:
            return False
        tokens = [t for t in inline_token.children if t.type != "softbreak"]
        if not tokens or tokens[0].type != "link_open":
            return False
        depth = 0
        for idx, t in enumerate(tokens):
            if t.type == "link_open":
                depth += 1
            elif t.type == "link_close":
                depth -= 1
                if depth == 0:
                    return idx == len(tokens) - 1
        return False

    def convert(self, markdown_content: str) -> str:
        """Convert a Markdown string to Gemtext.

        Args:
            markdown_content: The Markdown source string.

        Returns:
            The converted Gemtext string.
        """
        if not markdown_content.strip():
            return ""

        tokens = self._md.parse(markdown_content)
        document: list[ContentCapture] = []

        i = 0
        while i < len(tokens):
            token = tokens[i]

            match token.type:
                # Front matter
                case "front_matter":
                    if not self._options.hide_front_matter:
                        content = token.content.strip("\n")
                        document.append(
                            Preformatted("frontmatter", content, self._options)
                        )

                # Heading
                case "heading_open":
                    level = int(token.tag[1:]) if len(token.tag) > 1 else 1
                    i += 1
                    inline_token = tokens[i]
                    text, links = self._render_inline(inline_token, with_markers=True)
                    i += 1  # heading_close
                    document.append(Heading(level, text, links, self._options))

                # Paragraph
                case "paragraph_open":
                    i += 1
                    inline_token = tokens[i]
                    if (
                        inline_token.children
                        and len(inline_token.children) == 1
                        and inline_token.children[0].type == "image"
                    ):
                        img = inline_token.children[0]
                        src = str(img.attrs.get("src", "")) if img.attrs else ""
                        alt = str(
                            img.content
                            or (img.attrs.get("alt", "") if img.attrs else "")
                        )
                        document.append(SoloLink(src, alt, self._options))
                    else:
                        text, links = self._render_inline(
                            inline_token, with_markers=True
                        )
                        document.append(Paragraph(text, links, self._options))
                    i += 1  # paragraph_close

                # Bullet / Unordered list
                case "bullet_list_open":
                    i += 1
                    list_items: list[ListItem] = []
                    while i < len(tokens) and tokens[i].type != "bullet_list_close":
                        if tokens[i].type == "list_item_open":
                            i += 1
                            item_inline_tokens: list[Token] = []
                            while (
                                i < len(tokens) and tokens[i].type != "list_item_close"
                            ):
                                if tokens[i].type == "inline":
                                    item_inline_tokens.append(tokens[i])
                                i += 1
                            for inline_tok in item_inline_tokens:
                                if self._is_solo_link_inline(inline_tok):
                                    text, links = self._render_inline(
                                        inline_tok, with_markers=False
                                    )
                                    list_items.append(
                                        ListItem(
                                            text,
                                            links,
                                            is_solo_link=True,
                                            options=self._options,
                                        )
                                    )
                                else:
                                    text, links = self._render_inline(
                                        inline_tok, with_markers=True
                                    )
                                    list_items.append(
                                        ListItem(
                                            text,
                                            links,
                                            is_solo_link=False,
                                            options=self._options,
                                        )
                                    )
                        i += 1
                    if list_items:
                        list_items[-1].mark_last_in_list()
                        document.extend(list_items)

                # Ordered / Numbered list
                case "ordered_list_open":
                    start_num = int(token.attrs.get("start", 1)) if token.attrs else 1
                    curr_num = start_num
                    i += 1
                    while i < len(tokens) and tokens[i].type != "ordered_list_close":
                        if tokens[i].type == "list_item_open":
                            if tokens[i].info and tokens[i].info.isdigit():
                                curr_num = int(tokens[i].info)
                            i += 1
                            item_inline_tokens = []
                            while (
                                i < len(tokens) and tokens[i].type != "list_item_close"
                            ):
                                if tokens[i].type == "inline":
                                    item_inline_tokens.append(tokens[i])
                                i += 1
                            for inline_tok in item_inline_tokens:
                                text, links = self._render_inline(
                                    inline_tok, with_markers=True
                                )
                                document.append(
                                    NumberedListItem(
                                        prefix=f"{curr_num}.",
                                        text=text,
                                        links=links,
                                        options=self._options,
                                    )
                                )
                            curr_num += 1
                        i += 1

                # Fenced code block
                case "fence":
                    info = token.info.strip() if token.info else ""
                    content = token.content.rstrip("\n")
                    document.append(Preformatted(info, content, self._options))

                # Indented code block
                case "code_block":
                    content = token.content.rstrip("\n")
                    document.append(Preformatted("", content, self._options))

                # Blockquotes (including merging consecutive blockquotes)
                case "blockquote_open":
                    quote_paragraphs: list[str] = []
                    quote_links: list[tuple[str, str, str]] = []
                    quote_link_counter = 0
                    while i < len(tokens) and tokens[i].type == "blockquote_open":
                        i += 1
                        while i < len(tokens) and tokens[i].type != "blockquote_close":
                            if tokens[i].type == "inline":
                                text, links = self._render_inline(
                                    tokens[i],
                                    with_markers=True,
                                    start_marker_index=quote_link_counter,
                                )
                                quote_link_counter += len(links)
                                if text:
                                    quote_paragraphs.append(text)
                                quote_links.extend(links)
                            i += 1
                        i += 1  # Skip blockquote_close

                    document.append(
                        Blockquote(quote_paragraphs, quote_links, self._options)
                    )
                    continue

                # Footnotes block
                case "footnote_block_open":
                    i += 1
                    while i < len(tokens) and tokens[i].type != "footnote_block_close":
                        if tokens[i].type == "footnote_open":
                            fn_id = (
                                int(tokens[i].meta.get("id", 0))
                                if tokens[i].meta
                                else 0
                            )
                            sup_label = to_superscript_number(fn_id + 1)
                            i += 1
                            fn_inline_tokens: list[Token] = []
                            while (
                                i < len(tokens) and tokens[i].type != "footnote_close"
                            ):
                                if tokens[i].type == "inline":
                                    fn_inline_tokens.append(tokens[i])
                                i += 1
                            for inline_tok in fn_inline_tokens:
                                text, links = self._render_inline(
                                    inline_tok, with_markers=True
                                )
                                document.append(
                                    NumberedListItem(
                                        prefix=sup_label,
                                        text=text,
                                        links=links,
                                        options=self._options,
                                    )
                                )
                        i += 1

                # Thematic break / Horizontal rule
                case "hr":
                    document.append(RawBlock("---", self._options))

                # Table
                case "table_open":
                    header_cells: list[str] = []
                    alignments: list[str] = []
                    table_rows: list[list[str]] = []
                    table_links: list[tuple[str, str, str]] = []
                    table_link_counter = 0
                    in_thead = False
                    current_row: list[str] = []

                    i += 1
                    while i < len(tokens) and tokens[i].type != "table_close":
                        tok = tokens[i]
                        if tok.type == "thead_open":
                            in_thead = True
                        elif tok.type == "thead_close":
                            in_thead = False
                        elif tok.type == "tr_open":
                            current_row = []
                        elif tok.type == "tr_close":
                            if not in_thead and current_row:
                                table_rows.append(current_row)
                        elif tok.type == "th_open":
                            style = str(tok.attrs.get("style", "")) if tok.attrs else ""
                            align = (
                                "center"
                                if "center" in style
                                else ("right" if "right" in style else "left")
                            )
                            alignments.append(align)
                        elif tok.type == "td_open":
                            pass
                        elif tok.type == "inline":
                            text, links = self._render_inline(
                                tok,
                                with_markers=True,
                                start_marker_index=table_link_counter,
                            )
                            table_link_counter += len(links)
                            if in_thead:
                                header_cells.append(text)
                            else:
                                current_row.append(text)
                            table_links.extend(links)
                        i += 1

                    num_cols = (
                        len(header_cells)
                        if header_cells
                        else (max(len(r) for r in table_rows) if table_rows else 0)
                    )
                    while len(alignments) < num_cols:
                        alignments.append("left")

                    col_widths = [
                        max(
                            len(header_cells[c]) if c < len(header_cells) else 0,
                            *(len(r[c]) if c < len(r) else 0 for r in table_rows),
                            3,
                        )
                        for c in range(num_cols)
                    ]

                    def fmt_cell(txt: str, w: int, al: str) -> str:
                        if al == "right":
                            return txt.rjust(w)
                        elif al == "center":
                            return txt.center(w)
                        return txt.ljust(w)

                    def fmt_sep(w: int, al: str) -> str:
                        if al == "center":
                            return f":{'-' * (w - 2)}:"
                        elif al == "right":
                            return f"{'-' * (w - 1)}:"
                        return f":{'-' * (w - 1)}"

                    table_lines: list[str] = []
                    if header_cells:
                        table_lines.append(
                            "| "
                            + " | ".join(
                                fmt_cell(
                                    header_cells[c],
                                    col_widths[c],
                                    alignments[c],
                                )
                                for c in range(num_cols)
                            )
                            + " |"
                        )
                        table_lines.append(
                            "| "
                            + " | ".join(
                                fmt_sep(col_widths[c], alignments[c])
                                for c in range(num_cols)
                            )
                            + " |"
                        )
                    for r in table_rows:
                        table_lines.append(
                            "| "
                            + " | ".join(
                                fmt_cell(
                                    r[c] if c < len(r) else "",
                                    col_widths[c],
                                    alignments[c] if c < len(alignments) else "left",
                                )
                                for c in range(num_cols)
                            )
                            + " |"
                        )

                    document.append(
                        Table("\n".join(table_lines), table_links, self._options)
                    )

                # HTML block
                case "html_block":
                    match self._options.html_block_handling:
                        case "convert":
                            html_opts = HTMLOptions(
                                space_after_paragraphs=self._options.space_after_paragraphs
                            )
                            converted = html_to_gemtext(
                                token.content, options=html_opts
                            )
                            if converted.strip():
                                document.append(RawBlock(converted, self._options))
                        case "preformat":
                            content = token.content.rstrip("\n")
                            document.append(
                                Preformatted("html", content, self._options)
                            )
                        case "striptags":
                            stripped = strip_html_tags(token.content)
                            if stripped.strip():
                                document.append(Paragraph(stripped, [], self._options))

                case _:
                    pass

            i += 1

        return "\n".join(str(capture) for capture in document)


### _converter.py ends here
