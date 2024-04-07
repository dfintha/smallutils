#! /usr/bin/env python3
"""Recursively lists shared library dependencies of an executable or library."""

import os
import subprocess
import sys

COLOR_BLUE = "\033[1m\033[34m"
COLOR_GREEN = "\033[1m\033[32m"
COLOR_WHITE = "\033[1m\033[37m"
COLOR_RESET = "\033[0m"


# This class is only used to parse, store, and represent dependencies.
# pylint: disable-next=R0903
class Dependency:
    """Represents a single dependency."""

    def __init__(self, ldd_line: str):
        if "=>" in ldd_line:
            arrow_split = ldd_line.split("=>")
            self.name = arrow_split[0].strip()
            paren_split = arrow_split[1].split("(")
            self.path = paren_split[0].strip()
            self.address = paren_split[1][:-1]
        else:
            paren_split = ldd_line.split("(")
            self.name = paren_split[0].strip()
            self.path = None
            self.address = paren_split[1][:-1]

        self.realpath = self.path
        if self.realpath is not None and os.path.islink(self.realpath):
            self.realpath = os.path.realpath(self.realpath)

        if self.name.startswith("/"):
            self.name = self.name.split("/")[-1]

    def __repr__(self):
        return f"<Dependency to {self.name}>"

    def __str__(self):
        name = f"{COLOR_WHITE}{self.name}{COLOR_RESET}"
        path = f" => {self.path}" if self.path is not None else ""
        if self.path is not None and self.path != self.realpath:
            path += f" -> {self.realpath}"
        address = f"{COLOR_BLUE}({self.address}){COLOR_RESET}"
        return f"{name}{path} {address}"


def ldd(path: str) -> list:
    """Returns the dependencies of a single binary."""
    process = subprocess.run(
        ["ldd", path], capture_output=True, encoding="utf-8", check=False
    )
    if process.stdout.strip() == "statically linked":
        return []
    lines = [
        Dependency(line)
        for line in process.stdout.split("\n")
        if line.strip() != ""
    ]
    return lines


def walk_dependencies(path: str, prefix: str = "  ") -> None:
    """Recursively walks through and lists dependencies."""
    entries = ldd(path)
    for entry in entries:
        print(f"{prefix}{str(entry)}")
        if entry.path is not None:
            walk_dependencies(entry.realpath, "  " + prefix)


def main() -> None:
    """Entry point of the program."""
    print(f"{COLOR_GREEN}{sys.argv[1]}{COLOR_RESET}")
    if len(ldd(sys.argv[1])) == 0:
        print("  statically linked")
        return
    walk_dependencies(sys.argv[1])


if __name__ == "__main__":
    main()
