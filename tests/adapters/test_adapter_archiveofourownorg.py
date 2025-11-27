import pytest
from unittest.mock import patch
from fanficfare.exceptions import HTTPErrorFFF

from fanficfare.adapters.adapter_archiveofourownorg import ArchiveOfOurOwnOrgAdapter as ao3adapter
from tests.adapters.generic_adapter_test import GenericAdapterTestExtractChapterUrlsAndMetadata, GenericAdapterTestGetChapterText
from tests.conftest import ao3_work_page_html, ao3_chapter_1_html

# Test data for AO3 adapter
# TODO: Update with real data from actual AO3 story page
SPECIFIC_TEST_DATA = {
    'adapter': ao3adapter,
    'url': 'https://archiveofourown.org/works/507461',
    'sections': ["archiveofourown.org"],
    'specific_path_adapter': 'adapter_archiveofourownorg.ArchiveOfOurOwnOrgAdapter',

    # Expected metadata (TODO: Update with real values from fixture)
    'title': 'Test AO3 Story Title',
    'author': 'TestAuthor',
    'authorId': 'TestAuthor',
    'datePublished': '2023-01-15',
    'dateUpdated': '2023-06-20',
    'intro': 'This is a test summary for the AO3 story.',

    # Expected chapters
    'expected_chapters': {
        0: {
            'title': 'Chapter 1: The Beginning',
            'url': 'https://archiveofourown.org/works/507461/chapters/1'
        },
    },

    # Fixtures
    'list_chapters_fixture': ao3_work_page_html,
    'chapter_fixture': ao3_chapter_1_html,

    # Additional AO3-specific metadata
    'status': 'Completed',
    'category': 'Harry Potter - J. K. Rowling',
    'genre': 'Time Travel, Fix-It',
    'rating': 'Mature',
    'words': '50000',
    'kudos': '1500',
}


class TestExtractChapterUrlsAndMetadata(GenericAdapterTestExtractChapterUrlsAndMetadata):
    """Test AO3 adapter metadata extraction"""

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

    # TODO: Add AO3-specific tests
    # - test_get_kudos
    # - test_get_bookmarks
    # - test_get_rating
    # - test_get_warnings
    # - test_get_tags


class TestGetChapterText(GenericAdapterTestGetChapterText):
    """Test AO3 adapter chapter text extraction"""

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
# 1. Run fanficfare CLI locally: fanficfare https://archiveofourown.org/works/507461
# 2. Capture the HTML responses
# 3. Update fixtures_ao3.py with real HTML
# 4. Extract actual values for SPECIFIC_TEST_DATA
# 5. Run tests: python -m pytest tests/adapters/test_adapter_archiveofourownorg.py -v
