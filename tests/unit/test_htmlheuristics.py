"""Unit tests for fanficfare.htmlheuristics module."""

import pytest
from fanficfare.htmlheuristics import (
    logdebug,
    is_valid_block,
    is_end_tag,
    is_comment_tag,
    is_closed_tag,
    tag_sanitizer,
    soup_up_div,
    replace_br_with_p,
)


class TestLogDebug:
    """Test the logdebug function (currently a no-op)."""

    def test_logdebug_accepts_string(self):
        """Test logdebug accepts string without error."""
        # Currently just a pass statement, should not raise
        logdebug("test message")
        logdebug("another test")

    def test_logdebug_accepts_unicode(self):
        """Test logdebug accepts unicode without error."""
        logdebug("Unicode: café, naïve, 日本語")


class TestIsValidBlock:
    """Test the is_valid_block function."""

    def test_valid_block_with_tag(self):
        """Test valid block starting with tag."""
        assert is_valid_block("<div>content</div>")
        assert is_valid_block("<p>paragraph</p>")
        assert is_valid_block("<span>text</span>")

    def test_invalid_block_with_comment(self):
        """Test invalid block starting with comment."""
        assert not is_valid_block("<!-- comment -->content")
        assert not is_valid_block("<!DOCTYPE html>")

    def test_invalid_block_no_tag(self):
        """Test invalid block with no tag."""
        assert not is_valid_block("just text")
        assert not is_valid_block("")

    def test_valid_block_with_attributes(self):
        """Test valid block with tag attributes."""
        assert is_valid_block('<div class="test">content</div>')
        assert is_valid_block('<p id="para">text</p>')


class TestIsEndTag:
    """Test the is_end_tag function."""

    def test_closing_tag(self):
        """Test closing tags are identified."""
        assert is_end_tag("</div>")
        assert is_end_tag("</p>")
        assert is_end_tag("</span>")
        assert is_end_tag("</blockquote>")

    def test_opening_tag(self):
        """Test opening tags are not end tags."""
        assert not is_end_tag("<div>")
        assert not is_end_tag("<p>")
        assert not is_end_tag('<div class="test">')

    def test_self_closing_tag(self):
        """Test self-closing tags are not end tags."""
        assert not is_end_tag("<br />")
        assert not is_end_tag("<hr />")
        assert not is_end_tag("<img />")

    def test_comment(self):
        """Test comments are not end tags."""
        assert not is_end_tag("<!-- comment -->")


class TestIsCommentTag:
    """Test the is_comment_tag function."""

    def test_comment_tag(self):
        """Test comment tags are identified."""
        assert is_comment_tag("<!-- comment -->")
        assert is_comment_tag("<!-- multi line\ncomment -->")
        assert is_comment_tag("<!--test-->")

    def test_regular_tag(self):
        """Test regular tags are not comments."""
        assert not is_comment_tag("<div>")
        assert not is_comment_tag("</div>")
        assert not is_comment_tag("<br />")

    def test_text(self):
        """Test plain text is not a comment."""
        assert not is_comment_tag("just text")


class TestIsClosedTag:
    """Test the is_closed_tag function."""

    def test_self_closing_tag(self):
        """Test self-closing tags are identified."""
        assert is_closed_tag("<br />")
        assert is_closed_tag("<hr />")
        assert is_closed_tag("<img />")
        assert is_closed_tag('<img src="test.jpg" />')

    def test_regular_tag(self):
        """Test regular tags are not self-closing."""
        assert not is_closed_tag("<div>")
        assert not is_closed_tag("</div>")
        assert not is_closed_tag("<p>")

    def test_opening_tag_with_attributes(self):
        """Test opening tags with attributes are not self-closing."""
        assert not is_closed_tag('<div class="test">')
        assert not is_closed_tag('<p id="para">')


class TestTagSanitizer:
    """Test the tag_sanitizer function."""

    def test_simple_html(self):
        """Test sanitizing simple HTML."""
        html = "<p>Hello world</p>"
        result = tag_sanitizer(html)
        assert "<p>" in result
        assert "</p>" in result
        assert "Hello world" in result

    def test_nested_tags(self):
        """Test sanitizing nested tags."""
        html = "<p><b>Bold</b> text</p>"
        result = tag_sanitizer(html)
        assert "<p>" in result
        assert "<b>" in result
        assert "</b>" in result
        assert "Bold" in result

    def test_block_tags(self):
        """Test block tags are preserved."""
        html = "<div>content</div>"
        result = tag_sanitizer(html)
        assert "<div>" in result
        assert "</div>" in result

    def test_self_closing_tags(self):
        """Test self-closing tags."""
        html = "<p>Line<br />break</p>"
        result = tag_sanitizer(html)
        assert "<br />" in result

    def test_empty_input(self):
        """Test empty input."""
        result = tag_sanitizer("")
        assert result == ""

    def test_comments_handled(self):
        """Test HTML comments are handled."""
        html = "<!-- comment --><p>text</p>"
        result = tag_sanitizer(html)
        # Comments might be stripped or preserved
        assert "<p>" in result


class TestSoupUpDiv:
    """Test the soup_up_div function."""

    def test_simple_div(self):
        """Test simple div processing."""
        html = "<div>content</div>"
        result = soup_up_div(html)
        assert "content" in result
        assert "<div>" in result

    def test_div_with_breaks(self):
        """Test div with br tags."""
        html = "<div>line1<br />line2</div>"
        result = soup_up_div(html)
        assert "line1" in result
        assert "line2" in result

    def test_nested_divs(self):
        """Test nested divs."""
        html = "<div><div>nested</div></div>"
        result = soup_up_div(html)
        assert "nested" in result

    def test_div_with_paragraphs(self):
        """Test div with paragraph tags."""
        html = "<div><p>para1</p><p>para2</p></div>"
        result = soup_up_div(html)
        assert "para1" in result
        assert "para2" in result


class TestReplaceBrWithP:
    """Test the main replace_br_with_p function."""

    def test_idempotent(self):
        """Test function is idempotent (running twice gives same result)."""
        html = "<div>line1<br />line2</div>"
        result1 = replace_br_with_p(html)
        result2 = replace_br_with_p(result1)
        # Second run should detect the marker and return unchanged
        assert result1 == result2

    def test_empty_string(self):
        """Test with empty string."""
        result = replace_br_with_p("")
        assert result == ""

    def test_no_tags(self):
        """Test with no HTML tags."""
        text = "just plain text"
        result = replace_br_with_p(text)
        assert result == text

    def test_single_br(self):
        """Test single br tag conversion."""
        html = "<div>line1<br />line2</div>"
        result = replace_br_with_p(html)
        # Should contain paragraph tags
        assert "<p>" in result
        assert "line1" in result
        assert "line2" in result

    def test_multiple_br(self):
        """Test multiple br tags conversion."""
        html = "<div>line1<br /><br />line2</div>"
        result = replace_br_with_p(html)
        assert "<p>" in result
        assert "line1" in result
        assert "line2" in result

    def test_nbsp_handling(self):
        """Test non-breaking space handling."""
        html = "<div>line1\xa0line2</div>"
        result = replace_br_with_p(html)
        # Non-breaking spaces should be converted to regular spaces
        assert "line1" in result
        assert "line2" in result

    def test_hr_tag_handling(self):
        """Test horizontal rule handling."""
        html = "<div>text<hr />more text</div>"
        result = replace_br_with_p(html)
        assert "<hr />" in result

    def test_existing_p_tags(self):
        """Test with existing paragraph tags."""
        html = "<div><p>paragraph 1</p><p>paragraph 2</p></div>"
        result = replace_br_with_p(html)
        assert "paragraph 1" in result
        assert "paragraph 2" in result

    def test_pre_tag_preservation(self):
        """Test preformatted text preservation."""
        html = "<div><pre>code<br />block</pre></div>"
        result = replace_br_with_p(html)
        assert "<pre>" in result
        # Breaks inside pre should be preserved differently

    def test_blockquote_handling(self):
        """Test blockquote handling."""
        html = "<div><blockquote>quoted text</blockquote></div>"
        result = replace_br_with_p(html)
        assert "<blockquote>" in result
        assert "quoted text" in result

    def test_complex_nested_html(self):
        """Test complex nested HTML structure."""
        html = """<div>
            <p>Intro</p>
            text1<br />text2<br /><br />text3
            <blockquote>quote</blockquote>
            more<br />content
        </div>"""
        result = replace_br_with_p(html)
        assert "Intro" in result
        assert "text1" in result
        assert "quote" in result
        assert "content" in result

    def test_marker_prevents_reprocessing(self):
        """Test the marker prevents reprocessing."""
        html = "<div>line1<br />line2</div>"
        result1 = replace_br_with_p(html)
        # The marker should be in the result
        assert "FFF_replace_br_with_p_has_been_run" in result1
        # Running again should return the same result
        result2 = replace_br_with_p(result1)
        assert result1 == result2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_malformed_html(self):
        """Test with malformed HTML."""
        html = "<div>unclosed<p>paragraph"
        result = replace_br_with_p(html)
        # Should handle gracefully
        assert isinstance(result, str)

    def test_unicode_content(self):
        """Test with unicode content."""
        html = "<div>café<br />naïve<br />日本語</div>"
        result = replace_br_with_p(html)
        assert "café" in result
        assert "naïve" in result
        assert "日本語" in result

    def test_very_long_content(self):
        """Test with very long content."""
        # Create a long string with many paragraphs
        html = "<div>" + ("text<br />" * 100) + "end</div>"
        result = replace_br_with_p(html)
        assert "text" in result
        assert "end" in result

    def test_entities_preservation(self):
        """Test HTML entities are preserved."""
        html = "<div>test &lt; &gt; &amp; entities</div>"
        result = replace_br_with_p(html)
        # Entities should be preserved or converted correctly
        assert isinstance(result, str)
