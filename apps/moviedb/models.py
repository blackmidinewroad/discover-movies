from django.db import models
from django.urls import reverse

from apps.services.utils import unique_slugify


class Country(models.Model):
    """Countries with ISO 3166-1 alpha-2 codes"""

    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=64)
    slug = models.SlugField(max_length=70, unique=True, blank=True)

    class Meta:
        verbose_name_plural = 'countries'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Get country url"""

        return reverse('movies_by_country', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """Create unique slug on save"""

        self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)


class Language(models.Model):
    """Languages with ISO 639-1 codes"""

    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=130, unique=True, blank=True)

    class Meta:
        verbose_name_plural = 'languages'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Get genre url"""

        return reverse('movies_by_language', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """Create unique slug on save"""

        self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)


class Genre(models.Model):
    """Genre of movies model"""

    tmdb_genre_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=32)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name_plural = 'genres'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Get genre url"""

        return reverse('movies_by_genre', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """Create unique slug on save"""

        self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)


class ProductionCompany(models.Model):
    """Production company model"""

    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=130, unique=True, blank=True)
    logo_path = models.URLField(blank=True, default='')
    origin_country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, related_name='origin_country_company')

    class Meta:
        verbose_name_plural = 'production companies'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Get production company url"""

        return reverse('movies_by_prod_company', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """Create unique slug on save"""

        self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)


class Movie(models.Model):
    """Movie model"""

    title = models.CharField(max_length=256)
    slug = models.SlugField(max_length=260, unique=True, blank=True)
    tmdb_id = models.IntegerField(unique=True)
    imdb_id = models.CharField(max_length=16, blank=True, default='')

    release_date = models.DateField(null=True, blank=True)

    genres = models.ManyToManyField(Genre, blank=True)

    original_title = models.CharField(max_length=256, blank=True, default='')
    original_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True, related_name='original_language')
    spoken_languages = models.ManyToManyField(Language, blank=True, related_name='spoken_languages')
    origin_country = models.ManyToManyField(Country, blank=True, related_name='origin_country_movie')

    overview = models.CharField(max_length=1024, blank=True, default='')
    tagline = models.CharField(max_length=256, blank=True, default='')

    poster_path = models.URLField(blank=True, default='')
    backdrop_path = models.URLField(blank=True, default='')

    production_companies = models.ManyToManyField(ProductionCompany, blank=True)
    production_countries = models.ManyToManyField(Country, blank=True, related_name='production_countries')

    STATUS_OPTIONS = (
        ('Rumored', 'Rumored'),
        ('Planned', 'Planned'),
        ('In Production', 'In Production'),
        ('Post Production', 'Post Production'),
        ('Released', 'Released'),
        ('Canceled', 'Canceled'),
        ('undefined', 'undefined'),
    )

    status = models.CharField(max_length=32, choices=STATUS_OPTIONS)

    budget = models.PositiveIntegerField()
    revenue = models.PositiveIntegerField()

    runtime = models.PositiveIntegerField()

    tmdb_popularity = models.PositiveIntegerField()
    tmdb_rating = models.FloatField()
    tmdb_vote_count = models.PositiveIntegerField()
    tmdb_url = models.URLField(null=True, blank=True)

    lb_rating = models.FloatField(null=True, blank=True)
    lb_vote_count = models.PositiveIntegerField(null=True, blank=True)
    lb_fans = models.PositiveIntegerField(null=True, blank=True)
    lb_watched = models.PositiveIntegerField(null=True, blank=True)
    lb_liked = models.PositiveIntegerField(null=True, blank=True)
    lb_url = models.URLField(null=True, blank=True)

    imdb_rating = models.FloatField(null=True, blank=True)
    imdb_vote_count = models.PositiveIntegerField(null=True, blank=True)
    immdb_popularity = models.PositiveIntegerField(null=True, blank=True)
    imdb_url = models.URLField(null=True, blank=True)

    kp_rating = models.FloatField(null=True, blank=True)
    kp_vote_count = models.PositiveIntegerField(null=True, blank=True)
    kp_url = models.URLField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'movies'
        ordering = ['title', '-release_date']

        indexes = [
            models.Index(
                fields=[
                    '-release_date',
                    '-budget',
                    '-tmdb_popularity',
                    '-immdb_popularity',
                    '-lb_rating',
                    '-lb_watched',
                    '-imdb_rating',
                    '-kp_rating',
                ]
            )
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Get movie url"""

        return reverse('movie_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """Create unique slug on save"""

        self.slug = unique_slugify(self, self.title)
        super().save(*args, **kwargs)
