from django.db import models
from django.urls import reverse

from apps.services.utils import unique_slugify


class Country(models.Model):
    """Countries with ISO 3166-1 alpha-2 codes"""

    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=64)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        verbose_name_plural = 'countries'
        ordering = ['name']
        indexes = [models.Index(fields=['name']), models.Index(fields=['slug'])]

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
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        verbose_name_plural = 'languages'
        ordering = ['name']
        indexes = [models.Index(fields=['name']), models.Index(fields=['slug'])]

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

    tmdb_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=32)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        verbose_name_plural = 'genres'
        ordering = ['name']
        indexes = [models.Index(fields=['name']), models.Index(fields=['slug'])]

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

    tmdb_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=256)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    logo_path = models.CharField(max_length=64, blank=True, default='')
    origin_country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, related_name='companies')

    class Meta:
        verbose_name = 'production company'
        verbose_name_plural = 'production companies'
        ordering = ['name']
        indexes = [models.Index(fields=['name']), models.Index(fields=['slug'])]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Get production company url"""

        return reverse('movies_by_prod_company', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """Create unique slug on save"""

        self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)


class Collection(models.Model):
    """Collection of movies model"""

    tmdb_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=256)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    overview = models.TextField(blank=True, default='')
    poster_path = models.CharField(max_length=64, blank=True, default='')
    backdrop_path = models.CharField(max_length=64, blank=True, default='')

    class Meta:
        verbose_name_plural = 'collections'
        ordering = ['name']
        indexes = [models.Index(fields=['name']), models.Index(fields=['slug'])]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Get collection url"""

        return reverse('movie_collection', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """Create unique slug on save"""

        self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)


class Movie(models.Model):
    """Movie model"""

    tmdb_id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=512)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    imdb_id = models.CharField(max_length=16, blank=True, default='')

    release_date = models.DateField(null=True, blank=True)

    genres = models.ManyToManyField(Genre, blank=True, related_name='movies')

    original_title = models.CharField(max_length=512, blank=True, default='')
    original_language = models.ForeignKey(
        Language,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movies_as_original_language',
    )
    spoken_languages = models.ManyToManyField(Language, blank=True, related_name='movies_spoken_in')
    origin_country = models.ManyToManyField(Country, blank=True, related_name='movies_originating_from')

    overview = models.TextField(blank=True, default='')
    tagline = models.CharField(max_length=512, blank=True, default='')

    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True, blank=True, related_name='movies')

    poster_path = models.CharField(max_length=64, blank=True, default='')
    backdrop_path = models.CharField(max_length=64, blank=True, default='')

    production_companies = models.ManyToManyField(ProductionCompany, blank=True, related_name='movies')
    production_countries = models.ManyToManyField(Country, blank=True, related_name='movies_produced_in')

    STATUS_OPTIONS = (
        ('', 'Unknown'),
        ('Rumored', 'Rumored'),
        ('Planned', 'Planned'),
        ('In Production', 'In Production'),
        ('Post Production', 'Post Production'),
        ('Released', 'Released'),
        ('Canceled', 'Canceled'),
    )

    status = models.CharField(max_length=32, choices=STATUS_OPTIONS, blank=True, default='')

    budget = models.BigIntegerField(blank=True, default=0)
    revenue = models.BigIntegerField(blank=True, default=0)

    # Runtime in minutes
    runtime = models.PositiveIntegerField(blank=True, default=0)

    class Meta:
        verbose_name_plural = 'movies'
        ordering = ['title', '-release_date']

        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['-release_date']),
            models.Index(fields=['-budget']),
            models.Index(fields=['-revenue']),
            models.Index(fields=['-runtime']),
            models.Index(fields=['slug']),
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


class MovieEngagement(models.Model):
    """Movie engagement model with ratings and popularity scores from TMDB, IMDB, letterboxd and Kinopoisk"""

    movie = models.OneToOneField(Movie, on_delete=models.CASCADE, related_name='engagement')

    tmdb_rating = models.FloatField(blank=True, default=0.0)
    tmdb_vote_count = models.PositiveIntegerField(blank=True, default=0)
    tmdb_popularity = models.FloatField(blank=True, default=0.0)

    lb_rating = models.FloatField(null=True, blank=True)
    lb_vote_count = models.PositiveIntegerField(null=True, blank=True)
    lb_fans = models.PositiveIntegerField(null=True, blank=True)
    lb_watched = models.PositiveIntegerField(null=True, blank=True)
    lb_liked = models.PositiveIntegerField(null=True, blank=True)

    imdb_rating = models.FloatField(null=True, blank=True)
    imdb_vote_count = models.PositiveIntegerField(null=True, blank=True)
    imdb_popularity = models.PositiveIntegerField(null=True, blank=True)

    kp_rating = models.FloatField(null=True, blank=True)
    kp_vote_count = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'movie engagement'
        verbose_name_plural = 'movie engagements'

        ordering = ['-lb_rating']

        indexes = [
            models.Index(fields=['-tmdb_popularity']),
            models.Index(fields=['-imdb_popularity']),
            models.Index(fields=['-lb_rating']),
            models.Index(fields=['-lb_watched']),
            models.Index(fields=['-imdb_rating']),
            models.Index(fields=['-kp_rating']),
        ]

    def __str__(self):
        return f'{self.movie} engagement'


class Person(models.Model):
    """Any people invovlved in making movies (e. g. actors, directors, writers)"""

    tmdb_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=512)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    imdb_id = models.CharField(max_length=16, blank=True, default='')

    known_for_department = models.CharField(max_length=64, blank=True, default='')
    biography = models.TextField(blank=True, default='')
    place_of_birth = models.CharField(max_length=256, blank=True, default='')

    GENDER_OPTIONS = (
        ('', 'Unknown'),
        ('F', 'Female'),
        ('M', 'Male'),
        ('NB', 'Non-binary'),
    )

    gender = models.CharField(max_length=2, choices=GENDER_OPTIONS, blank=True, default='')

    birthday = models.DateField(null=True, blank=True)
    deathday = models.DateField(null=True, blank=True)

    profile_path = models.CharField(max_length=64, blank=True, default='')

    tmdb_popularity = models.FloatField(blank=True, default=0.0)

    class Meta:
        verbose_name_plural = 'persons'
        ordering = ['name']
        indexes = [models.Index(fields=['name']), models.Index(fields=['slug']), models.Index(fields=['-tmdb_popularity'])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Create unique slug on save"""

        self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)


class MovieCast(models.Model):
    """Actors in a movie"""

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='cast')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='cast_roles')
    character = models.CharField(max_length=512, blank=True, default='')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('movie', 'person', 'character')
        ordering = ['order']

    def __str__(self):
        return f'{self.person} as "{self.character}" in «{self.movie}»'


class MovieCrew(models.Model):
    """Crew members (e.g. director, writer) in a movie"""

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='crew')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='crew_roles')
    department = models.CharField(max_length=64)
    job = models.CharField(max_length=64)

    class Meta:
        unique_together = ('movie', 'person', 'department', 'job')
        indexes = [models.Index(fields=['department', 'job'])]

    def __str__(self):
        return f'{self.person} as "{self.job}" in «{self.movie}»'
