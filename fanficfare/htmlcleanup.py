"""HTML entity and content cleanup utilities.

This module provides comprehensive HTML entity conversion, tag stripping,
and content cleanup functionality. It handles:
- Named HTML entities (&mdash;, &nbsp;, etc.)
- Numeric entities (&#8212;, &#x2014;, etc.)
- Zalgo text reduction (excessive combining diacritical marks)
- Email address decoding
- HTML tag removal

The entity handling is designed to work around quirks in BeautifulSoup's
entity parsing while maintaining proper XHTML compliance.
"""

# Copyright 2011 Fanficdownloader team, 2018 FanFicFare team
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

import logging
import re
from html import escape as htmlescape
from typing import Any, Dict, Match, Union
from urllib.parse import unquote

logger = logging.getLogger(__name__)

def _unirepl(match: Match[str]) -> str:
    """Convert numeric HTML entity to unicode character.

    Args:
        match: Regex match object with groups (number, trailing_chars)

    Returns:
        Unicode character followed by trailing chars, or empty string on error

    Note:
        Handles both decimal (&#123;) and hexadecimal (&#xAB;) entities.
    """
    if match.group(1).startswith('x'):
        radix = 16
        s = match.group(1)[1:]
    else:
        radix = 10
        s = match.group(1)
    try:
        value = int(s, radix)
        retval = f"{chr(value)}{match.group(2)}"
    except (ValueError, OverflowError):
        # This way, at least if there's more entities out there
        # that fail, it doesn't blow the entire download.
        logger.warning(
            f"Numeric entity translation failed, skipping: &#x{match.group(1)}{match.group(2)}"
        )
        retval = ""
    return retval

def _replaceNumberEntities(data: str) -> str:
    """Replace numeric HTML entities with unicode characters.

    Handles the quirk where SGMLParser inserts ';' incorrectly after
    number entities, including part of the next word if it's a-z.

    Args:
        data: String containing numeric entities

    Returns:
        String with numeric entities converted to characters

    Examples:
        >>> _replaceNumberEntities("Don't&#8212;do&#8212;that")
        "Don't—do—that"
    """
    # The same brokenish entity parsing in SGMLParser that inserts ';'
    # after non-entities will also insert ';' incorrectly after number
    # entities, including part of the next word if it's a-z.
    # "Don't&#8212ever&#8212do&#8212that&#8212again," becomes
    # "Don't&#8212e;ver&#8212d;o&#8212;that&#8212a;gain,"
    # Also need to allow for 5 digit decimal entities &#27861;
    # Last expression didn't allow for 2 digit hex correctly: &#xE9;
    p = re.compile(r'&#(x[0-9a-fA-F]{,4}|[0-9]{,5})([0-9a-fA-F]*?);')
    return p.sub(_unirepl, data)


def _replaceNotEntities(data: str) -> str:
    """Remove semicolons from malformed entity references.

    Args:
        data: String potentially containing malformed entities

    Returns:
        String with semicolons removed from non-entity references

    Note:
        SGMLParser incorrectly adds semicolons after text like "AT&T",
        turning it into "AT&T;". This removes those false semicolons.
    """
    # Not just \w or \S. Regexp from SGMLParser entityref pattern
    p = re.compile(r'&([a-zA-Z][-.a-zA-Z0-9]*);')
    return p.sub(r'&\1', data)

def stripHTML(soup: Union[str, Any], remove_all_entities: bool = True) -> str:
    """Remove HTML tags and optionally convert entities to characters.

    Args:
        soup: HTML string or BeautifulSoup object to clean
        remove_all_entities: If True, convert all entities including &lt;/&gt;/&amp;

    Returns:
        Plain text with HTML tags removed and entities converted

    Examples:
        >>> stripHTML("<p>Hello &mdash; world</p>")
        'Hello — world'
        >>> stripHTML("<div>Test&nbsp;text</div>")
        'Test text'
    """
    if isinstance(soup, str):
        retval = removeEntities(
            re.sub(r'<[^>]+>', '', f"{soup}"),
            remove_all_entities=remove_all_entities
        ).strip()
    else:
        # bs4 already converts all the entities to UTF8 chars.
        retval = soup.get_text(strip=True)
        if not remove_all_entities:
            # Put basic 3 entities back
            if '&' in retval and '&amp;' not in retval:
                # Check in case called more than once
                retval = retval.replace('&', '&amp;')
            retval = retval.replace('<', '&lt;').replace('>', '&gt;')

    # Some change in the python3 branch started making &nbsp; '\xc2\xa0'
    # instead of ' '
    return retval.replace('\xc2\xa0', ' ').strip()

def conditionalRemoveEntities(value: Any) -> Union[str, Any]:
    """Remove entities if value is a string, otherwise return unchanged.

    Args:
        value: Value to potentially clean (string or other type)

    Returns:
        Cleaned string if input was string, otherwise original value

    Examples:
        >>> conditionalRemoveEntities("Hello &mdash; world")
        'Hello — world'
        >>> conditionalRemoveEntities(123)
        123
    """
    if isinstance(value, str):
        return removeEntities(value).strip()
    else:
        return value


def removeAllEntities(text: str) -> str:
    """Remove all HTML entities including &lt;, &gt;, and &amp;.

    Args:
        text: String containing HTML entities

    Returns:
        String with all entities converted to characters

    Examples:
        >>> removeAllEntities("Hello &lt;world&gt;")
        'Hello <world>'
    """
    # Remove &lt; &lt; and &amp; also
    return removeEntities(text, remove_all_entities=True)

def removeEntities(
    text: str,
    space_only: bool = False,
    remove_all_entities: bool = False
) -> str:
    """Convert HTML entities to unicode characters.

    Handles 362+ named entities plus numeric entities. Preserves
    &amp;, &lt;, &gt; when remove_all_entities=False for XHTML compliance.

    Args:
        text: String containing HTML entities
        space_only: If True, only convert space-like entities
        remove_all_entities: If True, convert &lt;/&gt;/&amp; as well

    Returns:
        String with entities converted to unicode characters

    Examples:
        >>> removeEntities("Hello &mdash; world")
        'Hello — world'
        >>> removeEntities("A &amp; B", remove_all_entities=False)
        'A &amp; B'
        >>> removeEntities("A &amp; B", remove_all_entities=True)
        'A & B'

    Note:
        Keeps &amp;, &lt;, and &gt; when remove_all_entities=False.
        These are the only HTML entities allowed in XHTML.
    """
    # Keeps &amp;, &lt; and &gt; when remove_all_entities=False
    if text is None:
        return ""

    if not isinstance(text, str):
        text = str(text)

    # Replace numeric versions of [&<>] with named versions
    text = re.sub(r'&#0*38;', '&amp;', text)
    text = re.sub(r'&#0*60;', '&lt;', text)
    text = re.sub(r'&#0*62;', '&gt;', text)

    # Replace remaining &#000; entities with unicode value, such as &#039; -> '
    text = _replaceNumberEntities(text)

    # Replace several named entities with character, such as &mdash; -> —
    # Reverse sort will put entities with ; before the same one without, when valid.
    for e in reversed(sorted(entities.keys())):
        v = entities[e]
        if space_only and re.match(r"^[^\s]$", v, re.UNICODE | re.S):
            # If not space
            continue
        text = text.replace(e, v)

    # SGMLParser, and in turn, BeautifulStoneSoup doesn't parse
    # entities terribly well and inserts (;) after something that
    # it thinks might be an entity. AT&T becomes AT&T; All of my
    # attempts to fix this by changing the input to
    # BeautifulStoneSoup break something else instead. But at
    # this point, there should be *no* real entities left, so find
    # these not-entities and remove them here should be safe.
    text = _replaceNotEntities(text)

    if remove_all_entities:
        text = text.replace('&lt', '<').replace('&gt', '>').replace('&amp;', '&')
    else:
        # &lt; &gt; and &amp; are the only html entities allowed in xhtml, put those back.
        # They come out as &lt because _replaceNotEntities removes the ';'.
        text = text.replace('&', '&amp;').replace('&amp;lt', '&lt;').replace('&amp;gt', '&gt;')

    return text

## Currently used(optionally) by adapter_novelonlinefullcom and
## adapter_wwwnovelallcom only.  I hesitate to put the option in
## base_adapter.make_soup for all adapters due to concerns about it
## maybe breaking metadata parsing as it changes tags.
def fix_excess_space(text):
    # For easier extra space removing (when combining p an br)
    text = removeEntities(text, space_only=True)

    # Sometimes we don't have even tags like <p> or <br/>, so lets create <p> instead of two new_line
    text = re.sub(r"\n[ \s]*\n", "\n<p>", text, flags=re.UNICODE)

    # Combining all consequence of p and br to one <p>
    # bs4 will create </p> on his own, so don't worry
    text = re.sub(r"[ \s]*(</?p\b[^>]*>[ \s]*|<br\b[^>]*>[ \s]*)+", "\n<p>", text, flags=re.UNICODE)

    return text

import unicodedata
# Character categories for combining diacritical marks (Zalgo text)
ZALGO_CHAR_CATEGORIES = ['Mn', 'Me']


def reduce_zalgo(text: str, max_zalgo: int = 1) -> str:
    """Reduce excessive combining diacritical marks (Zalgo text).

    Limits the number of consecutive combining marks to prevent
    "Zalgo" text corruption while preserving normal diacritics.

    Args:
        text: Text potentially containing excessive combining marks
        max_zalgo: Maximum number of consecutive combining marks to allow

    Returns:
        Text with combining marks limited

    Note:
        Applies Unicode NFD normalization before processing.
        Based on: https://stackoverflow.com/questions/22277052/
    """
    lineout = []
    count = 0
    for c in unicodedata.normalize('NFD', text):
        if unicodedata.category(c) not in ZALGO_CHAR_CATEGORIES:
            lineout.append(c)
            count = 0
        else:
            if count < max_zalgo:
                lineout.append(c)
            count += 1

    return ''.join(lineout)

def parse_hex(n: str, c: int) -> int:
    """Parse a 2-character hexadecimal value from a string.

    Args:
        n: String containing hex digits
        c: Character offset to start parsing

    Returns:
        Integer value of the 2-character hex string

    Examples:
        >>> parse_hex("4A6B", 0)
        74  # 0x4A
        >>> parse_hex("4A6B", 2)
        107  # 0x6B
    """
    r = n[c:c+2]
    return int(r, 16)

def decode_email(n: str, c: int = 0) -> str:
    """Decode XOR-obfuscated email address.

    Some sites obfuscate email addresses by XORing each character
    with a key value stored at the beginning of the string.

    Args:
        n: Hex-encoded obfuscated email string
        c: Character offset to start decoding (default 0)

    Returns:
        Decoded and HTML-escaped email address

    Note:
        The first byte is the XOR key, subsequent bytes are the
        encoded email address.
    """
    o = ""
    a = parse_hex(n, c)

    for i in range(c + 2, len(n), 2):
        l = parse_hex(n, i) ^ a
        o += chr(l)

    o = unquote(o)
    return htmlescape(o)


# Entity list from http://code.google.com/p/doctype/wiki/CharacterEntitiesConsistent
# 362+ named HTML entities mapping to unicode characters
entities: Dict[str, str] = { '&aacute;' : 'á',
         '&Aacute;' : 'Á',
         '&Aacute' : 'Á',
         '&aacute' : 'á',
         '&acirc;' : 'â',
         '&Acirc;' : 'Â',
         '&Acirc' : 'Â',
         '&acirc' : 'â',
         '&acute;' : '´',
         '&acute' : '´',
         '&AElig;' : 'Æ',
         '&aelig;' : 'æ',
         '&AElig' : 'Æ',
         '&aelig' : 'æ',
         '&agrave;' : 'à',
         '&Agrave;' : 'À',
         '&Agrave' : 'À',
         '&agrave' : 'à',
         '&alefsym;' : 'ℵ',
         '&alpha;' : 'α',
         '&Alpha;' : 'Α',
         '&amp;' : '&',
         '&AMP;' : '&',
         '&AMP' : '&',
         '&amp' : '&',
         '&and;' : '∧',
         '&ang;' : '∠',
         '&aring;' : 'å',
         '&Aring;' : 'Å',
         '&Aring' : 'Å',
         '&aring' : 'å',
         '&asymp;' : '≈',
         '&atilde;' : 'ã',
         '&Atilde;' : 'Ã',
         '&Atilde' : 'Ã',
         '&atilde' : 'ã',
         '&auml;' : 'ä',
         '&Auml;' : 'Ä',
         '&Auml' : 'Ä',
         '&auml' : 'ä',
         '&bdquo;' : '„',
         '&beta;' : 'β',
         '&Beta;' : 'Β',
         '&brvbar;' : '¦',
         '&brvbar' : '¦',
         '&bull;' : '•',
         '&cap;' : '∩',
         '&ccedil;' : 'ç',
         '&Ccedil;' : 'Ç',
         '&Ccedil' : 'Ç',
         '&ccedil' : 'ç',
         '&cedil;' : '¸',
         '&cedil' : '¸',
         '&cent;' : '¢',
         '&cent' : '¢',
         '&chi;' : 'χ',
         '&Chi;' : 'Χ',
         '&circ;' : 'ˆ',
         '&clubs;' : '♣',
         '&cong;' : '≅',
         '&copy;' : '©',
         '&COPY;' : '©',
         '&COPY' : '©',
         '&copy' : '©',
         '&crarr;' : '↵',
         '&cup;' : '∪',
         '&curren;' : '¤',
         '&curren' : '¤',
         '&dagger;' : '†',
         '&Dagger;' : '‡',
         '&darr;' : '↓',
         '&dArr;' : '⇓',
         '&deg;' : '°',
         '&deg' : '°',
         '&delta;' : 'δ',
         '&Delta;' : 'Δ',
         '&diams;' : '♦',
         '&divide;' : '÷',
         '&divide' : '÷',
         '&eacute;' : 'é',
         '&Eacute;' : 'É',
         '&Eacute' : 'É',
         '&eacute' : 'é',
         '&ecirc;' : 'ê',
         '&Ecirc;' : 'Ê',
         '&Ecirc' : 'Ê',
         '&ecirc' : 'ê',
         '&egrave;' : 'è',
         '&Egrave;' : 'È',
         '&Egrave' : 'È',
         '&egrave' : 'è',
         '&empty;' : '∅',
         '&emsp;' : ' ',
         '&ensp;' : ' ',
         '&epsilon;' : 'ε',
         '&Epsilon;' : 'Ε',
         '&equiv;' : '≡',
         '&eta;' : 'η',
         '&Eta;' : 'Η',
         '&eth;' : 'ð',
         '&ETH;' : 'Ð',
         '&ETH' : 'Ð',
         '&eth' : 'ð',
         '&euml;' : 'ë',
         '&Euml;' : 'Ë',
         '&Euml' : 'Ë',
         '&euml' : 'ë',
         '&euro;' : '€',
         '&exist;' : '∃',
         '&fnof;' : 'ƒ',
         '&forall;' : '∀',
         '&frac12;' : '½',
         '&frac12' : '½',
         '&frac14;' : '¼',
         '&frac14' : '¼',
         '&frac34;' : '¾',
         '&frac34' : '¾',
         '&frasl;' : '⁄',
         '&gamma;' : 'γ',
         '&Gamma;' : 'Γ',
         '&ge;' : '≥',
         #'&gt;' : '>',
         #'&GT;' : '>',
         #'&GT' : '>',
         #'&gt' : '>',
         '&harr;' : '↔',
         '&hArr;' : '⇔',
         '&hearts;' : '♥',
         '&hellip;' : '…',
         '&iacute;' : 'í',
         '&Iacute;' : 'Í',
         '&Iacute' : 'Í',
         '&iacute' : 'í',
         '&icirc;' : 'î',
         '&Icirc;' : 'Î',
         '&Icirc' : 'Î',
         '&icirc' : 'î',
         '&iexcl;' : '¡',
         '&iexcl' : '¡',
         '&igrave;' : 'ì',
         '&Igrave;' : 'Ì',
         '&Igrave' : 'Ì',
         '&igrave' : 'ì',
         '&image;' : 'ℑ',
         '&infin;' : '∞',
         '&int;' : '∫',
         '&iota;' : 'ι',
         '&Iota;' : 'Ι',
         '&iquest;' : '¿',
         '&iquest' : '¿',
         '&isin;' : '∈',
         '&iuml;' : 'ï',
         '&Iuml;' : 'Ï',
         '&Iuml' : 'Ï',
         '&iuml' : 'ï',
         '&kappa;' : 'κ',
         '&Kappa;' : 'Κ',
         '&lambda;' : 'λ',
         '&Lambda;' : 'Λ',
         '&laquo;' : '«',
         '&laquo' : '«',
         '&larr;' : '←',
         '&lArr;' : '⇐',
         '&lceil;' : '⌈',
         '&ldquo;' : '“',
         '&le;' : '≤',
         '&lfloor;' : '⌊',
         '&lowast;' : '∗',
         '&loz;' : '◊',
         '&lrm;' : '‎',
         '&lsaquo;' : '‹',
         '&lsquo;' : '‘',
         #'&lt;' : '<',
         #'&LT;' : '<',
         #'&LT' : '<',
         #'&lt' : '<',
         '&macr;' : '¯',
         '&macr' : '¯',
         '&mdash;' : '—',
         '&micro;' : 'µ',
         '&micro' : 'µ',
         '&middot;' : '·',
         '&middot' : '·',
         '&minus;' : '−',
         '&mu;' : 'μ',
         '&Mu;' : 'Μ',
         '&nabla;' : '∇',
         '&nbsp;' : ' ',
         '&nbsp' : ' ',
         '&ndash;' : '–',
         '&ne;' : '≠',
         '&ni;' : '∋',
         '&not;' : '¬',
         '&not' : '¬',
         '&notin;' : '∉',
         '&nsub;' : '⊄',
         '&ntilde;' : 'ñ',
         '&Ntilde;' : 'Ñ',
         '&Ntilde' : 'Ñ',
         '&ntilde' : 'ñ',
         '&nu;' : 'ν',
         '&Nu;' : 'Ν',
         '&oacute;' : 'ó',
         '&Oacute;' : 'Ó',
         '&Oacute' : 'Ó',
         '&oacute' : 'ó',
         '&ocirc;' : 'ô',
         '&Ocirc;' : 'Ô',
         '&Ocirc' : 'Ô',
         '&ocirc' : 'ô',
         '&OElig;' : 'Œ',
         '&oelig;' : 'œ',
         '&ograve;' : 'ò',
         '&Ograve;' : 'Ò',
         '&Ograve' : 'Ò',
         '&ograve' : 'ò',
         '&oline;' : '‾',
         '&omega;' : 'ω',
         '&Omega;' : 'Ω',
         '&omicron;' : 'ο',
         '&Omicron;' : 'Ο',
         '&oplus;' : '⊕',
         '&or;' : '∨',
         '&ordf;' : 'ª',
         '&ordf' : 'ª',
         '&ordm;' : 'º',
         '&ordm' : 'º',
         '&oslash;' : 'ø',
         '&Oslash;' : 'Ø',
         '&Oslash' : 'Ø',
         '&oslash' : 'ø',
         '&otilde;' : 'õ',
         '&Otilde;' : 'Õ',
         '&Otilde' : 'Õ',
         '&otilde' : 'õ',
         '&otimes;' : '⊗',
         '&ouml;' : 'ö',
         '&Ouml;' : 'Ö',
         '&Ouml' : 'Ö',
         '&ouml' : 'ö',
         '&para;' : '¶',
         '&para' : '¶',
         '&part;' : '∂',
         '&permil;' : '‰',
         '&perp;' : '⊥',
         '&phi;' : 'φ',
         '&Phi;' : 'Φ',
         '&pi;' : 'π',
         '&Pi;' : 'Π',
         '&piv;' : 'ϖ',
         '&plusmn;' : '±',
         '&plusmn' : '±',
         '&pound;' : '£',
         '&pound' : '£',
         '&prime;' : '′',
         '&Prime;' : '″',
         '&prod;' : '∏',
         '&prop;' : '∝',
         '&psi;' : 'ψ',
         '&Psi;' : 'Ψ',
         '&quot;' : '"',
         '&QUOT;' : '"',
         '&QUOT' : '"',
         '&quot' : '"',
         '&radic;' : '√',
         '&raquo;' : '»',
         '&raquo' : '»',
         '&rarr;' : '→',
         '&rArr;' : '⇒',
         '&rceil;' : '⌉',
         '&rdquo;' : '”',
         '&real;' : 'ℜ',
         '&reg;' : '®',
         '&REG;' : '®',
         '&REG' : '®',
         '&reg' : '®',
         '&rfloor;' : '⌋',
         '&rho;' : 'ρ',
         '&Rho;' : 'Ρ',
         '&rlm;' : '‏',
         '&rsaquo;' : '›',
         '&rsquo;' : '’',
         '&sbquo;' : '‚',
         '&scaron;' : 'š',
         '&Scaron;' : 'Š',
         '&sdot;' : '⋅',
         '&sect;' : '§',
         '&sect' : '§',
         '&shy;' : '­', # strange optional hyphenation control character, not just a dash
         '&shy' : '­',
         '&sigma;' : 'σ',
         '&Sigma;' : 'Σ',
         '&sigmaf;' : 'ς',
         '&sim;' : '∼',
         '&spades;' : '♠',
         '&sub;' : '⊂',
         '&sube;' : '⊆',
         '&sum;' : '∑',
         '&sup1;' : '¹',
         '&sup1' : '¹',
         '&sup2;' : '²',
         '&sup2' : '²',
         '&sup3;' : '³',
         '&sup3' : '³',
         '&sup;' : '⊃',
         '&supe;' : '⊇',
         '&szlig;' : 'ß',
         '&szlig' : 'ß',
         '&tau;' : 'τ',
         '&Tau;' : 'Τ',
         '&there4;' : '∴',
         '&theta;' : 'θ',
         '&Theta;' : 'Θ',
         '&thetasym;' : 'ϑ',
         '&thinsp;' : ' ',
         '&thorn;' : 'þ',
         '&THORN;' : 'Þ',
         '&THORN' : 'Þ',
         '&thorn' : 'þ',
         '&tilde;' : '˜',
         '&times;' : '×',
         '&times' : '×',
         '&trade;' : '™',
         '&uacute;' : 'ú',
         '&Uacute;' : 'Ú',
         '&Uacute' : 'Ú',
         '&uacute' : 'ú',
         '&uarr;' : '↑',
         '&uArr;' : '⇑',
         '&ucirc;' : 'û',
         '&Ucirc;' : 'Û',
         '&Ucirc' : 'Û',
         '&ucirc' : 'û',
         '&ugrave;' : 'ù',
         '&Ugrave;' : 'Ù',
         '&Ugrave' : 'Ù',
         '&ugrave' : 'ù',
         '&uml;' : '¨',
         '&uml' : '¨',
         '&upsih;' : 'ϒ',
         '&upsilon;' : 'υ',
         '&Upsilon;' : 'Υ',
         '&uuml;' : 'ü',
         '&Uuml;' : 'Ü',
         '&Uuml' : 'Ü',
         '&uuml' : 'ü',
         '&weierp;' : '℘',
         '&xi;' : 'ξ',
         '&Xi;' : 'Ξ',
         '&yacute;' : 'ý',
         '&Yacute;' : 'Ý',
         '&Yacute' : 'Ý',
         '&yacute' : 'ý',
         '&yen;' : '¥',
         '&yen' : '¥',
         '&yuml;' : 'ÿ',
         '&Yuml;' : 'Ÿ',
         '&yuml' : 'ÿ',
         '&zeta;' : 'ζ',
         '&Zeta;' : 'Ζ',
         '&zwj;' : '‍',  # strange spacing control character, not just a space
         '&zwnj;' : '‌',  # strange spacing control character, not just a space
         }
