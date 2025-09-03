from django.test import TestCase
from django.urls import resolve, reverse

from apps.moviedb.views import (
    CollectionDetailView,
    CollectionsListView,
    CompanyListView,
    CountryListView,
    LanguageListView,
    MovieDetailView,
    MovieListView,
    PeopleListView,
    PersonDetailView,
)


class URLTests(TestCase):
    """Tests for URL patterns in moviedb.urls."""

    def test_main_url(self):
        url = reverse('main')
        self.assertEqual(url, '/')
        resolver = resolve('/')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'main')

    def test_movies_url(self):
        url = reverse('movies')
        self.assertEqual(url, '/movies/')
        resolver = resolve('/movies/')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'movies')

    def test_movies_sort_url(self):
        url = reverse('movies_sort', kwargs={'sort_by': 'release_date'})
        self.assertEqual(url, '/movies/by/release_date')
        resolver = resolve('/movies/by/release_date')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'movies_sort')
        self.assertEqual(resolver.kwargs['sort_by'], 'release_date')

    def test_movies_decade_url(self):
        url = reverse('movies_decade', kwargs={'sort_by': 'release_date', 'decade': '2020s'})
        self.assertEqual(url, '/movies/by/release_date/decade/2020s')
        resolver = resolve('/movies/by/release_date/decade/2020s')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'movies_decade')
        self.assertEqual(resolver.kwargs['sort_by'], 'release_date')
        self.assertEqual(resolver.kwargs['decade'], '2020s')

    def test_movies_year_url(self):
        url = reverse('movies_year', kwargs={'sort_by': 'release_date', 'decade': '2020s', 'year': 2023})
        self.assertEqual(url, '/movies/by/release_date/decade/2020s/year/2023')
        resolver = resolve('/movies/by/release_date/decade/2020s/year/2023')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'movies_year')
        self.assertEqual(resolver.kwargs['sort_by'], 'release_date')
        self.assertEqual(resolver.kwargs['decade'], '2020s')
        self.assertEqual(resolver.kwargs['year'], 2023)

    def test_movie_detail_url(self):
        url = reverse('movie_detail', kwargs={'slug': 'the-matrix'})
        self.assertEqual(url, '/movie/the-matrix/')
        resolver = resolve('/movie/the-matrix/')
        self.assertEqual(resolver.func.view_class, MovieDetailView)
        self.assertEqual(resolver.view_name, 'movie_detail')
        self.assertEqual(resolver.kwargs['slug'], 'the-matrix')

    def test_other_url(self):
        url = reverse('other')
        self.assertEqual(url, '/other/')
        resolver = resolve('/other/')
        self.assertEqual(resolver.func.view_class, CountryListView)
        self.assertEqual(resolver.view_name, 'other')

    def test_countries_url(self):
        url = reverse('countries')
        self.assertEqual(url, '/countries/')
        resolver = resolve('/countries/')
        self.assertEqual(resolver.func.view_class, CountryListView)
        self.assertEqual(resolver.view_name, 'countries')

    def test_languages_url(self):
        url = reverse('languages')
        self.assertEqual(url, '/languages/')
        resolver = resolve('/languages/')
        self.assertEqual(resolver.func.view_class, LanguageListView)
        self.assertEqual(resolver.view_name, 'languages')

    def test_collections_url(self):
        url = reverse('collections')
        self.assertEqual(url, '/collections/')
        resolver = resolve('/collections/')
        self.assertEqual(resolver.func.view_class, CollectionsListView)
        self.assertEqual(resolver.view_name, 'collections')

    def test_collection_detail_url(self):
        url = reverse('collection_detail', kwargs={'slug': 'star-wars'})
        self.assertEqual(url, '/collection/star-wars/')
        resolver = resolve('/collection/star-wars/')
        self.assertEqual(resolver.func.view_class, CollectionDetailView)
        self.assertEqual(resolver.view_name, 'collection_detail')
        self.assertEqual(resolver.kwargs['slug'], 'star-wars')

    def test_companies_url(self):
        url = reverse('companies')
        self.assertEqual(url, '/production-companies/')
        resolver = resolve('/production-companies/')
        self.assertEqual(resolver.func.view_class, CompanyListView)
        self.assertEqual(resolver.view_name, 'companies')

    def test_companies_sort_url(self):
        url = reverse('companies_sort', kwargs={'sort_by': 'movie_count'})
        self.assertEqual(url, '/production-companies/by/movie_count')
        resolver = resolve('/production-companies/by/movie_count')
        self.assertEqual(resolver.func.view_class, CompanyListView)
        self.assertEqual(resolver.view_name, 'companies_sort')
        self.assertEqual(resolver.kwargs['sort_by'], 'movie_count')

    def test_movies_country_url(self):
        url = reverse('movies_country', kwargs={'slug': 'united-states'})
        self.assertEqual(url, '/movies-by-country/united-states/')
        resolver = resolve('/movies-by-country/united-states/')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'movies_country')
        self.assertEqual(resolver.kwargs['slug'], 'united-states')

    def test_movies_decade_country_url(self):
        url = reverse('movies_decade_country', kwargs={'slug': 'united-states', 'sort_by': 'release_date', 'decade': '2020s'})
        self.assertEqual(url, '/movies-by-country/united-states/by/release_date/decade/2020s/')
        resolver = resolve('/movies-by-country/united-states/by/release_date/decade/2020s/')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'movies_decade_country')
        self.assertEqual(resolver.kwargs['slug'], 'united-states')
        self.assertEqual(resolver.kwargs['sort_by'], 'release_date')
        self.assertEqual(resolver.kwargs['decade'], '2020s')

    def test_movies_year_country_url(self):
        url = reverse('movies_year_country', kwargs={'slug': 'united-states', 'sort_by': 'release_date', 'decade': '2020s', 'year': 2023})
        self.assertEqual(url, '/movies-by-country/united-states/by/release_date/decade/2020s/year/2023/')
        resolver = resolve('/movies-by-country/united-states/by/release_date/decade/2020s/year/2023/')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'movies_year_country')
        self.assertEqual(resolver.kwargs['slug'], 'united-states')
        self.assertEqual(resolver.kwargs['sort_by'], 'release_date')
        self.assertEqual(resolver.kwargs['decade'], '2020s')
        self.assertEqual(resolver.kwargs['year'], 2023)

    def test_movies_language_url(self):
        url = reverse('movies_language', kwargs={'slug': 'english'})
        self.assertEqual(url, '/movies-by-language/english')
        resolver = resolve('/movies-by-language/english')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'movies_language')
        self.assertEqual(resolver.kwargs['slug'], 'english')

    def test_movies_decade_language_url(self):
        url = reverse('movies_decade_language', kwargs={'slug': 'english', 'sort_by': 'release_date', 'decade': '2020s'})
        self.assertEqual(url, '/movies-by-language/english/by/release_date/decade/2020s/')
        resolver = resolve('/movies-by-language/english/by/release_date/decade/2020s/')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'movies_decade_language')
        self.assertEqual(resolver.kwargs['slug'], 'english')
        self.assertEqual(resolver.kwargs['sort_by'], 'release_date')
        self.assertEqual(resolver.kwargs['decade'], '2020s')

    def test_movies_year_language_url(self):
        url = reverse('movies_year_language', kwargs={'slug': 'english', 'sort_by': 'release_date', 'decade': '2020s', 'year': 2023})
        self.assertEqual(url, '/movies-by-language/english/by/release_date/decade/2020s/year/2023/')
        resolver = resolve('/movies-by-language/english/by/release_date/decade/2020s/year/2023/')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'movies_year_language')
        self.assertEqual(resolver.kwargs['slug'], 'english')
        self.assertEqual(resolver.kwargs['sort_by'], 'release_date')
        self.assertEqual(resolver.kwargs['decade'], '2020s')
        self.assertEqual(resolver.kwargs['year'], 2023)

    def test_movies_company_url(self):
        url = reverse('movies_company', kwargs={'slug': 'paramount-pictures'})
        self.assertEqual(url, '/production-company/paramount-pictures/')
        resolver = resolve('/production-company/paramount-pictures/')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'movies_company')
        self.assertEqual(resolver.kwargs['slug'], 'paramount-pictures')

    def test_movies_decade_company_url(self):
        url = reverse('movies_decade_company', kwargs={'slug': 'paramount-pictures', 'sort_by': 'release_date', 'decade': '2020s'})
        self.assertEqual(url, '/production-company/paramount-pictures/by/release_date/decade/2020s/')
        resolver = resolve('/production-company/paramount-pictures/by/release_date/decade/2020s/')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'movies_decade_company')
        self.assertEqual(resolver.kwargs['slug'], 'paramount-pictures')
        self.assertEqual(resolver.kwargs['sort_by'], 'release_date')
        self.assertEqual(resolver.kwargs['decade'], '2020s')

    def test_movies_year_company_url(self):
        url = reverse(
            'movies_year_company', kwargs={'slug': 'paramount-pictures', 'sort_by': 'release_date', 'decade': '2020s', 'year': 2023}
        )
        self.assertEqual(url, '/production-company/paramount-pictures/by/release_date/decade/2020s/year/2023/')
        resolver = resolve('/production-company/paramount-pictures/by/release_date/decade/2020s/year/2023/')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'movies_year_company')
        self.assertEqual(resolver.kwargs['slug'], 'paramount-pictures')
        self.assertEqual(resolver.kwargs['sort_by'], 'release_date')
        self.assertEqual(resolver.kwargs['decade'], '2020s')
        self.assertEqual(resolver.kwargs['year'], 2023)

    def test_movies_genre_url(self):
        url = reverse('movies_genre', kwargs={'slug': 'action'})
        self.assertEqual(url, '/genre/action/')
        resolver = resolve('/genre/action/')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'movies_genre')
        self.assertEqual(resolver.kwargs['slug'], 'action')

    def test_movies_decade_genre_url(self):
        url = reverse('movies_decade_genre', kwargs={'slug': 'action', 'sort_by': 'release_date', 'decade': '2020s'})
        self.assertEqual(url, '/genre/action/by/release_date/decade/2020s/')
        resolver = resolve('/genre/action/by/release_date/decade/2020s/')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'movies_decade_genre')
        self.assertEqual(resolver.kwargs['slug'], 'action')
        self.assertEqual(resolver.kwargs['sort_by'], 'release_date')
        self.assertEqual(resolver.kwargs['decade'], '2020s')

    def test_movies_year_genre_url(self):
        url = reverse('movies_year_genre', kwargs={'slug': 'action', 'sort_by': 'release_date', 'decade': '2020s', 'year': 2023})
        self.assertEqual(url, '/genre/action/by/release_date/decade/2020s/year/2023/')
        resolver = resolve('/genre/action/by/release_date/decade/2020s/year/2023/')
        self.assertEqual(resolver.func.view_class, MovieListView)
        self.assertEqual(resolver.view_name, 'movies_year_genre')
        self.assertEqual(resolver.kwargs['slug'], 'action')
        self.assertEqual(resolver.kwargs['sort_by'], 'release_date')
        self.assertEqual(resolver.kwargs['decade'], '2020s')
        self.assertEqual(resolver.kwargs['year'], 2023)

    def test_people_url(self):
        url = reverse('people')
        self.assertEqual(url, '/people/')
        resolver = resolve('/people/')
        self.assertEqual(resolver.func.view_class, PeopleListView)
        self.assertEqual(resolver.view_name, 'people')

    def test_people_sort_url(self):
        url = reverse('people_sort', kwargs={'sort_by': 'tmdb_popularity'})
        self.assertEqual(url, '/people/by/tmdb_popularity/')
        resolver = resolve('/people/by/tmdb_popularity/')
        self.assertEqual(resolver.func.view_class, PeopleListView)
        self.assertEqual(resolver.view_name, 'people_sort')
        self.assertEqual(resolver.kwargs['sort_by'], 'tmdb_popularity')

    def test_people_department_sort_url(self):
        url = reverse('people_department_sort', kwargs={'department': 'directing', 'sort_by': 'tmdb_popularity'})
        self.assertEqual(url, '/people/department/directing/by/tmdb_popularity/')
        resolver = resolve('/people/department/directing/by/tmdb_popularity/')
        self.assertEqual(resolver.func.view_class, PeopleListView)
        self.assertEqual(resolver.view_name, 'people_department_sort')
        self.assertEqual(resolver.kwargs['department'], 'directing')
        self.assertEqual(resolver.kwargs['sort_by'], 'tmdb_popularity')

    def test_person_detail_url(self):
        url = reverse('person_detail', kwargs={'slug': 'john-doe'})
        self.assertEqual(url, '/person/john-doe/')
        resolver = resolve('/person/john-doe/')
        self.assertEqual(resolver.func.view_class, PersonDetailView)
        self.assertEqual(resolver.view_name, 'person_detail')
        self.assertEqual(resolver.kwargs['slug'], 'john-doe')

    def test_person_job_url(self):
        url = reverse('person_job', kwargs={'slug': 'john-doe', 'job': 'director'})
        self.assertEqual(url, '/person/john-doe/director')
        resolver = resolve('/person/john-doe/director')
        self.assertEqual(resolver.func.view_class, PersonDetailView)
        self.assertEqual(resolver.view_name, 'person_job')
        self.assertEqual(resolver.kwargs['slug'], 'john-doe')
        self.assertEqual(resolver.kwargs['job'], 'director')

    def test_person_sort_url(self):
        url = reverse('person_sort', kwargs={'slug': 'john-doe', 'job': 'director', 'sort_by': 'release_date'})
        self.assertEqual(url, '/person/john-doe/director/by/release_date')
        resolver = resolve('/person/john-doe/director/by/release_date')
        self.assertEqual(resolver.func.view_class, PersonDetailView)
        self.assertEqual(resolver.view_name, 'person_sort')
        self.assertEqual(resolver.kwargs['slug'], 'john-doe')
        self.assertEqual(resolver.kwargs['job'], 'director')
        self.assertEqual(resolver.kwargs['sort_by'], 'release_date')
