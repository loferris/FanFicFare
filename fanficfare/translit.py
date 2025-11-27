"""Cyrillic transliteration utilities.

This module provides transliteration from Cyrillic alphabets (Russian, Ukrainian,
Bulgarian, Serbian) to Latin characters. The implementation is based on Unicode
character names and handles various Cyrillic scripts.

Code adapted from http://python.su/forum/viewtopic.php?pid=66946

Note:
    Currently only supports Cyrillic scripts. Other Unicode scripts will raise
    an assertion error.
"""

# Copyright 2018 FanFicFare team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unicodedata
from typing import Callable, Union


def is_syllable(letter: str) -> bool:
    """Check if a character is a vowel/syllable.

    Args:
        letter: Single character to check

    Returns:
        True if character is A, E, I, O, U (case insensitive), False otherwise

    Examples:
        >>> is_syllable('A')
        True
        >>> is_syllable('b')
        False
    """
    syllables = ("A", "E", "I", "O", "U", "a", "e", "i", "o", "u")
    if letter in syllables:
        return True
    return False


def is_consonant(letter: str) -> bool:
    """Check if a character is a consonant.

    Args:
        letter: Single character to check

    Returns:
        True if character is not a vowel, False otherwise

    Examples:
        >>> is_consonant('B')
        True
        >>> is_consonant('a')
        False
    """
    return not is_syllable(letter)


def romanize(letter: str) -> str:
    """Transliterate a single character from Cyrillic to Latin alphabet.

    Uses Unicode character names to determine the appropriate Latin equivalent.
    Handles special cases like quotes, dashes, and Cyrillic-specific letters.

    Args:
        letter: Single character to transliterate

    Returns:
        Transliterated Latin character(s) or original if already ASCII

    Raises:
        AssertionError: If character is not Cyrillic or a known exception

    Examples:
        >>> romanize('А')  # Cyrillic A
        'A'
        >>> romanize('я')  # Cyrillic ya
        'ya'
    """
    # Check if character is already ASCII/Latin
    try:
        letter.encode('ascii')
        return letter  # Already ASCII, return unchanged
    except (UnicodeEncodeError, AttributeError):
        pass  # Not ASCII, need to transliterate

    unid = unicodedata.name(letter)

    # Handle special punctuation and symbols
    exceptions = {
        "NUMERO SIGN": "No",
        "LEFT-POINTING DOUBLE ANGLE QUOTATION MARK": "\"",
        "RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK": "\"",
        "DASH": "-"
    }
    for name_contains in exceptions:
        if unid.find(name_contains) != -1:
            return exceptions[name_contains]

    # Only Cyrillic is supported
    assert unid.startswith("CYRILLIC"), f"Not ready to romanize non-Cyrillic: {unid}"

    # Determine capitalization based on character type
    transformation_pairs = {
        "CYRILLIC CAPITAL LETTER ": str.capitalize,
        "CYRILLIC SMALL LETTER ": str.lower
    }
    func: Callable[[str], str] = str.lower
    for name_contains in transformation_pairs:
        if unid.find(name_contains) != -1:
            func = transformation_pairs[name_contains]
            unid = unid.replace(name_contains, "")

    # Handle special Cyrillic letters with unique transliterations
    cyrillic_exceptions = {
        "YERU": "y",
        "SHORT I": "y",
        "HARD SIGN": "'",
        "SOFT SIGN": "'",
        "BYELORUSSIAN-UKRAINIAN I": "i",
        "GHE WITH UPTURN": "g",
        "UKRAINIAN IE": "ie",
        "YU": "yu",
        "YA": "ya"
    }
    for name_contains in cyrillic_exceptions:
        if unid.find(name_contains) != -1:
            return cyrillic_exceptions[name_contains]

    # For standard letters, extract vowels/consonants from Unicode name
    if all(map(is_syllable, unid)):
        return func(unid)
    else:
        return func(''.join(filter(is_consonant, unid)))


def translit(text: Union[str, bytes]) -> str:
    """Transliterate Cyrillic text to Latin alphabet.

    Processes each character in the input string and converts Cyrillic
    characters to their Latin equivalents. ASCII characters pass through
    unchanged.

    Args:
        text: Text containing Cyrillic characters to transliterate (str or bytes)

    Returns:
        Transliterated text with Latin characters

    Examples:
        >>> translit("Привет")
        'Priviet'
        >>> translit("Hello мир")
        'Hello mir'

    Note:
        Supports Russian, Ukrainian, Bulgarian, and Serbian Cyrillic.
        Other scripts will raise an AssertionError.
    """
    # Handle byte string input (convert to str)
    if isinstance(text, bytes):
        text = text.decode('utf-8')

    output = ""
    for letter in text:
        output += romanize(letter)
    return output


# Example usage (commented out):
# def main():
#     text = "русск.: Любя, съешь щипцы, — вздохнёт мэр, — кайф жгуч."
#     print(translit(text))
#     # Output: russk.: Lyubya, s'iesh' shchiptsy, - vzdohniot mer, - kayf zhghuch.
#
#     text = "укр.: Гей, хлопці, не вспію - на ґанку ваша файна їжа знищується бурундучком."
#     print(translit(text))
#     # Output: ukr.: Ghiey, hloptsi, nie vspiyu - na ganku vasha fayna yzha znishchuiet'sya burunduchkom.
#
#     text = "болг.: Ах, чудна българска земьо, полюшквай цъфтящи жита."
#     print(translit(text))
#     # Output: bolgh.: Ah, chudna b'lgharska ziem'o, polyushkvay ts'ftyashchi zhita.
#
#     text = "серб.: Неуредне ноћне даме досађивале су Џеку К."
#     print(translit(text))
#     # Output: sierb.: Nieuriednie notshnie damie dosadjivalie su Dzhieku K.
#
# if __name__ == "__main__":
#     main()
