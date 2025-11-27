import pytest
from unittest.mock import patch
from fanficfare.exceptions import HTTPErrorFFF

from fanficfare.adapters.adapter_fanfictionnet import FanFictionNetSiteAdapter as ffnadapter
from tests.adapters.generic_adapter_test import GenericAdapterTestExtractChapterUrlsAndMetadata, GenericAdapterTestGetChapterText
from tests.conftest import ffn_story_page_html, ffn_chapter_1_html

# Test data for FanFiction.Net adapter
# TODO: Update with real data from actual FFN story page
SPECIFIC_TEST_DATA = {
    'adapter': ffnadapter,
    'url': 'https://www.fanfiction.net/s/4536005/1/',
    'sections': ["fanfiction.net"],
    'specific_path_adapter': 'adapter_fanfictionnet.FanFictionNetSiteAdapter',

    # Expected metadata (TODO: Update with real values from fixture)
    'title': 'Test FFN Story Title',
    'author': 'TestAuthor',
    'authorId': '123456',
    'datePublished': '2023-01-01',
    'dateUpdated': '2023-06-15',
    'intro': 'This is a test summary for the FFN story.',

    # Expected chapters
    'expected_chapters': {
        0: {
            'title': '1. Chapter One: The Start',
            'url': 'https://www.fanfiction.net/s/4536005/1/'
        },
        1: {
            'title': '2. Chapter Two: The Middle',
            'url': 'https://www.fanfiction.net/s/4536005/2/'
        },
    },

    # Fixtures
    'list_chapters_fixture': ffn_story_page_html,
    'chapter_fixture': ffn_chapter_1_html,

    # Additional FFN-specific metadata
    'status': 'Complete',
    'category': 'Harry Potter',
    'genre': 'Adventure, Fantasy',
    'rating': 'Fiction M',
    'words': '125000',
    'reviews': '2500',
    'favorites': '5000',
    'follows': '3000',
}


class TestExtractChapterUrlsAndMetadata(GenericAdapterTestExtractChapterUrlsAndMetadata):
    """Test FFN adapter metadata extraction"""

    def setup_method(self):
        self.expected_data = SPECIFIC_TEST_DATA

        super().setup_method(
            SPECIFIC_TEST_DATA['adapter'],
            SPECIFIC_TEST_DATA['url'],
            SPECIFIC_TEST_DATA['sections'],
            SPECIFIC_TEST_DATA['specific_path_adapter'],
            SPECIFIC_TEST_DATA['list_chapters_fixture'])

    @pytest.fixture(autouse=True)
    def setup_env(self):
        with patch(f'fanficfare.adapters.{self.path_adapter}.setDescription') as mock_setDescription, \
             patch(f'fanficfare.adapters.{self.path_adapter}.setCoverImage') as mock_setCoverImage, \
             patch(f'fanficfare.adapters.{self.path_adapter}._fetchUrl') as mock_fetchUrl:

            self.mock_setCoverImage = mock_setCoverImage
            self.mock_setDescription = mock_setDescription
            self.mock_fetchUrl = mock_fetchUrl

            # Return fixture HTML when adapter fetches URL
            self.mock_fetchUrl.return_value = self.fixture

            yield

    # TODO: Add FFN-specific tests
    # - test_get_reviews
    # - test_get_favorites
    # - test_get_follows
    # - test_get_rating
    # - test_get_genre


class TestGetChapterText(GenericAdapterTestGetChapterText):
    """Test FFN adapter chapter text extraction"""

    def setup_method(self):
        self.expected_data = SPECIFIC_TEST_DATA

        super().setup_method(
            SPECIFIC_TEST_DATA['adapter'],
            SPECIFIC_TEST_DATA['url'],
            SPECIFIC_TEST_DATA['sections'],
            SPECIFIC_TEST_DATA['specific_path_adapter'],
            SPECIFIC_TEST_DATA['chapter_fixture'])

    @pytest.fixture(autouse=True)
    def setup_env(self):
        with patch(f'fanficfare.adapters.{self.path_adapter}.setDescription') as mock_setDescription, \
             patch(f'fanficfare.adapters.{self.path_adapter}.setCoverImage') as mock_setCoverImage, \
             patch(f'fanficfare.adapters.{self.path_adapter}._fetchUrl') as mock_fetchUrl:

            self.mock_setCoverImage = mock_setCoverImage
            self.mock_setDescription = mock_setDescription
            self.mock_fetchUrl = mock_fetchUrl

            # Return fixture HTML when adapter fetches URL
            self.mock_fetchUrl.return_value = self.fixture

            yield


# Note: To populate with real data:
# 1. Run fanficfare CLI locally: fanficfare https://www.fanfiction.net/s/4536005/1/
# 2. Capture the HTML responses
# 3. Update fixtures_ffn.py with real HTML
# 4. Extract actual values for SPECIFIC_TEST_DATA
# 5. Run tests: python -m pytest tests/adapters/test_adapter_fanfictionnet.py -v
