from django.db import models
from django.urls import reverse

from apps.services.utils import unique_slugify


class Genre(models.Model):
    """Genre of movies model"""

    tmdb_genre_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=32)
    slug = models.SlugField(unique=True, blank=True)

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
    name = models.CharField(max_length=64)
    slug = models.SlugField(unique=True, blank=True)
    logo_path = models.URLField(blank=True, default='')

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
    slug = models.SlugField(unique=True, blank=True)
    tmdb_id = models.IntegerField(unique=True)
    imdb_id = models.CharField(max_length=16, blank=True, default='')

    release_date = models.DateField(null=True, blank=True)

    genres = models.ManyToManyField(Genre, blank=True)

    original_title = models.CharField(max_length=256, blank=True, default='')
    original_language = models.CharField(max_length=32, blank=True, default='')
    spoken_languages = models.CharField(max_length=1024, blank=True, default='')

    overview = models.CharField(max_length=1024, blank=True, default='')
    tagline = models.CharField(max_length=256, blank=True, default='')

    poster_path = models.URLField(blank=True, default='')
    backdrop_path = models.URLField(blank=True, default='')

    production_companies = models.ManyToManyField(ProductionCompany, blank=True)
    production_countries = models.CharField(max_length=256, blank=True, default='')

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
    tmdb_url = models.URLField()

    lb_rating = models.FloatField(null=True, blank=True)
    lb_vote_count = models.PositiveIntegerField(null=True, blank=True)
    lb_fans = models.PositiveIntegerField(null=True, blank=True)
    lb_watched = models.PositiveIntegerField(null=True, blank=True)
    lb_liked = models.PositiveIntegerField(null=True, blank=True)
    lb_url = models.URLField()

    imdb_rating = models.FloatField(null=True, blank=True)
    imdb_vote_count = models.PositiveIntegerField(null=True, blank=True)
    immdb_popularity = models.PositiveIntegerField(null=True, blank=True)
    imdb_url = models.URLField()

    kp_rating = models.FloatField(null=True, blank=True)
    kp_vote_count = models.PositiveIntegerField(null=True, blank=True)
    kp_url = models.URLField()

    class Meta:
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
