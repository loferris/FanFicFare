"""Unit tests for fanficfare.requestable module."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from fanficfare.requestable import Requestable
from fanficfare.configurable import Configurable


class TestRequestable:
    """Test Requestable class encoding and request handling."""

    @pytest.fixture
    def mock_configuration(self):
        """Create a mock configuration object."""
        config = Mock()
        config.getConfig = Mock(return_value=None)
        config.getConfigList = Mock(return_value=["utf8", "Windows-1252"])
        config.get_fetcher = Mock()
        return config

    @pytest.fixture
    def requestable(self, mock_configuration):
        """Create a Requestable instance with mock configuration."""
        req = Requestable(mock_configuration)
        return req

    def test_init(self, mock_configuration):
        """Test Requestable initialization."""
        req = Requestable(mock_configuration)
        assert isinstance(req, Requestable)
        assert isinstance(req, Configurable)

    def test_do_decode_utf8(self, requestable, mock_configuration):
        """Test decoding UTF-8 encoded data."""
        mock_configuration.getConfigList.return_value = ["utf8"]
        data = "Hello World".encode('utf-8')
        result = requestable.do_decode(data)
        assert result == "Hello World"

    def test_do_decode_windows1252(self, requestable, mock_configuration):
        """Test decoding Windows-1252 encoded data."""
        mock_configuration.getConfigList.return_value = ["Windows-1252"]
        # Windows-1252 specific character (smart quote)
        data = b"Hello\x92World"  # \x92 is right single quote in Windows-1252
        result = requestable.do_decode(data)
        assert "Hello" in result
        assert "World" in result

    def test_do_decode_fallback_chain(self, requestable, mock_configuration):
        """Test falling back through encoding chain."""
        mock_configuration.getConfigList.return_value = ["ascii", "utf8", "Windows-1252"]
        # UTF-8 data that's not valid ASCII
        data = "Café".encode('utf-8')
        result = requestable.do_decode(data)
        assert result == "Café"

    def test_do_decode_with_errors_ignore(self, requestable, mock_configuration):
        """Test decoding with errors='ignore' parameter."""
        mock_configuration.getConfigList.return_value = ["utf8:ignore"]
        # Invalid UTF-8 sequence
        data = b"Hello\xff\xfeWorld"
        result = requestable.do_decode(data)
        # Should skip invalid bytes and continue
        assert "Hello" in result
        assert "World" in result

    @patch('fanficfare.requestable.chardet')
    def test_do_decode_auto_high_confidence(self, mock_chardet, requestable, mock_configuration):
        """Test auto-detection with high confidence."""
        mock_configuration.getConfigList.return_value = ["auto"]
        mock_configuration.getConfig.return_value = "0.9"

        # Mock chardet to detect UTF-8 with 95% confidence
        mock_chardet.detect.return_value = {
            'encoding': 'utf-8',
            'confidence': 0.95
        }

        data = "Test".encode('utf-8')
        result = requestable.do_decode(data)
        assert result == "Test"
        mock_chardet.detect.assert_called_once_with(data)

    @patch('fanficfare.requestable.chardet')
    def test_do_decode_auto_low_confidence(self, mock_chardet, requestable, mock_configuration):
        """Test auto-detection with low confidence falls through."""
        mock_configuration.getConfigList.return_value = ["auto", "utf8"]
        mock_configuration.getConfig.return_value = "0.9"

        # Mock chardet to detect with only 50% confidence
        mock_chardet.detect.return_value = {
            'encoding': 'utf-8',
            'confidence': 0.5
        }

        data = "Test".encode('utf-8')
        result = requestable.do_decode(data)
        assert result == "Test"
        # Should fall through to utf8 in the list

    @patch('fanficfare.requestable.chardet', None)
    def test_do_decode_auto_no_chardet(self, requestable, mock_configuration):
        """Test auto-detection when chardet is not available."""
        mock_configuration.getConfigList.return_value = ["auto", "utf8"]

        data = "Test".encode('utf-8')
        result = requestable.do_decode(data)
        assert result == "Test"
        # Should skip 'auto' and use utf8

    def test_do_decode_all_fail_strips_ascii(self, requestable, mock_configuration):
        """Test fallback to ASCII stripping when all encodings fail."""
        mock_configuration.getConfigList.return_value = ["ascii"]
        # Data that's not valid in any encoding (but contains ASCII)
        data = b"Hello\xff\xfe\xfd\xfcWorld"
        result = requestable.do_decode(data)
        # Should contain only ASCII characters
        assert "Hello" in result
        assert "World" in result
        # Non-ASCII should be stripped
        for char in result:
            assert ord(char) < 128

    def test_do_decode_already_string(self, requestable):
        """Test handling data that's already a string (from pickle)."""
        data = "Already decoded"
        result = requestable.do_decode(data)
        assert result == "Already decoded"

    def test_do_reduce_zalgo_disabled(self, requestable, mock_configuration):
        """Test zalgo reduction when disabled (default)."""
        mock_configuration.getConfig.return_value = "-1"
        data = "Normal text"
        result = requestable.do_reduce_zalgo(data)
        assert result == "Normal text"

    @patch('fanficfare.requestable.reduce_zalgo')
    def test_do_reduce_zalgo_enabled(self, mock_reduce_zalgo, requestable, mock_configuration):
        """Test zalgo reduction when enabled."""
        mock_configuration.getConfig.return_value = "5"
        mock_reduce_zalgo.return_value = "cleaned text"

        data = "z̴̡̢̧͖̹̼̮̺̫̳̪̰͚̻̣̈́̈́̈́ą̷̧̛̛̙̱̮̗̟̹͚̮̼̭̥͔̘̏̇̈́͂̊̈́̊̄͗̚l̴̨̡̜̺̰̟̳̙̘̙̱͎̼̇̓̌͂̓̑̐̾͐̾̔̕g̴̢̨̛̛̮̠̹̼͔̼̪̫̼̯͐̌̈́̓̅̈́͘͜ơ̸̢̨̼̪̠̝̤̖͔̗͖̼̪̈́̆̑̓̌̓͑́̚"
        result = requestable.do_reduce_zalgo(data)
        assert result == "cleaned text"
        mock_reduce_zalgo.assert_called_once_with(data, 5)

    @patch('fanficfare.requestable.reduce_zalgo')
    def test_do_reduce_zalgo_exception_handling(self, mock_reduce_zalgo, requestable, mock_configuration):
        """Test zalgo reduction handles exceptions gracefully."""
        mock_configuration.getConfig.return_value = "5"
        mock_reduce_zalgo.side_effect = ValueError("Test error")

        data = "test data"
        result = requestable.do_reduce_zalgo(data)
        # Should return original data on exception
        assert result == "test data"

    def test_decode_data_combines_both(self, requestable, mock_configuration):
        """Test decode_data combines decoding and zalgo reduction."""
        mock_configuration.getConfigList.return_value = ["utf8"]
        mock_configuration.getConfig.return_value = "-1"

        data = "Test".encode('utf-8')
        result = requestable.decode_data(data)
        assert result == "Test"

    def test_mod_url_request_default(self, requestable):
        """Test default URL modification (no-op)."""
        url = "https://example.com/test"
        result = requestable.mod_url_request(url)
        assert result == url

    def test_post_request(self, requestable, mock_configuration):
        """Test POST request with decoding."""
        mock_fetcher = Mock()
        mock_fetcher.post_request.return_value = b"Response data"
        mock_configuration.get_fetcher.return_value = mock_fetcher
        mock_configuration.getConfigList.return_value = ["utf8"]
        mock_configuration.getConfig.return_value = "-1"

        result = requestable.post_request("https://example.com/post", parameters={"key": "value"})

        assert result == "Response data"
        mock_fetcher.post_request.assert_called_once_with(
            "https://example.com/post",
            parameters={"key": "value"},
            usecache=True
        )

    def test_get_request_redirected(self, requestable, mock_configuration):
        """Test GET request with redirect tracking."""
        mock_fetcher = Mock()
        mock_fetcher.get_request_redirected.return_value = (b"Response", "https://example.com/redirected", None)
        mock_configuration.get_fetcher.return_value = mock_fetcher
        mock_configuration.getConfigList.return_value = ["utf8"]
        mock_configuration.getConfig.return_value = "-1"

        data, rurl = requestable.get_request_redirected("https://example.com/test")

        assert data == "Response"
        assert rurl == "https://example.com/redirected"

    def test_get_request(self, requestable, mock_configuration):
        """Test simple GET request."""
        mock_fetcher = Mock()
        mock_fetcher.get_request_redirected.return_value = (b"Response", "https://example.com/test", None)
        mock_configuration.get_fetcher.return_value = mock_fetcher
        mock_configuration.getConfigList.return_value = ["utf8"]
        mock_configuration.getConfig.return_value = "-1"

        result = requestable.get_request("https://example.com/test")

        assert result == "Response"

    def test_get_request_raw(self, requestable, mock_configuration):
        """Test raw GET request without decoding."""
        mock_fetcher = Mock()
        mock_fetcher.get_request_redirected.return_value = (b"\xff\xfe\xfd", "url", None)
        mock_configuration.get_fetcher.return_value = mock_fetcher

        result = requestable.get_request_raw("https://example.com/image.jpg", image=True)

        # Should return raw bytes, not decoded
        assert result == b"\xff\xfe\xfd"
        mock_fetcher.get_request_redirected.assert_called_once_with(
            "https://example.com/image.jpg",
            referer=None,
            usecache=True,
            image=True
        )

    def test_get_request_with_referer(self, requestable, mock_configuration):
        """Test raw GET request with referer header."""
        mock_fetcher = Mock()
        mock_fetcher.get_request_redirected.return_value = (b"data", "url", None)
        mock_configuration.get_fetcher.return_value = mock_fetcher

        result = requestable.get_request_raw(
            "https://example.com/image.jpg",
            referer="https://example.com",
            image=True
        )

        mock_fetcher.get_request_redirected.assert_called_once_with(
            "https://example.com/image.jpg",
            referer="https://example.com",
            usecache=True,
            image=True
        )
