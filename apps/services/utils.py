from django.template.defaultfilters import slugify
from unidecode import unidecode


def unique_slugify(instance, value):
    """Generate unique slug for models"""

    model = instance.__class__

    # Transliterate the non-English words into their closest ASCII equivalents
    ascii_text = unidecode(value)

    # Truncate long slugs
    slug_field = og_slug = slugify(ascii_text)[:57]

    counter = 1
    while model.objects.filter(slug=slug_field).exclude(pk=instance.pk).exists():
        slug_field = f'{og_slug}-{counter}'
        counter += 1

    return slug_field
