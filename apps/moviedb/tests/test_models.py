from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.moviedb.models import (
    Collection,
    Country,
    Genre,
    Language,
    Movie,
    MovieCast,
    MovieCrew,
    MovieEngagement,
    Person,
    ProductionCompany,
)


class BaseTestCase(TestCase):
    """Base test case with common setup for models."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country = Country.objects.create(code='US', name='United States')
        cls.language = Language.objects.create(code='EN', name='English')
        cls.genre = Genre.objects.create(tmdb_id=28, name='Action')
        cls.collection = Collection.objects.create(tmdb_id=1, name='Star Wars Collection')


class SlugMixinTests(TestCase):
    """Tests for SlugMixin functionality."""

    def test_slug_generation(self):
        country = Country(code='CA', name='Canada')
        country.save()
        self.assertEqual(country.slug, 'canada')

    def test_slug_uniqueness(self):
        Country.objects.create(code='US', name='United States')
        country2 = Country(code='UK', name='United States')
        country2.save()
        self.assertEqual(country2.slug, 'united-states-1')

    def test_set_slug_manually(self):
        country = Country(code='CA', name='Canada')
        country.set_slug()
        self.assertEqual(country.slug, 'canada')

    def test_set_slug_with_duplicates(self):
        Country.objects.create(code='US', name='United States')
        country2 = Country(code='UK', name='United States')
        used_slugs = {'united-states'}
        country2.set_slug(cur_bulk_slugs=used_slugs)
        self.assertEqual(country2.slug, 'united-states-1')

    def test_slug_special_characters(self):
        country = Country(code='FR', name='France & Germany')
        country.save()
        self.assertEqual(country.slug, 'france-germany')

    def test_empty_name_slug(self):
        country = Country(code='XX', name='')
        country.save()
        self.assertTrue(len(country.slug) == 36)

    def test_invalid_country_code_length(self):
        with self.assertRaises(ValidationError):
            country = Country(code='USA', name='United States')
            country.full_clean()


class CountryModelTests(BaseTestCase):
    """Tests for the Country model."""

    def test_country_creation(self):
        country = Country.objects.create(code='CA', name='Canada', alias_name='CA')
        self.assertEqual(country.code, 'CA')
        self.assertEqual(country.name, 'Canada')
        self.assertEqual(country.alias_name, 'CA')
        self.assertEqual(country.slug, 'canada')

    def test_country_string_representation(self):
        self.assertEqual(str(self.country), 'United States')

    def test_country_get_absolute_url(self):
        expected_url = reverse('movies_country', kwargs={'slug': self.country.slug})
        self.assertEqual(self.country.get_absolute_url(), expected_url)

    def test_country_unique_code(self):
        with self.assertRaises(IntegrityError):
            Country.objects.create(code='US', name='United States Duplicate')

    def test_country_ordering(self):
        ca = Country.objects.create(code='CA', name='Canada')
        us = self.country
        self.assertEqual(list(Country.objects.all()), [ca, us])


class LanguageModelTests(BaseTestCase):
    """Tests for the Language model."""

    def test_language_creation(self):
        language = Language.objects.create(code='FR', name='French')
        self.assertEqual(language.code, 'FR')
        self.assertEqual(language.name, 'French')
        self.assertEqual(language.slug, 'french')

    def test_language_string_representation(self):
        self.assertEqual(str(self.language), 'English')

    def test_language_get_absolute_url(self):
        expected_url = reverse('movies_language', kwargs={'slug': self.language.slug})
        self.assertEqual(self.language.get_absolute_url(), expected_url)

    def test_language_unique_code(self):
        with self.assertRaises(IntegrityError):
            Language.objects.create(code='EN', name='English Duplicate')

    def test_language_ordering(self):
        lang2 = Language.objects.create(code='AA', name='Aardvark')
        self.assertEqual(list(Language.objects.all())[0], lang2)


class GenreModelTests(BaseTestCase):
    """Tests for the Genre model."""

    def test_genre_creation(self):
        genre = Genre.objects.create(tmdb_id=12, name='Adventure')
        self.assertEqual(genre.tmdb_id, 12)
        self.assertEqual(genre.name, 'Adventure')
        self.assertEqual(genre.slug, 'adventure')

    def test_genre_string_representation(self):
        self.assertEqual(str(self.genre), 'Action')

    def test_genre_get_absolute_url(self):
        expected_url = reverse('movies_genre', kwargs={'slug': self.genre.slug})
        self.assertEqual(self.genre.get_absolute_url(), expected_url)

    def test_genre_ordering(self):
        g2 = Genre.objects.create(tmdb_id=99, name='Zoology')
        self.assertEqual(list(Genre.objects.all())[-1], g2)


class ProductionCompanyModelTests(BaseTestCase):
    """Tests for the ProductionCompany model."""

    def setUp(self):
        self.company = ProductionCompany.objects.create(
            tmdb_id=2,
            name='Paramount Pictures',
            logo_path='/logo.png',
            origin_country=self.country,
            movie_count=50,
            adult=False,
            removed_from_tmdb=False,
        )

    def test_production_company_creation(self):
        self.assertEqual(self.company.tmdb_id, 2)
        self.assertEqual(self.company.name, 'Paramount Pictures')
        self.assertEqual(self.company.origin_country, self.country)
        self.assertEqual(self.company.movie_count, 50)
        self.assertFalse(self.company.adult)
        self.assertFalse(self.company.removed_from_tmdb)
        self.assertEqual(self.company.slug, 'paramount-pictures')

    def test_production_company_string_representation(self):
        self.assertEqual(str(self.company), 'Paramount Pictures')

    def test_production_company_get_absolute_url(self):
        expected_url = reverse('movies_company', kwargs={'slug': self.company.slug})
        self.assertEqual(self.company.get_absolute_url(), expected_url)

    def test_production_company_ordering(self):
        company2 = ProductionCompany.objects.create(tmdb_id=3, name='Disney', movie_count=100)
        self.assertEqual(list(ProductionCompany.objects.all()), [company2, self.company])


class CollectionModelTests(BaseTestCase):
    """Tests for the Collection model."""

    def setUp(self):
        self.collection_new = Collection.objects.create(
            tmdb_id=2,
            name='Marvel Collection',
            overview='Superhero movies.',
            poster_path='/poster.png',
            backdrop_path='/backdrop.png',
            movies_released=20,
            avg_popularity=90.0,
            adult=False,
            removed_from_tmdb=False,
        )

    def test_collection_creation(self):
        self.assertEqual(self.collection_new.tmdb_id, 2)
        self.assertEqual(self.collection_new.name, 'Marvel Collection')
        self.assertEqual(self.collection_new.movies_released, 20)
        self.assertEqual(self.collection_new.avg_popularity, 90.0)
        self.assertFalse(self.collection_new.adult)
        self.assertFalse(self.collection_new.removed_from_tmdb)
        self.assertEqual(self.collection_new.slug, 'marvel-collection')

    def test_collection_string_representation(self):
        self.assertEqual(str(self.collection_new), 'Marvel Collection')

    def test_collection_get_absolute_url(self):
        expected_url = reverse('collection_detail', kwargs={'slug': self.collection_new.slug})
        self.assertEqual(self.collection_new.get_absolute_url(), expected_url)

    def test_collection_ordering(self):
        self.assertEqual(list(Collection.objects.all())[0], self.collection_new)


class PersonModelTests(BaseTestCase):
    """Tests for the Person model."""

    def setUp(self):
        self.person = Person.objects.create(
            tmdb_id=2,
            name='Jane Doe',
            imdb_id='nm0000002',
            known_for_department='Directing',
            biography='A director.',
            place_of_birth='Los Angeles, USA',
            gender='F',
            birthday=timezone.now().date(),
            tmdb_popularity=75.0,
            cast_roles_count=5,
            crew_roles_count=3,
            adult=False,
            removed_from_tmdb=False,
        )

    def test_person_creation(self):
        self.assertEqual(self.person.tmdb_id, 2)
        self.assertEqual(self.person.name, 'Jane Doe')
        self.assertEqual(self.person.known_for_department, 'Directing')
        self.assertEqual(self.person.gender, 'F')
        self.assertEqual(self.person.tmdb_popularity, 75.0)
        self.assertFalse(self.person.adult)
        self.assertFalse(self.person.removed_from_tmdb)
        self.assertEqual(self.person.slug, 'jane-doe')

    def test_person_string_representation(self):
        self.assertEqual(str(self.person), 'Jane Doe')

    def test_person_get_absolute_url(self):
        expected_url = reverse('person_detail', kwargs={'slug': self.person.slug})
        self.assertEqual(self.person.get_absolute_url(), expected_url)

    def test_person_update_last_modified(self):
        original_date = self.person.last_update
        self.person.update_last_modified()
        self.assertNotEqual(self.person.last_update, original_date)
        self.assertEqual(self.person.last_update, timezone.now().date())

    def test_person_gender_choices(self):
        self.person.gender = 'NB'
        self.person.save()
        self.assertEqual(self.person.gender, 'NB')
        with self.assertRaises(ValidationError):
            self.person.gender = 'X'
            self.person.full_clean()

    def test_person_ordering(self):
        p2 = Person.objects.create(tmdb_id=3, name='Another Person', tmdb_popularity=100.0)
        self.assertEqual(list(Person.objects.all())[0], p2)


class MovieModelTests(BaseTestCase):
    """Tests for the Movie model."""

    def setUp(self):
        self.movie = Movie.objects.create(
            tmdb_id=2,
            title='The Matrix',
            release_date=timezone.now().date(),
            original_language=self.language,
            collection=self.collection,
            tmdb_popularity=85.0,
            runtime=136,
            adult=False,
            removed_from_tmdb=False,
        )
        self.movie.genres.add(self.genre)
        self.movie.origin_country.add(self.country)
        self.movie.production_countries.add(self.country)

    def test_movie_creation(self):
        self.assertEqual(self.movie.tmdb_id, 2)
        self.assertEqual(self.movie.title, 'The Matrix')
        self.assertEqual(self.movie.original_language, self.language)
        self.assertEqual(self.movie.collection, self.collection)
        self.assertEqual(self.movie.tmdb_popularity, 85.0)
        self.assertFalse(self.movie.adult)
        self.assertFalse(self.movie.removed_from_tmdb)
        self.assertEqual(self.movie.slug, 'the-matrix')
        self.assertIn(self.genre, self.movie.genres.all())
        self.assertIn(self.country, self.movie.origin_country.all())

    def test_movie_string_representation(self):
        self.assertEqual(str(self.movie), 'The Matrix')

    def test_movie_get_absolute_url(self):
        expected_url = reverse('movie_detail', kwargs={'slug': self.movie.slug})
        self.assertEqual(self.movie.get_absolute_url(), expected_url)

    def test_movie_categorize(self):
        self.movie.categorize(genre_ids=[99, 10770])
        self.assertTrue(self.movie.documentary)
        self.assertTrue(self.movie.tv_movie)
        self.assertFalse(self.movie.short)

    def test_movie_short_film(self):
        short_movie = Movie.objects.create(tmdb_id=3, title='Short Film', runtime=30)
        short_movie.categorize(genre_ids=[])
        self.assertTrue(short_movie.short)

    def test_movie_categorize_runtime_edge_cases(self):
        m1 = Movie.objects.create(tmdb_id=4, title='Edge 40', runtime=40)
        m1.categorize([])
        self.assertTrue(m1.short)
        m2 = Movie.objects.create(tmdb_id=5, title='Edge 0', runtime=0)
        m2.categorize([])
        self.assertFalse(m2.short)

    def test_movie_update_last_modified(self):
        original_date = self.movie.last_update
        self.movie.update_last_modified()
        self.assertNotEqual(self.movie.last_update, original_date)
        self.assertEqual(self.movie.last_update, timezone.now().date())

    def test_movie_status_choices(self):
        self.movie.status = 6
        self.movie.save()
        self.assertEqual(self.movie.status, 6)
        with self.assertRaises(ValidationError):
            self.movie.status = 999
            self.movie.full_clean()

    def test_movie_ordering(self):
        m2 = Movie.objects.create(tmdb_id=6, title='Zeta', tmdb_popularity=999)
        self.assertEqual(list(Movie.objects.all())[0], m2)


class MovieEngagementModelTests(BaseTestCase):
    """Tests for the MovieEngagement model."""

    def setUp(self):
        self.movie = Movie.objects.create(tmdb_id=3, title='Inception')
        self.engagement = MovieEngagement.objects.create(
            movie=self.movie,
            tmdb_rating=8.8,
            tmdb_vote_count=2000,
            tmdb_popularity=95.0,
            lb_rating=4.2,
            lb_vote_count=1000,
            lb_fans=200,
            lb_watched=3000,
            lb_liked=2500,
            imdb_rating=8.9,
            imdb_vote_count=1500,
            imdb_popularity=60,
            kp_rating=8.7,
            kp_vote_count=1200,
        )

    def test_movie_engagement_creation(self):
        self.assertEqual(self.engagement.movie, self.movie)
        self.assertEqual(self.engagement.tmdb_rating, 8.8)
        self.assertEqual(self.engagement.tmdb_vote_count, 2000)
        self.assertEqual(self.engagement.tmdb_popularity, 95.0)
        self.assertEqual(self.engagement.lb_rating, 4.2)
        self.assertEqual(self.engagement.imdb_rating, 8.9)
        self.assertEqual(self.engagement.kp_rating, 8.7)

    def test_movie_engagement_string_representation(self):
        self.assertEqual(str(self.engagement), 'Inception engagement')

    def test_movie_engagement_one_to_one(self):
        with self.assertRaises(IntegrityError):
            MovieEngagement.objects.create(movie=self.movie, tmdb_rating=7.0)


class MovieCastModelTests(BaseTestCase):
    """Tests for the MovieCast model."""

    def setUp(self):
        self.movie = Movie.objects.create(tmdb_id=4, title='Avatar')
        self.person = Person.objects.create(tmdb_id=3, name='Sam Worthington')
        self.cast = MovieCast.objects.create(movie=self.movie, person=self.person, character='Jake Sully', order=1)

    def test_movie_cast_creation(self):
        self.assertEqual(self.cast.movie, self.movie)
        self.assertEqual(self.cast.person, self.person)
        self.assertEqual(self.cast.character, 'Jake Sully')
        self.assertEqual(self.cast.order, 1)

    def test_movie_cast_string_representation(self):
        self.assertEqual(str(self.cast), 'Sam Worthington as "Jake Sully" in «Avatar»')

    def test_movie_cast_unique_together(self):
        with self.assertRaises(IntegrityError):
            MovieCast.objects.create(movie=self.movie, person=self.person, character='Jake Sully', order=2)


class MovieCrewModelTests(BaseTestCase):
    """Tests for the MovieCrew model."""

    def setUp(self):
        self.movie = Movie.objects.create(tmdb_id=5, title='Titanic')
        self.person = Person.objects.create(tmdb_id=4, name='James Cameron')
        self.crew = MovieCrew.objects.create(movie=self.movie, person=self.person, department='Directing', job='Director')

    def test_movie_crew_creation(self):
        self.assertEqual(self.crew.movie, self.movie)
        self.assertEqual(self.crew.person, self.person)
        self.assertEqual(self.crew.department, 'Directing')
        self.assertEqual(self.crew.job, 'Director')

    def test_movie_crew_string_representation(self):
        self.assertEqual(str(self.crew), 'James Cameron as "Director" in «Titanic»')

    def test_movie_crew_unique_together(self):
        with self.assertRaises(IntegrityError):
            MovieCrew.objects.create(movie=self.movie, person=self.person, department='Directing', job='Director')
