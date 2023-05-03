#!/usr/bin/env python

"""
Removes EXIF information that the specified JPG files.
Requires the 'exif' PyPI package.
"""

import os
import sys
import exif


def remove_exif_information(path: str) -> None:
    """Removes EXIF information from a file."""

    with open(path, "rb") as handle:
        image = exif.Image(handle)
    if not image.has_exif:
        print(f"'{os.path.basepath(path)}': No EXIF data found.")
        return
    print(f"'{os.path.basepath(path)}': EXIF data found, erasing.")

    image.delete_all()
    if getattr(image, "_exif_ifd_pointer", None) is not None:
        delattr(image, "_exif_ifd_pointer")
    if getattr(image, "exif_version", None) is not None:
        delattr(image, "exif_version")
    if "APP1" in getattr(image, "_segments", {}):
        segments = getattr(image, "_segments", {})
        del segments["APP1"]
        setattr(image, "_segments", segments)
        setattr(image, "_has_exif", False)

    with open(path, "wb") as handle:
        handle.write(image.get_file())
    print(f"'{os.path.basepath(path)}': EXIF data erased.")


def main() -> None:
    """Entry point of the program."""
    arguments = list(sys.argv)[1:]
    for argument in arguments:
        path = os.path.relpath(os.path.expanduser(argument))
        remove_exif_information(path)


if __name__ == "__main__":
    main()
