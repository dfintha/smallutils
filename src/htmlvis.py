#!/usr/bin/env python3

"""HTML document object model visualizer using dot/graphviz."""

import html.parser
import sys
import urllib.parse
import urllib.request


class HTMLGrapher(html.parser.HTMLParser):
    """Parser class, that builds a tree to graph."""

    def __init__(self, filename: str):
        super().__init__()
        self.current_id = 1
        self.previous = []
        self.graph = f"digraph \"{filename}\" {{\n"

    def handle_starttag(self, tag: str, attributes: list) -> None:
        """Callback to handle start tags."""
        current = f"\"{tag}#{self.current_id}\""
        self.graph += f"  {current} [label={current.split('#')[0]}\", fontsize=30, width=2, height=0.75, shape=\"box\"];\n"
        if self.previous:
            self.graph += f"  {self.previous[-1]} -> {current}\n"
        self.previous.append(current)
        self.current_id += 1

    def handle_endtag(self, tag: str) -> None:
        """Callback to handle end tags."""
        self.previous = self.previous[:-1]

    def feed(self, source: str) -> str:
        """Feed a document to the grapher."""
        super().feed(source)
        self.graph += "}\n"
        return self.graph


def main() -> None:
    """Entry point of the program."""
    if len(list(sys.argv)) != 2:
        print("usage: htmlvis.py <FILE>")
        return

    if sys.argv[1].startswith("http"):
        source = urllib.request.urlopen(sys.argv[1]).read().decode("utf-8")
    else:
        try:
            with open(sys.argv[1], "r", encoding="utf-8") as handle:
                source = handle.read()
        except Exception as exception:
            print(f"error: {exception}")

    parser = HTMLGrapher(sys.argv[1])
    graph = parser.feed(source)

    link = (
        "https://quickchart.io/graphviz?format=png&graph=" +
        urllib.parse.quote_plus(graph.replace("\n", " "))
    )
    print("Use this link to get a graphical representation of the document.\n")
    print(link)

    ## If dot is installed on your computer, you can uncomment this part to
    ## create a PNG representation locally.
    # import os
    # with open("./TEMP.dot", "w+", encoding="utf-8") as handle:
    #     handle.write(graph)
    # os.popen("dot -Tpng TEMP.dot -o graph.png")


if __name__ == "__main__":
    main()
