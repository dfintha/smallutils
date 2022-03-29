#!/usr/bin/env python3

"""Simple HTMLM (HTML with Macros) preprocessor."""

import re
import sys


def main() -> None:
    """Entry point of the program."""
    for argument in sys.argv[1:]:
        print(process_htmlm_file(argument))


def process_htmlm_file(path: str) -> str:
    """Processes a single HTMLM file."""
    with open(path, "rt", encoding="utf-8") as file:
        contents = file.read()

    pattern = re.compile(r"\s*<define\s+([a-zA-Z]\w+)\s+(.*)\s*/>")
    definitions = re.findall(pattern, contents)
    contents = re.subn(pattern, "", contents)[0]

    for (name, definition) in definitions:
        tag = definition.split(" ")[0]
        contents = re.subn(f"<:{name}(.*)>", f"<{definition}\\1>", contents)[0]
        contents = re.subn(f"</:{name}>", f"</{tag}>", contents)[0]
    return contents


if __name__ == "__main__":
    main()
