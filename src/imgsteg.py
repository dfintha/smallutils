#!/usr/bin/env python3
"""Image steganography tool, using PIL/Pillow."""

import argparse
import PIL.Image


class ImageSteganographyBuffer:
    """Steganography buffer class."""

    def __init__(self, width: int, height: int, data: list, alpha: list):
        self.width = width
        self.height = height
        self.data = data
        self.alpha = alpha

    @classmethod
    def load(cls, path: str):
        """Loads an image."""
        with PIL.Image.open(path) as image:
            image.convert("RGBA")
            data = image.getdata()
            result = []
            for pixel in data:
                result.append(pixel[0])  # R
                result.append(pixel[1])  # G
                result.append(pixel[2])  # B
            alpha = PIL.Image.frombytes(
                "L",
                (image.width, image.height),
                bytes([pixel[3] for pixel in data]),
            )
        return cls(image.width, image.height, result, alpha)

    def _make_pil_image(self) -> PIL.Image.Image:
        image = PIL.Image.frombytes(
            "RGB", (self.width, self.height), bytes(self.data)
        )
        image.putalpha(self.alpha)
        return image

    def save(self, path: str) -> None:
        """Saves the image to the specified path."""
        self._make_pil_image().save(path)

    def show(self) -> None:
        """Displays the image."""
        self._make_pil_image().show()

    def encode(self, string: str) -> None:
        """Encodes a string into an image."""
        if len(string) > (len(self.data) // 8):
            raise AttributeError(
                "The specified string is too long for the specified image."
            )
        string = bytearray(string.encode("utf-8"))
        string.append(0)
        where = 0
        for character in string:
            values = [((character & (1 << index)) != 0) for index in range(8)]
            for value in values:
                if value == 1 and self.data[where] % 2 != 1:
                    self.data[where] += 1
                elif value == 0 and self.data[where] % 2 != 0:
                    self.data[where] -= 1
                where += 1

    def decode(self) -> str:
        """Decodes the encoded string from an image."""
        string = bytearray(b"")
        binary_buffer = ""
        for byte in self.data:
            value = byte % 2
            binary_buffer += str(value).strip()
            if len(binary_buffer) == 8:
                string.append(int(binary_buffer[::-1], 2))
                if string[-1] == 0:
                    break
                binary_buffer = ""
        return string.decode("utf-8")


def main() -> None:
    """Entry point of the program."""
    program = "imgsteg.py"
    description = "Steganography tool to encode strings in images."
    parser = argparse.ArgumentParser(description=description, prog=program)
    subparsers = parser.add_subparsers(required=True, metavar="COMMAND")

    encode_subparser = subparsers.add_parser(
        "encode", help="Encode a string into an image."
    )
    encode_subparser.add_argument(
        "source",
        type=str,
        help="The image file, which server as a basis for the encoding.",
        metavar="SOURCE",
    )
    encode_subparser.add_argument(
        "destination",
        type=str,
        help="The path where the resulting image will be saved.",
        metavar="DESTINATION",
    )
    encode_subparser.add_argument(
        "information",
        type=str,
        help="The string to encode in the image.",
        metavar="INFORMATION",
    )
    encode_subparser.set_defaults(command="encode")

    decode_subparser = subparsers.add_parser(
        "decode", help="Decode a string from an image."
    )
    decode_subparser.add_argument(
        "source", type=str, help="The iamge file to decode.", metavar="SOURCE"
    )
    decode_subparser.set_defaults(command="decode")

    arguments = vars(parser.parse_args())
    if arguments["command"] == "encode":
        buffer = ImageSteganographyBuffer.load(arguments["source"])
        buffer.encode(arguments["information"])
        buffer.save(arguments["destination"])
    elif arguments["command"] == "decode":
        buffer = ImageSteganographyBuffer.load(arguments["source"])
        print(buffer.decode())


if __name__ == "__main__":
    main()
