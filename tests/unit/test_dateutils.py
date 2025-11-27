import pytest
from datetime import datetime, timedelta
from fanficfare import dateutils
from freezegun import freeze_time


class TestUtcnow:
    """Test utcnow() function"""

    def test_returns_datetime(self):
        result = dateutils.utcnow()
        assert isinstance(result, datetime)

    def test_is_current_time(self):
        # Should be very close to current time (within 1 second)
        now = datetime.utcnow()
        result = dateutils.utcnow()
        diff = abs((now - result.replace(tzinfo=None)).total_seconds())
        assert diff < 1.0


class TestParseRelativeDateString:
    """Test parse_relative_date_string() function"""

    @freeze_time("2023-06-15 12:00:00")
    def test_parse_seconds(self):
        result = dateutils.parse_relative_date_string("30 seconds ago")
        expected = datetime(2023, 6, 15, 11, 59, 30)
        assert result.replace(tzinfo=None) == expected

    @freeze_time("2023-06-15 12:00:00")
    def test_parse_minutes(self):
        result = dateutils.parse_relative_date_string("15 minutes ago")
        expected = datetime(2023, 6, 15, 11, 45, 0)
        assert result.replace(tzinfo=None) == expected

    @freeze_time("2023-06-15 12:00:00")
    def test_parse_hours(self):
        result = dateutils.parse_relative_date_string("3 hours ago")
        expected = datetime(2023, 6, 15, 9, 0, 0)
        assert result.replace(tzinfo=None) == expected

    @freeze_time("2023-06-15 12:00:00")
    def test_parse_days(self):
        result = dateutils.parse_relative_date_string("5 days ago")
        expected = datetime(2023, 6, 10, 12, 0, 0)
        assert result.replace(tzinfo=None) == expected

    @freeze_time("2023-06-15 12:00:00")
    def test_parse_weeks(self):
        result = dateutils.parse_relative_date_string("2 weeks ago")
        expected = datetime(2023, 6, 1, 12, 0, 0)
        assert result.replace(tzinfo=None) == expected

    @freeze_time("2023-06-15 12:00:00")
    def test_parse_months(self):
        # Months are converted to 31 days
        result = dateutils.parse_relative_date_string("2 mth ago")
        expected = datetime(2023, 6, 15, 12, 0, 0) - timedelta(days=62)
        assert result.replace(tzinfo=None) == expected

    @freeze_time("2023-06-15 12:00:00")
    def test_parse_years(self):
        # Years are converted to 365 days
        result = dateutils.parse_relative_date_string("1 yr ago")
        expected = datetime(2023, 6, 15, 12, 0, 0) - timedelta(days=365)
        assert result.replace(tzinfo=None) == expected

    @freeze_time("2023-06-15 12:00:00")
    def test_parse_yesterday(self):
        result = dateutils.parse_relative_date_string("Yesterday")
        expected = datetime(2023, 6, 14, 12, 0, 0)
        assert result.replace(tzinfo=None) == expected

    @freeze_time("2023-06-15 12:00:00")
    def test_parse_just_now(self):
        result = dateutils.parse_relative_date_string("just now")
        expected = datetime(2023, 6, 15, 12, 0, 0)
        assert result.replace(tzinfo=None) == expected

    @freeze_time("2023-06-15 12:00:00")
    def test_parse_with_unit_variations(self):
        # Test different unit spellings
        test_cases = [
            ("1 second ago", timedelta(seconds=1)),
            ("1 minute ago", timedelta(minutes=1)),
            ("1 hour ago", timedelta(hours=1)),
            ("1 day ago", timedelta(days=1)),
            ("1 week ago", timedelta(weeks=1)),
            ("5 mins ago", timedelta(minutes=5)),
            ("3 min ago", timedelta(minutes=3)),
            ("2 h ago", timedelta(hours=2)),
            ("7 d ago", timedelta(days=7)),
        ]

        base_time = datetime(2023, 6, 15, 12, 0, 0)
        for date_string, delta in test_cases:
            result = dateutils.parse_relative_date_string(date_string)
            expected = base_time - delta
            assert result.replace(tzinfo=None) == expected, f"Failed for: {date_string}"

    def test_parse_invalid_returns_unix_epoch(self):
        # Invalid date strings should return UNIX_EPOCHE
        result = dateutils.parse_relative_date_string("invalid date string")
        # UNIX_EPOCHE is Jan 2, 1970
        assert result == dateutils.UNIX_EPOCHE

    def test_parse_empty_string_returns_unix_epoch(self):
        result = dateutils.parse_relative_date_string("")
        assert result == dateutils.UNIX_EPOCHE


class TestMakeDate:
    """Test makeDate() function"""

    def test_basic_date_parsing(self):
        result = dateutils.makeDate("2023-06-15", "%Y-%m-%d")
        expected = datetime(2023, 6, 15)
        assert result == expected

    def test_parse_with_time(self):
        result = dateutils.makeDate("2023-06-15 14:30:00", "%Y-%m-%d %H:%M:%S")
        expected = datetime(2023, 6, 15, 14, 30, 0)
        assert result == expected

    def test_parse_full_month_name(self):
        result = dateutils.makeDate("June 15, 2023", "%B %d, %Y")
        expected = datetime(2023, 6, 15)
        assert result == expected

    def test_parse_abbreviated_month_name(self):
        result = dateutils.makeDate("Jun 15, 2023", "%b %d, %Y")
        expected = datetime(2023, 6, 15)
        assert result == expected

    def test_parse_all_months_full(self):
        # Test all month names
        months = [
            ("January 1, 2023", 1),
            ("February 1, 2023", 2),
            ("March 1, 2023", 3),
            ("April 1, 2023", 4),
            ("May 1, 2023", 5),
            ("June 1, 2023", 6),
            ("July 1, 2023", 7),
            ("August 1, 2023", 8),
            ("September 1, 2023", 9),
            ("October 1, 2023", 10),
            ("November 1, 2023", 11),
            ("December 1, 2023", 12),
        ]

        for date_string, month_num in months:
            result = dateutils.makeDate(date_string, "%B %d, %Y")
            assert result.month == month_num

    def test_parse_abbreviated_months(self):
        # Test abbreviated month names
        result = dateutils.makeDate("Jan 1, 2023", "%b %d, %Y")
        assert result.month == 1

        result = dateutils.makeDate("Dec 31, 2023", "%b %d, %Y")
        assert result.month == 12

    def test_parse_with_am_pm(self):
        # Test AM
        result = dateutils.makeDate("2023-06-15 09:30 AM", "%Y-%m-%d %I:%M %p")
        expected = datetime(2023, 6, 15, 9, 30)
        assert result == expected

        # Test PM (should add 12 hours)
        result = dateutils.makeDate("2023-06-15 02:30 PM", "%Y-%m-%d %I:%M %p")
        expected = datetime(2023, 6, 15, 14, 30)
        assert result == expected

    def test_parse_lowercase_am_pm(self):
        result = dateutils.makeDate("2023-06-15 03:00 pm", "%Y-%m-%d %I:%M %p")
        expected = datetime(2023, 6, 15, 15, 0)
        assert result == expected

    def test_parse_12_hour_fallback_to_24_hour(self):
        # If %I (12-hour) fails, should try %H (24-hour)
        # This tests time like "23:00" with %I format
        result = dateutils.makeDate("2023-06-15 23:00", "%Y-%m-%d %I:%M")
        expected = datetime(2023, 6, 15, 23, 0)
        assert result == expected

    def test_strip_whitespace(self):
        # Should handle extra whitespace
        result = dateutils.makeDate("  2023-06-15  ", "%Y-%m-%d")
        expected = datetime(2023, 6, 15)
        assert result == expected

    def test_various_date_formats(self):
        test_cases = [
            ("15/06/2023", "%d/%m/%Y", datetime(2023, 6, 15)),
            ("06-15-2023", "%m-%d-%Y", datetime(2023, 6, 15)),
            ("2023.06.15", "%Y.%m.%d", datetime(2023, 6, 15)),
            ("15 Jun 2023", "%d %b %Y", datetime(2023, 6, 15)),
        ]

        for date_string, date_format, expected in test_cases:
            result = dateutils.makeDate(date_string, date_format)
            assert result == expected, f"Failed for format: {date_format}"

    def test_invalid_date_raises_error(self):
        with pytest.raises(ValueError):
            dateutils.makeDate("invalid", "%Y-%m-%d")

    def test_mismatched_format_raises_error(self):
        with pytest.raises(ValueError):
            dateutils.makeDate("2023-06-15", "%d/%m/%Y")  # Wrong format


class TestConstants:
    """Test module constants"""

    def test_unix_epoche_is_datetime(self):
        assert isinstance(dateutils.UNIX_EPOCHE, datetime)

    def test_unix_epoche_is_jan_2_1970(self):
        # Should be January 2, 1970 (one day after epoch due to Windows/Py3 bug)
        assert dateutils.UNIX_EPOCHE.year == 1970
        assert dateutils.UNIX_EPOCHE.month == 1
        assert dateutils.UNIX_EPOCHE.day == 2

    def test_unit_to_keyword_mapping(self):
        # Verify the unit conversion dictionary has expected mappings
        assert dateutils.unit_to_keyword['second'] == 'seconds'
        assert dateutils.unit_to_keyword['minute'] == 'minutes'
        assert dateutils.unit_to_keyword['hour'] == 'hours'
        assert dateutils.unit_to_keyword['day'] == 'days'
        assert dateutils.unit_to_keyword['week'] == 'weeks'
        assert dateutils.unit_to_keyword['mins'] == 'minutes'
        assert dateutils.unit_to_keyword['min'] == 'minutes'
        assert dateutils.unit_to_keyword['h'] == 'hours'
        assert dateutils.unit_to_keyword['d'] == 'days'
        assert dateutils.unit_to_keyword['mth'] == 'months'
        assert dateutils.unit_to_keyword['yr'] == 'years'

    def test_fullmon_mapping(self):
        # Verify month name to number mapping
        assert dateutils.fullmon['January'] == '01'
        assert dateutils.fullmon['December'] == '12'
        assert len(dateutils.fullmon) == 12  # Should have all 12 months
