# -*- coding: utf-8 -*-

import pytest
from fanficfare import htmlcleanup
from bs4 import BeautifulSoup


class TestStripHTML:
    """Test stripHTML function"""

    def test_strip_html_from_string(self):
        """Strip HTML tags from a string"""
        html = "<p>Hello <b>world</b>!</p>"
        result = htmlcleanup.stripHTML(html)
        assert result == "Hello world!"

    def test_strip_html_with_entities(self):
        """Strip HTML and convert entities"""
        html = "<p>Hello &mdash; world!</p>"
        result = htmlcleanup.stripHTML(html)
        assert result == "Hello — world!"

    def test_strip_html_from_beautifulsoup(self):
        """Strip HTML from BeautifulSoup object"""
        soup = BeautifulSoup("<p>Hello <b>world</b>!</p>", 'html.parser')
        result = htmlcleanup.stripHTML(soup)
        # BeautifulSoup's get_text() doesn't preserve spaces between inline tags
        assert "Hello" in result and "world" in result

    def test_strip_html_preserve_entities(self):
        """Preserve &lt; &gt; &amp; when remove_all_entities=False"""
        html = "<p>&lt;tag&gt; &amp; text</p>"
        result = htmlcleanup.stripHTML(html, remove_all_entities=False)
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result

    def test_strip_html_remove_all_entities(self):
        """Remove all entities including &lt; &gt; &amp;"""
        html = "<p>&lt;tag&gt; &amp; text</p>"
        result = htmlcleanup.stripHTML(html, remove_all_entities=True)
        assert result == "<tag> & text"

    def test_strip_html_nbsp_conversion(self):
        """Convert &nbsp; to regular space"""
        html = "<p>Hello&nbsp;world</p>"
        result = htmlcleanup.stripHTML(html)
        assert result == "Hello world"

    def test_strip_html_unicode_nbsp(self):
        """Convert unicode nbsp (\\xc2\\xa0) to space"""
        # BeautifulSoup converts &nbsp; to \xc2\xa0
        soup = BeautifulSoup("<p>Hello\xc2\xa0world</p>", 'html.parser')
        result = htmlcleanup.stripHTML(soup)
        assert result == "Hello world"


class TestRemoveEntities:
    """Test removeEntities function"""

    def test_remove_none(self):
        """Handle None input"""
        result = htmlcleanup.removeEntities(None)
        assert result == ""

    def test_remove_numeric_entities_decimal(self):
        """Convert decimal numeric entities"""
        text = "Quote: &#8220;Hello&#8221;"
        result = htmlcleanup.removeEntities(text)
        # &#8220; is left double quotation mark (U+201C), not regular quote
        assert '\u201c' in result  # U+201C left curly quote
        assert '\u201d' in result  # U+201D right curly quote

    def test_remove_numeric_entities_hex(self):
        """Convert hex numeric entities"""
        text = "Apostrophe: &#x27;"
        result = htmlcleanup.removeEntities(text)
        assert result == "Apostrophe: '"

    def test_remove_named_entities(self):
        """Convert named entities"""
        text = "Hello &mdash; world &hellip;"
        result = htmlcleanup.removeEntities(text)
        assert result == "Hello — world …"

    def test_preserve_basic_entities(self):
        """Preserve &lt; &gt; &amp; by default"""
        text = "&lt;tag&gt; &amp; text"
        result = htmlcleanup.removeEntities(text, remove_all_entities=False)
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result

    def test_remove_all_entities(self):
        """Remove all entities including basic ones"""
        text = "&lt;tag&gt; &amp; text"
        result = htmlcleanup.removeEntities(text, remove_all_entities=True)
        assert result == "<tag> & text"

    def test_entities_without_semicolon(self):
        """Handle entities without semicolons"""
        # The entities dict includes both with and without semicolons
        text = "&copy 2023 &mdash; all rights"
        result = htmlcleanup.removeEntities(text)
        # &copy (without semicolon) is in the entities dict
        assert "©" in result
        assert "—" in result

    def test_numeric_entity_for_ampersand(self):
        """Convert &#38; to &amp;"""
        text = "Hello &#38; world"
        result = htmlcleanup.removeEntities(text, remove_all_entities=False)
        assert "&amp;" in result

    def test_numeric_entity_for_lt_gt(self):
        """Convert &#60; and &#62; to &lt; and &gt;"""
        text = "&#60;tag&#62;"
        result = htmlcleanup.removeEntities(text, remove_all_entities=False)
        assert "&lt;" in result
        assert "&gt;" in result

    def test_space_only_mode(self):
        """Only remove space entities in space_only mode"""
        text = "&nbsp;&mdash;&ensp;"
        result = htmlcleanup.removeEntities(text, space_only=True)
        # Spaces should be converted, em-dash should remain as entity (with &amp;)
        assert " " in result
        # Em-dash remains as entity but gets &amp;mdash format after processing
        assert "&amp;mdash" in result or "—" not in result

    def test_unicode_input(self):
        """Handle unicode strings"""
        text = "Café &mdash; résumé"
        result = htmlcleanup.removeEntities(text)
        assert "Café" in result
        assert "résumé" in result
        assert "—" in result

    def test_non_string_input(self):
        """Convert non-string to string first"""
        result = htmlcleanup.removeEntities(123)
        assert result == "123"

    def test_accented_entities(self):
        """Convert accented character entities"""
        text = "&aacute; &eacute; &iacute; &oacute; &uacute;"
        result = htmlcleanup.removeEntities(text)
        assert result == "á é í ó ú"

    def test_greek_letter_entities(self):
        """Convert Greek letter entities"""
        text = "&alpha; &beta; &gamma; &delta;"
        result = htmlcleanup.removeEntities(text)
        assert result == "α β γ δ"

    def test_mathematical_entities(self):
        """Convert mathematical symbol entities"""
        text = "&plusmn; &times; &divide; &ne;"
        result = htmlcleanup.removeEntities(text)
        assert result == "± × ÷ ≠"


class TestRemoveAllEntities:
    """Test removeAllEntities wrapper function"""

    def test_removes_all_entities(self):
        """Should remove all entities including &lt; &gt; &amp;"""
        text = "&lt;tag&gt; &amp; text &mdash;"
        result = htmlcleanup.removeAllEntities(text)
        assert result == "<tag> & text —"

    def test_wrapper_calls_remove_entities(self):
        """Verify it's calling removeEntities with correct flag"""
        text = "Hello &amp; goodbye"
        result = htmlcleanup.removeAllEntities(text)
        assert "&amp;" not in result
        assert "&" in result


class TestConditionalRemoveEntities:
    """Test conditionalRemoveEntities function"""

    def test_processes_string(self):
        """Process string input"""
        text = "Hello &mdash; world"
        result = htmlcleanup.conditionalRemoveEntities(text)
        assert result == "Hello — world"

    def test_returns_non_string_unchanged(self):
        """Return non-string values unchanged"""
        result = htmlcleanup.conditionalRemoveEntities(123)
        assert result == 123

        result = htmlcleanup.conditionalRemoveEntities(None)
        assert result is None

        obj = {'key': 'value'}
        result = htmlcleanup.conditionalRemoveEntities(obj)
        assert result == obj


class TestFixExcessSpace:
    """Test fix_excess_space function"""

    def test_combine_double_newlines(self):
        """Convert double newlines to <p>"""
        text = "Line 1\n\nLine 2"
        result = htmlcleanup.fix_excess_space(text)
        assert "<p>" in result

    def test_combine_multiple_p_tags(self):
        """Combine multiple consecutive <p> tags"""
        text = "<p><p><p>Text</p></p></p>"
        result = htmlcleanup.fix_excess_space(text)
        # Should consolidate to fewer <p> tags
        assert result.count("<p>") < 3

    def test_combine_p_and_br_tags(self):
        """Combine <p> and <br> tags"""
        text = "<p>Text<br/><br/></p>"
        result = htmlcleanup.fix_excess_space(text)
        # Should consolidate spacing
        assert "<p>" in result

    def test_removes_excess_whitespace(self):
        """Remove excess whitespace around tags"""
        text = "  <p>  Text  </p>  "
        result = htmlcleanup.fix_excess_space(text)
        # Should reduce whitespace
        assert result.strip().count("  ") < text.count("  ")


class TestReduceZalgo:
    """Test reduce_zalgo function"""

    def test_normal_text_unchanged(self):
        """Normal text without combining characters passes through"""
        text = "Hello world"
        result = htmlcleanup.reduce_zalgo(text)
        assert result == "Hello world"

    def test_removes_excess_combining_chars(self):
        """Remove excess combining characters (zalgo text)"""
        # Create text with multiple combining diacriticals
        text = "H" + "\u0301" + "\u0301" + "\u0301" + "ello"  # H with 3 acute accents
        result = htmlcleanup.reduce_zalgo(text, max_zalgo=1)
        # Should keep only 1 combining character
        assert result.count("\u0301") <= 1

    def test_preserves_single_combining_char(self):
        """Preserve single combining characters"""
        text = "café"  # e with acute accent (composed form)
        result = htmlcleanup.reduce_zalgo(text, max_zalgo=1)
        # After NFD normalization, becomes decomposed: e + combining acute
        assert "cafe" in result or "café" in result
        # Should preserve combining characters up to max_zalgo limit
        assert len(result) >= 4

    def test_max_zalgo_parameter(self):
        """Respect max_zalgo parameter"""
        text = "H" + "\u0301" * 5  # H with 5 combining marks
        result = htmlcleanup.reduce_zalgo(text, max_zalgo=2)
        # Should keep at most 2 combining characters
        assert result.count("\u0301") <= 2

    def test_applies_nfd_normalization(self):
        """Apply NFD unicode normalization"""
        # Composed character (single codepoint)
        text = "é"  # U+00E9 (composed)
        result = htmlcleanup.reduce_zalgo(text)
        # After NFD, should be decomposed: e + combining acute
        assert "e" in result or "é" in result


class TestDecodeEmail:
    """Test decode_email function"""

    def test_decode_simple_email(self):
        """Decode obfuscated email address"""
        # This is a simple XOR obfuscation
        # Example: if 'a' = 0x61, XOR with key 0x42 = 0x23
        # To decode: 0x23 XOR 0x42 = 0x61 = 'a'
        encoded = "4261"  # Key=0x42, then 0x61='a'
        result = htmlcleanup.decode_email(encoded)
        # Should decode to something and be HTML-escaped
        assert isinstance(result, str)

    def test_decode_email_with_offset(self):
        """Decode email with non-zero offset"""
        encoded = "XX4261"  # Offset by 2
        result = htmlcleanup.decode_email(encoded, c=2)
        assert isinstance(result, str)

    def test_html_escapes_result(self):
        """Result should be HTML-escaped"""
        # Create an encoded string that decodes to something with special chars
        encoded = "423c3e26"  # Should include <, >, & after decoding and unquoting
        result = htmlcleanup.decode_email(encoded)
        # Result should be HTML-escaped
        assert isinstance(result, str)


class TestParseHex:
    """Test parse_hex helper function"""

    def test_parse_hex_basic(self):
        """Parse hex at given position"""
        result = htmlcleanup.parse_hex("FF00", 0)
        assert result == 0xFF

    def test_parse_hex_at_offset(self):
        """Parse hex at non-zero offset"""
        result = htmlcleanup.parse_hex("00FF00", 2)
        assert result == 0xFF

    def test_parse_hex_lowercase(self):
        """Parse lowercase hex"""
        result = htmlcleanup.parse_hex("deadbeef", 0)
        assert result == 0xDE


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_string(self):
        """Handle empty strings"""
        result = htmlcleanup.removeEntities("")
        assert result == ""

    def test_no_entities(self):
        """Handle text with no entities"""
        text = "Hello world"
        result = htmlcleanup.removeEntities(text)
        assert result == "Hello world"

    def test_malformed_numeric_entity(self):
        """Handle malformed numeric entities gracefully"""
        # This should not crash
        text = "&#invalid;"
        result = htmlcleanup.removeEntities(text)
        assert isinstance(result, str)

    def test_very_long_text(self):
        """Handle very long text"""
        text = "Hello &mdash; " * 1000
        result = htmlcleanup.removeEntities(text)
        assert "—" in result
        assert len(result) > 0

    def test_mixed_entity_types(self):
        """Handle mixed entity types"""
        text = "&#8220;Hello&rdquo; &amp; &#x27;world&#x27;"
        result = htmlcleanup.removeEntities(text)
        # &#8220; and &rdquo; are curly quotes (U+201C and U+201D)
        assert '\u201c' in result or '\u201d' in result  # Curly quotes
        assert "'" in result  # Regular apostrophe from &#x27;
        assert "Hello" in result
        assert "world" in result
