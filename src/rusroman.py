#!/usr/bin/env python3

"""Russian cyrillic romanizer."""

# Too many return statements and branches are here because of the string
# (letter) matching in _romanize_letter().
# pylint: disable=R0911,R0912

import sys


def _is_vowel(letter: str) -> bool:
    return letter.lower() in "аеёийоуэюя"


def _is_space(letter: str) -> bool:
    return letter in " \n\t"


def _romanize_letter(
    letter: str,
    previous_vowel: bool,
    previous_space: bool
) -> str:

    def _same_case(original: str, new: str) -> str:
        if original.islower():
            return new.lower()
        return new

    if letter.lower() == "а":
        return _same_case(letter, "A")

    if letter.lower() == "б":
        return _same_case(letter, "B")

    if letter.lower() == "в":
        return _same_case(letter, "V")

    if letter.lower() == "г":
        return _same_case(letter, "G")

    if letter.lower() == "д":
        return _same_case(letter, "D")

    if letter.lower() == "е":
        return _same_case(letter, "Ye" if previous_vowel else "E")

    if letter.lower() == "ё":
        return _same_case(letter, "Yo")

    if letter.lower() == "ж":
        return _same_case(letter, "Zh")

    if letter.lower() == "з":
        return _same_case(letter, "Z")

    if letter.lower() == "и":
        return _same_case(letter, "I")

    if letter.lower() == "й":
        return _same_case(letter, "Y")

    if letter.lower() == "к":
        return _same_case(letter, "K")

    if letter.lower() == "л":
        return _same_case(letter, "L")

    if letter.lower() == "м":
        return _same_case(letter, "M")

    if letter.lower() == "н":
        return _same_case(letter, "N")

    if letter.lower() == "о":
        return _same_case(letter, "O")

    if letter.lower() == "п":
        return _same_case(letter, "P")

    if letter.lower() == "р":
        return _same_case(letter, "R")

    if letter.lower() == "с":
        return _same_case(letter, "S")

    if letter.lower() == "т":
        return _same_case(letter, "T")

    if letter.lower() == "у":
        return _same_case(letter, "U")

    if letter.lower() == "ф":
        return _same_case(letter, "F")

    if letter.lower() == "х":
        return _same_case(letter, "H" if previous_space else "Kh")

    if letter.lower() == "ц":
        return _same_case(letter, "Ts")

    if letter.lower() == "ч":
        return _same_case(letter, "Ch")

    if letter.lower() == "ш":
        return _same_case(letter, "Sh")

    if letter.lower() == "щ":
        return _same_case(letter, "Sch")

    if letter.lower() == "ъ":
        return ""

    if letter.lower() == "ы":
        return _same_case(letter, "Y")

    if letter.lower() == "ь":
        return ""

    if letter.lower() == "э":
        return _same_case(letter, "E")

    if letter.lower() == "ю":
        return _same_case(letter, "Yu")

    if letter.lower() == "я":
        return _same_case(letter, "Ya")

    return letter


def _romanize_text(text: str) -> str:
    result = ""
    previous_vowel = False
    previous_space = True
    for character in text:
        result += _romanize_letter(character, previous_vowel, previous_space)
        previous_vowel = _is_vowel(character)
        previous_space = _is_space(character)
    return result


def _main() -> None:
    for argument in sys.argv[1:]:
        with open(argument, "rt", encoding="utf-8") as handle:
            for line in handle.readlines():
                print(_romanize_text(line), end="")


if __name__ == "__main__":
    _main()
