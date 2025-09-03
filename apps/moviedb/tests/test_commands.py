import logging
from datetime import date
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import TestCase

from apps.moviedb.models import Collection, Country, Genre, Language, Movie, MovieCast, MovieCrew, Person, ProductionCompany


class UpdateAdultCommandTests(TestCase):
    """Tests for the update_adult command."""

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.collection = Collection.objects.create(tmdb_id=1, name='Adult Collection', adult=True)
        self.company = ProductionCompany.objects.create(tmdb_id=1, name='Adult Company', adult=True)
        self.movie1 = Movie.objects.create(tmdb_id=1, title='Movie 1', adult=False)
        self.movie2 = Movie.objects.create(tmdb_id=2, title='Movie 2', adult=False)
        self.movie3 = Movie.objects.create(tmdb_id=3, title='Movie 3', adult=False)
        self.collection.movies.add(self.movie1)
        self.company.movies.add(self.movie2)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_handle(self):
        call_command('update_adult')
        self.movie1.refresh_from_db()
        self.movie2.refresh_from_db()
        self.movie3.refresh_from_db()
        self.assertTrue(self.movie1.adult)
        self.assertTrue(self.movie2.adult)
        self.assertFalse(self.movie3.adult)

    def test_no_adult_collections_or_companies(self):
        Collection.objects.all().delete()
        ProductionCompany.objects.all().delete()
        call_command('update_adult')
        self.movie1.refresh_from_db()
        self.assertFalse(self.movie1.adult)


class UpdateCollectionsCommandTests(TestCase):
    """Tests for the update_collections command."""

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.sample_collection = {
            'id': 1,
            'name': 'Test Collection',
            'overview': 'Overview',
            'poster_path': '/poster.jpg',
            'backdrop_path': '/backdrop.jpg',
        }
        Movie.objects.all().delete()
        Collection.objects.all().delete()

    def tearDown(self):
        logging.disable(logging.NOTSET)
        Collection.objects.all().delete()
        Movie.objects.all().delete()

    @patch('apps.moviedb.integrations.tmdb.id_exports.IDExport.fetch_ids')
    @patch('apps.moviedb.integrations.tmdb.api.asyncTMDB.fetch_collections_by_id')
    def test_daily_export(self, mock_fetch_collections, mock_fetch_ids):
        mock_fetch_ids.return_value = [1]
        mock_fetch_collections.return_value = ([self.sample_collection], [])
        call_command('update_collections', 'daily_export', '--date', '09_03_2025', '--batch_size', '50', '--language', 'fr-CA')
        collection = Collection.objects.get(tmdb_id=1)
        self.assertEqual(collection.name, 'Test Collection')
        self.assertEqual(collection.overview, 'Overview')
        mock_fetch_ids.assert_called_once_with('collection', published_date='09_03_2025')
        mock_fetch_collections.assert_called_once_with([1], batch_size=50, language='fr-CA')

    @patch('apps.moviedb.integrations.tmdb.id_exports.IDExport.fetch_ids')
    def test_daily_export_no_ids(self, mock_fetch_ids):
        mock_fetch_ids.return_value = []
        call_command('update_collections', 'daily_export')
        count = Collection.objects.count()
        self.assertEqual(count, 0)

    @patch('apps.moviedb.integrations.tmdb.api.asyncTMDB.fetch_collections_by_id')
    def test_daily_export_specific_ids(self, mock_fetch_collections):
        mock_fetch_collections.return_value = ([self.sample_collection], [])
        call_command('update_collections', 'daily_export', '--specific_ids', '1')
        collection = Collection.objects.get(tmdb_id=1)
        self.assertEqual(collection.name, 'Test Collection')
        mock_fetch_collections.assert_called_once_with([1], batch_size=100, language='en-US')

    def test_movies_released(self):
        collection = Collection.objects.create(tmdb_id=1, name="Test Collection")
        movie = Movie.objects.create(tmdb_id=999, title="Test Movie", status=6, removed_from_tmdb=False)
        collection.movies.add(movie)
        call_command('update_collections', 'movies_released')
        collection = Collection.objects.get(tmdb_id=1)
        self.assertEqual(collection.movies_released, 1)

    def test_avg_popularity(self):
        collection = Collection.objects.create(tmdb_id=1, name="Test Collection")
        movie = Movie.objects.create(tmdb_id=999, title="Test Movie", tmdb_popularity=50.0, removed_from_tmdb=False)
        collection.movies.add(movie)
        call_command('update_collections', 'avg_popularity')
        collection = Collection.objects.get(tmdb_id=1)
        self.assertEqual(collection.avg_popularity, 50.0)


class UpdateCompaniesCommandTests(TestCase):
    """Tests for the update_companies command."""

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.sample_company = {'id': 1, 'name': 'Test Company', 'logo_path': '/logo.jpg', 'origin_country': 'US'}
        Country.objects.all().delete()
        Movie.objects.all().delete()
        ProductionCompany.objects.all().delete()
        Country.objects.create(code='US', name='United States')

    def tearDown(self):
        logging.disable(logging.NOTSET)
        ProductionCompany.objects.all().delete()
        Country.objects.all().delete()
        Movie.objects.all().delete()

    @patch('apps.moviedb.integrations.tmdb.id_exports.IDExport.fetch_ids')
    @patch('apps.moviedb.integrations.tmdb.api.asyncTMDB.fetch_companies_by_id')
    def test_daily_export(self, mock_fetch_companies, mock_fetch_ids):
        mock_fetch_ids.return_value = [1]
        mock_fetch_companies.return_value = ([self.sample_company], [])
        call_command('update_companies', 'daily_export', '--date', '09_03_2025', '--batch_size', '50')
        company = ProductionCompany.objects.get(tmdb_id=1)
        self.assertEqual(company.name, 'Test Company')
        self.assertEqual(company.origin_country.code, 'US')
        mock_fetch_ids.assert_called_once_with('company', published_date='09_03_2025')
        mock_fetch_companies.assert_called_once_with([1], batch_size=50)

    @patch('apps.moviedb.integrations.tmdb.id_exports.IDExport.fetch_ids')
    def test_daily_export_no_ids(self, mock_fetch_ids):
        mock_fetch_ids.return_value = []
        call_command('update_companies', 'daily_export')
        count = ProductionCompany.objects.count()
        self.assertEqual(count, 0)

    @patch('apps.moviedb.integrations.tmdb.api.asyncTMDB.fetch_companies_by_id')
    def test_daily_export_specific_ids(self, mock_fetch_companies):
        mock_fetch_companies.return_value = ([self.sample_company], [])
        call_command('update_companies', 'daily_export', '--specific_ids', '1')
        company = ProductionCompany.objects.get(tmdb_id=1)
        self.assertEqual(company.name, 'Test Company')
        mock_fetch_companies.assert_called_once_with([1], batch_size=100)

    def test_movie_count(self):
        company = ProductionCompany.objects.create(tmdb_id=1, name="Test Company")
        movie = Movie.objects.create(tmdb_id=999, title="Test Movie", removed_from_tmdb=False)
        company.movies.add(movie)
        call_command('update_companies', 'movie_count')
        company = ProductionCompany.objects.get(tmdb_id=1)
        self.assertEqual(company.movie_count, 1)


class UpdateCountriesCommandTests(TestCase):
    """Tests for the update_countries command."""

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.sample_country = [{'iso_3166_1': 'US', 'english_name': 'United States'}]

    def tearDown(self):
        logging.disable(logging.NOTSET)
        Country.objects.all().delete()

    @patch('apps.moviedb.integrations.tmdb.api.TMDB.fetch_countries')
    def test_handle(self, mock_fetch_countries):
        mock_fetch_countries.return_value = self.sample_country
        call_command('update_countries', '--language', 'fr-CA')
        country = Country.objects.get(code='US')
        self.assertEqual(country.name, 'United States')
        mock_fetch_countries.assert_called_once_with('fr-CA')

    @patch('apps.moviedb.integrations.tmdb.api.TMDB.fetch_countries')
    def test_handle_empty(self, mock_fetch_countries):
        mock_fetch_countries.return_value = []
        call_command('update_countries')
        self.assertEqual(Country.objects.count(), 0)


class UpdateGenresCommandTests(TestCase):
    """Tests for the update_genres command."""

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.sample_genre = [{'id': 28, 'name': 'Action'}]

    def tearDown(self):
        logging.disable(logging.NOTSET)
        Genre.objects.all().delete()

    @patch('apps.moviedb.integrations.tmdb.api.TMDB.fetch_genres')
    def test_handle(self, mock_fetch_genres):
        mock_fetch_genres.return_value = self.sample_genre
        call_command('update_genres', '--language', 'fr')
        genre = Genre.objects.get(tmdb_id=28)
        self.assertEqual(genre.name, 'Action')
        mock_fetch_genres.assert_called_once_with(language='fr')

    @patch('apps.moviedb.integrations.tmdb.api.TMDB.fetch_genres')
    def test_handle_empty(self, mock_fetch_genres):
        mock_fetch_genres.return_value = []
        call_command('update_genres')
        self.assertEqual(Genre.objects.count(), 0)


class UpdateLanguagesCommandTests(TestCase):
    """Tests for the update_languages command."""

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.sample_language = [{'iso_639_1': 'en', 'english_name': 'English'}]

    def tearDown(self):
        logging.disable(logging.NOTSET)
        Language.objects.all().delete()

    @patch('apps.moviedb.integrations.tmdb.api.TMDB.fetch_languages')
    def test_handle(self, mock_fetch_languages):
        mock_fetch_languages.return_value = self.sample_language
        call_command('update_languages')
        language = Language.objects.get(code='en')
        self.assertEqual(language.name, 'English')
        mock_fetch_languages.assert_called_once()

    @patch('apps.moviedb.integrations.tmdb.api.TMDB.fetch_languages')
    def test_handle_empty(self, mock_fetch_languages):
        mock_fetch_languages.return_value = []
        call_command('update_languages')
        self.assertEqual(Language.objects.count(), 0)


class UpdateMoviesCommandTests(TestCase):
    """Tests for the update_movies command."""

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.sample_movie = {
            'id': 1,
            'title': 'Test Movie',
            'original_title': 'Original',
            'overview': 'Overview',
            'release_date': '2025-01-01',
            'status': 'Released',
            'budget': 1000,
            'revenue': 2000,
            'runtime': 120,
            'popularity': 50.0,
            'adult': False,
            'genres': [{'id': 28, 'name': 'Action'}],
            'spoken_languages': [{'iso_639_1': 'en', 'english_name': 'English'}],
            'origin_country': ['US'],
            'production_countries': [{'iso_3166_1': 'US', 'name': 'United States'}],
            'production_companies': [{'id': 1, 'name': 'Test Company'}],
            'credits': {
                'cast': [{'id': 1, 'character': 'Hero', 'order': 0}],
                'crew': [{'id': 2, 'department': 'Directing', 'job': 'Director'}],
            },
        }
        Movie.objects.all().delete()
        Country.objects.all().delete()
        Language.objects.all().delete()
        ProductionCompany.objects.all().delete()
        Person.objects.all().delete()
        Country.objects.create(code='US', name='United States')
        Language.objects.create(code='en', name='English')
        ProductionCompany.objects.create(tmdb_id=1, name='Test Company')
        Person.objects.create(tmdb_id=1, name='Actor')
        Person.objects.create(tmdb_id=2, name='Director')

    def tearDown(self):
        logging.disable(logging.NOTSET)
        Movie.objects.all().delete()
        Country.objects.all().delete()
        Language.objects.all().delete()
        ProductionCompany.objects.all().delete()
        Person.objects.all().delete()

    @patch('apps.moviedb.integrations.tmdb.id_exports.IDExport.fetch_ids')
    @patch('apps.moviedb.integrations.tmdb.api.asyncTMDB.fetch_movies_by_id')
    def test_daily_export(self, mock_fetch_movies, mock_fetch_ids):
        mock_fetch_ids.return_value = [1]
        mock_fetch_movies.return_value = ([self.sample_movie], [])
        call_command('update_movies', 'daily_export', '--date', '09_03_2025', '--batch_size', '50', '--language', 'fr-CA')
        movie = Movie.objects.get(tmdb_id=1)
        self.assertEqual(movie.title, 'Test Movie')
        self.assertEqual(movie.genres.count(), 1)
        self.assertEqual(MovieCast.objects.filter(movie=movie).count(), 1)
        mock_fetch_ids.assert_called_once_with('movie', published_date='09_03_2025', sort_by_popularity=False)
        mock_fetch_movies.assert_called_once_with([1], batch_size=50, language='fr-CA', append_to_response=['credits'])

    @patch('apps.moviedb.integrations.tmdb.api.asyncTMDB.fetch_changed_ids')
    @patch('apps.moviedb.integrations.tmdb.api.asyncTMDB.fetch_movies_by_id')
    def test_update_changed(self, mock_fetch_movies, mock_fetch_changed_ids):
        Movie.objects.create(tmdb_id=999, title="Test Movie", last_update=date(2025, 8, 1))
        mock_fetch_changed_ids.return_value = ({999}, date(2025, 9, 3))
        sample_movie = self.sample_movie.copy()
        sample_movie['id'] = 999
        mock_fetch_movies.return_value = ([sample_movie], [])
        call_command('update_movies', 'update_changed', '--days', '5')
        movie = Movie.objects.get(tmdb_id=999)
        self.assertEqual(movie.title, 'Test Movie')
        mock_fetch_changed_ids.assert_called_once_with('movie', days=5)

    @patch('apps.moviedb.integrations.tmdb.api.asyncTMDB.fetch_top_rated_movie_ids')
    @patch('apps.moviedb.integrations.tmdb.api.asyncTMDB.fetch_movies_by_id')
    def test_add_top_rated(self, mock_fetch_movies, mock_fetch_top_rated):
        mock_fetch_top_rated.return_value = [1]
        mock_fetch_movies.return_value = ([self.sample_movie], [])
        call_command('update_movies', 'add_top_rated')
        movie = Movie.objects.get(tmdb_id=1)
        self.assertEqual(movie.title, 'Test Movie')
        mock_fetch_top_rated.assert_called_once_with(last_page=500)

    @patch('apps.moviedb.integrations.tmdb.api.asyncTMDB.fetch_movies_by_id')
    def test_specific_ids(self, mock_fetch_movies):
        mock_fetch_movies.return_value = ([self.sample_movie], [])
        call_command('update_movies', 'specific_ids', '--ids', '1')
        movie = Movie.objects.get(tmdb_id=1)
        self.assertEqual(movie.title, 'Test Movie')
        mock_fetch_movies.assert_called_once_with([1], batch_size=100, language='en-US', append_to_response=['credits'])

    def test_specific_ids_no_ids(self):
        with self.assertRaises(CommandError):
            call_command('update_movies', 'specific_ids')


class UpdatePeopleCommandTests(TestCase):
    """Tests for the update_people command."""

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.sample_person = {
            'id': 1,
            'name': 'Test Person',
            'imdb_id': 'nm123',
            'known_for_department': 'Acting',
            'biography': 'Bio',
            'place_of_birth': 'City',
            'gender': 2,
            'birthday': '1980-01-01',
            'profile_path': '/profile.jpg',
            'popularity': 10.0,
            'adult': False,
        }
        Person.objects.all().delete()
        Movie.objects.all().delete()

    def tearDown(self):
        logging.disable(logging.NOTSET)
        Person.objects.all().delete()
        Movie.objects.all().delete()

    @patch('apps.moviedb.integrations.tmdb.id_exports.IDExport.fetch_ids')
    @patch('apps.moviedb.integrations.tmdb.api.asyncTMDB.fetch_people_by_id')
    def test_daily_export(self, mock_fetch_people, mock_fetch_ids):
        mock_fetch_ids.return_value = [1]
        mock_fetch_people.return_value = ([self.sample_person], [])
        call_command('update_people', 'daily_export', '--date', '09_03_2025', '--batch_size', '50')
        person = Person.objects.get(tmdb_id=1)
        self.assertEqual(person.name, 'Test Person')
        self.assertEqual(person.gender, 'M')
        mock_fetch_ids.assert_called_once_with('person', published_date='09_03_2025', sort_by_popularity=False)
        mock_fetch_people.assert_called_once_with([1], batch_size=50, language='en-US')

    @patch('apps.moviedb.integrations.tmdb.api.asyncTMDB.fetch_changed_ids')
    @patch('apps.moviedb.integrations.tmdb.api.asyncTMDB.fetch_people_by_id')
    def test_update_changed(self, mock_fetch_people, mock_fetch_changed_ids):
        Person.objects.create(tmdb_id=999, name="Old Person", last_update=date(2025, 8, 1))
        mock_fetch_changed_ids.return_value = ({999}, date(2025, 9, 3))
        sample_person = self.sample_person.copy()
        sample_person['id'] = 999
        mock_fetch_people.return_value = ([sample_person], [])
        call_command('update_people', 'update_changed', '--days', '5')
        person = Person.objects.get(tmdb_id=999)
        self.assertEqual(person.name, 'Test Person')
        mock_fetch_changed_ids.assert_called_once_with('person', days=5)

    @patch('apps.moviedb.integrations.tmdb.api.asyncTMDB.fetch_people_by_id')
    def test_specific_ids(self, mock_fetch_people):
        mock_fetch_people.return_value = ([self.sample_person], [])
        call_command('update_people', 'specific_ids', '--ids', '1')
        person = Person.objects.get(tmdb_id=1)
        self.assertEqual(person.name, 'Test Person')
        mock_fetch_people.assert_called_once_with([1], batch_size=100, language='en-US')

    def test_specific_ids_no_ids(self):
        with self.assertRaises(CommandError):
            call_command('update_people', 'specific_ids')

    def test_roles_count(self):
        person = Person.objects.create(tmdb_id=1, name="Test Person")
        movie = Movie.objects.create(tmdb_id=999, title="Test Movie", removed_from_tmdb=False)
        MovieCast.objects.create(movie=movie, person=person, character="Hero")
        MovieCrew.objects.create(movie=movie, person=person, department="Directing", job="Director")
        call_command('update_people', 'roles_count')
        person = Person.objects.get(tmdb_id=1)
        self.assertEqual(person.cast_roles_count, 1)
        self.assertEqual(person.crew_roles_count, 1)


class UpdatePopularityCommandTests(TestCase):
    """Tests for the update_popularity command."""

    def setUp(self):
        logging.disable(logging.CRITICAL)
        Movie.objects.create(tmdb_id=999, title="Test Movie", tmdb_popularity=10.0)
        Person.objects.create(tmdb_id=999, name="Test Person", tmdb_popularity=5.0)

    def tearDown(self):
        logging.disable(logging.NOTSET)
        Movie.objects.all().delete()
        Person.objects.all().delete()

    @patch('apps.moviedb.integrations.tmdb.id_exports.IDExport.fetch_ids')
    def test_update_movie_popularity(self, mock_fetch_ids):
        mock_fetch_ids.return_value = [(999, 20.0)]
        call_command('update_popularity', 'movie', '--date', '09_03_2025', '--limit', '1')
        movie = Movie.objects.get(tmdb_id=999)
        self.assertEqual(movie.tmdb_popularity, 20.0)
        mock_fetch_ids.assert_called_once_with('movie', published_date='09_03_2025', sort_by_popularity=True, include_popularity=True)

    @patch('apps.moviedb.integrations.tmdb.id_exports.IDExport.fetch_ids')
    def test_update_person_popularity(self, mock_fetch_ids):
        mock_fetch_ids.return_value = [(999, 15.0)]
        call_command('update_popularity', 'person', '--limit', '1')
        person = Person.objects.get(tmdb_id=999)
        self.assertEqual(person.tmdb_popularity, 15.0)
        mock_fetch_ids.assert_called_once_with('person', published_date=None, sort_by_popularity=True, include_popularity=True)

    @patch('apps.moviedb.integrations.tmdb.id_exports.IDExport.fetch_ids')
    def test_no_ids(self, mock_fetch_ids):
        mock_fetch_ids.return_value = []
        call_command('update_popularity', 'movie')
        movie = Movie.objects.get(tmdb_id=999)
        self.assertEqual(movie.tmdb_popularity, 10.0)


class UpdateRemovedCommandTests(TestCase):
    """Tests for the update_removed command."""

    def setUp(self):
        logging.disable(logging.CRITICAL)
        Movie.objects.all().delete()
        Person.objects.all().delete()
        Collection.objects.all().delete()
        ProductionCompany.objects.all().delete()
        Movie.objects.create(tmdb_id=999, title="Test Movie", removed_from_tmdb=False)
        Person.objects.create(tmdb_id=999, name="Test Person", removed_from_tmdb=False)
        Collection.objects.create(tmdb_id=999, name="Test Collection", removed_from_tmdb=False)
        ProductionCompany.objects.create(tmdb_id=999, name="Test Company", removed_from_tmdb=False)

    def tearDown(self):
        logging.disable(logging.NOTSET)
        Movie.objects.all().delete()
        Person.objects.all().delete()
        Collection.objects.all().delete()
        ProductionCompany.objects.all().delete()

    @patch('apps.moviedb.integrations.tmdb.id_exports.IDExport.fetch_ids')
    @patch('apps.moviedb.integrations.tmdb.api.asyncTMDB.fetch_movies_by_id')
    def test_update_removed_movies(self, mock_fetch_movies, mock_fetch_ids):
        mock_fetch_ids.return_value = []
        mock_fetch_movies.return_value = ([], [999])
        call_command('update_removed', 'movie')
        movie = Movie.objects.get(tmdb_id=999)
        self.assertTrue(movie.removed_from_tmdb)
        mock_fetch_ids.assert_called_once_with('movie')
        mock_fetch_movies.assert_called_once_with([999], batch_size=1000)

    @patch('apps.moviedb.integrations.tmdb.api.asyncTMDB.fetch_people_by_id')
    @patch('apps.moviedb.integrations.tmdb.id_exports.IDExport.fetch_ids')
    def test_update_removed_people(self, mock_fetch_ids, mock_fetch_people):
        mock_fetch_ids.return_value = []
        mock_fetch_people.return_value = ([], [999])
        call_command('update_removed', 'person')
        person = Person.objects.get(tmdb_id=999)
        self.assertTrue(person.removed_from_tmdb)
        mock_fetch_ids.assert_called_once_with('person')
        mock_fetch_people.assert_called_once_with([999], batch_size=1000)

    def test_invalid_data_type(self):
        with self.assertRaises(CommandError):
            call_command('update_removed', 'invalid')
