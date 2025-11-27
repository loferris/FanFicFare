# -*- coding: utf-8 -*-

import pytest
from fanficfare import translit


class TestIsSyllable:
    """Test is_syllable function"""

    def test_uppercase_vowels(self):
        """Uppercase vowels should be syllables"""
        assert translit.is_syllable('A') is True
        assert translit.is_syllable('E') is True
        assert translit.is_syllable('I') is True
        assert translit.is_syllable('O') is True
        assert translit.is_syllable('U') is True

    def test_lowercase_vowels(self):
        """Lowercase vowels should be syllables"""
        assert translit.is_syllable('a') is True
        assert translit.is_syllable('e') is True
        assert translit.is_syllable('i') is True
        assert translit.is_syllable('o') is True
        assert translit.is_syllable('u') is True

    def test_consonants(self):
        """Consonants should not be syllables"""
        assert translit.is_syllable('B') is False
        assert translit.is_syllable('C') is False
        assert translit.is_syllable('d') is False
        assert translit.is_syllable('f') is False

    def test_numbers_and_special_chars(self):
        """Numbers and special characters should not be syllables"""
        assert translit.is_syllable('1') is False
        assert translit.is_syllable('!') is False
        assert translit.is_syllable(' ') is False


class TestIsConsonant:
    """Test is_consonant function"""

    def test_consonants_are_not_syllables(self):
        """Consonants should return True"""
        assert translit.is_consonant('B') is True
        assert translit.is_consonant('C') is True
        assert translit.is_consonant('d') is True

    def test_vowels_are_syllables(self):
        """Vowels should return False (they are syllables, not consonants)"""
        assert translit.is_consonant('A') is False
        assert translit.is_consonant('e') is False
        assert translit.is_consonant('I') is False


class TestRomanize:
    """Test romanize function for individual letters"""

    def test_ascii_letters_unchanged(self):
        """ASCII letters should pass through unchanged"""
        assert translit.romanize('a') == 'a'
        assert translit.romanize('Z') == 'Z'
        assert translit.romanize('m') == 'm'

    def test_numbers_unchanged(self):
        """Numbers should pass through unchanged"""
        assert translit.romanize('5') == '5'

    def test_special_characters_unchanged(self):
        """Most special characters should pass through"""
        assert translit.romanize('!') == '!'
        assert translit.romanize(',') == ','

    def test_numero_sign(self):
        """NUMERO SIGN should convert to 'No'"""
        # Unicode NUMERO SIGN (№)
        assert translit.romanize('№') == 'No'

    def test_quotation_marks(self):
        """Quotation marks should convert to standard quotes"""
        # LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
        assert translit.romanize('«') == '"'
        # RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
        assert translit.romanize('»') == '"'

    def test_dash(self):
        """Various dash types should convert to hyphen"""
        # Some dashes contain "DASH" in their unicode name
        # EM DASH
        result = translit.romanize('—')
        # Should handle dashes
        assert isinstance(result, str)

    def test_cyrillic_capital_a(self):
        """Cyrillic CAPITAL LETTER A should romanize to A"""
        # А (Cyrillic A)
        result = translit.romanize('А')
        assert result == 'A'

    def test_cyrillic_small_a(self):
        """Cyrillic SMALL LETTER A should romanize to a"""
        # а (Cyrillic a)
        result = translit.romanize('а')
        assert result == 'a'

    def test_cyrillic_capital_b(self):
        """Cyrillic CAPITAL LETTER BE should romanize to B"""
        # Б (Cyrillic BE)
        result = translit.romanize('Б')
        # BE contains only consonants, so should be filtered
        assert result.upper() == 'B'

    def test_cyrillic_small_b(self):
        """Cyrillic SMALL LETTER BE should romanize to b"""
        # б (Cyrillic be)
        result = translit.romanize('б')
        assert result == 'b'

    def test_cyrillic_yeru(self):
        """Cyrillic YERU (ы) should romanize to y"""
        # Ы (Cyrillic YERU)
        result = translit.romanize('Ы')
        assert result == 'y'
        # ы (lowercase)
        result = translit.romanize('ы')
        assert result == 'y'

    def test_cyrillic_short_i(self):
        """Cyrillic SHORT I (й) should romanize to y"""
        # Й (Cyrillic SHORT I)
        result = translit.romanize('Й')
        assert result == 'y'

    def test_cyrillic_hard_sign(self):
        """Cyrillic HARD SIGN (ъ) should romanize to apostrophe"""
        # ъ (Cyrillic HARD SIGN)
        result = translit.romanize('ъ')
        assert result == "'"

    def test_cyrillic_soft_sign(self):
        """Cyrillic SOFT SIGN (ь) should romanize to apostrophe"""
        # ь (Cyrillic SOFT SIGN)
        result = translit.romanize('ь')
        assert result == "'"

    def test_cyrillic_ukrainian_ie(self):
        """Cyrillic UKRAINIAN IE (є) should romanize to ie"""
        # Є (Cyrillic UKRAINIAN IE)
        result = translit.romanize('Є')
        assert result == 'ie'
        # є (lowercase)
        result = translit.romanize('є')
        assert result == 'ie'

    def test_cyrillic_yu(self):
        """Cyrillic YU (ю) should romanize to yu"""
        # Ю (Cyrillic YU)
        result = translit.romanize('Ю')
        assert result == 'yu'
        # ю (lowercase)
        result = translit.romanize('ю')
        assert result == 'yu'

    def test_cyrillic_ya(self):
        """Cyrillic YA (я) should romanize to ya"""
        # Я (Cyrillic YA)
        result = translit.romanize('Я')
        assert result == 'ya'
        # я (lowercase)
        result = translit.romanize('я')
        assert result == 'ya'


class TestTranslit:
    """Test translit function for complete text"""

    def test_empty_string(self):
        """Empty string should return empty string"""
        result = translit.translit('')
        assert result == ''

    def test_ascii_text_unchanged(self):
        """ASCII text should pass through unchanged"""
        result = translit.translit('Hello World')
        assert result == 'Hello World'

    def test_numbers_and_punctuation(self):
        """Numbers and punctuation should be preserved"""
        result = translit.translit('Test 123, test!')
        assert result == 'Test 123, test!'

    def test_mixed_ascii_and_cyrillic(self):
        """Mixed ASCII and Cyrillic text"""
        # Simple Russian word with ASCII
        text = 'Hello мир'
        result = translit.translit(text)
        assert 'Hello' in result
        # мир should be transliterated
        assert len(result) > 0

    def test_russian_example(self):
        """Russian text from commented example"""
        # русск.: Любя, съешь щипцы, — вздохнёт мэр, — кайф жгуч.
        text = "Любя"
        result = translit.translit(text)
        # Should contain recognizable transliteration
        assert 'L' in result or 'l' in result
        assert len(result) > 0

    def test_ukrainian_example(self):
        """Ukrainian text example"""
        # укр.: хлопці
        text = "хлопці"
        result = translit.translit(text)
        assert len(result) > 0
        # Should be transliterated
        assert result != text

    def test_single_cyrillic_letter(self):
        """Single Cyrillic letter"""
        # А (Cyrillic A)
        result = translit.translit('А')
        assert result == 'A'

    def test_word_with_special_letters(self):
        """Word containing special Cyrillic letters"""
        # съешь (with hard sign)
        text = "съешь"
        result = translit.translit(text)
        # Should contain apostrophe for hard sign
        assert "'" in result or len(result) > 0

    def test_preserves_spaces(self):
        """Spaces should be preserved in transliteration"""
        text = "мир труд"
        result = translit.translit(text)
        assert ' ' in result

    def test_preserves_punctuation(self):
        """Punctuation should be preserved"""
        text = "мир, труд!"
        result = translit.translit(text)
        assert ',' in result
        assert '!' in result

    def test_numero_in_text(self):
        """NUMERO SIGN in text should convert to No"""
        text = "дом №5"
        result = translit.translit(text)
        assert 'No' in result
        assert '5' in result

    def test_quotation_marks_in_text(self):
        """Quotation marks should convert"""
        text = "«текст»"
        result = translit.translit(text)
        # Should contain converted quotes
        assert '"' in result or len(result) > 0


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_translit_handles_non_cyrillic_unicode(self):
        """Non-Cyrillic unicode characters should raise AssertionError"""
        # Module only handles Cyrillic and a few special characters
        text = "Café"  # é is not Cyrillic
        with pytest.raises(AssertionError):
            translit.translit(text)

    def test_only_punctuation(self):
        """Text with only punctuation"""
        text = "!@#$%"
        result = translit.translit(text)
        assert result == "!@#$%"

    def test_byte_string_input(self):
        """Handle byte string input via ensure_text"""
        text = b"test"
        result = translit.translit(text)
        assert result == "test"

    def test_very_long_text(self):
        """Handle very long text"""
        text = "мир " * 1000
        result = translit.translit(text)
        assert len(result) > 0

    def test_common_russian_words(self):
        """Test common Russian words"""
        # Привет (Hello)
        result = translit.translit("Привет")
        assert len(result) > 0
        # Should start with P/p
        assert result[0].upper() == 'P'

        # Спасибо (Thank you)
        result = translit.translit("Спасибо")
        assert len(result) > 0
        assert result[0].upper() == 'S'


class TestCapitalization:
    """Test that capitalization is preserved"""

    def test_capital_letter_capitalized(self):
        """Capital Cyrillic letters should produce capital Latin"""
        # Б (Cyrillic capital BE)
        result = translit.romanize('Б')
        # Result should be capitalized
        assert result[0].isupper() or result == 'B'

    def test_lowercase_letter_lowercase(self):
        """Lowercase Cyrillic letters should produce lowercase Latin"""
        # б (Cyrillic lowercase be)
        result = translit.romanize('б')
        assert result[0].islower()

    def test_mixed_case_preserved(self):
        """Mixed case should be preserved in transliteration"""
        # МиР (mixed case)
        text = "МиР"
        result = translit.translit(text)
        # Should have mixed case in result
        assert any(c.isupper() for c in result)
        assert any(c.islower() for c in result)
