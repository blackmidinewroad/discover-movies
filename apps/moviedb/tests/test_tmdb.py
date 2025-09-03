import gzip
import json
import logging
from datetime import date
from io import BytesIO
from unittest.mock import AsyncMock, Mock, patch

from django.test import TestCase
from django.utils import timezone
from requests.exceptions import HTTPError, RequestException

from apps.moviedb.integrations.tmdb.api import TMDB, asyncTMDB
from apps.moviedb.integrations.tmdb.id_exports import IDExport


class IDExportTests(TestCase):
    """Tests for the IDExport class."""

    def setUp(self):
        self.id_export = IDExport()
        self.media_type = 'movie'
        self.published_date = '09_03_2025'
        self.sample_data = [{'id': 1, 'popularity': 85.0}, {'id': 2, 'popularity': 75.0}, {'id': 3, 'popularity': 90.0}]
        self.compressed_data = self._create_compressed_data(self.sample_data)

    def _create_compressed_data(self, data):
        """Helper to create gzip-compressed JSON data."""
        buffer = BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
            for item in data:
                gz_file.write(json.dumps(item).encode('utf-8') + b'\n')
        return buffer.getvalue()

    def test_build_url_with_date(self):
        url, date = self.id_export._build_url(self.media_type, self.published_date)
        self.assertEqual(url, 'http://files.tmdb.org/p/exports/movie_ids_09_03_2025.json.gz')
        self.assertEqual(date, '09_03_2025')

    def test_build_url_without_date(self):
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.datetime(2025, 9, 3)
            url, date = self.id_export._build_url(self.media_type, None)
            self.assertEqual(url, 'http://files.tmdb.org/p/exports/movie_ids_09_03_2025.json.gz')
            self.assertEqual(date, '09_03_2025')

    def test_build_url_invalid_media_type(self):
        url, date = self.id_export._build_url('invalid', self.published_date)
        self.assertEqual(url, 'http://files.tmdb.org/p/exports/_ids_09_03_2025.json.gz')
        self.assertEqual(date, '09_03_2025')

    @patch('requests.get')
    def test_fetch_id_file_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = self.compressed_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.id_export._fetch_id_file(self.media_type, self.published_date)
        self.assertEqual(result, self.compressed_data)
        mock_get.assert_called_once_with('http://files.tmdb.org/p/exports/movie_ids_09_03_2025.json.gz', timeout=20)

    @patch('requests.get')
    def test_fetch_id_file_request_exception(self, mock_get):
        mock_get.side_effect = RequestException('Network error')
        with patch('logging.Logger.error') as mock_logger:
            result = self.id_export._fetch_id_file(self.media_type, self.published_date)
            self.assertIsNone(result)
            mock_logger.assert_called_once_with(
                "Couldn't fetch ID file for media type: %s, date: %s.", self.media_type, self.published_date
            )

    def test_get_ids_no_sort_no_popularity(self):
        ids = self.id_export._get_ids(self.compressed_data)
        self.assertEqual(ids, [1, 2, 3])

    def test_get_ids_sort_by_popularity(self):
        ids = self.id_export._get_ids(self.compressed_data, sort_by_popularity=True)
        self.assertEqual(ids, [3, 1, 2])

    def test_get_ids_include_popularity(self):
        ids = self.id_export._get_ids(self.compressed_data, include_popularity=True)
        self.assertEqual(ids, [(1, 85.0), (2, 75.0), (3, 90.0)])

    def test_get_ids_sort_and_include_popularity(self):
        ids = self.id_export._get_ids(self.compressed_data, sort_by_popularity=True, include_popularity=True)
        self.assertEqual(ids, [(3, 90.0), (1, 85.0), (2, 75.0)])

    def test_get_ids_empty_file(self):
        empty_data = self._create_compressed_data([])
        ids = self.id_export._get_ids(empty_data)
        self.assertEqual(ids, [])

    def test_get_ids_missing_popularity(self):
        data = [{'id': 1}, {'id': 2, 'popularity': 75.0}]
        compressed_data = self._create_compressed_data(data)
        ids = self.id_export._get_ids(compressed_data, include_popularity=True)
        self.assertEqual(ids, [(1, 0), (2, 75.0)])

    @patch('apps.moviedb.integrations.tmdb.id_exports.IDExport._fetch_id_file')
    def test_fetch_ids_valid_media_type(self, mock_fetch):
        mock_fetch.return_value = self.compressed_data
        ids = self.id_export.fetch_ids('movie', self.published_date)
        self.assertEqual(ids, [1, 2, 3])
        mock_fetch.assert_called_once_with('movie', self.published_date)

    @patch('apps.moviedb.integrations.tmdb.id_exports.IDExport._fetch_id_file')
    def test_fetch_ids_sort_by_popularity(self, mock_fetch):
        mock_fetch.return_value = self.compressed_data
        ids = self.id_export.fetch_ids('movie', self.published_date, sort_by_popularity=True)
        self.assertEqual(ids, [3, 1, 2])

    @patch('apps.moviedb.integrations.tmdb.id_exports.IDExport._fetch_id_file')
    def test_fetch_ids_include_popularity(self, mock_fetch):
        mock_fetch.return_value = self.compressed_data
        ids = self.id_export.fetch_ids('movie', self.published_date, include_popularity=True)
        self.assertEqual(ids, [(1, 85.0), (2, 75.0), (3, 90.0)])

    def test_fetch_ids_invalid_media_type(self):
        with self.assertRaises(ValueError) as cm:
            self.id_export.fetch_ids('invalid')
        self.assertTrue('Invalid media type' in str(cm.exception))

    @patch('apps.moviedb.integrations.tmdb.id_exports.IDExport._fetch_id_file')
    def test_fetch_ids_fetch_failure(self, mock_fetch):
        mock_fetch.return_value = None
        result = self.id_export.fetch_ids('movie', self.published_date)
        self.assertIsNone(result)


class TMDBTests(TestCase):
    """Tests for the TMDB class."""

    def setUp(self):
        self.tmdb = TMDB()
        self.sample_genres = [{'id': 28, 'name': 'Action'}]
        self.sample_countries = [{'iso_3166_1': 'US', 'name': 'United States'}]
        self.sample_languages = [{'iso_639_1': 'en', 'name': 'English'}]
        self.sample_movie = {'id': 1, 'title': 'The Matrix', 'adult': False}
        self.sample_person = {'id': 1, 'name': 'John Doe'}
        self.sample_company = {'id': 1, 'name': 'Paramount'}
        self.sample_collection = {'id': 1, 'name': 'Star Wars Collection'}
        self.sample_page = {'results': [self.sample_movie], 'total_pages': 1}
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_build_url(self):
        url = self.tmdb._build_url('movie/1', {'language': 'en-US'})
        self.assertEqual(url, 'https://api.themoviedb.org/3/movie/1?language=en-US')

    def test_build_url_no_params(self):
        url = self.tmdb._build_url('movie/1')
        self.assertEqual(url, 'https://api.themoviedb.org/3/movie/1?')

    @patch('requests.Session.get')
    def test_fetch_data_success(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_movie
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.tmdb._fetch_data('movie/1', {'language': 'en-US'})
        self.assertEqual(result, self.sample_movie)
        mock_get.assert_called_once_with('https://api.themoviedb.org/3/movie/1?language=en-US', timeout=10)

    @patch('requests.Session.get')
    def test_fetch_data_unauthorized(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
        mock_get.return_value = mock_response

        with patch('logging.Logger.error') as mock_logger:
            with self.assertRaises(HTTPError):
                self.tmdb._fetch_data('movie/1')
            mock_logger.assert_called_once()

    @patch('requests.Session.get')
    def test_fetch_data_request_exception(self, mock_get):
        mock_get.side_effect = RequestException("Network error")
        with patch('logging.Logger.warning') as mock_logger:
            result = self.tmdb._fetch_data('movie/1')
            self.assertIsNone(result)
            mock_logger.assert_called_once_with('Failed to fetch data: %s.', 'RequestException')

    @patch('requests.Session.get')
    def test_fetch_genres(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {'genres': self.sample_genres}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.tmdb.fetch_genres(language='en')
        self.assertEqual(result, self.sample_genres)
        mock_get.assert_called_once_with('https://api.themoviedb.org/3/genre/movie/list?language=en', timeout=10)

    @patch('requests.Session.get')
    def test_fetch_countries(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = self.sample_countries
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.tmdb.fetch_countries(language='en-US')
        self.assertEqual(result, self.sample_countries)
        mock_get.assert_called_once_with('https://api.themoviedb.org/3/configuration/countries?language=en-US', timeout=10)

    @patch('requests.Session.get')
    def test_fetch_languages(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = self.sample_languages
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.tmdb.fetch_languages()
        self.assertEqual(result, self.sample_languages)
        mock_get.assert_called_once_with('https://api.themoviedb.org/3/configuration/languages?', timeout=10)

    @patch('requests.Session.get')
    def test_fetch_movie_by_id(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = self.sample_movie
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.tmdb.fetch_movie_by_id(1, language='en-US', append_to_response=['credits'])
        self.assertEqual(result, self.sample_movie)
        mock_get.assert_called_once_with('https://api.themoviedb.org/3/movie/1?language=en-US&append_to_response=credits', timeout=10)

    @patch('requests.Session.get')
    def test_fetch_person_by_id(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = self.sample_person
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.tmdb.fetch_person_by_id(1, language='en-US')
        self.assertEqual(result, self.sample_person)
        mock_get.assert_called_once_with('https://api.themoviedb.org/3/person/1?language=en-US', timeout=10)

    @patch('requests.Session.get')
    def test_fetch_company_by_id(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = self.sample_company
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.tmdb.fetch_company_by_id(1)
        self.assertEqual(result, self.sample_company)
        mock_get.assert_called_once_with('https://api.themoviedb.org/3/company/1?', timeout=10)

    @patch('requests.Session.get')
    def test_fetch_collection_by_id(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = self.sample_collection
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.tmdb.fetch_collection_by_id(1, language='en-US')
        self.assertEqual(result, self.sample_collection)
        mock_get.assert_called_once_with('https://api.themoviedb.org/3/collection/1?language=en-US', timeout=10)

    @patch('requests.Session.get')
    def test_fetch_pages(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = self.sample_page
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.tmdb._fetch_pages('movie/popular', first_page=1, last_page=2, language='en-US', region='US')
        self.assertEqual(result, [self.sample_page, self.sample_page])
        mock_get.assert_any_call('https://api.themoviedb.org/3/movie/popular?page=1&language=en-US&region=US', timeout=10)
        mock_get.assert_any_call('https://api.themoviedb.org/3/movie/popular?page=2&language=en-US&region=US', timeout=10)

    @patch('requests.Session.get')
    def test_fetch_popular_movies(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = self.sample_page
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.tmdb.fetch_popular_movies(first_page=1, last_page=1, language='en-US')
        self.assertEqual(result, [self.sample_page])

    @patch('requests.Session.get')
    def test_fetch_top_rated_movies(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = self.sample_page
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.tmdb.fetch_top_rated_movies(first_page=1, last_page=1, language='en-US')
        self.assertEqual(result, [self.sample_page])

    @patch('requests.Session.get')
    def test_fetch_trending_movies(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = self.sample_page
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.tmdb.fetch_trending_movies(time_window='day', first_page=1, last_page=1)
        self.assertEqual(result, [self.sample_page])
        mock_get.assert_called_once_with('https://api.themoviedb.org/3/trending/movie/day?page=1&language=en-US', timeout=10)

    @patch('requests.Session.get')
    def test_fetch_trending_people(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {'results': [self.sample_person], 'total_pages': 1}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.tmdb.fetch_trending_people(time_window='week', first_page=1, last_page=1)
        self.assertEqual(result, [{'results': [self.sample_person], 'total_pages': 1}])


class AsyncTMDBTests(TestCase):
    """Tests for the asyncTMDB class."""

    def setUp(self):
        self.async_tmdb = asyncTMDB()
        self.sample_genres = [{'id': 28, 'name': 'Action'}]
        self.sample_movie = {'id': 1, 'title': 'The Matrix', 'adult': False}
        self.sample_person = {'id': 1, 'name': 'John Doe'}
        self.sample_company = {'id': 1, 'name': 'Paramount'}
        self.sample_collection = {'id': 1, 'name': 'Star Wars Collection'}
        self.sample_page = {'results': [self.sample_movie], 'total_pages': 1}

    def test_build_url(self):
        url = self.async_tmdb._build_url('movie/1', {'language': 'en-US'})
        self.assertEqual(url, 'https://api.themoviedb.org/3/movie/1?language=en-US')

    @patch('aiohttp.ClientSession')
    async def test_fetch_data_success(self, mock_session):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=self.sample_movie)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

        async with await self.async_tmdb._get_session():
            result = await self.async_tmdb._fetch_data('movie/1', {'language': 'en-US'}, is_by_id=True)
            self.assertEqual(result, self.sample_movie)
            mock_session.return_value.get.assert_called_once_with('https://api.themoviedb.org/3/movie/1?language=en-US', timeout=10)

    @patch('aiohttp.ClientSession')
    async def test_batch_fetch(self, mock_session):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=self.sample_movie)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

        task_details = [('movie/1', {'language': 'en-US'}), ('movie/2', {'language': 'en-US'})]
        async with await self.async_tmdb._get_session():
            results, not_fetched = await self.async_tmdb._batch_fetch(task_details, is_by_id=True)
            self.assertEqual(results, [self.sample_movie, self.sample_movie])
            self.assertEqual(not_fetched, [])
            mock_session.return_value.get.assert_any_call('https://api.themoviedb.org/3/movie/1?language=en-US', timeout=10)
            mock_session.return_value.get.assert_any_call('https://api.themoviedb.org/3/movie/2?language=en-US', timeout=10)

    @patch('aiohttp.ClientSession')
    async def test_fetch_by_id(self, mock_session):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=self.sample_movie)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

        paths = ['movie/1', 'movie/2']
        async with await self.async_tmdb._get_session():
            results, not_fetched = await self.async_tmdb._fetch_by_id(paths, language='en-US', batch_size=1)
            self.assertEqual(results, [self.sample_movie])
            self.assertEqual(not_fetched, [])

    @patch('aiohttp.ClientSession')
    def test_fetch_movies_by_id(self, mock_session):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=self.sample_movie)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

        results, not_fetched = self.async_tmdb.fetch_movies_by_id([1, 2], language='en-US', batch_size=1)
        self.assertEqual(results, [self.sample_movie])
        self.assertEqual(not_fetched, [])

    @patch('aiohttp.ClientSession')
    def test_fetch_people_by_id(self, mock_session):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=self.sample_person)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

        results, not_fetched = self.async_tmdb.fetch_people_by_id([1, 2], language='en-US')
        self.assertEqual(results, [self.sample_person])
        self.assertEqual(not_fetched, [])

    @patch('aiohttp.ClientSession')
    def test_fetch_companies_by_id(self, mock_session):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=self.sample_company)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

        results, not_fetched = self.async_tmdb.fetch_companies_by_id([1, 2])
        self.assertEqual(results, [self.sample_company])
        self.assertEqual(not_fetched, [])

    @patch('aiohttp.ClientSession')
    def test_fetch_collections_by_id(self, mock_session):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=self.sample_collection)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

        results, not_fetched = self.async_tmdb.fetch_collections_by_id([1, 2], language='en-US')
        self.assertEqual(results, [self.sample_collection])
        self.assertEqual(not_fetched, [])

    @patch('aiohttp.ClientSession')
    async def test_fetch_pages(self, mock_session):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=self.sample_page)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

        async with await self.async_tmdb._get_session():
            results = await self.async_tmdb._fetch_pages('movie/popular', first_page=1, last_page=2, language='en-US')
            self.assertEqual(results, [self.sample_page, self.sample_page])

    @patch('aiohttp.ClientSession')
    def test_fetch_popular_movies(self, mock_session):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=self.sample_page)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

        results = self.async_tmdb.fetch_popular_movies(first_page=1, last_page=1)
        self.assertEqual(results, [self.sample_page])

    @patch('aiohttp.ClientSession')
    def test_fetch_top_rated_movies(self, mock_session):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=self.sample_page)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

        results = self.async_tmdb.fetch_top_rated_movies(first_page=1, last_page=1)
        self.assertEqual(results, [self.sample_page])

    @patch('aiohttp.ClientSession')
    def test_fetch_top_rated_movie_ids(self, mock_session):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=self.sample_page)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

        results = self.async_tmdb.fetch_top_rated_movie_ids(first_page=1, last_page=1)
        self.assertEqual(results, [1])

    @patch('aiohttp.ClientSession')
    def test_fetch_trending_movies(self, mock_session):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=self.sample_page)
        mock_response.raise_for_status = Mock(return_value=None)
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

        results = self.async_tmdb.fetch_trending_movies(time_window='day', first_page=1, last_page=1)
        self.assertEqual(results, [self.sample_page])

    @patch('aiohttp.ClientSession')
    def test_fetch_trending_people(self, mock_session):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'results': [self.sample_person], 'total_pages': 1})
        mock_response.raise_for_status = Mock(return_value=None)
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

        results = self.async_tmdb.fetch_trending_people(time_window='week', first_page=1, last_page=1)
        self.assertEqual(results, [{'results': [self.sample_person], 'total_pages': 1}])

    @patch('aiohttp.ClientSession')
    def test_fetch_changed_ids(self, mock_session):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'results': [{'id': 1, 'adult': False}], 'total_pages': 1})
        mock_response.raise_for_status = Mock(return_value=None)
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.datetime(2025, 9, 3)
            ids, earliest_date = self.async_tmdb.fetch_changed_ids('movie', days=1)
            self.assertEqual(ids, {1})
            self.assertEqual(earliest_date, date(2025, 9, 3))

    def test_fetch_changed_ids_invalid_type(self):
        with self.assertRaises(ValueError):
            self.async_tmdb.fetch_changed_ids('invalid')

    @patch('aiohttp.ClientSession')
    def test_fetch_changed_ids_empty_response(self, mock_session):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'results': [], 'total_pages': 1})
        mock_response.raise_for_status = Mock(return_value=None)
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.datetime(2025, 9, 3)
            ids, earliest_date = self.async_tmdb.fetch_changed_ids('movie', days=1)
            self.assertEqual(ids, set())
            self.assertEqual(earliest_date, date(2025, 9, 3))

    @patch('aiohttp.ClientSession')
    def test_fetch_changed_ids_multiple_days(self, mock_session):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'results': [{'id': 1, 'adult': False}], 'total_pages': 1})
        mock_response.raise_for_status = Mock(return_value=None)
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response

        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.datetime(2025, 9, 3)
            ids, earliest_date = self.async_tmdb.fetch_changed_ids('movie', days=2)
            self.assertEqual(ids, {1})
            self.assertEqual(earliest_date, date(2025, 9, 2))
