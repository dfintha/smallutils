#!/usr/bin/env python3
"""Utility that prints the occurrences of C/C++ #includes in a directory."""

import shutil
import subprocess
import sys


def run_grep(directory: str) -> str:
    """Runs `grep` in the directory, returns its output."""
    grep = subprocess.run(
        ["grep", "^\\s*#include", "-r", directory],
        capture_output=True,
        check=False,
        encoding="utf-8",
    )
    return grep.stdout if grep.returncode == 0 else ""


def run_ripgrep(directory: str) -> str:
    """Runs `rg` in the directory, returns its output."""
    ripgrep = subprocess.run(
        ["rg", "-e", "^\\s*#include", "--no-heading", directory],
        capture_output=True,
        check=False,
        encoding="utf-8",
    )
    return ripgrep.stdout if ripgrep.returncode == 0 else ""


def run_some_grep(directory: str) -> str:
    """Runs `rg` or `grep` in the target directory, returns its output."""
    if shutil.which("rg") is not None:
        return run_ripgrep(directory)
    return run_grep(directory)


def summarize_occurrences(grep_output: str) -> list[tuple[str, int]]:
    """Summarizes the result of the output of a grep command."""

    parts = [
        line.split(":")[1].strip()
        for line in grep_output.split("\n")
        if line != ""
    ]

    mapping = {}
    for inclusion in parts:
        if inclusion in mapping:
            mapping[inclusion] += 1
        else:
            mapping[inclusion] = 1

    result = []
    for inclusion, count in mapping.items():
        result.append((inclusion.replace("#include", "").strip(), count))

    result = sorted(result, key=lambda x: x[1], reverse=True)
    return result


def print_occurrences(summarized: list) -> None:
    """Prints the occurrences in human-readable format."""

    if len(summarized) == 0:
        print("No inclusions occur in the project.")
        return

    bar_width = 64
    denominator = summarized[0][1] / bar_width
    longest_name = len(max(summarized, key=lambda x: len(x[0]))[0])
    total_inclusions = 0

    for item in summarized:
        total_inclusions += item[1]

    for item in summarized:
        bar_length = int(item[1] / denominator)
        bar_pad = bar_width - bar_length
        name_pad = (longest_name + 2) - len(item[0])
        percent = item[1] / total_inclusions
        print(
            f"{name_pad * ' '}{item[0]} "
            + f"[{'=' * bar_length}{' ' * bar_pad}] "
            + f"{item[1]} ({percent * 100:.02n}%)"
        )


def main() -> None:
    """Entry point of the program."""
    if len(sys.argv) != 2:
        print("usage: includecount.py <SOURCE_DIRECTORY>")
        return
    print_occurrences(summarize_occurrences(run_some_grep(sys.argv[1])))


if __name__ == "__main__":
    main()
