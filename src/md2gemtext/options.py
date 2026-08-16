"""Configuration options for the converter."""

##############################################################################
# Python imports.
from typing import Literal, NamedTuple

##############################################################################
type HTMLBlockHandling = Literal["convert", "preformat", "striptags"]
"""Options for handling the conversion of HTML blocks."""
type HTMLInlineHandling = Literal["keep", "striptags"]
"""Options for handling the conversion of inline HTML tags."""


##############################################################################
class Options(NamedTuple):
    """Configuration options for the converter."""

    retain_inline_markup: bool = True
    """Whether to retain inline Markdown markup (e.g. *italic*, **bold**, `code`)."""

    space_after_paragraphs: bool = True
    """Whether to add an empty line after paragraphs."""

    space_after_blockquotes: bool = True
    """Whether to add an empty line after blockquotes."""

    space_after_lists: bool = True
    """Whether to add an empty line after a run of list items is broken."""

    hide_front_matter: bool = False
    """Whether to hide front matter. If False (default), emits it as preformatted text."""

    extra_linkable_protocols: (
        list[str] | tuple[str, ...] | set[str] | frozenset[str]
    ) = ()
    """Additional protocol names to linkify (e.g. ['spartan', 'finger', 'nex'])."""

    preformat_tables: bool = True
    """Whether to format tables as preformatted blocks with alt-text 'table'."""

    html_block_handling: HTMLBlockHandling = "convert"
    """How to handle HTML blocks: 'convert', 'preformat', or 'striptags'."""

    html_inline_handling: HTMLInlineHandling = "striptags"
    """How to handle inline HTML tags: 'keep' or 'striptags'."""


### options.py ends here
