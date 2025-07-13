import time
from functools import wraps

from django.template.defaultfilters import slugify
from unidecode import unidecode


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
    slug_field = og_slug = slugify(ascii_text)[:57]

    counter = 1
    while model.objects.filter(slug=slug_field).exclude(pk=instance.pk).exists() or slug_field in cur_bulk_slugs:
        slug_field = f'{og_slug}-{counter}'
        counter += 1

    return slug_field


def runtime(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        res = func(*args, **kwargs)
        end = time.perf_counter()

        runtime_in_secs = int(end - start)
        hours, remainder = divmod(runtime_in_secs, 3600)
        minutes, secs = divmod(remainder, 60)

        print(f'{Colors.PURPLE}Runtime: {hours:02}:{minutes:02}:{secs:02}{Colors.RESET}')

        return res

    return wrapper
