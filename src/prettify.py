#!/usr/bin/env python
"""A simple program, which prettifies XML/JSON/Python data."""

import argparse
import ast
import json
import pprint
import sys
import xml.dom.minidom


def main() -> None:
    """Entry point of the program."""
    program = "reformat.py"
    description = "Utility to reformat various data descriptions."
    parser = argparse.ArgumentParser(description=description, prog=program)
    parser.add_argument("doctype", type=str, choices=["json", "xml", "python"])
    arguments = vars(parser.parse_args())
    original = sys.stdin.read()
    prettified = reformat(original, arguments["doctype"])
    print(prettified)


def reformat(original: str, doctype: str) -> str:
    """Prettifies a document."""
    reformatters = {
        "json": reformat_json,
        "xml": reformat_xml,
        "python": reformat_python,
    }

    if doctype not in reformatters.keys():
        return original
    return reformatters[doctype](original)


def reformat_xml(original: str) -> str:
    """Prettifies an XML document."""
    parsed = xml.dom.minidom.parseString(original)
    encoded = parsed.toprettyxml(indent="    ", encoding="utf-8")
    return encoded.decode("utf-8")


def reformat_json(original: str) -> str:
    """Prettifies a JSON document."""
    parsed = json.loads(original)
    return json.dumps(parsed, indent="    ")


def reformat_python(original: str) -> str:
    """Prettifies a Python object representation."""
    parsed = ast.literal_eval(original)
    return pprint.pformat(parsed)


if __name__ == "__main__":
    main()
