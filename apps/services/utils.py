from django.template.defaultfilters import slugify
from unidecode import unidecode


def unique_slugify(instance, value: str, cur_bulk_slugs: set[str] = None):
    """Generate unique slug for models"""

    if cur_bulk_slugs is None:
        cur_bulk_slugs = set()

    model = instance.__class__

    # Transliterate the non-English words into their closest ASCII equivalents
    ascii_text = unidecode(value)

    # Truncate long slugs
    slug_field = og_slug = slugify(ascii_text)[:57]

    counter = 1
    while model.objects.filter(slug=slug_field).exclude(pk=instance.pk).exists() or slug_field in cur_bulk_slugs:
        slug_field = f'{og_slug}-{counter}'
        counter += 1

    return slug_field
