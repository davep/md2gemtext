"""A simple Markdown to Gemtext converter."""

##############################################################################
# Python imports.
from importlib.metadata import version

######################################################################
# Main library information.
__author__ = "Dave Pearson"
__copyright__ = "Copyright 2026, Dave Pearson"
__credits__ = ["Dave Pearson"]
__maintainer__ = "Dave Pearson"
__email__ = "davep@davep.org"
__version__: str = version("md2gemtext")
__licence__ = "MIT"

##############################################################################
# Local imports.
from .convert import markdown_to_gemtext
from .options import HTMLBlockHandling, HTMLInlineHandling, Options

##############################################################################
# Exports.
__all__ = [
    "HTMLBlockHandling",
    "HTMLInlineHandling",
    "markdown_to_gemtext",
    "Options",
]


### __init__.py ends here
