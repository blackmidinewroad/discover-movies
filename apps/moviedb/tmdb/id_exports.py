import gzip
import json
from datetime import datetime, timezone
from io import BytesIO

import requests
from requests.exceptions import RequestException


class IDExport:
    BASE_URL = 'http://files.tmdb.org/p/exports/'
    MEDIA_TYPES = {
        'movie': 'movie',
        'tv': 'tv_series',
        'people': 'person',
        'collection': 'collection',
        'network': 'tv_network',
        'keyword': 'keyword',
        'company': 'production_company',
    }

    def _build_url(self, media_type: str, published_date: str) -> str:
        """Build URL"""

        if published_date is None:
            published_date = datetime.now(timezone.utc).strftime("%m_%d_%Y")

        path = f'{self.MEDIA_TYPES.get(media_type, '')}_ids_{published_date}.json.gz'

        return self.BASE_URL + path

    def _fetch_file(self, media_type: str, published_date: str) -> bytes:
        """Fetch ID file"""

        url = self._build_url(media_type, published_date)

        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            return response.content
        except RequestException as e:
            raise RuntimeError(f'Error fetching ID file: {e}')

    def _get_ids(self, compressed_file: bytes) -> list[int]:
        """Get IDs from compressed file"""

        ids = []
        with gzip.GzipFile(fileobj=BytesIO(compressed_file)) as gz_file:
            for line in gz_file:
                line = line.decode('utf-8').strip()
                if line:
                    data = json.loads(line)
                    ids.append(data['id'])
        return ids

    def fetch_ids(self, media_type: str, published_date: str = None) -> list[int]:
        """Fetch list of a valid TMDB IDs for the specified media type and date.

        Args:
            media_type (str): type of media to fetch IDs for. Must be one of:
                - 'movie': For movie IDs
                - 'tv': For TV series IDs
                - 'people': For person IDs
                - 'collection': For collection IDs
                - 'network': For TV network IDs
                - 'keyword': For keyword IDs
                - 'company': For production company IDs
            published_date (str, optional): date of the export file in 'DD_MM_YYYY' format. Defaults to None.
                If not provided, uses the most recent available file.

        Returns:
            list[int]: list of TMDB IDs
        """

        if media_type not in self.MEDIA_TYPES:
            raise ValueError(
                '''Invalid media type. 
                Must be one of:
                    - 'movie': For movie IDs
                    - 'tv': For TV series IDs
                    - 'people': For person IDs
                    - 'collection': For collection IDs
                    - 'network': For TV network IDs
                    - 'keyword': For keyword IDs
                    - 'company': For production company IDs'''
            )

        id_file = self._fetch_file(media_type, published_date)
        ids = self._get_ids(id_file)
        return ids
