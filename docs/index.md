# md2gemtext - A simple library for converting Markdown to Gemtext

## Introduction

`md2gemtext` is a small and simple library that provides code for
converting Markdown into [the hypertext markup language of the Gemini
project](https://geminiprotocol.net/docs/gemtext-specification.gmi).

## Installation

`md2gemtext` is available from PyPI and can be installed with your
package installer of choice.

With `pip`:

```shell
pip install md2gemtext
```

With `uv`:

```shell
uv add md2gemtext
```

## Quick start

The library provides a main conversion function called `markdown_to_gemtext`.
It is passed a string of Markdown you wish to convert, and returns the converted
Gemtext string:

```python
from md2gemtext import markdown_to_gemtext, Options

markdown = """
# Welcome

This is a paragraph with [a link](https://example.com) inside.
"""

gemtext = markdown_to_gemtext(markdown)
print(gemtext)
```

Output:

```gemtext
# Welcome

This is a paragraph with a link{a} inside.

=> https://example.com {a} a link
```

### Options

Conversion behavior can be configured using the `Options` class:

```python
from md2gemtext import Options, markdown_to_gemtext

options = Options(
    retain_inline_markup=False,   # Strip bold, italic, code markup
    space_after_paragraphs=True,  # Add empty line after paragraphs
    space_after_blockquotes=True, # Add empty line after blockquotes
    space_after_lists=True,       # Add empty line after runs of list items
    hide_front_matter=True,       # Hide/filter out front matter (default is False, which emits it)
    extra_linkable_protocols=["spartan", "finger", "nex"], # Additional protocols to linkify
    preformat_tables=True,        # Emit tables as preformatted blocks with alt-text 'table'
    html_block_handling="convert", # HTML blocks: 'convert', 'preformat', or 'striptags'
    html_inline_handling="striptags", # Inline HTML tags: 'striptags' (default) or 'keep'
)

gemtext = markdown_to_gemtext(markdown, options=options)
```

## Command Line Interface

`md2gemtext` includes a command-line tool which reads from files or stdin:

```shell
# Read from file
md2gemtext document.md

# Read from stdin
cat document.md | md2gemtext

# Strip inline markup
md2gemtext --strip-inline-markup document.md

# Add extra protocols to linkify
md2gemtext --extra-protocol spartan --extra-protocol nex document.md

# Emit tables as plain aligned text instead of preformatted blocks
md2gemtext --no-preformat-tables document.md

# Set HTML block handling mode ('convert', 'preformat', or 'striptags')
md2gemtext --html-block-handling preformat document.md

# Keep inline HTML tags rather than stripping them
md2gemtext --html-inline-handling keep document.md
```

[//]: # (index.md ends here)
