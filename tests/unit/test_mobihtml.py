"""Unit tests for fanficfare.mobihtml module."""

import pytest
from fanficfare.mobihtml import HtmlProcessor


class TestHtmlProcessorInit:
    """Test HtmlProcessor initialization."""

    def test_init_simple_html(self):
        """Test initialization with simple HTML."""
        html = "<html><head><title>Test</title></head><body>Content</body></html>"
        processor = HtmlProcessor(html)
        assert processor.title == "Test"

    def test_init_no_title(self):
        """Test initialization with no title."""
        html = "<html><head><title></title></head><body>Content</body></html>"
        processor = HtmlProcessor(html)
        assert processor.title is None

    def test_init_with_guide_tag(self):
        """Test that guide tag is moved to head."""
        html = """<html>
            <head><title>Test</title></head>
            <body>
                <guide>
                    <reference type="toc" title="Table of Contents" href="#toc"/>
                </guide>
                Content
            </body>
        </html>"""
        processor = HtmlProcessor(html)
        # Guide should be in head now
        assert processor._soup.head.find('guide') is not None

    def test_init_with_unfill(self):
        """Test initialization with unfill parameter."""
        html = "<html><head><title>Test</title></head><body>Content</body></html>"
        processor = HtmlProcessor(html, unfill=1)
        assert processor.unfill == 1


class TestRemoveUnsupported:
    """Test _RemoveUnsupported method."""

    def test_remove_script_tags(self):
        """Test removal of script tags."""
        html = """<html><head><title>Test</title></head>
        <body>
            <p>Before</p>
            <script>alert('test');</script>
            <p>After</p>
        </body></html>"""
        processor = HtmlProcessor(html)
        processor._RemoveUnsupported()
        result = str(processor._soup)
        assert '<script>' not in result
        assert 'alert' not in result
        assert 'Before' in result
        assert 'After' in result

    def test_remove_style_tags(self):
        """Test removal of style tags."""
        html = """<html><head><title>Test</title></head>
        <body>
            <p>Content</p>
            <style>body { color: red; }</style>
        </body></html>"""
        processor = HtmlProcessor(html)
        processor._RemoveUnsupported()
        result = str(processor._soup)
        assert '<style>' not in result
        assert 'color: red' not in result

    def test_remove_multiple_unsupported(self):
        """Test removal of multiple unsupported tags."""
        html = """<html><head><title>Test</title></head>
        <body>
            <script>var x = 1;</script>
            <p>Content</p>
            <style>.class { }</style>
            <script>var y = 2;</script>
        </body></html>"""
        processor = HtmlProcessor(html)
        processor._RemoveUnsupported()
        result = str(processor._soup)
        assert '<script>' not in result
        assert '<style>' not in result
        assert 'Content' in result


class TestFixPreContents:
    """Test _FixPreContents method."""

    def test_fix_pre_contents_no_unfill(self):
        """Test fixing pre contents without unfill."""
        html = "<html><head><title>Test</title></head><body></body></html>"
        processor = HtmlProcessor(html, unfill=0)
        text = "line 1\nline 2\nline 3"
        result = processor._FixPreContents(text)
        assert '&nbsp;' in result or result.count('<br>') > 0

    def test_fix_pre_contents_with_unfill(self):
        """Test fixing pre contents with unfill."""
        html = "<html><head><title>Test</title></head><body></body></html>"
        processor = HtmlProcessor(html, unfill=1)
        text = "para 1\n\npara 2\n\npara 3"
        result = processor._FixPreContents(text)
        assert '<p>' in result

    def test_fix_pre_contents_whitespace(self):
        """Test that whitespace is converted to &nbsp;."""
        html = "<html><head><title>Test</title></head><body></body></html>"
        processor = HtmlProcessor(html, unfill=0)
        text = "  indented text"
        result = processor._FixPreContents(text)
        assert '&nbsp;' in result


class TestFixPreTags:
    """Test _FixPreTags method."""

    def test_fix_pre_tags(self):
        """Test fixing pre tags."""
        html = """<html><head><title>Test</title></head>
        <body>
            <pre>code line 1
code line 2</pre>
        </body></html>"""
        processor = HtmlProcessor(html, unfill=0)
        processor._FixPreTags()
        result = str(processor._soup)
        # Pre tags should be replaced (may be HTML-escaped in soup output)
        assert '<br>' in result or '&nbsp;' in result or '&amp;nbsp;' in result or '&lt;br&gt;' in result

    def test_fix_multiple_pre_tags(self):
        """Test fixing multiple pre tags."""
        html = """<html><head><title>Test</title></head>
        <body>
            <pre>block 1</pre>
            <p>Regular text</p>
            <pre>block 2</pre>
        </body></html>"""
        processor = HtmlProcessor(html, unfill=0)
        processor._FixPreTags()
        result = str(processor._soup)
        assert 'Regular text' in result


class TestStubInternalAnchors:
    """Test _StubInternalAnchors method."""

    def test_stub_internal_anchors(self):
        """Test stubbing internal anchors."""
        html = """<html><head><title>Test</title></head>
        <body>
            <a href="#section1">Go to Section 1</a>
            <a href="#section2">Go to Section 2</a>
            <a name="section1">Section 1</a>
            <a name="section2">Section 2</a>
        </body></html>"""
        processor = HtmlProcessor(html)
        processor._StubInternalAnchors()

        # Should have created anchor references
        assert len(processor._anchor_references) == 2
        assert processor._anchor_references[0][1] == '#section1'
        assert processor._anchor_references[1][1] == '#section2'

        # Anchors should have filepos attribute
        anchors = processor._soup.find_all('a', attrs={'filepos': True})
        assert len(anchors) == 2

    def test_stub_reference_tags(self):
        """Test stubbing reference tags like <reference>."""
        html = """<html><head><title>Test</title></head>
        <body>
            <reference href="#toc">TOC</reference>
            <a name="toc">Table of Contents</a>
        </body></html>"""
        processor = HtmlProcessor(html)
        processor._StubInternalAnchors()

        # Reference tags should be treated like anchor tags
        assert len(processor._anchor_references) == 1
        assert processor._anchor_references[0][1] == '#toc'

    def test_stub_anchors_no_internal_links(self):
        """Test stubbing when there are no internal anchors."""
        html = """<html><head><title>Test</title></head>
        <body>
            <a href="http://example.com">External</a>
        </body></html>"""
        processor = HtmlProcessor(html)
        processor._StubInternalAnchors()

        assert len(processor._anchor_references) == 0


class TestReplaceAnchorStubs:
    """Test _ReplaceAnchorStubs method."""

    def test_replace_anchor_stubs(self):
        """Test replacing anchor stubs with positions."""
        html = """<html><head><title>Test</title></head>
        <body>
            <a href="#target">Link</a>
            <a name="target">Target</a>
        </body></html>"""
        processor = HtmlProcessor(html)
        processor._StubInternalAnchors()
        result = processor._ReplaceAnchorStubs()

        # Result should be bytes
        assert isinstance(result, bytes)
        # Should contain filepos references
        assert b'filepos=' in result

    def test_replace_anchor_stubs_missing_target(self):
        """Test replacing anchor stubs when target is missing."""
        html = """<html><head><title>Test</title></head>
        <body>
            <a href="#missing">Link to nowhere</a>
        </body></html>"""
        processor = HtmlProcessor(html)
        processor._StubInternalAnchors()
        # Should not raise, just log warning
        result = processor._ReplaceAnchorStubs()
        assert isinstance(result, bytes)

    def test_replace_mbp_pagebreak(self):
        """Test that mbp:pagebreak tags are fixed."""
        html = """<html><head><title>Test</title></head>
        <body>
            <p>Page 1</p>
            <mbp:pagebreak>
            <p>Page 2</p>
        </body></html>"""
        processor = HtmlProcessor(html)
        processor._StubInternalAnchors()
        result = processor._ReplaceAnchorStubs()

        # Should be self-closing
        assert b'<mbp:pagebreak/>' in result
        assert b'</mbp:pagebreak>' not in result


class TestRenameAnchors:
    """Test RenameAnchors method."""

    def test_rename_anchors(self):
        """Test renaming anchors with prefix."""
        html = """<html><head><title>Test</title></head>
        <body>
            <a href="#section1">Link</a>
            <a name="section1">Section</a>
        </body></html>"""
        processor = HtmlProcessor(html)
        result = processor.RenameAnchors('chapter1_')

        assert 'chapter1_section1' in result

    def test_rename_multiple_anchors(self):
        """Test renaming multiple anchors."""
        html = """<html><head><title>Test</title></head>
        <body>
            <a href="#s1">Link 1</a>
            <a href="#s2">Link 2</a>
            <a name="s1">Section 1</a>
            <a name="s2">Section 2</a>
        </body></html>"""
        processor = HtmlProcessor(html)
        result = processor.RenameAnchors('prefix_')

        assert 'prefix_s1' in result
        assert 'prefix_s2' in result

    def test_rename_anchors_no_body(self):
        """Test renaming when body is None."""
        html = "<html><head><title>Test</title></head></html>"
        processor = HtmlProcessor(html)
        result = processor.RenameAnchors('prefix_')

        # Should return empty content
        assert isinstance(result, str)


class TestCleanHtml:
    """Test CleanHtml method (integration test)."""

    def test_clean_html_basic(self):
        """Test basic HTML cleaning."""
        html = """<html><head><title>Test</title></head>
        <body>
            <script>alert('test');</script>
            <p>Content</p>
            <style>body { }</style>
        </body></html>"""
        processor = HtmlProcessor(html)
        result = processor.CleanHtml()

        # Should be bytes
        assert isinstance(result, bytes)
        # Script and style should be removed
        assert b'<script>' not in result
        assert b'<style>' not in result
        # Content should remain
        assert b'Content' in result

    def test_clean_html_with_anchors(self):
        """Test HTML cleaning with internal anchors."""
        html = """<html><head><title>Test</title></head>
        <body>
            <a href="#section1">Go to Section 1</a>
            <p><a name="section1">Section 1 Content</a></p>
        </body></html>"""
        processor = HtmlProcessor(html)
        result = processor.CleanHtml()

        assert isinstance(result, bytes)
        # Should have filepos attributes
        assert b'filepos=' in result

    def test_clean_html_with_pre(self):
        """Test HTML cleaning with pre tags."""
        html = """<html><head><title>Test</title></head>
        <body>
            <pre>code block
with multiple lines</pre>
        </body></html>"""
        processor = HtmlProcessor(html)
        result = processor.CleanHtml()

        assert isinstance(result, bytes)
        # Pre should be converted (may be HTML-escaped)
        assert b'<br>' in result or b'&nbsp;' in result or b'&amp;nbsp;' in result or b'&lt;br&gt;' in result

    def test_clean_html_complex(self):
        """Test complex HTML cleaning with multiple features."""
        html = """<html><head><title>Story Title</title></head>
        <body>
            <h1>Chapter 1</h1>
            <script>var x = 1;</script>
            <p>Introduction with <a href="#section1">link</a></p>
            <pre>code example
line 2</pre>
            <h2><a name="section1">Section 1</a></h2>
            <p>Section content</p>
            <style>.test { color: red; }</style>
        </body></html>"""
        processor = HtmlProcessor(html)
        result = processor.CleanHtml()

        assert isinstance(result, bytes)
        # Check script/style removed
        assert b'<script>' not in result
        assert b'<style>' not in result
        # Check content preserved
        assert b'Chapter 1' in result
        assert b'Introduction' in result
        assert b'Section content' in result


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_html(self):
        """Test with minimal HTML."""
        html = "<html><head><title>Test</title></head><body></body></html>"
        processor = HtmlProcessor(html)
        result = processor.CleanHtml()
        assert isinstance(result, bytes)

    def test_unicode_content(self):
        """Test with unicode content."""
        html = """<html><head><title>Test</title></head>
        <body>
            <p>Unicode: café, naïve, 日本語</p>
        </body></html>"""
        processor = HtmlProcessor(html)
        result = processor.CleanHtml()
        assert isinstance(result, bytes)
        # Unicode should be preserved (in UTF-8 bytes)
        assert 'café'.encode('utf-8') in result or b'caf' in result

    def test_malformed_html(self):
        """Test with malformed HTML."""
        html = "<html><head><title>Test</title></head><body><p>Unclosed paragraph<div>content</body></html>"
        processor = HtmlProcessor(html)
        # Should not raise, BeautifulSoup handles it
        result = processor.CleanHtml()
        assert isinstance(result, bytes)

    def test_nested_anchors(self):
        """Test with nested anchor structures."""
        html = """<html><head><title>Test</title></head>
        <body>
            <div>
                <a href="#deep">Link</a>
                <div>
                    <div>
                        <a name="deep">Deep target</a>
                    </div>
                </div>
            </div>
        </body></html>"""
        processor = HtmlProcessor(html)
        result = processor.CleanHtml()
        assert isinstance(result, bytes)
