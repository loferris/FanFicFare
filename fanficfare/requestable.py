"""HTTP request handling with encoding detection and decoding.

This module provides the Requestable class which handles HTTP GET/POST requests
with automatic encoding detection and decoding. It supports multiple encoding
strategies including chardet auto-detection and fallback chains.
"""

# Copyright 2021 FanFicFare team
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
#

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

try:
    import chardet
except ImportError:
    chardet = None

from .configurable import Configurable
from .htmlcleanup import reduce_zalgo


class Requestable(Configurable):
    """Base class for making HTTP requests with automatic encoding handling.

    Extends Configurable to provide HTTP request capabilities with:
    - Automatic encoding detection and decoding
    - Multiple encoding fallback strategies
    - Optional chardet auto-detection
    - Zalgo text reduction
    - Support for GET/POST requests with caching

    Attributes:
        configuration: Configuration object from parent Configurable class
    """

    def __init__(self, configuration: Any) -> None:
        """Initialize Requestable with configuration.

        Args:
            configuration: Configuration object containing settings for
                          encoding, fetcher, and other options
        """
        Configurable.__init__(self, configuration)

    def do_decode(self, data: Union[bytes, str]) -> str:
        """Decode bytes to string using configured encoding strategies.

        Website encoding detection and decoding. In theory, each website reports
        the character encoding they use for each page. In practice, some sites
        report it incorrectly. Each adapter has a default list, usually
        "utf8, Windows-1252" or "Windows-1252, utf8".

        The special value 'auto' will call chardet and use the encoding it reports
        if it has +90% confidence. 'auto' is not reliable. Windows-1252 is a
        superset of iso-8859-1. Most sites that claim to be iso-8859-1 (and some
        that claim to be utf8) are really Windows-1252.

        Args:
            data: Bytes to decode, or string if already decoded (from pickle)

        Returns:
            Decoded string. Falls back to ASCII-only if all encodings fail.

        Examples:
            >>> # requestable.do_decode(b"Hello World")
            >>> # "Hello World"
        """
        if not hasattr(data, 'decode'):
            # py3 str() from pickle doesn't have .decode and is
            # already decoded. Should always be bytes now (Jan2021),
            # but keeping this just in case.
            return data

        decode = self.getConfigList(
            'website_encodings',
            default=["utf8", "Windows-1252", "iso-8859-1"]
        )

        for code in decode:
            try:
                logger.debug(f"Encoding: {code}")
                errors = None
                if ':' in code:
                    (code, errors) = code.split(':')

                if code == "auto":
                    if not chardet:
                        logger.info("chardet not available, skipping 'auto' encoding")
                        continue
                    detected = chardet.detect(data)
                    confidence_limit = float(self.getConfig("chardet_confidence_limit", 0.9))
                    if detected['confidence'] > confidence_limit:
                        logger.debug(
                            f"using chardet detected encoding: {detected['encoding']} "
                            f"({detected['confidence']})"
                        )
                        code = detected['encoding']
                    else:
                        logger.debug(
                            f"chardet confidence too low: {detected['encoding']} "
                            f"({detected['confidence']})"
                        )
                        continue

                if errors == 'ignore':  # only allow ignore
                    return data.decode(code, errors='ignore')
                else:
                    return data.decode(code)

            except Exception as e:
                logger.debug(f"code failed: {code}")
                logger.debug(e)

        logger.info(f"Could not decode story, tried: {decode} Stripping non-ASCII.")
        # Python 3: strip non-ASCII bytes
        return "".join([chr(x) for x in data if x < 128])

    def do_reduce_zalgo(self, data: str) -> str:
        """Apply zalgo text reduction if configured.

        Zalgo text is text with excessive combining diacritical marks that can
        make text unreadable. This method reduces the number of combining marks
        to a maximum threshold if max_zalgo configuration is set.

        Args:
            data: Text potentially containing zalgo

        Returns:
            Text with zalgo reduced (if configured), or original text

        Examples:
            >>> # requestable.do_reduce_zalgo("normal text")
            >>> # "normal text"
        """
        max_zalgo = int(self.getConfig('max_zalgo', -1))
        if max_zalgo > -1:
            logger.debug(f"Applying max_zalgo: {max_zalgo}")
            try:
                return reduce_zalgo(data, max_zalgo)
            except Exception as e:
                logger.warning(f"reduce_zalgo failed ({e}), continuing.")
        return data

    def decode_data(self, data: Union[bytes, str]) -> str:
        """Decode data and apply zalgo reduction.

        Convenience method that combines do_decode() and do_reduce_zalgo().

        Args:
            data: Bytes or string to decode and clean

        Returns:
            Decoded and zalgo-reduced string
        """
        return self.do_reduce_zalgo(self.do_decode(data))

    def mod_url_request(self, url: str) -> str:
        """Modify URL before making request.

        Hook method that can be overridden by subclasses to modify URLs
        before requests are made. Default implementation returns URL unchanged.

        Args:
            url: Original URL

        Returns:
            Modified URL (or original if not overridden)
        """
        return url

    def post_request(
        self,
        url: str,
        parameters: Optional[Dict[str, Any]] = None,
        usecache: bool = True
    ) -> str:
        """Make POST request and decode response.

        Args:
            url: URL to POST to
            parameters: POST parameters/data
            usecache: Whether to use cached response if available

        Returns:
            Decoded response text
        """
        data = self.configuration.get_fetcher().post_request(
            self.mod_url_request(url),
            parameters=parameters,
            usecache=usecache
        )
        data = self.decode_data(data)
        return data

    def get_request_redirected(
        self,
        url: str,
        usecache: bool = True
    ) -> Tuple[str, str]:
        """Make GET request and return data with final URL after redirects.

        Args:
            url: URL to GET
            usecache: Whether to use cached response if available

        Returns:
            Tuple of (decoded response text, final URL after redirects)
        """
        (data, rurl) = self.configuration.get_fetcher().get_request_redirected(
            self.mod_url_request(url),
            usecache=usecache
        )[:2]
        data = self.decode_data(data)
        return (data, rurl)

    def get_request(self, url: str, usecache: bool = True) -> str:
        """Make GET request and return decoded response.

        Args:
            url: URL to GET
            usecache: Whether to use cached response if available

        Returns:
            Decoded response text
        """
        return self.get_request_redirected(
            self.mod_url_request(url),
            usecache
        )[0]

    def get_request_raw(
        self,
        url: str,
        referer: Optional[str] = None,
        usecache: bool = True,
        image: bool = False
    ) -> bytes:
        """Make GET request and return raw bytes without decoding.

        Used for binary content like images. The referer parameter is
        commonly used with raw requests for images.

        Args:
            url: URL to GET
            referer: Referer header value
            usecache: Whether to use cached response if available
            image: Whether this is an image request

        Returns:
            Raw response bytes (not decoded)
        """
        return self.configuration.get_fetcher().get_request_redirected(
            self.mod_url_request(url),
            referer=referer,
            usecache=usecache,
            image=image
        )[0]
