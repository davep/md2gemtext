"""Command line interface for md2gemtext."""

##############################################################################
# Python imports.
import argparse
import sys

##############################################################################
# Local imports.
from .convert import markdown_to_gemtext
from .options import Options


##############################################################################
def convert() -> None:
    """Parse the input from stdin or files and print the parsed Gemtext."""
    parser = argparse.ArgumentParser(
        prog="md2gemtext",
        description="A simple Markdown to Gemtext converter.",
    )
    parser.add_argument(
        "files",
        nargs="*",
        default=["-"],
        help="Markdown file(s) to convert (default: stdin).",
    )
    parser.add_argument(
        "--strip-inline-markup",
        "--no-retain-inline-markup",
        dest="retain_inline_markup",
        action="store_false",
        default=True,
        help="Strip inline Markdown markup (bold, italics, etc.).",
    )
    parser.add_argument(
        "--no-space-after-paragraphs",
        dest="space_after_paragraphs",
        action="store_false",
        default=True,
        help="Do not add an empty line after paragraphs.",
    )
    parser.add_argument(
        "--no-space-after-blockquotes",
        dest="space_after_blockquotes",
        action="store_false",
        default=True,
        help="Do not add an empty line after blockquotes.",
    )
    parser.add_argument(
        "--no-space-after-lists",
        dest="space_after_lists",
        action="store_false",
        default=True,
        help="Do not add an empty line after a run of list items.",
    )
    parser.add_argument(
        "--hide-front-matter",
        dest="hide_front_matter",
        action="store_true",
        default=False,
        help="Hide/filter out front matter from output (default: false).",
    )
    parser.add_argument(
        "--extra-protocol",
        action="append",
        default=[],
        dest="extra_linkable_protocols",
        help="Additional protocol to linkify (e.g. --extra-protocol spartan).",
    )
    parser.add_argument(
        "--no-preformat-tables",
        dest="preformat_tables",
        action="store_false",
        default=True,
        help="Do not emit tables as preformatted blocks (emit as plain aligned text).",
    )
    parser.add_argument(
        "--html-block-handling",
        choices=["convert", "preformat", "striptags"],
        default="convert",
        dest="html_block_handling",
        help="How to handle HTML blocks: 'convert', 'preformat', or 'striptags' (default: convert).",
    )
    parser.add_argument(
        "--html-inline-handling",
        choices=["keep", "striptags"],
        default="striptags",
        dest="html_inline_handling",
        help="How to handle inline HTML tags: 'keep' or 'striptags' (default: striptags).",
    )
    args = parser.parse_args()

    options = Options(
        retain_inline_markup=args.retain_inline_markup,
        space_after_paragraphs=args.space_after_paragraphs,
        space_after_blockquotes=args.space_after_blockquotes,
        space_after_lists=args.space_after_lists,
        hide_front_matter=args.hide_front_matter,
        extra_linkable_protocols=args.extra_linkable_protocols,
        preformat_tables=args.preformat_tables,
        html_block_handling=args.html_block_handling,
        html_inline_handling=args.html_inline_handling,
    )

    content_list: list[str] = []
    for file_path in args.files:
        if file_path == "-":
            content_list.append(sys.stdin.read())
        else:
            with open(file_path, encoding="utf-8") as f:
                content_list.append(f.read())

    output = markdown_to_gemtext("".join(content_list), options=options)
    if output:
        print(output)


##############################################################################
if __name__ == "__main__":
    convert()


### __main__.py ends here
