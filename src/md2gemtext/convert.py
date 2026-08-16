"""Provides a simple Markdown to Gemtext converter."""

##############################################################################
# Local imports.
from ._converter import MarkdownToGemtextConverter
from .options import Options


##############################################################################
def markdown_to_gemtext(markdown_content: str, options: Options | None = None) -> str:
    """Convert Markdown content to Gemtext.

    Args:
        markdown_content: The Markdown content to convert.
        options: Optional conversion options.

    Returns:
        The converted Gemtext content.
    """
    return MarkdownToGemtextConverter(options).convert(markdown_content)


### convert.py ends here
