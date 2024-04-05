#!/usr/bin/env python3

"""Quick system information utility for Raspberry Pi devices."""

import argparse
import pprint
import re
import socket
import typing
import uuid

MODELS = [
    "Pi Model A",
    "Pi Model B",
    "Pi Model A+",
    "Pi Model B+",
    "Pi 2 Model B",
    "Alpha",
    "Compute Module 1",
    "Unknown",
    "Pi 3 Model B",
    "Pi Zero Model Zero",
    "Compute Module 3",
    "Unknown",
    "Pi Zero Model W/WH",
    "Pi 3 Model B+",
    "Pi 3 Model A+",
    "Unknown",
    "Compute Module 3+",
    "Pi 4 Model B",
    "Pi Zero Model 2W",
    "Compute Module 4",
    "Pi 4 Model 400",
]
PROCESSORS = ["BCM2835", "BCM2836", "BCM2837", "BCM2711"]
MANUFACTURERS = [
    "Sony UK",
    "Egoman",
    "Embest",
    "Sony Japan",
    "Embest",
    "Stadium",
]
STORAGES = [256, 512, 1024, 2048, 4096, 8192]


def get_cpuinfo_fields() -> dict:
    """Returns information about the device from /proc/cpuinfo."""

    relevant = ("Model", "Serial", "Revision")
    result = {}
    for key in relevant:
        result[key] = ""

    with open("/proc/cpuinfo", "rt", encoding="utf-8") as handle:
        content = handle.readlines()
        for line in content:
            parts = line.split(":")
            if len(parts) < 2:
                continue
            key = line.split(":")[0].strip(" \t")
            if key not in relevant:
                continue
            value = line.split(":")[1].strip(" \t\n")
            result[key] = value

    if "Serial" in result:
        result["Serial"] = result["Serial"].upper()

    if "Revision" in result:
        result["Revision"] = result["Revision"].upper()

    return result


def get_addresses() -> dict:
    """Returns the IP and MAC address of the device."""
    result = {}
    result["MACAddress"] = ":".join(re.findall("..", f"{uuid.getnode():012X}"))
    check_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    check_socket.settimeout(0)
    try:
        check_socket.connect(("1.1.1.1", 80))
        result["IPAddress"] = check_socket.getsockname()[0]
    except (InterruptedError, OSError, TimeoutError):
        result["IPAddress"] = "Disconnected"
    finally:
        check_socket.close()
    return result


def dump_as_xml(info: dict) -> None:
    """Dumps the information in XML format."""
    print('<?xml version="1.0" encoding="UTF-8" standalone="no" ?>')
    print("<Device>")
    for key, value in info.items():
        if isinstance(value, bool):
            print(f"    <{key}>{flag_to_literal(value)}</{key}>")
        else:
            print(f"    <{key}>{value}</{key}>")
    print("</Device>")


def dump_as_json(info: dict) -> None:
    """Dumps the information in JSON format."""
    print("{")
    for key, value in info.items():
        if isinstance(value, bool):
            print(f'    "{key}": {flag_to_literal(value)},')
        elif isinstance(value, str):
            print(f'    "{key}": "{value}",')
        else:
            print(f'    "{key}": {value},')
    print("}")


def dump_via_repr(info: dict) -> None:
    """Dumps the information in its Python representation."""
    print(repr(info))


def n_bits_at(revision: int, place: int, length: int) -> int:
    """Parses a bit quartet at the given position from a number."""
    mask = 0
    for _ in range(0, length):
        mask = (mask << 1) | 0x01
    return (revision & (mask << place)) >> place


def flag_to_literal(flag: int) -> str:
    """Converts a flag to a lower-case boolean literal."""
    return str(bool(flag)).lower()


def parse_revision_string(revision_string: str) -> dict:
    """Parses the Revision field from the cpuinfo query."""

    revision = int("0x" + revision_string, 16)
    fields = {}

    encoded = n_bits_at(revision, 23, 1) == 1
    fields["RevisionEncodesInformation"] = encoded
    if not encoded:
        return fields

    fields["PCBRevision"] = n_bits_at(revision, 0, 4)
    fields["ModelName"] = MODELS[n_bits_at(revision, 4, 8)]
    fields["Processor"] = PROCESSORS[n_bits_at(revision, 12, 4)]
    fields["Manufacturer"] = MANUFACTURERS[n_bits_at(revision, 16, 4)]
    fields["MemorySizeMB"] = STORAGES[n_bits_at(revision, 20, 3)]

    warranty_old = n_bits_at(revision, 24, 1) == 1
    warranty_new = n_bits_at(revision, 25, 1) == 1
    fields["WarrantyVoid"] = warranty_old or warranty_new

    return fields


def main() -> typing.NoReturn:
    """Entry point of the program."""

    formatted_printers = {
        "xml": dump_as_xml,
        "json": dump_as_json,
        "pprint": pprint.pprint,
        "repr": dump_via_repr,
    }

    parser = argparse.ArgumentParser(
        description="Quick system information for Raspberry Pi devices.",
        prog="rpinfo.py",
        epilog="Format type can be either 'xml', 'json', 'pprint', or 'repr'. "
        "The 'pprint' and 'repr' formats only differ in whitespace "
        "characters and can be parsed by a Python interpreter.",
    )
    parser.add_argument(
        "--format",
        dest="format",
        default="pprint",
        choices=formatted_printers.keys(),
        help="specifies output format",
        metavar="FORMAT",
    )

    selected_format = vars(parser.parse_args())["format"]
    info = get_cpuinfo_fields()
    info.update(get_addresses())
    info.update(parse_revision_string(info["Revision"]))
    formatted_printers[selected_format](info)


if __name__ == "__main__":
    main()
