#!/usr/bin/env python3

"""Automated image converter to generate Slack-compatible emojis."""

import math
import os
import subprocess
import sys


def main():
    """Entry point of the program."""

    arguments = list(sys.argv)[1:]
    garbage = set()

    for file in arguments:
        if not os.path.exists(file):
            print(f"(main) '{file}' does not exist, skipping")
            continue

        extension = os.path.splitext(file)[1].lower()
        if extension != ".gif":
            converted = convert(file, "png")
        else:
            converted = convert(file, "gif")
        if converted is None:
            print(f"(main) failed to convert '{file}', skipping")
            continue
        garbage.add(converted)

        squarified = squarify(converted)
        if squarified is None:
            print(f"(main) failed to squarify '{file}', skipping")
            continue
        garbage.add(squarified)

        filtered = filter(squarified)
        if filtered is None:
            print(f"(main) failed to fuzzy erase '{file}', skipping")
            continue
        garbage.add(filtered)

        downscaled = downscale(filtered, 128)
        if downscaled is None:
            print(f"(main) failed to downscale '{file}', skipping")
        if downscaled in garbage:
            garbage.remove(downscaled)

    garbage = {file for file in garbage if file not in arguments}
    for file in garbage:
        try:
            os.remove(file)
        except OSError:
            pass


def convert(image: str, new_format: str) -> str:
    """Converts `image` to `new_format` and returns the new file's name."""

    new_format = new_format.strip()
    if os.path.splitext(image)[1][1:].lower() == new_format:
        print(
            f"(convert) '{os.path.basename(image)}' "
            f"is already in {new_format} format, skipping"
        )
        return image

    print(
        f"(convert) converting '{os.path.basename(image)}' to {new_format} "
        "format"
    )

    new_filename = f"{os.path.splitext(image)[0]}.{new_format}"
    if execute(["magick", "mogrify", "-format", new_format, image]):
        return new_filename
    return None


def squarify(image: str):
    """Crops `image` to an 1:1 aspect ratio, and returns the new file's name."""

    width, height, _ = measure(image)
    if width == height:
        print(
            f"(squarify) '{os.path.basename(image)}' is already a square, "
            "skipping"
        )
        return image

    smaller = width
    if height < width:
        smaller = height

    print(
        f"(squarify) cropping '{os.path.basename(image)}' to "
        f"{smaller}x{smaller} pixels"
    )
    return crop(image, smaller, smaller)


def filter(image: str) -> str:
    """
    Attempts to remove the background of `image`, and returns the new file's
    name.
    """

    extension = os.path.splitext(image)[1].lower()
    if extension == ".gif":
        print(f"(filter) '{os.path.basename(image)}' may be animated, skipping")
        return image

    new_basename = f"{os.path.splitext(image)[0]}_filtered"
    new_filename = f"{new_basename}{os.path.splitext(image)[1]}"

    print(
        "(filter) attempting to erase the background of "
        f"'{os.path.basename(image)}'"
    )

    color = pick(image, 0, 0)
    if color is None:
        return None

    # https://stackoverflow.com/a/44542839
    # fmt: off
    command = [
        "convert",
        image,
        "-alpha", "off",
        "-bordercolor", color,
        "-border", "1",
        "(",
            "+clone",
            "-fuzz", "30%",
            "-fill", "none",
            "-floodfill", "+0+0", color,
            "-alpha", "extract",
            "-geometry", "200%",
            "-blur", "0x0.5",
            "-morphology", "erode", "square:1",
            "-geometry", "50%",
        ")",
        "-compose", "CopyOpacity",
        "-composite",
        "-shave", "1",
        new_filename,
    ]
    # fmt: on

    if not execute(command):
        return None

    command = [
        "convert",
        new_filename,
        "-fuzz", "5%",
        "-transparent", "white",
        new_filename
    ]

    if execute(command):
        return new_filename
    return None


def downscale(image: str, target_size_kb: int) -> str:
    """
    Downscales `image` until its size is barely under `target_size_kb`, and
    returns the new file's name.
    """

    width, height, file_size = measure(image)
    if (file_size / 1000) <= target_size_kb:
        print(
            f"(downscale) image '{os.path.basename(image)}' is already "
            f"smaller than {target_size_kb} kilobytes, skipping"
        )
        return image

    print(
        f"(downscale) downscaling '{os.path.basename(image)}' to fit under "
        f"{target_size_kb} kilobytes"
    )

    divisor = math.gcd(width, height)
    if divisor in (1, width, height):
        divisor = 20

    width_step = width // divisor
    height_step = height // divisor

    while True:
        width -= width_step
        height -= height_step

        if width == 0 or height == 0:
            return None

        result = scale(image, width, height)
        if result is None:
            return None

        _, _, file_size = measure(result)
        if (file_size / 1000) < target_size_kb:
            return result

        os.remove(result)


def scale(image: str, width: int, height: int) -> str:
    """
    Scales `image` to `width` times `height` resolution, and returns the new
    file's name.
    """

    new_basename = f"{os.path.splitext(image)[0]}_scaled_{width}x{height}"
    new_filename = f"{new_basename}{os.path.splitext(image)[1]}"

    command = [
        "convert",
        image,
        "-coalesce",
        "-resize",
        f"{width}x{height}",
        "-deconstruct",
        new_filename,
    ]

    if execute(command):
        return new_filename
    return None


def crop(
    image: str,
    width: int,
    height: int,
    x_offset: int = None,
    y_offset: int = None,
) -> str:
    """
    Crops `image` to `width` times `height` resolution. If both `x_offset` and
    `y_offset` are specified, they will be used to specify the top left corner
    where the crop should start. Otherwise it will be centered.
    """

    new_basename = f"{os.path.splitext(image)[0]}_cropped_{width}x{height}"
    new_filename = f"{new_basename}{os.path.splitext(image)[1]}"

    original_width, original_height, _ = measure(image)

    if x_offset is None or y_offset is None:
        x_offset = (original_width - width) // 2
        y_offset = (original_height - height) // 2

    command = [
        "convert",
        image,
        "-repage",
        "-0x0",
        "-crop",
        f"{width}x{height}+{x_offset}+{y_offset}",
        "+repage",
        new_filename,
    ]

    if execute(command):
        return new_filename
    return None


def measure(image: str) -> (int, int, int):
    """Returns the width, height, and file size of `image`."""

    try:
        file_size = os.path.getsize(image)
    except OSError:
        return (None, None, None)
    result = execute(["identify", "-verbose", image])
    if result is not None:
        lines = [
            line.strip()
            for line in result.split("\n")
            if line.startswith("  Geometry: ")
        ]
        if len(lines) == 0:
            return (None, None, None)
        width, height = lines[0].split(":")[1].split("+")[0].split("x")
        return (int(width), int(height), file_size)
    return (None, None, None)


def pick(image: str, x: int, y: int) -> str:
    """
    Picks the color the pixel at coordinates (`x`, `y`) of `image`, and returns
    it in hexadecimal RRGGBB format. For animated images, the first frame will
    be used.
    """

    command = [
        "magick",
        image,
        "-format",
        f"%[hex:u.p{{{x},{y}}}]\\n",
        "info:",
    ]

    result = execute(command)
    if result is None:
        return None

    lines = [line.strip() for line in result.split("\n")]
    if len(lines) == 0:
        return None

    return lines[0]


def execute(command: list) -> bool:
    """
    Executes the given command and returns its standard output on success, or
    None otherwise.
    """

    task = subprocess.run(
        command, capture_output=True, check=False, encoding="utf-8"
    )

    if task.returncode == 0:
        return " " + task.stdout
    print(task.stderr)
    return None


if __name__ == "__main__":
    main()
