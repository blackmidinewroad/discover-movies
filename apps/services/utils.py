import logging
import time
from functools import wraps
from uuid import uuid4

from django.template.defaultfilters import slugify
from django.utils.http import urlencode
from unidecode import unidecode

logger = logging.getLogger('moviedb')


class Colors:
    """Change color in terminal."""

    RED = '\033[0;31m'
    YELLOW = '\033[33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    RESET = '\033[0m'


class GenreIDs:
    """TMDB IDs of genres."""

    ACTION = 28
    ADVENTURE = 12
    ANIMATION = 16
    COMEDY = 35
    CRIME = 80
    DOCUMENTARY = 99
    DRAMA = 18
    FAMILY = 10751
    FANTASY = 14
    HISTORY = 36
    HORROR = 27
    MUSIC = 10402
    MYSTERY = 9648
    ROMANCE = 10749
    SCIENCE_FICTION = 878
    THRILLER = 53
    TV_MOVIE = 10770
    WAR = 10752
    WESTERN = 37


GENRE_DICT = {
    'Action': GenreIDs.ACTION,
    'Adventure': GenreIDs.ADVENTURE,
    'Animation': GenreIDs.ANIMATION,
    'Comedy': GenreIDs.COMEDY,
    'Crime': GenreIDs.CRIME,
    'Drama': GenreIDs.DRAMA,
    'Family': GenreIDs.FAMILY,
    'Fantasy': GenreIDs.FANTASY,
    'History': GenreIDs.HISTORY,
    'Horror': GenreIDs.HORROR,
    'Music': GenreIDs.MUSIC,
    'Mystery': GenreIDs.MYSTERY,
    'Romance': GenreIDs.ROMANCE,
    'Science Fiction': GenreIDs.SCIENCE_FICTION,
    'Thriller': GenreIDs.THRILLER,
    'War': GenreIDs.WAR,
    'Western': GenreIDs.WESTERN,
}

# Map to convert TMDB gender of people
GENDERS = {0: '', 1: 'F', 2: 'M', 3: 'NB'}

# Map of statuses for movies
STATUS_MAP = {
    '': 0,
    'Canceled': 1,
    'Rumored': 2,
    'Planned': 3,
    'In Production': 4,
    'Post Production': 5,
    'Released': 6,
}


def unique_slugify(instance, value: str, cur_bulk_slugs: set[str] = None) -> str:
    """Generate unique slug for a model.

    Args:
        instance: the model instance for which the slug needs to be generated.
        value (str): the value from which to generate the slug.
        cur_bulk_slugs (set[str], optional): set of current slugs that are not in db yet, for bulk creation. Defaults to None.

    Returns:
        str: final slug.
    """

    if cur_bulk_slugs is None:
        cur_bulk_slugs = set()

    model = instance.__class__

    # Transliterate the non-english words into their closest ASCII equivalents
    ascii_text = unidecode(value)

    # Truncate long slugs
    slug_field = instance._meta.get_field('slug')
    max_length = slug_field.max_length
    # Offset length by 4 to add counter at the end if duplicate slug
    slug_field_value = og_slug = slugify(ascii_text)[: max_length - 4]

    # If value is empty generate uuid4
    if not slug_field_value:
        return str(uuid4())

    existing_slugs = set(model.objects.filter(slug__startswith=og_slug).exclude(pk=instance.pk).values_list('slug', flat=True))

    counter = 1
    while slug_field_value in existing_slugs or slug_field_value in cur_bulk_slugs:
        slug_field_value = f'{og_slug}-{counter}'
        counter += 1

        # If too many similar slugs generate uuid4 instead
        if counter == 1000:
            return str(uuid4())

    return slug_field_value


def runtime(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        res = func(*args, **kwargs)
        end = time.perf_counter()

        runtime_in_secs = int(end - start)
        hours, remainder = divmod(runtime_in_secs, 3600)
        minutes, secs = divmod(remainder, 60)

        logger.info('Runtime: %s.', f'{hours:02}:{minutes:02}:{secs:02}')

        return res

    return wrapper


def get_base_query(request):
    query_params = request.GET.copy()
    base_query = {}

    if 'query' in query_params:
        base_query['query'] = query_params['query']

    base_query = urlencode(base_query)

    return base_query
