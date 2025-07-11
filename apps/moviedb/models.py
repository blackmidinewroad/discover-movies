from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.services.utils import unique_slugify


class SlugMixin(models.Model):
    """Slug Mixin to create slug field, create slug on save and to set slug manually."""

    slug = models.SlugField(max_length=60, unique=True, blank=True)

    # By default use "name" field to create slug
    slug_source_field = 'name'

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Create unique slug before saving."""

        value = getattr(self, self.slug_source_field)
        self.slug = unique_slugify(self, value)
        super().save(*args, **kwargs)

    def set_slug(self, value: str, cur_bulk_slugs: set[str] = None) -> None:
        """Set slug manually when save() is not called."""

        value = getattr(self, self.slug_source_field)
        self.slug = unique_slugify(self, value, cur_bulk_slugs=cur_bulk_slugs)


class Country(SlugMixin):
    """Countries with ISO 3166-1 alpha-2 codes."""

    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=64)

    class Meta:
        verbose_name_plural = 'countries'
        ordering = ['name']
        indexes = [models.Index(fields=['name']), models.Index(fields=['slug'])]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('movies_by_country', kwargs={'slug': self.slug})


class Language(SlugMixin):
    """Languages with ISO 639-1 codes."""

    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=128)

    class Meta:
        verbose_name_plural = 'languages'
        ordering = ['name']
        indexes = [models.Index(fields=['name']), models.Index(fields=['slug'])]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('movies_by_language', kwargs={'slug': self.slug})


class Genre(SlugMixin):
    tmdb_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=32)

    class Meta:
        verbose_name_plural = 'genres'
        ordering = ['name']
        indexes = [models.Index(fields=['name']), models.Index(fields=['slug'])]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('movies_by_genre', kwargs={'slug': self.slug})


class ProductionCompany(SlugMixin):
    tmdb_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=256)

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
        return reverse('movies_by_prod_company', kwargs={'slug': self.slug})


class Collection(SlugMixin):
    """Collection of movies model (e.g. Star Wars Collection, Indiana Jones Collection)."""

    tmdb_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=256)

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
        return reverse('movie_collection', kwargs={'slug': self.slug})


class Person(SlugMixin):
    """Any person invovlved in the making of movies (e. g. actors, directors, writers)."""

    tmdb_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=1024)

    imdb_id = models.CharField(max_length=16, blank=True, default='')

    # Main occupation
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

    last_update = models.DateField()

    class Meta:
        verbose_name_plural = 'people'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
            models.Index(fields=['-tmdb_popularity']),
        ]

    def __str__(self):
        return self.name

    def pre_bulk_create(self):
        """Set last_update field before bulk create"""

        self.last_update = timezone.now().date()


class Movie(SlugMixin):
    tmdb_id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=1024)

    # Use title to create slug
    slug_source_field = 'title'

    imdb_id = models.CharField(max_length=16, blank=True, default='')

    directors = models.ManyToManyField(Person, blank=True, verbose_name='Directed by', related_name='directed_movies')

    release_date = models.DateField(null=True, blank=True)

    genres = models.ManyToManyField(Genre, blank=True, related_name='movies')

    # Is this a documentary
    documentary = models.BooleanField(blank=True, default=False)

    # Is this a TV movie
    tv_movie = models.BooleanField(blank=True, default=False)

    original_title = models.CharField(max_length=1024, blank=True, default='')
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

    # Budget and revenue in USD
    budget = models.BigIntegerField(blank=True, default=0)
    revenue = models.BigIntegerField(blank=True, default=0)

    # Runtime in minutes
    runtime = models.PositiveIntegerField(blank=True, default=0)

    # Is this a short movie (<= 40 mins)
    short = models.BooleanField(blank=True, default=False)

    last_update = models.DateField(blank=True)

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
        return reverse('movie_detail', kwargs={'slug': self.slug})

    def pre_bulk_create(self, genre_ids: list[int]):
        """Set documentary, tv_movie, short and last_update fields before bulk create"""

        # Genre IDs of documentary and TV movie
        DOCUMENTARY = 99
        TV_MOVIE = 10770

        self.documentary = DOCUMENTARY in genre_ids
        self.tv_movie = TV_MOVIE in genre_ids
        self.short = self.runtime and self.runtime <= 40

        self.last_update = timezone.now().date()


class MovieEngagement(models.Model):
    """Movie engagement model with ratings and popularity scores from TMDB, IMDB, letterboxd and Kinopoisk."""

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


class MovieCast(models.Model):
    """Cast of a movie - all actors."""

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
    """Crew of a movie (e.g. director, writer)."""

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='crew')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='crew_roles')
    department = models.CharField(max_length=64)
    job = models.CharField(max_length=64)

    class Meta:
        unique_together = ('movie', 'person', 'department', 'job')
        indexes = [models.Index(fields=['department', 'job'])]

    def __str__(self):
        return f'{self.person} as "{self.job}" in «{self.movie}»'
