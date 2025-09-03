from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.moviedb.models import Collection, Country, Genre, Language, Movie, MovieCast, MovieCrew, Person, ProductionCompany
from apps.services.utils import VERBOSE_SORT_BY_MOVIES, GenreIDs


class BaseTestCase(TestCase):
    """Base test case with common setup for views."""

    @classmethod
    def setUpTestData(cls):
        cls.client = Client()
        cls.country = Country.objects.create(code='US', name='United States', slug='united-states')
        cls.language = Language.objects.create(code='EN', name='English', slug='english')
        cls.genre = Genre.objects.create(tmdb_id=GenreIDs.ACTION, name='Action', slug='action')
        cls.company = ProductionCompany.objects.create(tmdb_id=1, name='Paramount Pictures', slug='paramount-pictures')
        cls.collection = Collection.objects.create(
            tmdb_id=1,
            name='Star Wars Collection',
            slug='star-wars-collection',
            adult=False,
            movies_released=2,
        )
        cls.person = Person.objects.create(
            tmdb_id=1, name='John Doe', slug='john-doe', known_for_department='Directing', tmdb_popularity=75.0
        )
        cls.movie = Movie.objects.create(
            tmdb_id=1,
            title='The Matrix',
            slug='the-matrix',
            release_date=timezone.datetime(1999, 3, 31).date(),
            original_language=cls.language,
            collection=cls.collection,
            tmdb_popularity=85.0,
            runtime=136,
            status=6,
        )
        cls.movie2 = Movie.objects.create(
            tmdb_id=2,
            title='The Matrix Reloaded',
            slug='the-matrix-reloaded',
            release_date=timezone.datetime(2003, 5, 15).date(),
            original_language=cls.language,
            collection=cls.collection,
            tmdb_popularity=80.0,
            runtime=138,
            status=6,
        )
        cls.movie.genres.add(cls.genre)
        cls.movie2.genres.add(cls.genre)
        cls.movie.origin_country.add(cls.country)
        cls.movie2.origin_country.add(cls.country)
        cls.movie.production_countries.add(cls.country)
        cls.movie2.production_countries.add(cls.country)
        cls.movie.production_companies.add(cls.company)
        cls.movie2.production_companies.add(cls.company)
        cls.cast = MovieCast.objects.create(movie=cls.movie, person=cls.person, character='Neo', order=1)
        cls.crew = MovieCrew.objects.create(movie=cls.movie, person=cls.person, department='Directing', job='Director')

    def setUp(self):
        self.client.get('/')


class MovieListViewTests(BaseTestCase):
    """Tests for the MovieListView."""

    def test_get_main_view(self):
        response = self.client.get(reverse('main'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/main.html')
        self.assertEqual(response.context['title'], 'Discover Movies')
        self.assertEqual(response.context['list_type'], 'movies')
        self.assertIn(self.movie, response.context['movies'])
        self.assertEqual(response.context['sort_by'], '-tmdb_popularity')
        self.assertEqual(response.context['decade'], 'any')

    def test_get_movies_sort(self):
        response = self.client.get(reverse('movies_sort', kwargs={'sort_by': 'release_date'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/main.html')
        self.assertEqual(response.context['sort_by'], 'release_date')
        self.assertEqual(response.context['verbose_sort_by'], VERBOSE_SORT_BY_MOVIES['release_date'])

    def test_get_movies_decade(self):
        response = self.client.get(reverse('movies_decade', kwargs={'sort_by': 'release_date', 'decade': '1990s'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/main.html')
        self.assertEqual(response.context['decade'], '1990s')
        self.assertIn(self.movie, response.context['movies'])

    def test_get_movies_year(self):
        response = self.client.get(reverse('movies_year', kwargs={'sort_by': 'release_date', 'decade': '1990s', 'year': 1999}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/main.html')
        self.assertEqual(response.context['year'], 1999)
        self.assertEqual(response.context['decade'], '1990s')
        self.assertIn(self.movie, response.context['movies'])

    def test_get_movies_country(self):
        response = self.client.get(reverse('movies_country', kwargs={'slug': 'united-states'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/main.html')
        self.assertEqual(response.context['title'], 'United States')
        self.assertEqual(response.context['country'], self.country)
        self.assertIn(self.movie, response.context['movies'])

    def test_get_movies_language_htmx(self):
        response = self.client.get(reverse('movies_language', kwargs={'slug': 'english'}), {'query': 'matrix'}, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/movies/partials/content_grid.html')
        self.assertEqual(response.context['language'], self.language)
        self.assertIn(self.movie, response.context['movies'])

    def test_get_movies_with_filters(self):
        response = self.client.get(reverse('movies'), {'filter': ['hide_documentary']}, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/movies/partials/content_grid.html')
        self.assertEqual(response.context['filtered'], ['hide_documentary'])
        self.assertEqual(response.context['filter_dict']['hide_documentary'], 'Hide Documentary')

    def test_get_movies_with_genres(self):
        response = self.client.get(reverse('movies_genre', kwargs={'slug': 'action'}), {'genres': ['Action']}, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/movies/partials/content_grid.html')
        self.assertEqual(response.context['genre'], self.genre)
        self.assertIn(self.movie, response.context['movies'])
        self.assertEqual(response.context['checked_genres'], ['Action'])


class MovieDetailViewTests(BaseTestCase):
    """Tests for the MovieDetailView."""

    def test_get_movie_detail(self):
        response = self.client.get(reverse('movie_detail', kwargs={'slug': 'the-matrix'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/movies/movie_detail.html')
        self.assertEqual(response.context['movie'], self.movie)
        self.assertEqual(response.context['title'], 'The Matrix - 1999')
        self.assertIn(self.genre, response.context['genres'])
        self.assertIn(self.country, response.context['countries'])
        self.assertIn(self.company, response.context['companies'])
        self.assertIn(self.cast, response.context['cast'])
        self.assertIn(self.person.tmdb_id, response.context['crew_map']['Director']['objs'])

    def test_get_movie_detail_invalid_slug(self):
        response = self.client.get(reverse('movie_detail', kwargs={'slug': 'invalid'}))
        self.assertEqual(response.status_code, 404)


class CountryListViewTests(BaseTestCase):
    """Tests for the CountryListView."""

    def test_get_countries(self):
        response = self.client.get(reverse('countries'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/other.html')
        self.assertEqual(response.context['title'], 'Countries')
        self.assertEqual(response.context['list_type'], 'countries')
        self.assertIn(self.country, response.context['countries'])

    def test_get_countries_search(self):
        response = self.client.get(reverse('countries'), {'query': 'united'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/other/partials/content_grid.html')
        self.assertIn(self.country, response.context['countries'])


class LanguageListViewTests(BaseTestCase):
    """Tests for the LanguageListView."""

    def test_get_languages(self):
        response = self.client.get(reverse('languages'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/other.html')
        self.assertEqual(response.context['title'], 'Languages')
        self.assertEqual(response.context['list_type'], 'languages')
        self.assertIn(self.language, response.context['languages'])

    def test_get_languages_search_htmx(self):
        response = self.client.get(reverse('languages'), {'query': 'english'}, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/other/partials/content_grid.html')
        self.assertIn(self.language, response.context['languages'])


class CollectionsListViewTests(BaseTestCase):
    """Tests for the CollectionsListView."""

    def test_get_collections(self):
        response = self.client.get(reverse('collections'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/other.html')
        self.assertEqual(response.context['title'], 'Collections')
        self.assertEqual(response.context['list_type'], 'collections')
        self.assertIn(self.collection, response.context['collections'])

    def test_get_collections_search(self):
        response = self.client.get(reverse('collections'), {'query': 'star wars'}, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/other/partials/content_grid.html')
        self.assertIn(self.collection, response.context['collections'])


class CollectionDetailViewTests(BaseTestCase):
    """Tests for the CollectionDetailView."""

    def test_get_collection_detail(self):
        response = self.client.get(reverse('collection_detail', kwargs={'slug': 'star-wars-collection'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/other/collection_detail.html')
        self.assertEqual(response.context['collection'], self.collection)
        self.assertEqual(response.context['title'], 'Star Wars Collection')
        self.assertIn(self.movie, response.context['movies'])

    def test_get_collection_detail_invalid_slug(self):
        response = self.client.get(reverse('collection_detail', kwargs={'slug': 'invalid'}))
        self.assertEqual(response.status_code, 404)


class CompanyListViewTests(BaseTestCase):
    """Tests for the CompanyListView."""

    def test_get_companies(self):
        response = self.client.get(reverse('companies'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/other.html')
        self.assertEqual(response.context['title'], 'Production Companies')
        self.assertEqual(response.context['list_type'], 'companies')
        self.assertIn(self.company, response.context['companies'])

    def test_get_companies_sort(self):
        response = self.client.get(reverse('companies_sort', kwargs={'sort_by': 'movie_count'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/other.html')
        self.assertEqual(response.context['sort_by'], 'movie_count')
        self.assertEqual(response.context['verbose_sort_by'], 'Number of movies ↓')

    def test_get_companies_search(self):
        response = self.client.get(reverse('companies'), {'query': 'paramount'}, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/other/partials/content_grid.html')
        self.assertIn(self.company, response.context['companies'])


class PeopleListViewTests(BaseTestCase):
    """Tests for the PeopleListView."""

    def test_get_people(self):
        response = self.client.get(reverse('people'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/main.html')
        self.assertEqual(response.context['title'], 'People')
        self.assertEqual(response.context['list_type'], 'people')
        self.assertIn(self.person, response.context['people'])

    def test_get_people_department_sort(self):
        response = self.client.get(reverse('people_department_sort', kwargs={'department': 'directing', 'sort_by': 'tmdb_popularity'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/main.html')
        self.assertEqual(response.context['department'], 'directing')
        self.assertEqual(response.context['verbose_department'], 'Directing')
        self.assertIn(self.person, response.context['people'])

    def test_get_people_search(self):
        response = self.client.get(reverse('people'), {'query': 'john'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/main.html')
        self.assertIn(self.person, response.context['people'])


class PersonDetailViewTests(BaseTestCase):
    """Tests for the PersonDetailView."""

    def test_get_person_detail(self):
        response = self.client.get(reverse('person_detail', kwargs={'slug': 'john-doe'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/people/person_detail.html')
        self.assertEqual(response.context['person'], self.person)
        self.assertEqual(response.context['title'], 'John Doe')
        self.assertEqual(response.context['known_for'], 'Directing')
        self.assertIn('Director', response.context['roles_map'])
        self.assertIn('Actor', response.context['roles_map'])
        self.assertIn(self.movie.tmdb_id, response.context['roles_map']['Director']['objs'])
        self.assertIn(self.movie.tmdb_id, response.context['roles_map']['Actor']['objs'])

    def test_get_person_job(self):
        response = self.client.get(reverse('person_job', kwargs={'slug': 'john-doe', 'job': 'director'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/people/person_detail.html')
        self.assertEqual(response.context['role_type'], 'Director')
        self.assertIn(self.movie, response.context['movies'])

    def test_get_person_sort(self):
        response = self.client.get(reverse('person_sort', kwargs={'slug': 'john-doe', 'job': 'director', 'sort_by': 'release_date'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'moviedb/people/person_detail.html')
        self.assertEqual(response.context['sort_by'], 'release_date')
        self.assertEqual(response.context['verbose_sort_by'], VERBOSE_SORT_BY_MOVIES['release_date'])

    def test_get_person_detail_invalid_slug(self):
        response = self.client.get(reverse('person_detail', kwargs={'slug': 'invalid'}))
        self.assertEqual(response.status_code, 404)
