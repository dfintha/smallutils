#!/usr/bin/env python
"""Manual serial communication utility."""

import sys
import serial
import serial.tools.list_ports

COLOR_BLUE = "\033[1m\033[34m"
COLOR_GREEN = "\033[1m\033[32m"
COLOR_RESET = "\033[0m"
RESPONSE_BUFFER_SIZE = 1024


def main() -> None:
    """Entry point of the program."""

    print("Querying available devices...")
    devices = _get_devices()
    if len(devices) == 0:
        print("No available devices found, exiting.")
        sys.exit(0)

    print("The following devices are available.")
    for index, port in enumerate(devices):
        print(f"  {index}: {port[1]}")

    try:
        max_index = len(devices) - 1
        index = _choose_integer(f"Device? (0-{max_index}) ", 0, max_index)
        baudrate = _choose_integer("Baudrate? ", 75, 256000)
        terminator = _choose_string(
            "Line terminator (cr, lf, crlf)? ", ["cr", "lf", "crlf"]
        )
    except KeyboardInterrupt:
        print("\nInterrupted, exiting.")
        sys.exit(0)

    device = devices[index][0]
    terminator = terminator.replace("lf", "\n").replace("cr", "\r")

    print("Connecting to the selected device...")
    connection = serial.Serial(port=device, baudrate=baudrate, timeout=0.2)
    print("Connected. Press ^C to finish the session.")
    print("-" * 80)
    try:
        while True:
            _exchange_messages(connection, terminator)
    except KeyboardInterrupt:
        print(f"{COLOR_RESET}^C\n{'-' * 80}")
        print("Closing connection...")
        connection.close()
        connection = None
        print("Session finished.")
        sys.exit(0)


def _get_devices() -> list:
    return [
        (port.device, f"{port.device} ({port.serial_number})")
        for port in serial.tools.list_ports.comports()
        if port.device.startswith("COM") and port.serial_number is not None
    ]


def _choose_integer(prompt: str, minimum: int, maximum: int) -> int:
    value = None
    while value is None or value < minimum or value > maximum:
        try:
            value = int(input(prompt))
        except ValueError:
            value = None
    return value


def _choose_string(prompt: str, choices: list) -> str:
    chosen = None
    while chosen is None or chosen not in choices:
        try:
            chosen = input(prompt).lower()
        except ValueError:
            chosen = None
    return chosen


def _exchange_messages(connection, terminator: str) -> None:
    command = bytes(input(f"<<< {COLOR_BLUE}") + terminator, "latin1")
    print(COLOR_RESET, end="")
    connection.write(command)
    response = connection.read(RESPONSE_BUFFER_SIZE).decode("latin1")
    response = response.strip("\n").strip("\r").strip("\n")
    response = response.replace("\n", f"\n{COLOR_RESET}>>>{COLOR_GREEN} ")
    print(f">>> {COLOR_GREEN}{response}{COLOR_RESET}")


if __name__ == "__main__":
    main()
