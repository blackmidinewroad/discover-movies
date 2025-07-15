import logging
import time
from functools import wraps
from uuid import uuid4

from django.template.defaultfilters import slugify
from unidecode import unidecode

logger = logging.getLogger('moviedb')


class Colors:
    """Change color in terminal."""

    RED = '\033[0;31m'
    YELLOW = '\033[33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    RESET = '\033[0m'


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
    if not value:
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
