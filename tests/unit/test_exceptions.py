import pytest
from fanficfare import exceptions


class TestFailedToDownload:
    """Test FailedToDownload exception"""

    def test_exception_creation(self):
        error = exceptions.FailedToDownload("Connection timeout")
        assert error.error == "Connection timeout"
        assert str(error) == "Connection timeout"

    def test_exception_raised(self):
        with pytest.raises(exceptions.FailedToDownload) as exc_info:
            raise exceptions.FailedToDownload("Test error")
        assert "Test error" in str(exc_info.value)


class TestAccessDenied:
    """Test AccessDenied exception"""

    def test_exception_creation(self):
        error = exceptions.AccessDenied("403 Forbidden")
        assert error.error == "403 Forbidden"
        assert str(error) == "403 Forbidden"

    def test_exception_raised(self):
        with pytest.raises(exceptions.AccessDenied):
            raise exceptions.AccessDenied("Access denied")


class TestInvalidStoryURL:
    """Test InvalidStoryURL exception"""

    def test_exception_creation(self):
        error = exceptions.InvalidStoryURL(
            "https://invalid.com/story/123",
            "example.com",
            "https://example.com/works/123"
        )
        assert error.url == "https://invalid.com/story/123"
        assert error.domain == "example.com"
        assert error.example == "https://example.com/works/123"

    def test_exception_message(self):
        error = exceptions.InvalidStoryURL(
            "https://bad.url/123",
            "goodsite.com",
            "https://goodsite.com/story/123"
        )
        message = str(error)
        assert "Bad Story URL" in message
        assert "https://bad.url/123" in message
        assert "goodsite.com" in message
        assert "https://goodsite.com/story/123" in message


class TestFailedToLogin:
    """Test FailedToLogin exception"""

    def test_with_username(self):
        error = exceptions.FailedToLogin(
            "https://site.com/login",
            "testuser",
            passwdonly=False
        )
        message = str(error)
        assert "Failed to Login" in message
        assert "testuser" in message
        assert "https://site.com/login" in message

    def test_password_only(self):
        error = exceptions.FailedToLogin(
            "https://site.com/story/123",
            "testuser",
            passwdonly=True
        )
        message = str(error)
        assert "password required" in message
        assert "https://site.com/story/123" in message
        # Username should not be in message when passwdonly=True
        assert "testuser" not in message


class TestNeedTimedOneTimePassword:
    """Test NeedTimedOneTimePassword exception"""

    def test_exception_creation(self):
        error = exceptions.NeedTimedOneTimePassword("https://site.com/2fa")
        assert error.url == "https://site.com/2fa"

    def test_exception_message(self):
        error = exceptions.NeedTimedOneTimePassword("https://example.com/verify")
        message = str(error)
        assert "TOTP" in message
        assert "2FA" in message
        assert "https://example.com/verify" in message


class TestAdultCheckRequired:
    """Test AdultCheckRequired exception"""

    def test_exception_creation(self):
        error = exceptions.AdultCheckRequired("https://site.com/adult/123")
        assert error.url == "https://site.com/adult/123"

    def test_exception_message(self):
        error = exceptions.AdultCheckRequired("https://example.com/mature/456")
        message = str(error)
        assert "adult status" in message
        assert "https://example.com/mature/456" in message


class TestStoryDoesNotExist:
    """Test StoryDoesNotExist exception"""

    def test_exception_creation(self):
        error = exceptions.StoryDoesNotExist("https://site.com/deleted/123")
        assert error.url == "https://site.com/deleted/123"

    def test_exception_message(self):
        error = exceptions.StoryDoesNotExist("https://example.com/gone/456")
        message = str(error)
        assert "does not exist" in message
        assert "https://example.com/gone/456" in message


class TestUnknownSite:
    """Test UnknownSite exception"""

    def test_exception_creation(self):
        sites = ["ao3.org", "fanfiction.net", "wattpad.com"]
        error = exceptions.UnknownSite("https://unknown.com/story/123", sites)
        assert error.url == "https://unknown.com/story/123"
        assert error.supported_sites_list == sorted(sites)

    def test_exception_message(self):
        sites = ["site1.com", "site2.com", "site3.com"]
        error = exceptions.UnknownSite("https://badsite.com", sites)
        message = str(error)
        assert "Unknown Site" in message
        assert "https://badsite.com" in message
        assert "site1.com" in message
        assert "site2.com" in message
        assert "site3.com" in message

    def test_sites_are_sorted(self):
        sites = ["zzz.com", "aaa.com", "mmm.com"]
        error = exceptions.UnknownSite("https://test.com", sites)
        # Should be sorted alphabetically
        assert error.supported_sites_list == ["aaa.com", "mmm.com", "zzz.com"]


class TestPersonalIniFailed:
    """Test PersonalIniFailed exception"""

    def test_exception_creation(self):
        error = exceptions.PersonalIniFailed("syntax error", "section", "line 5")
        assert error.error == "syntax error"
        assert error.part == "section"
        assert error.line == "line 5"

    def test_exception_message(self):
        error = exceptions.PersonalIniFailed("invalid value", "defaults", "15")
        message = str(error)
        assert "personal.ini Error" in message
        assert "invalid value" in message
        assert "defaults" in message
        assert "15" in message


class TestRegularExpressionFailed:
    """Test RegularExpresssionFailed exception"""

    def test_exception_inherits_personal_ini(self):
        error = exceptions.RegularExpresssionFailed("bad regex", "replacements", "10")
        assert isinstance(error, exceptions.PersonalIniFailed)

    def test_exception_message(self):
        error = exceptions.RegularExpresssionFailed("unterminated group", "section", "20")
        message = str(error)
        assert "Regular Expression Error" in message
        assert "unterminated group" in message
        assert "section" in message
        assert "20" in message


class TestHTTPErrorFFF:
    """Test HTTPErrorFFF exception"""

    def test_exception_creation(self):
        error = exceptions.HTTPErrorFFF(
            "https://site.com/story/123",
            404,
            "Not Found"
        )
        assert error.url == "https://site.com/story/123"
        assert error.status_code == 404
        assert error.error_msg == "Not Found"

    def test_exception_with_data(self):
        error = exceptions.HTTPErrorFFF(
            "https://site.com/api",
            500,
            "Internal Server Error",
            data={"error": "database connection failed"}
        )
        assert error.data == {"error": "database connection failed"}

    def test_message_without_url_in_error(self):
        error = exceptions.HTTPErrorFFF(
            "https://example.com/test",
            403,
            "Forbidden"
        )
        message = str(error)
        assert "HTTP Error in FFF" in message
        assert "Forbidden" in message
        assert "403" in message
        assert "https://example.com/test" in message

    def test_message_with_url_in_error(self):
        # When URL is already in error message, don't duplicate it
        error = exceptions.HTTPErrorFFF(
            "https://example.com/test",
            404,
            "Not found: https://example.com/test"
        )
        message = str(error)
        assert "HTTP Error in FFF" in message
        assert "404" in message
        # URL should only appear once (in error_msg, not appended)
        assert message.count("https://example.com/test") == 1


class TestOtherExceptions:
    """Test remaining exception classes"""

    def test_reject_image(self):
        error = exceptions.RejectImage("Image too large")
        assert str(error) == "Image too large"

    def test_failed_to_write_output(self):
        error = exceptions.FailedToWriteOutput("Permission denied")
        assert str(error) == "Permission denied"

    def test_fetch_email_failed(self):
        error = exceptions.FetchEmailFailed("SMTP connection failed")
        assert str(error) == "SMTP connection failed"

    def test_cache_cleared(self):
        error = exceptions.CacheCleared("Cache was cleared")
        assert str(error) == "Cache was cleared"

    def test_browser_cache_exception(self):
        error = exceptions.BrowserCacheException()
        assert isinstance(error, Exception)
        # BrowserCacheException doesn't have custom __str__, uses default
