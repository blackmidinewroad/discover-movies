import gzip
import json
import logging
from io import BytesIO

import requests
from django.utils import timezone
from requests.exceptions import RequestException

logger = logging.getLogger('moviedb')


class IDExport:
    """Download and extract TMDB daily ID export files."""

    BASE_URL = 'http://files.tmdb.org/p/exports/'
    MEDIA_TYPES = {
        'movie': 'movie',
        'tv': 'tv_series',
        'person': 'person',
        'collection': 'collection',
        'network': 'tv_network',
        'keyword': 'keyword',
        'company': 'production_company',
    }

    def _build_url(self, media_type: str, published_date: str) -> str:
        if published_date is None:
            published_date = timezone.now().strftime('%m_%d_%Y')

        path = f'{self.MEDIA_TYPES.get(media_type, '')}_ids_{published_date}.json.gz'

        return self.BASE_URL + path

    def _fetch_id_file(self, media_type: str, published_date: str) -> bytes | None:
        url = self._build_url(media_type, published_date)

        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            return response.content
        except RequestException:
            logger.error("Couldn't fetch ID file for media type: %s, date: %s.", media_type, published_date)

    def _get_ids(self, compressed_file: bytes, sort_by_popularity: bool = False) -> list[int]:
        """
        Unzip fetched file, deserialize lines containing JSON to python dict, store IDs and popularity in a list
        then sort it by popularity if needed, return list of IDs.
        """

        ids = []
        with gzip.GzipFile(fileobj=BytesIO(compressed_file)) as gz_file:
            for line in gz_file:
                line = line.decode('utf-8').strip()
                if line:
                    data = json.loads(line)

                    # Store tuples of id and popularity
                    ids.append((data['id'], data.get('popularity', 0)))

        if sort_by_popularity:
            ids.sort(key=lambda el: -el[1])

        return [id for id, _ in ids]

    def fetch_ids(self, media_type: str, published_date: str = None, sort_by_popularity: bool = False) -> list[int]:
        """Fetch list of a valid TMDB IDs for the specified media type and date.

        Args:
            media_type (str): type of media to fetch IDs for. Must be one of:
                - 'movie': For movie IDs
                - 'tv': For TV series IDs
                - 'person': For person IDs
                - 'collection': For collection IDs
                - 'network': For TV network IDs
                - 'keyword': For keyword IDs
                - 'company': For production company IDs
            published_date (str, optional): date of the export file in 'MM_DD_YYYY' format.
                Files are available by 8:00 AM UTC of each day.
                Defaults to None. If not provided, uses the most recent available file.
            sort_by_popularity (bool, optional): sort IDs by popularity if possible. Defaults to False.

        Returns:
            list[int]: list of TMDB IDs.
        """

        if media_type not in self.MEDIA_TYPES:
            raise ValueError(
                '''Invalid media type. 
                Must be one of:
                    - 'movie': For movie IDs
                    - 'tv': For TV series IDs
                    - 'person': For person IDs
                    - 'collection': For collection IDs
                    - 'network': For TV network IDs
                    - 'keyword': For keyword IDs
                    - 'company': For production company IDs'''
            )

        id_file = self._fetch_id_file(media_type, published_date)
        if id_file is None:
            return
        
        ids = self._get_ids(id_file, sort_by_popularity=sort_by_popularity)

        return ids
