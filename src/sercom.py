#!/usr/bin/env python
"""Manual serial communication utility."""

import datetime
import sys
import serial
import serial.tools.list_ports

COLOR_BLUE = "\033[1m\033[34m"
COLOR_GREEN = "\033[1m\033[32m"
COLOR_RESET = "\033[0m"
RESPONSE_BUFFER_SIZE = 1024

BYTESIZE_VALUES = {
    5: serial.FIVEBITS,
    6: serial.SIXBITS,
    7: serial.SEVENBITS,
    8: serial.EIGHTBITS,
}

PARITY_VALUES = {
    "none": serial.PARITY_NONE,
    "odd": serial.PARITY_ODD,
    "even": serial.PARITY_EVEN,
    "mark": serial.PARITY_MARK,
    "space": serial.PARITY_SPACE,
}

STOPBITS_VALUES = {
    "one": serial.STOPBITS_ONE,
    "onehalf": serial.STOPBITS_ONE_POINT_FIVE,
    "two": serial.STOPBITS_TWO,
}


def main(write_manifest: bool) -> None:
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
        index = _choose_integer("Device?", range(len(devices)), True, 0)
        baudrate = _choose_integer("Baudrate?", range(50, 256001), True, 9600)
        terminator = _choose_string(
            "Line terminator?", ["none", "cr", "lf", "crlf"], "crlf"
        )
        timeout = _choose_integer(
            "Timeout in milliseconds?", range(100, 10001), True, 200
        )
        bytesize = _choose_integer("Data bits?", [5, 6, 7, 8], True, 8)
        stopbits = _choose_string(
            "Stop bits?", ["one", "onehalf", "two"], "one"
        )
        parity = _choose_string(
            "Parity?", ["none", "odd", "even", "mark", "space"], "none"
        )
        flowcontrol = _choose_string(
            "Flow control?", ["none", "rtscts", "dtrdsr", "xonxoff"], "none"
        )
    except KeyboardInterrupt:
        print("\nInterrupted, exiting.")
        sys.exit(0)

    timeout = timeout / 1000
    stopbits = STOPBITS_VALUES[stopbits]
    start = datetime.datetime.now()
    manifest = (
        f"      Device: {devices[index][1]}\n"
        + f"   Baud Rate: {baudrate}\n"
        + f"  Terminator: {terminator}\n"
        + f"   Byte Size: {bytesize}\n"
        + f"   Stop Bits: {stopbits}\n"
        + f"      Parity: {parity}\n"
        + f"     Timeout: {timeout} seconds\n"
        + f"Flow Control: {flowcontrol}\n"
        + f"       Start: {start.strftime('%Y-%m-%d %H:%M:%S')}\n"
        + "         End: $ENDTS\n"
        + "-" * 80
        + "\n"
    )

    port = devices[index][0]
    bytesize = BYTESIZE_VALUES[bytesize]
    parity = PARITY_VALUES[parity]
    terminator = (
        terminator.replace("lf", "\n").replace("cr", "\r").replace("none", "")
    )

    print("Connecting to the selected device...")
    connection = serial.Serial(
        port=port,
        baudrate=baudrate,
        bytesize=bytesize,
        parity=parity,
        stopbits=stopbits,
        timeout=timeout,
        xonxoff=(flowcontrol == "xonxoff"),
        rtscts=(flowcontrol == "rtscts"),
        dsrdtr=(flowcontrol == "dsrdtr"),
    )
    print("Connected. Press ^C to finish the session.")
    print("-" * 80)
    try:
        while True:
            manifest += _exchange_messages(connection, terminator)
    except KeyboardInterrupt:
        print(f"{COLOR_RESET}^C\n{'-' * 80}")
        print("Connection closed, session finished.")
    except serial.serialutil.SerialException:
        print(f"{COLOR_RESET}{'-' * 80}")
        print("Connection interrupted, session finished.")
    finally:
        if write_manifest:
            _dump_manifest(port, start, manifest)


def _get_devices() -> list:
    return [
        (port.device, f"{port.device} ({port.serial_number})")
        for port in serial.tools.list_ports.comports()
        if port.device.startswith("COM") and port.serial_number is not None
    ]


def _choose_integer(
    prompt: str, values: list, linear: bool, default: int
) -> int:
    value = None
    if linear:
        choices = f"{values[0]}-{values[-1]}"
    else:
        choices = ", ".join([str(value) for value in values])
    prompt = f"{prompt} ({choices}) "
    if default is not None:
        prompt += f"[{default}] "
    while value is None or value not in values:
        try:
            value = input(prompt)
            if value.strip() == "" and default is not None:
                value = default
            else:
                value = int(value)
        except ValueError:
            value = None
    return value


def _choose_string(prompt: str, choices: list, default: str) -> str:
    chosen = None
    choices = ", ".join(choices)
    prompt = f"{prompt} ({choices}) "
    if default is not None:
        prompt += f"[{default}] "
    while chosen is None or chosen not in choices:
        try:
            chosen = input(prompt).lower()
            if chosen.strip() == "" and default is not None:
                chosen = default
        except ValueError:
            chosen = None
    return chosen


def _exchange_messages(connection, terminator: str) -> str:
    command = input(f"<<< {COLOR_BLUE}")
    manifest = f"<<< {command}\n"
    command = bytes(command + terminator, "latin1")
    print(COLOR_RESET, end="")
    connection.write(command)
    response = connection.read(RESPONSE_BUFFER_SIZE).decode("latin1")
    response = response.strip("\n").strip("\r").strip("\n")
    manifest += ">>> " + response.replace("\n", ">>> ") + "\n"
    response = response.replace("\n", f"\n{COLOR_RESET}>>>{COLOR_GREEN} ")
    print(f">>> {COLOR_GREEN}{response}{COLOR_RESET}")
    return manifest


def _dump_manifest(port: str, start: str, manifest: str) -> None:
    filename = f"sercom-{port}-{start.strftime('%Y%m%d-%H%M%S')}.log"
    with open(filename, "wt", encoding="utf-8") as handle:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        manifest = manifest.replace("$ENDTS", now) + "-" * 80 + "\n"
        handle.write(manifest)


if __name__ == "__main__":
    main("--manifest" in list(sys.argv))
