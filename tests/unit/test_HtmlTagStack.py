# -*- coding: utf-8 -*-

import pytest
from fanficfare import HtmlTagStack


class TestGetEndTag:
    """Test get_end_tag function"""

    def test_simple_tag(self):
        """Convert simple opening tag to closing tag"""
        result = HtmlTagStack.get_end_tag('<div>')
        assert result == '</div>'

    def test_tag_with_attributes(self):
        """Convert tag with attributes to closing tag"""
        result = HtmlTagStack.get_end_tag('<div class="foo" id="bar">')
        assert result == '</div>'

    def test_self_closing_tag(self):
        """Handle self-closing tag"""
        result = HtmlTagStack.get_end_tag('<br />')
        assert result == '</br>'

    def test_tag_with_space_before_bracket(self):
        """Handle tag with space before closing bracket"""
        result = HtmlTagStack.get_end_tag('<div class="test" >')
        assert result == '</div>'

    def test_empty_string(self):
        """Handle empty string"""
        result = HtmlTagStack.get_end_tag('')
        assert result == ''

    def test_no_brackets(self):
        """Handle string without brackets"""
        result = HtmlTagStack.get_end_tag('div')
        assert result == ''

    def test_only_opening_bracket(self):
        """Handle string with only opening bracket"""
        result = HtmlTagStack.get_end_tag('<div')
        assert result == ''

    def test_only_closing_bracket(self):
        """Handle string with only closing bracket"""
        result = HtmlTagStack.get_end_tag('div>')
        assert result == ''

    def test_nested_brackets(self):
        """Handle tag with nested brackets (invalid HTML)"""
        result = HtmlTagStack.get_end_tag('<div<span>>')
        # Should extract the first tag name
        assert '</div' in result or '</span>' in result


class TestGetTagName:
    """Test get_tag_name function"""

    def test_simple_tag(self):
        """Extract tag name from simple tag"""
        result = HtmlTagStack.get_tag_name('<div>')
        assert result == 'div'

    def test_tag_with_attributes(self):
        """Extract tag name from tag with attributes"""
        result = HtmlTagStack.get_tag_name('<div class="foo">')
        assert result == 'div'

    def test_closing_tag(self):
        """Extract tag name from closing tag"""
        result = HtmlTagStack.get_tag_name('</div>')
        assert result == 'div'

    def test_self_closing_tag(self):
        """Extract tag name from self-closing tag"""
        result = HtmlTagStack.get_tag_name('<br />')
        assert result == 'br'

    def test_empty_string(self):
        """Handle empty string"""
        result = HtmlTagStack.get_tag_name('')
        assert result == ''

    def test_no_brackets(self):
        """Handle string without brackets"""
        result = HtmlTagStack.get_tag_name('div')
        assert result == ''


class TestStackOperations:
    """Test stack push/pop operations"""

    def setup_method(self):
        """Clear stack before each test"""
        HtmlTagStack.flush()

    def teardown_method(self):
        """Clear stack after each test"""
        HtmlTagStack.flush()

    def test_push_single_tag(self):
        """Push a single tag onto stack"""
        HtmlTagStack.push('<div>')
        assert HtmlTagStack.has_elements()
        stack = HtmlTagStack.get_stack()
        assert len(stack) == 1
        assert stack[0] == '<div>'

    def test_push_multiple_tags(self):
        """Push multiple tags onto stack"""
        HtmlTagStack.push('<div>')
        HtmlTagStack.push('<span>')
        HtmlTagStack.push('<p>')
        stack = HtmlTagStack.get_stack()
        assert len(stack) == 3
        assert stack[0] == '<div>'
        assert stack[1] == '<span>'
        assert stack[2] == '<p>'

    def test_push_empty_string(self):
        """Push empty string should not add to stack"""
        HtmlTagStack.push('')
        assert not HtmlTagStack.has_elements()

    def test_push_invalid_tag(self):
        """Push invalid tag (no brackets) should not add to stack"""
        HtmlTagStack.push('div')
        assert not HtmlTagStack.has_elements()

    def test_pop_single_tag(self):
        """Pop a single tag from stack"""
        HtmlTagStack.push('<div>')
        result = HtmlTagStack.pop()
        assert result == '<div>'
        assert not HtmlTagStack.has_elements()

    def test_pop_multiple_tags(self):
        """Pop multiple tags in LIFO order"""
        HtmlTagStack.push('<div>')
        HtmlTagStack.push('<span>')
        HtmlTagStack.push('<p>')

        assert HtmlTagStack.pop() == '<p>'
        assert HtmlTagStack.pop() == '<span>'
        assert HtmlTagStack.pop() == '<div>'
        assert not HtmlTagStack.has_elements()

    def test_pop_empty_stack(self):
        """Pop from empty stack returns empty string"""
        result = HtmlTagStack.pop()
        assert result == ''

    def test_pop_end_tag(self):
        """Pop and convert to end tag"""
        HtmlTagStack.push('<div class="test">')
        result = HtmlTagStack.pop_end_tag()
        assert result == '</div>'
        assert not HtmlTagStack.has_elements()

    def test_pop_end_tag_empty_stack(self):
        """Pop end tag from empty stack"""
        result = HtmlTagStack.pop_end_tag()
        assert result == ''


class TestSpoolOperations:
    """Test spool_end and spool_start operations"""

    def setup_method(self):
        """Clear stack before each test"""
        HtmlTagStack.flush()

    def teardown_method(self):
        """Clear stack after each test"""
        HtmlTagStack.flush()

    def test_spool_end_single_tag(self):
        """Spool end tags for single tag"""
        HtmlTagStack.push('<div>')
        result = HtmlTagStack.spool_end()
        assert result == '</div>'
        # Stack should not be modified by spool
        assert HtmlTagStack.has_elements()

    def test_spool_end_multiple_tags(self):
        """Spool end tags for multiple tags (reversed order)"""
        HtmlTagStack.push('<div>')
        HtmlTagStack.push('<span>')
        HtmlTagStack.push('<p>')
        result = HtmlTagStack.spool_end()
        # Should be in reverse order: </p></span></div>
        assert result == '</p></span></div>'
        # Stack should still have elements
        assert len(HtmlTagStack.get_stack()) == 3

    def test_spool_end_empty_stack(self):
        """Spool end from empty stack"""
        result = HtmlTagStack.spool_end()
        assert result == ''

    def test_spool_start_single_tag(self):
        """Spool start tags for single tag"""
        HtmlTagStack.push('<div>')
        result = HtmlTagStack.spool_start()
        assert result == '<div>'

    def test_spool_start_multiple_tags(self):
        """Spool start tags for multiple tags (original order)"""
        HtmlTagStack.push('<div class="outer">')
        HtmlTagStack.push('<span id="middle">')
        HtmlTagStack.push('<p>')
        result = HtmlTagStack.spool_start()
        # Should be in original order
        assert '<div class="outer">' in result
        assert '<span id="middle">' in result
        assert '<p>' in result
        assert result == '<div class="outer"><span id="middle"><p>'

    def test_spool_start_empty_stack(self):
        """Spool start from empty stack"""
        result = HtmlTagStack.spool_start()
        assert result == ''


class TestUtilityFunctions:
    """Test utility functions"""

    def setup_method(self):
        """Clear stack before each test"""
        HtmlTagStack.flush()

    def teardown_method(self):
        """Clear stack after each test"""
        HtmlTagStack.flush()

    def test_has_elements_true(self):
        """Check has_elements returns True when stack has items"""
        HtmlTagStack.push('<div>')
        assert HtmlTagStack.has_elements() is True

    def test_has_elements_false(self):
        """Check has_elements returns False when stack is empty"""
        assert HtmlTagStack.has_elements() is False

    def test_get_last_single_element(self):
        """Get last element from stack with one item"""
        HtmlTagStack.push('<div>')
        result = HtmlTagStack.get_last()
        assert result == '<div>'
        # Should not remove element
        assert HtmlTagStack.has_elements()

    def test_get_last_multiple_elements(self):
        """Get last element from stack with multiple items"""
        HtmlTagStack.push('<div>')
        HtmlTagStack.push('<span>')
        HtmlTagStack.push('<p>')
        result = HtmlTagStack.get_last()
        assert result == '<p>'
        # Stack should still have all 3 elements
        assert len(HtmlTagStack.get_stack()) == 3

    def test_get_last_empty_stack(self):
        """Get last from empty stack returns empty string"""
        result = HtmlTagStack.get_last()
        assert result == ''

    def test_flush_clears_stack(self):
        """Flush clears all elements from stack"""
        HtmlTagStack.push('<div>')
        HtmlTagStack.push('<span>')
        HtmlTagStack.push('<p>')
        assert HtmlTagStack.has_elements()

        HtmlTagStack.flush()
        assert not HtmlTagStack.has_elements()
        assert len(HtmlTagStack.get_stack()) == 0

    def test_flush_empty_stack(self):
        """Flush on empty stack doesn't cause errors"""
        HtmlTagStack.flush()  # Should not raise exception
        assert not HtmlTagStack.has_elements()

    def test_get_stack_returns_actual_stack(self):
        """get_stack returns the actual stack list"""
        HtmlTagStack.push('<div>')
        HtmlTagStack.push('<span>')
        stack = HtmlTagStack.get_stack()
        assert isinstance(stack, list)
        assert len(stack) == 2
        assert stack[0] == '<div>'
        assert stack[1] == '<span>'


class TestComplexScenarios:
    """Test complex usage scenarios"""

    def setup_method(self):
        """Clear stack before each test"""
        HtmlTagStack.flush()

    def teardown_method(self):
        """Clear stack after each test"""
        HtmlTagStack.flush()

    def test_push_pop_interleaved(self):
        """Test interleaved push and pop operations"""
        HtmlTagStack.push('<div>')
        HtmlTagStack.push('<span>')
        assert HtmlTagStack.pop() == '<span>'
        HtmlTagStack.push('<p>')
        assert HtmlTagStack.pop() == '<p>'
        assert HtmlTagStack.pop() == '<div>'
        assert not HtmlTagStack.has_elements()

    def test_spool_preserves_stack(self):
        """Verify spool operations don't modify stack"""
        HtmlTagStack.push('<div>')
        HtmlTagStack.push('<span>')

        start = HtmlTagStack.spool_start()
        end = HtmlTagStack.spool_end()

        # Stack should still have 2 elements
        assert len(HtmlTagStack.get_stack()) == 2
        assert HtmlTagStack.get_last() == '<span>'

    def test_nested_tag_scenario(self):
        """Test realistic nested tag scenario"""
        # Simulate opening nested tags
        HtmlTagStack.push('<html>')
        HtmlTagStack.push('<body>')
        HtmlTagStack.push('<div class="container">')
        HtmlTagStack.push('<p>')

        # Get all closing tags
        closing = HtmlTagStack.spool_end()
        assert closing == '</p></div></body></html>'

        # Pop tags one by one
        assert HtmlTagStack.pop_end_tag() == '</p>'
        assert HtmlTagStack.pop_end_tag() == '</div>'
        assert HtmlTagStack.pop_end_tag() == '</body>'
        assert HtmlTagStack.pop_end_tag() == '</html>'
        assert not HtmlTagStack.has_elements()

    def test_unicode_tags(self):
        """Test with unicode tag names"""
        HtmlTagStack.push('<див>')
        result = HtmlTagStack.get_tag_name('<διв>')
        # Should handle unicode in tag names
        assert len(result) > 0

    def test_tags_with_special_attributes(self):
        """Test tags with special characters in attributes"""
        tag = '<div data-value="test&quot;value" class=\'foo\'>'
        HtmlTagStack.push(tag)
        result = HtmlTagStack.pop_end_tag()
        assert result == '</div>'
