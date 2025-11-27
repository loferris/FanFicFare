"""Custom exception classes for FanFicFare.

This module defines all custom exceptions used throughout the FanFicFare
application for handling various error conditions during story downloads
and processing.
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

from typing import List, Optional


class FailedToDownload(Exception):
    """Raised when story download fails.

    Attributes:
        error: Description of the download failure
    """

    def __init__(self, error: str) -> None:
        """Initialize with error message.

        Args:
            error: Description of what failed during download
        """
        self.error = error
        super().__init__(error)

    def __str__(self) -> str:
        """Return error message as string."""
        return str(self.error)


class AccessDenied(Exception):
    """Raised when access to a story or resource is denied.

    Attributes:
        error: Description of the access denial
    """

    def __init__(self, error: str) -> None:
        """Initialize with error message.

        Args:
            error: Description of why access was denied
        """
        self.error = error
        super().__init__(error)

    def __str__(self) -> str:
        """Return error message as string."""
        return str(self.error)


class RejectImage(Exception):
    """Raised when an image is rejected during processing.

    Attributes:
        error: Reason for image rejection
    """

    def __init__(self, error: str) -> None:
        """Initialize with rejection reason.

        Args:
            error: Reason why the image was rejected
        """
        self.error = error
        super().__init__(error)

    def __str__(self) -> str:
        """Return rejection reason as string."""
        return str(self.error)


class InvalidStoryURL(Exception):
    """Raised when a story URL doesn't match expected format.

    Attributes:
        url: The invalid URL provided
        domain: The expected domain/site
        example: An example of a valid URL
    """

    def __init__(self, url: str, domain: str, example: str) -> None:
        """Initialize with URL details.

        Args:
            url: The invalid URL that was provided
            domain: The expected domain/site name
            example: An example of a valid URL for this site
        """
        self.url = url
        self.domain = domain
        self.example = example
        message = f"Bad Story URL: ({url}) for site: ({domain}) Example: ({example})"
        super().__init__(message)

    def __str__(self) -> str:
        """Return formatted error message."""
        return f"Bad Story URL: ({self.url}) for site: ({self.domain}) Example: ({self.example})"


class FailedToLogin(Exception):
    """Raised when login to a site fails.

    Attributes:
        url: The URL that required login
        username: The username that was used
        passwdonly: Whether only password was required (no username)
    """

    def __init__(self, url: str, username: str, passwdonly: bool = False) -> None:
        """Initialize with login details.

        Args:
            url: The URL that required authentication
            username: The username attempted for login
            passwdonly: If True, only password was required (not username)
        """
        self.url = url
        self.username = username
        self.passwdonly = passwdonly
        super().__init__(f"Failed to login for {url}")

    def __str__(self) -> str:
        """Return formatted error message."""
        if self.passwdonly:
            return f"URL Failed, password required: ({self.url})"
        else:
            return f"Failed to Login for URL: ({self.url}) with username: ({self.username})"


class NeedTimedOneTimePassword(Exception):
    """Raised when two-factor authentication (2FA/TOTP) is required.

    Attributes:
        url: The URL requiring 2FA
    """

    def __init__(self, url: str) -> None:
        """Initialize with URL requiring 2FA.

        Args:
            url: The URL that requires TOTP authentication
        """
        self.url = url
        super().__init__(f"TOTP required for {url}")

    def __str__(self) -> str:
        """Return formatted error message."""
        return f"Timed One Time Password(TOTP) required for 2 Factor Authentication(2FA): ({self.url})"


class AdultCheckRequired(Exception):
    """Raised when story requires adult content confirmation.

    Attributes:
        url: The URL requiring adult confirmation
    """

    def __init__(self, url: str) -> None:
        """Initialize with URL requiring adult check.

        Args:
            url: The URL requiring adult status confirmation
        """
        self.url = url
        super().__init__(f"Adult check required for {url}")

    def __str__(self) -> str:
        """Return formatted error message."""
        return f"Story requires confirmation of adult status: ({self.url})"


class StoryDoesNotExist(Exception):
    """Raised when a story cannot be found at the given URL.

    Attributes:
        url: The URL where story was not found
    """

    def __init__(self, url: str) -> None:
        """Initialize with story URL.

        Args:
            url: The URL where the story was expected but not found
        """
        self.url = url
        super().__init__(f"Story does not exist: {url}")

    def __str__(self) -> str:
        """Return formatted error message."""
        return f"Story does not exist: ({self.url})"


class UnknownSite(Exception):
    """Raised when URL is from an unsupported site.

    Attributes:
        url: The unsupported URL
        supported_sites_list: List of supported site domains
    """

    def __init__(self, url: str, supported_sites_list: List[str]) -> None:
        """Initialize with URL and supported sites list.

        Args:
            url: The URL from an unsupported site
            supported_sites_list: List of supported site domains
        """
        self.url = url
        self.supported_sites_list = sorted(supported_sites_list)
        super().__init__(f"Unknown site: {url}")

    def __str__(self) -> str:
        """Return formatted error message with supported sites."""
        sites = ", ".join(self.supported_sites_list)
        return f"Unknown Site({self.url}). Supported sites: ({sites})"


class FailedToWriteOutput(Exception):
    """Raised when output file cannot be written.

    Attributes:
        error: Description of the write failure
    """

    def __init__(self, error: str) -> None:
        """Initialize with error message.

        Args:
            error: Description of why the write failed
        """
        self.error = error
        super().__init__(error)

    def __str__(self) -> str:
        """Return error message as string."""
        return str(self.error)


class PersonalIniFailed(Exception):
    """Raised when personal.ini configuration file has errors.

    Attributes:
        error: The error description
        part: The section/part of the ini file with the error
        line: The line number with the error
    """

    def __init__(self, error: str, part: str, line: str) -> None:
        """Initialize with error details.

        Args:
            error: Description of the error
            part: The section/part of the ini file
            line: The line number where error occurred
        """
        self.error = error
        self.part = part
        self.line = line
        super().__init__(f"personal.ini error: {error}")

    def __str__(self) -> str:
        """Return formatted error message."""
        return f"personal.ini Error '{self.error}' in '{self.part}' in line '{self.line}'"


class RegularExpresssionFailed(PersonalIniFailed):
    """Raised when a regular expression in personal.ini is invalid.

    Attributes:
        error: The regex error description
        part: The section/part of the ini file with the error
        line: The line number with the error
    """

    def __init__(self, error: str, part: str, line: str) -> None:
        """Initialize with regex error details.

        Args:
            error: Description of the regex error
            part: The section/part of the ini file
            line: The line number where error occurred
        """
        super().__init__(error, part, line)

    def __str__(self) -> str:
        """Return formatted error message."""
        return f"Regular Expression Error '{self.error}' in part '{self.part}' in line '{self.line}'"


class FetchEmailFailed(Exception):
    """Raised when email fetching fails.

    Attributes:
        error: Description of the fetch failure
    """

    def __init__(self, error: str) -> None:
        """Initialize with error message.

        Args:
            error: Description of why email fetch failed
        """
        self.error = error
        super().__init__(error)

    def __str__(self) -> str:
        """Return error message as string."""
        return str(self.error)


class CacheCleared(Exception):
    """Raised when cache is cleared (informational exception).

    Attributes:
        error: Description of cache clearing
    """

    def __init__(self, error: str) -> None:
        """Initialize with message.

        Args:
            error: Description of cache clearing operation
        """
        self.error = error
        super().__init__(error)

    def __str__(self) -> str:
        """Return message as string."""
        return str(self.error)


class HTTPErrorFFF(Exception):
    """Raised when HTTP request fails.

    Attributes:
        url: The URL that failed
        status_code: HTTP status code
        error_msg: Error message from the request
        data: Optional response data
    """

    def __init__(
        self,
        url: str,
        status_code: int,
        error_msg: str,
        data: Optional[bytes] = None
    ) -> None:
        """Initialize with HTTP error details.

        Args:
            url: The URL that returned an error
            status_code: The HTTP status code (e.g., 404, 500)
            error_msg: Descriptive error message
            data: Optional response body data
        """
        self.url = url
        self.status_code = status_code
        self.error_msg = error_msg
        self.data = data
        super().__init__(f"HTTP {status_code}: {error_msg}")

    def __str__(self) -> str:
        """Return formatted error message.

        Avoids duplicating URL if it's already in the error message.
        """
        if self.url in self.error_msg:
            return f"HTTP Error in FFF '{self.error_msg}'({self.status_code})"
        else:
            return f"HTTP Error in FFF '{self.error_msg}'({self.status_code}) URL:'{self.url}'"


class BrowserCacheException(Exception):
    """Raised when browser cache operations fail.

    This is a base exception for browser cache-related errors.
    """
    pass
