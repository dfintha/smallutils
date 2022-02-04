#!/usr/bin/env python3

"""Tool to perform periodic auto-clicking with the mouse."""

import argparse
import time
import subprocess
import sys
import keyboard


def main():
    """Entry point and main logic of the program."""

    parser = argparse.ArgumentParser(
        description="Auto-clicking tool. Requires root privileges on Linux."
    )
    parser.add_argument(
        "interval",
        metavar="INTERVAL",
        type=int,
        nargs="?",
        help="interval of the auto-clicking in milliseconds (default: 200)",
        default=200,
    )

    interval = parser.parse_args().interval
    print(f"Interval is {interval} milliseconds.")

    try:
        # This is a dummy call, which acts as a root privilege check.
        keyboard.parse_hotkey("space")
    except ImportError as error:
        print(error)
        sys.exit(1)

    state = {"running": True, "clicking": True}

    print("Press space to start auto-clicking.")
    keyboard.wait("space", suppress=True)
    print("\b", end="", flush=True)

    print("Press space to stop auto-clicking or escape to quit.")

    def space_handler():
        state["clicking"] = not state["clicking"]
        print(f"\bSpace pressed, clicking toggled to {state['clicking']}.")

    keyboard.add_hotkey("space", space_handler, suppress=True)

    def escape_handler():
        state["running"] = False
        print("\bEscape pressed, exiting.")

    keyboard.add_hotkey("esc", escape_handler, suppress=True)

    while state["running"]:
        if state["clicking"]:
            subprocess.call(["xdotool", "click", "1"])
        time.sleep(interval / 1000)
    print("")


if __name__ == "__main__":
    main()
