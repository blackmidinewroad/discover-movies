import asyncio
import os
from urllib.parse import urlencode, urljoin

import aiohttp
import requests
from aiolimiter import AsyncLimiter
from ratelimit import limits, sleep_and_retry
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util import Retry


class BaseTMDB:
    """Base class for TMDB API wrapper"""

    BASE_URL = 'https://api.themoviedb.org/3/'

    def _build_url(self, path: str, params: dict = None) -> str:
        """Build URL"""

        if params is None:
            params = {}

        return f'{urljoin(self.BASE_URL, path)}?{urlencode(params)}'

    class colors:
        RED = '\033[0;31m'
        BLUE = '\033[0;34m'
        RESET = '\033[0m'


class TMDB(BaseTMDB):
    """TMDB API wrapper"""

    # 45 calls per 1 second
    CALLS = 45
    RATE_LIMIT = 1

    # Requests retry strategy
    RETRY = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                'accept': 'application/json',
                'Authorization': f'Bearer {os.getenv("TMDB_ACCESS_TOKEN")}',
            }
        )
        self.session.mount('https://', HTTPAdapter(max_retries=self.RETRY))

    @sleep_and_retry
    @limits(calls=CALLS, period=RATE_LIMIT)
    def _fetch_data(self, path: str, params: dict = None) -> {}:
        """Fetch data"""

        url = self._build_url(path, params)
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            print(f'{self.colors.RED}Failed to fetch: {e}\n{self.colors.BLUE}path: {path}\nparams: {params}{self.colors.RESET}')

    def fetch_genres(self, language: str = 'en') -> list[dict]:
        """Fetch the list of official genres for movies.

        Args:
            language (str, optional): language in ISO 639-1 code (e.g. en, fr, ru). Defaults to 'en'.

        Returns:
            list[dict]: list of genres
        """

        path = 'genre/movie/list'
        params = {'language': language}
        data = self._fetch_data(path, params)

        return data.get('genres', [])

    def _fetch_configuration(self, config_for: str, language: str = None) -> list[dict]:
        """Fetch TMDB configuration"""

        path = f'configuration/{config_for}'
        params = {'language': language} if language is not None else {}
        return self._fetch_data(path, params)

    def fetch_countries(self, language: str = 'en-US') -> list[dict]:
        """Get the list of countries (ISO 3166-1 tags) used throughout TMDB.

        Args:
            language (str, optional): locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to 'en-US'.

        Returns:
            list[dict]: list of countries with ISO 3166-1 tags, names and english names.
        """

        config_for = 'countries'
        return self._fetch_configuration(config_for, language=language)

    def fetch_languages(self) -> list[dict]:
        """Get the list of languages (ISO 639-1 tags) used throughout TMDB.

        Returns:
            list[dict]: list of languages with ISO 639-1 tags, names and english names.
        """

        config_for = 'languages'
        return self._fetch_configuration(config_for)

    def _fetch_details(self, path: str, language: str = None, append_to_response: list[str] = None) -> dict:
        """Fetch details"""

        params = {}
        if language is not None:
            params['language'] = language
        if append_to_response is not None:
            params['append_to_response'] = ','.join(append_to_response)

        return self._fetch_data(path, params)

    def fetch_movie_by_id(self, movie_id: int, language: str = 'en-US', append_to_response: list[str] = None) -> dict:
        """Fetch movie details by ID.

        Args:
            movie_id (int): TMDB ID of a movie.
            language (str, optional): locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to 'en-US'.
            append_to_response (list[str], optional): list of endpoints within this namespace, 20 items max. Defaults to ''.

        Returns:
            dict: dict with movie details
        """

        path = f'movie/{movie_id}'

        return self._fetch_details(path=path, language=language, append_to_response=append_to_response)

    def fetch_person_by_id(self, person_id: int, language: str = 'en-US', append_to_response: list[str] = None) -> dict:
        """Fetch person details by ID.

        Args:
            person_id (int): TMDB ID of a person.
            language (str, optional): locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to 'en-US'.
            append_to_response (list[str], optional): list of endpoints within this namespace, 20 items max. Defaults to ''.

        Returns:
            dict: dict with person details.
        """

        path = f'person/{person_id}'

        return self._fetch_details(path=path, language=language, append_to_response=append_to_response)

    def fetch_company_by_id(self, company_id: int) -> dict:
        """Fetch production company details by ID.

        Args:
            company_id (int): TMDB ID of a production company.

        Returns:
            dict: dict with company details.
        """

        path = f'company/{company_id}'

        return self._fetch_details(path=path)

    def _discover(self, path: str, first_page: int, last_page: int, language: str, region: str = None) -> list[dict]:
        """Discover"""

        if last_page is None:
            last_page = first_page

        pages = []

        for page in range(first_page, last_page + 1):
            params = {'page': page, 'language': language}
            if region is not None:
                params['region'] = region

            pages.append(self._fetch_data(path, params))

        return pages

    def fetch_popular_movies(self, first_page: int = 1, last_page: int = None, language: str = 'en-US', region: str = None) -> list[dict]:
        """Fetch most popular movies.

        Args:
            first_page (int, optional): first page, max=500. Defaults to 1.
            last_page (int, optional): last page, leave blank if need 1 page, max=500. Defaults to None.
            language (str, optional): locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to 'en-US'.
            region (str, optional): ISO 3166-1 code (e.g. US, FR, RU). Defaults to None.

        Returns:
            list[dict]: list of pages with movie details.
        """

        path = 'movie/popular'

        return self._discover(path=path, first_page=first_page, last_page=last_page, language=language, region=region)

    def fetch_top_rated_movies(self, first_page: int = 1, last_page: int = None, language: str = 'en-US', region: str = None) -> list[dict]:
        """Fetch top rated movies.

        Args:
            first_page (int, optional): first page, max=500. Defaults to 1.
            last_page (int, optional): last page, leave blank if need 1 page, max=500. Defaults to None.
            language (str, optional): locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to 'en-US'.
            region (str, optional): ISO 3166-1 code (e.g. US, FR, RU). Defaults to None.

        Returns:
            list[dict]: list of pages with movie details.
        """

        path = 'movie/top_rated'

        return self._discover(path=path, first_page=first_page, last_page=last_page, language=language, region=region)

    def fetch_trending_movies(
        self, time_window: str = 'day', first_page: int = 1, last_page: int = None, language: str = 'en-US'
    ) -> list[dict]:
        """Fetch trending movies.

        Args:
            time_window (str, optional): time window, day or week. Defaults to 'day'.
            first_page (int, optional): first page, max=500. Defaults to 1.
            last_page (int, optional): last page, leave blank if need 1 page, max=500. Defaults to None.
            language (str, optional): locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to 'en-US'.

        Returns:
            list[dict]: list of pages with movie details.
        """

        path = f'trending/movie/{time_window}'

        return self._discover(path=path, first_page=first_page, last_page=last_page, language=language)

    def fetch_trending_people(
        self, time_window: str = 'day', first_page: int = 1, last_page: int = None, language: str = 'en-US'
    ) -> list[dict]:
        """Fetch trending people.

        Args:
            time_window (str, optional): time window, day or week. Defaults to 'day'.
            first_page (int, optional): first page, max=500. Defaults to 1.
            last_page (int, optional): last page, leave blank if need 1 page, max=500. Defaults to None.
            language (str, optional): locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to 'en-US'.

        Returns:
            list[dict]: list of pages with people details.
        """

        path = f'trending/person/{time_window}'

        return self._discover(path=path, first_page=first_page, last_page=last_page, language=language)


class asyncTMDB(BaseTMDB):
    """TMDB API wrapper for async requests"""

    # 45 calls per 1 second
    CALLS = 45
    RATE_LIMIT = 1

    def __init__(self):
        self.header = {
            'accept': 'application/json',
            'Authorization': f'Bearer {os.getenv("TMDB_ACCESS_TOKEN")}',
        }
        self.limiter = AsyncLimiter(self.CALLS, self.RATE_LIMIT)

    async def _fetch_data(
        self,
        session: aiohttp.ClientSession,
        path: str,
        params: dict = None,
    ) -> dict:
        """Fetch data asynchronously"""

        url = self._build_url(path, params)

        async with self.limiter:
            try:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data
            except aiohttp.ClientError as e:
                print(f'{self.colors.RED}Failed to fetch: {e}\n{self.colors.BLUE}path: {path}\nparams: {params}{self.colors.RESET}')

    async def _batch_fetch(self, task_details: list[dict], const_params: dict = None) -> list[dict]:
        """Batch fetch data asynchronously"""

        results = []
        connector = aiohttp.TCPConnector(limit=self.CALLS)
        timeout = aiohttp.ClientTimeout(total=20)

        async with aiohttp.ClientSession(headers=self.header, connector=connector, timeout=timeout) as session:
            if const_params is None:
                tasks = [self._fetch_data(session, path, params) for path, params in task_details]
            else:
                tasks = [self._fetch_data(session, path, const_params) for path in task_details]

            responses = await asyncio.gather(*tasks)

            for result in responses:
                if result:
                    results.append(result)

        return results

    def _batch_fetch_details(self, paths: tuple[str], language: str = None, append_to_response: list[str] = None) -> list[dict]:
        """Batch fetch details"""

        params = {}
        if language is not None:
            params['language'] = language
        if append_to_response is not None:
            params['append_to_response'] = ','.join(append_to_response)

        return asyncio.run(self._batch_fetch(paths, const_params=params))

    def batch_fetch_movies_by_id(self, movie_ids: list[int], language: str = 'en-US', append_to_response: list[str] = None) -> list[dict]:
        """Fetch movie details for list of IDs.

        Args:
            movie_ids (list[int]): list of TMDB movie IDs.
            language (str, optional): locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to 'en-US'.
            append_to_response (list[str], optional): list of endpoints within this namespace, will appended to each movie, 20 items max. Defaults to None.

        Returns:
            list[dict]: list of movies with details.
        """

        paths = tuple(f'movie/{movie_id}' for movie_id in movie_ids)

        return self._batch_fetch_details(paths=paths, language=language, append_to_response=append_to_response)

    def batch_fetch_persons_by_id(self, person_ids: list[int], language: str = 'en-US', append_to_response: list[str] = None) -> list[dict]:
        """Fetch person details for list of IDs.

        Args:
            person_ids (list[int]): list of TMDB pesron IDs.
            language (str, optional): locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to 'en-US'.
            append_to_response (list[str], optional): list of endpoints within this namespace, will appended to each movie, 20 items max. Defaults to None.

        Returns:
            list[dict]: list of persons with details.
        """

        paths = tuple(f'person/{person_id}' for person_id in person_ids)

        return self._batch_fetch_details(paths=paths, language=language, append_to_response=append_to_response)

    def batch_fetch_companies_by_id(self, company_ids: list[int]) -> list[dict]:
        """Fetch company details for list of IDs.

        Args:
            company_ids (list[int]): list of TMDB company IDs.
            language (str, optional): locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to 'en-US'.
            append_to_response (list[str], optional): list of endpoints within this namespace, will appended to each movie, 20 items max. Defaults to None.

        Returns:
            list[dict]: list of companies with details.
        """

        paths = tuple(f'company/{company_id}' for company_id in company_ids)

        return self._batch_fetch_details(paths=paths)

    def _discover(self, path: str, first_page: int, last_page: int, language: str, region: str = None) -> list[dict]:
        if last_page is None:
            last_page = first_page

        task_details = tuple((path, {'page': page, 'language': language, 'region': region}) for page in range(first_page, last_page + 1))

        pages = asyncio.run(self._batch_fetch(task_details))

        return pages

    def fetch_popular_movies(self, first_page: int = 1, last_page: int = None, language: str = 'en-US', region: str = None) -> list[dict]:
        path = 'movie/popular'

        return self._discover(path=path, first_page=first_page, last_page=last_page, language=language, region=region)

    def fetch_top_rated_movies(self, first_page: int = 1, last_page: int = None, language: str = 'en-US', region: str = None) -> list[dict]:
        path = 'movie/top_rated'

        return self._discover(path=path, first_page=first_page, last_page=last_page, language=language, region=region)

    def fetch_trending_movies(
        self, time_window: str = 'day', first_page: int = 1, last_page: int = None, language: str = 'en-US'
    ) -> list[dict]:
        path = f'trending/movie/{time_window}'

        return self._discover(path=path, first_page=first_page, last_page=last_page, language=language)

    def fetch_trending_people(
        self, time_window: str = 'day', first_page: int = 1, last_page: int = None, language: str = 'en-US'
    ) -> list[dict]:
        path = f'trending/person/{time_window}'

        return self._discover(path=path, first_page=first_page, last_page=last_page, language=language)
