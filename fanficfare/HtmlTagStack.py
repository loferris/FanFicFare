"""HTML tag stack for managing nested tag structure.

This module provides a global stack for tracking HTML tag nesting, useful
for ensuring proper tag closing when processing HTML content.
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

import re
from typing import List

# Global stack for HTML tags
stack: List[str] = []


def get_end_tag(tag: str) -> str:
    """Extract closing tag from an opening HTML tag.

    Args:
        tag: Opening HTML tag (e.g., "<div class='foo'>")

    Returns:
        Corresponding closing tag (e.g., "</div>") or empty string if invalid

    Examples:
        >>> get_end_tag('<div class="test">')
        '</div>'
        >>> get_end_tag('<br />')
        '</br>'
    """
    if len(tag) > 0 and tag.find('<') > -1 and tag.rfind('>') > -1:
        return re.sub(r'.*<([^\ >]+).*', r'</\1>', tag)
    return ''


def get_tag_name(tag: str) -> str:
    """Extract tag name from an HTML tag.

    Args:
        tag: HTML tag (opening or closing)

    Returns:
        Tag name without brackets and attributes, or empty string if invalid

    Examples:
        >>> get_tag_name('<div class="test">')
        'div'
        >>> get_tag_name('</span>')
        'span'
    """
    if len(tag) > 0 and tag.find('<') > -1 and tag.rfind('>') > -1:
        return re.sub(r'</*([^\ >]+).*', r'\1', tag)
    return ''


def push(tag: str) -> None:
    """Push an HTML tag onto the stack.

    Args:
        tag: HTML tag to push (must contain < and >)

    Note:
        Only valid HTML tags (containing < and >) are pushed.
        Invalid tags are silently ignored.
    """
    if len(tag) > 0 and tag.find('<') > -1 and tag.rfind('>') > -1:
        stack.append(tag)


def pop() -> str:
    """Pop and return the most recent HTML tag from the stack.

    Returns:
        Most recently pushed tag, or empty string if stack is empty

    Examples:
        >>> push('<div>')
        >>> pop()
        '<div>'
    """
    if len(stack) > 0:
        return stack.pop()
    return ''


def pop_end_tag() -> str:
    """Pop the most recent tag and return its closing tag.

    Returns:
        Closing tag for the most recently pushed tag, or empty string

    Examples:
        >>> push('<div class="test">')
        >>> pop_end_tag()
        '</div>'
    """
    return str(get_end_tag(pop()))


def spool_end() -> str:
    """Generate closing tags for all tags on the stack (in reverse order).

    Returns:
        String of closing tags from most recent to oldest

    Note:
        Does not modify the stack.

    Examples:
        >>> push('<div>')
        >>> push('<span>')
        >>> spool_end()
        '</span></div>'
    """
    html = ''
    for tag in reversed(stack):
        html += get_end_tag(tag)
    return html


def spool_start() -> str:
    """Generate all opening tags currently on the stack.

    Returns:
        String of all opening tags in original order

    Note:
        Does not modify the stack.

    Examples:
        >>> push('<div>')
        >>> push('<span>')
        >>> spool_start()
        '<div><span>'
    """
    html = ''
    for item in stack:
        html += item
    return html


def has_elements() -> bool:
    """Check if the stack has any elements.

    Returns:
        True if stack contains tags, False otherwise
    """
    return len(stack) > 0


def get_last() -> str:
    """Get the most recent tag without removing it from the stack.

    Returns:
        Most recently pushed tag, or empty string if stack is empty

    Examples:
        >>> push('<div>')
        >>> get_last()
        '<div>'
        >>> has_elements()  # Stack still has the element
        True
    """
    if len(stack) > 0:
        return stack[len(stack) - 1]
    return ''


def flush() -> None:
    """Clear all tags from the stack.

    After calling flush(), the stack will be empty and has_elements()
    will return False.
    """
    del stack[:]


def get_stack() -> List[str]:
    """Get direct reference to the stack list.

    Returns:
        The actual stack list object (not a copy)

    Warning:
        Returns a reference to the internal stack. Modifications will
        affect the global stack state.
    """
    return stack
