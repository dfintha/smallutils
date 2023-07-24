#!/usr/bin/env python
"""
Simple program that draws black and white images in the terminal. Requires the
PIL/Pillow and termcolor Python packages.
"""

import math
import sys
from PIL import Image
from termcolor import colored


def draw_bw(image_file_path: str, downscale_factor: float = 1.0) -> None:
    """
    Draws a black and white image to the terminal using unicode box drawing
    characters.
    """
    with Image.open(image_file_path) as original:
        width, height = original.size
        width = math.floor(width / downscale_factor)
        height = math.floor(height / downscale_factor)
        # The PIL.Image modules does actually have a member named NEAREST.
        # pylint: disable-next=E1101
        with original.resize((width, height), resample=Image.NEAREST) as scaled:
            for i in range(height):
                for j in range(width):
                    pixel = scaled.getpixel(xy=(j, i))
                    if isinstance(pixel, int):
                        pixel_value = pixel
                        light_threshold = 128
                        is_transparent = False
                    else:
                        pixel_value = sum(list(pixel))
                        light_threshold = (255 * len(pixel)) / 2
                        is_transparent = len(pixel) == 4 and pixel[3] == 0
                    if pixel_value > light_threshold or is_transparent:
                        print(colored("██", "white", attrs=["bold"]), end="")
                    else:
                        print(colored("██", "black", attrs=["bold"]), end="")
                print("")


def main() -> None:
    """Entry point of the program."""
    if len(sys.argv) not in (2, 3):
        print("usage: bwtermdraw <PATH> [DOWNSCALE FACTOR]")
    else:
        image_file_path = sys.argv[1]
        downscale_factor = float(sys.argv[2]) if len(sys.argv) == 3 else 1.0
        draw_bw(image_file_path, downscale_factor)


if __name__ == "__main__":
    main()
