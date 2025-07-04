from django.template.defaultfilters import slugify


def unique_slugify(instance, value):
    """Generate unique slug for models"""
    
    model = instance.__class__
    slug_field = og_slug = slugify(value)
    
    counter = 1
    while model.objects.filter(slug=slug_field).exclude(pk=instance.pk).exists():
        slug_field = f'{og_slug}-{counter}'
        counter += 1
        
    return slug_field
