from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.services.utils import GenreIDs, unique_slugify


class SlugMixin(models.Model):
    """Slug Mixin to create slug field, create slug on save and to set slug manually."""

    slug = models.SlugField(max_length=60, unique=True, blank=True, db_index=True)

    # By default use 'name' field to create slug
    slug_source_field = 'name'

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Create unique slug before saving."""

        if not self.slug:
            value = getattr(self, self.slug_source_field)
            self.slug = unique_slugify(self, value)

        super().save(*args, **kwargs)

    def set_slug(self, cur_bulk_slugs: set[str] = None) -> None:
        """Set slug manually when 'save()' is not called."""

        value = getattr(self, self.slug_source_field)
        self.slug = unique_slugify(self, value, cur_bulk_slugs=cur_bulk_slugs)


class Country(SlugMixin):
    """Countries with ISO 3166-1 alpha-2 codes."""

    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=64, db_index=True)

    class Meta:
        verbose_name = 'country'
        verbose_name_plural = 'countries'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('movies_country', kwargs={'slug': self.slug})


class Language(SlugMixin):
    """Languages with ISO 639-1 codes."""

    code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=32, db_index=True)

    class Meta:
        verbose_name = 'language'
        verbose_name_plural = 'languages'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('movies_language', kwargs={'slug': self.slug})


class Genre(SlugMixin):
    tmdb_id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=32, db_index=True)

    class Meta:
        verbose_name = 'genre'
        verbose_name_plural = 'genres'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('movies_genre', kwargs={'slug': self.slug})


class ProductionCompany(SlugMixin):
    tmdb_id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=256, db_index=True)

    logo_path = models.CharField(max_length=64, blank=True, default='')
    origin_country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, related_name='production_companies')

    class Meta:
        verbose_name = 'production company'
        verbose_name_plural = 'production companies'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('movies_company', kwargs={'slug': self.slug})


class Collection(SlugMixin):
    """Collection of movies model (e.g. Star Wars Collection, Indiana Jones Collection)."""

    tmdb_id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=256, db_index=True)

    overview = models.TextField(blank=True, default='')
    poster_path = models.CharField(max_length=64, blank=True, default='')
    backdrop_path = models.CharField(max_length=64, blank=True, default='')

    class Meta:
        verbose_name = 'collection'
        verbose_name_plural = 'collections'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('collection_detail', kwargs={'slug': self.slug})


class Person(SlugMixin):
    """Any person involved in the making of movies (e.g. actors, directors, writers)."""

    tmdb_id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=128, db_index=True)

    imdb_id = models.CharField(max_length=16, blank=True, default='')

    # Main occupation
    known_for_department = models.CharField(max_length=32, blank=True, default='')

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

    tmdb_popularity = models.FloatField(blank=True, default=0.0, db_index=True)

    # Actors in adult movies
    adult = models.BooleanField(blank=True, default=False)

    last_update = models.DateField(blank=True, default=timezone.now)
    created_at = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = 'person'
        verbose_name_plural = 'people'
        ordering = ['-tmdb_popularity']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('person_detail', kwargs={'slug': self.slug})

    def update_last_modified(self):
        """Set last_update field."""

        self.last_update = timezone.now().date()


class Movie(SlugMixin):
    tmdb_id = models.PositiveIntegerField(primary_key=True)
    title = models.CharField(max_length=512, db_index=True)

    # Use title to create slug
    slug_source_field = 'title'

    imdb_id = models.CharField(max_length=16, blank=True, default='')

    directors = models.ManyToManyField(Person, blank=True, verbose_name='Directed by', related_name='directed_movies', db_index=True)

    release_date = models.DateField(null=True, blank=True, db_index=True)

    genres = models.ManyToManyField(Genre, blank=True, related_name='movies', db_index=True)

    # Is this a documentary
    documentary = models.BooleanField(blank=True, default=False)

    # Is this a TV movie
    tv_movie = models.BooleanField(blank=True, default=False)

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
        (0, 'Unknown'),
        (1, 'Canceled'),
        (2, 'Rumored'),
        (3, 'Planned'),
        (4, 'In Production'),
        (5, 'Post Production'),
        (6, 'Released'),
    )
    status = models.IntegerField(choices=STATUS_OPTIONS, blank=True, default=0)

    # Budget and revenue in USD
    budget = models.BigIntegerField(blank=True, default=0)
    revenue = models.BigIntegerField(blank=True, default=0)

    # Runtime in minutes
    runtime = models.PositiveIntegerField(blank=True, default=0)

    # Is this a short movie (<= 40 mins)
    short = models.BooleanField(blank=True, default=False)

    tmdb_popularity = models.FloatField(blank=True, default=0.0)

    # There are adult movies on TMDB and sometimes they are falsely flagged as not adult and later corrected.
    # This field is for filtering out adult movies and manually change them to adult if needed.
    adult = models.BooleanField(blank=True, default=False)

    last_update = models.DateField(blank=True, default=timezone.now)
    created_at = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = 'movie'
        verbose_name_plural = 'movies'
        ordering = ['-tmdb_popularity']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('movie_detail', kwargs={'slug': self.slug})

    def categorize(self, genre_ids: list[int]):
        """Set documentary, tv_movie and short fields based on genres and runtime."""

        self.documentary = GenreIDs.DOCUMENTARY in genre_ids
        self.tv_movie = GenreIDs.TV_MOVIE in genre_ids
        self.short = bool(self.runtime and self.runtime <= 40)

    def update_last_modified(self):
        """Set last_update field."""

        self.last_update = timezone.now().date()


class MovieEngagement(models.Model):
    """Movie engagement model with ratings and popularity scores from TMDB, IMDB, letterboxd and Kinopoisk."""

    movie = models.OneToOneField(Movie, on_delete=models.CASCADE, related_name='engagement', db_index=True)

    tmdb_rating = models.FloatField(blank=True, default=0.0)
    tmdb_vote_count = models.PositiveIntegerField(blank=True, default=0)
    tmdb_popularity = models.FloatField(blank=True, default=0.0)

    lb_rating = models.FloatField(null=True, blank=True, db_index=True)
    lb_vote_count = models.PositiveIntegerField(null=True, blank=True)
    lb_fans = models.PositiveIntegerField(null=True, blank=True)
    lb_watched = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    lb_liked = models.PositiveIntegerField(null=True, blank=True)

    imdb_rating = models.FloatField(null=True, blank=True)
    imdb_vote_count = models.PositiveIntegerField(null=True, blank=True)
    imdb_popularity = models.PositiveIntegerField(null=True, blank=True)

    kp_rating = models.FloatField(null=True, blank=True)
    kp_vote_count = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'engagement'
        verbose_name_plural = 'engagements'
        ordering = ['-lb_rating']

    def __str__(self):
        return f'{self.movie} engagement'


class MovieCast(models.Model):
    """Cast of a movie - all actors."""

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='cast', db_index=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='cast_roles', db_index=True)
    character = models.CharField(max_length=512, blank=True, default='')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'cast'
        verbose_name_plural = 'cast'
        unique_together = ('movie', 'person', 'character')
        ordering = ['order']

    def __str__(self):
        return f'{self.person} as "{self.character}" in «{self.movie}»'


class MovieCrew(models.Model):
    """Crew of a movie (e.g. director, writer)."""

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='crew', db_index=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='crew_roles', db_index=True)
    department = models.CharField(max_length=32)
    job = models.CharField(max_length=64)

    class Meta:
        verbose_name = 'crew'
        verbose_name_plural = 'crew'
        unique_together = ('movie', 'person', 'department', 'job')
        indexes = [models.Index(fields=['department', 'job'])]

    def __str__(self):
        return f'{self.person} as "{self.job}" in «{self.movie}»'
