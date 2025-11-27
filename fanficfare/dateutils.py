"""Date parsing and manipulation utilities.

This module provides utilities for parsing various date formats encountered
in fan fiction sites, including relative dates ("2 hours ago", "Yesterday")
and absolute dates with flexible formatting.
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

from datetime import datetime, timedelta
from typing import Dict
import re
import logging

logger = logging.getLogger(__name__)

# There's a Windows / Python 3 bug that prevents using timestamp 0.
# So Jan 2, 1970 instead.
UNIX_EPOCHE = datetime.fromtimestamp(86400)

# Regex pattern for relative date strings (e.g., "5 days ago")
relrexp = re.compile(r'^(?P<val>\d+) *(?P<unit>[^ ]+).*$')

# Mapping of various time unit representations to timedelta keywords
# Keep this explicit instead of replacing parentheses in case we
# discover a format that is not so easily translated as a
# keyword-argument to timedelta.
unit_to_keyword: Dict[str, str] = {
    'second(s)': 'seconds',
    'minute(s)': 'minutes',
    'hour(s)': 'hours',
    'day(s)': 'days',
    'week(s)': 'weeks',
    'seconds': 'seconds',
    'minutes': 'minutes',
    'hours': 'hours',
    'days': 'days',
    'weeks': 'weeks',
    'second': 'seconds',
    'minute': 'minutes',
    'mins': 'minutes',
    'min': 'minutes',
    'hour': 'hours',
    'day': 'days',
    'week': 'weeks',
    'mth': 'months',
    'h': 'hours',
    'd': 'days',
    'yr': 'years',
}

# Mapping of full English month names to numeric strings
fullmon: Dict[str, str] = {
    "January": "01",
    "February": "02",
    "March": "03",
    "April": "04",
    "May": "05",
    "June": "06",
    "July": "07",
    "August": "08",
    "September": "09",
    "October": "10",
    "November": "11",
    "December": "12"
}


def utcnow() -> datetime:
    """Get current UTC time.

    Uses datetime.UTC if available (Python 3.11+), otherwise falls back
    to datetime.utcnow() for older Python versions.

    Returns:
        Current UTC datetime

    Examples:
        >>> now = utcnow()
        >>> isinstance(now, datetime)
        True
    """
    try:
        from datetime import UTC
        # Python 3.11+
        return datetime.now(UTC)
    except ImportError:
        # Older Python versions
        return datetime.utcnow()


def parse_relative_date_string(reldatein: str) -> datetime:
    """Parse a relative date string into an absolute datetime.

    Handles various relative date formats like:
    - "5 minutes ago"
    - "2 days"
    - "Yesterday"
    - "just now"
    - "3 years ago"

    For imprecise units (years, months), uses approximate conversions:
    - 1 year = 365 days
    - 1 month = 31 days

    Args:
        reldatein: Relative date string to parse

    Returns:
        Datetime object representing the parsed date. Falls back to
        UNIX_EPOCHE (Jan 2, 1970) if parsing fails.

    Examples:
        >>> # parse_relative_date_string("5 minutes ago")
        >>> # Returns datetime 5 minutes before current time
        >>> parse_relative_date_string("just now")  # doctest: +SKIP
        datetime(...)

    Note:
        Currently used by adapter_webnovelcom & adapter_wwwnovelallcom
    """
    # logger.debug(f"parse_relative_date_string({reldatein})")

    # Discard trailing ' ago' if present and extract value/unit
    m = re.match(relrexp, reldatein)

    unit_string = None  # Use as a switch to do unit calc
    value = None

    # Matches <number> <word>
    if m:
        value = m.group('val')
        unit_string = m.group('unit')
    # If the date is displayed as Yesterday
    elif "Yesterday" in reldatein:
        value = 1
        unit_string = 'days'
    elif "just now" in reldatein:
        return utcnow()

    if unit_string:
        unit = unit_to_keyword.get(unit_string)
        logger.debug(f"val:{value} unit_string:{unit_string} unit:{unit}")

        # I'm not going to worry very much about accuracy for a site
        # that considers '2 years ago' an acceptable time stamp.
        if "year" in unit_string or (unit and 'year' in unit):
            value = str(int(value) * 365)
            unit = 'days'
        elif "month" in unit_string or (unit and 'month' in unit):
            value = str(int(value) * 31)
            unit = 'days'

        logger.debug(f"val:{value} unit_string:{unit_string} unit:{unit}")

        if unit:
            kwargs = {unit: int(value)}

            # "naive" dates without hours and seconds are created in
            # writers.base_writer.writeStory(), so we don't have to strip
            # hours and minutes from the base date. Using datetime objects
            # would result in a slightly different time (since we calculate
            # the last updated date based on the current time) during each
            # update, since the seconds and hours change.
            today = utcnow()
            time_ago = timedelta(**kwargs)
            return today - time_ago

    # This is "just as wrong" as always returning the current
    # date, but prevents unneeded updates each time
    logger.warning(
        'Failed to parse relative date string: %r, falling back to unix epoche',
        reldatein
    )
    return UNIX_EPOCHE


def makeDate(string: str, dateform: str) -> datetime:
    """Parse a date string using a flexible format specifier.

    Handles various date format challenges:
    - English month names (%B, %b) regardless of locale
    - AM/PM indicators (%p) even when locale doesn't define them
    - Both 12-hour (%I) and 24-hour (%H) time formats

    Args:
        string: Date string to parse (e.g., "January 15, 2020 3:30 PM")
        dateform: Format string using strptime directives (e.g., "%B %d, %Y %I:%M %p")

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If the date string cannot be parsed with the given format

    Examples:
        >>> makeDate("January 15, 2020", "%B %d, %Y")
        datetime.datetime(2020, 1, 15, 0, 0)
        >>> makeDate("15 Jan 2020 3:30 PM", "%d %b %Y %I:%M %p")
        datetime.datetime(2020, 1, 15, 15, 30)

    Note:
        This abstraction handles locale-specific issues by manually
        replacing English month names with numeric values, and by
        manually handling AM/PM conversion.
    """
    # Fudge English month names for people whose locale is set to
    # non-US English. Most current sites date in English, even if
    # there's non-English content -- ficbook.net, OTOH, has to do
    # something even more complicated to get Russian month names
    # correct everywhere.
    do_abbrev = "%b" in dateform

    if "%B" in dateform or do_abbrev:
        dateform = dateform.replace("%B", "%m").replace("%b", "%m")
        for (name, num) in fullmon.items():
            if do_abbrev:
                name = name[:3]  # First three chars for abbreviation
            if name in string:
                string = string.replace(name, num)
                break

    # Many locales don't define %p for AM/PM. So if %p, remove from
    # dateform, look for 'pm' in string, remove am/pm from string and
    # add 12 hours if pm found.
    add_hours = False
    if "%p" in dateform:
        dateform = dateform.replace("%p", "")
        if 'pm' in string or 'PM' in string:
            add_hours = True
        string = string.replace("AM", "").replace("PM", "").replace("am", "").replace("pm", "")

    dateform = dateform.strip()
    string = string.strip()

    try:
        date = datetime.strptime(string, dateform)
    except ValueError:
        # If parse fails and looking for 01-12 hours, try 01-24 hours too.
        # A moderately cheesy way to support 12 and 24 hour clocks.
        if "%I" in dateform:
            dateform = dateform.replace("%I", "%H")
            date = datetime.strptime(string, dateform)
            add_hours = False
        else:
            raise

    if add_hours:
        date += timedelta(hours=12)

    return date
