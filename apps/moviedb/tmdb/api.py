import os
from urllib.parse import urlencode, urljoin

import requests
from requests.exceptions import RequestException


class TMDB:
    """TMDB API wrapper"""

    BASE_URL = 'https://api.themoviedb.org/3/'

    def __init__(self):
        self.headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {os.getenv("TMDB_ACCESS_TOKEN")}',
        }

    def _build_url(self, path, params=None):
        """Build URL"""

        if params is None:
            params = {}

        url = f'{urljoin(self.BASE_URL, path)}?{urlencode(params)}'
        print(url)
        return url

    def _fetch_data(self, path, params=None):
        """Fetch data"""

        url = self._build_url(path, params)
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise RuntimeError(f'TMDB API error: {e}')

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

        return data.get('genres', {})

    def _fetch_details(self, path: str, language: str, append_to_response: list[str] = None) -> dict:
        """Fetch details"""

        params = {'language': language}
        if append_to_response is not None:
            params['append_to_response'] = ','.join(append_to_response)

        return self._fetch_data(path, params)

    def fetch_movie_by_id(self, movie_id: int, language: str = 'en-US', append_to_response: list[str] = None) -> dict:
        """Fetch movie details by ID.

        Args:
            movie_id (int): TMDB ID of a movie
            append_to_response (list[str], optional): list of endpoints within this namespace, 20 items max. Defaults to ''.
            language (str, optional): locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to 'en-US'.

        Returns:
            dict: dict with movie details
        """

        path = f'movie/{movie_id}'

        return self._fetch_details(path=path, language=language, append_to_response=append_to_response)

    def fetch_person_by_id(self, person_id: int, language: str = 'en-US', append_to_response: list[str] = None) -> dict:
        """Fetch person details by ID.

        Args:
            person_id (int): TMDB ID of a person
            append_to_response (list[str], optional): list of endpoints within this namespace, 20 items max. Defaults to ''.
            language (str, optional): locale (ISO 639-1-ISO 3166-1) code (e.g. en-UD, fr-CA, de_DE). Defaults to 'en-US'.

        Returns:
            dict: dict with person details
        """

        path = f'person/{person_id}'

        return self._fetch_details(path=path, language=language, append_to_response=append_to_response)

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
